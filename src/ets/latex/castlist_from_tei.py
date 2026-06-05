from __future__ import annotations

from os import PathLike
from pathlib import Path
import re

from lxml import etree

from .escaping import escape_latex_text


def tei_castlist_to_latex(xml_input: str | PathLike[str]) -> str:
    """Convert a TEI castList/dramatis personae source to a LaTeX fragment.

    The converter returns an internal standard LaTeX fragment only. If no
    ``castList`` is present, it returns an explicit LaTeX comment instead of
    raising, so a future PDF build can remain non-blocking for missing dramatis
    personae data.
    """
    root = _parse_xml_input(xml_input)
    cast_list = _find_cast_list(root)
    if cast_list is None:
        return "% DRAMATIS PERSONAE: no castList found.\n"

    blocks: list[str] = []
    head = _first_direct_child(cast_list, "head")
    if head is not None:
        blocks.append(rf"\subsection*{{{_normalize_inline(_render_inline(head))}}}")

    items = _render_cast_list_items(cast_list)
    if items:
        blocks.append("\\begin{description}\n" + "\n".join(items) + "\n\\end{description}")

    fragment = "\n\n".join(block for block in blocks if block.strip()).rstrip()
    return f"{fragment}\n" if fragment else ""


def _parse_xml_input(xml_input: str | PathLike[str]) -> etree._Element:
    if isinstance(xml_input, PathLike):
        return etree.parse(str(xml_input)).getroot()

    text = str(xml_input)
    if text.lstrip().startswith("<"):
        return etree.fromstring(text.encode("utf-8"))

    candidate = Path(text)
    if candidate.exists():
        return etree.parse(str(candidate)).getroot()
    return etree.fromstring(text.encode("utf-8"))


def _find_cast_list(root: etree._Element) -> etree._Element | None:
    if _local_name(root) == "castList":
        return root

    front_matches = root.xpath(
        ".//*[local-name()='text']/*[local-name()='front']//*[local-name()='castList'][1]"
    )
    if front_matches and isinstance(front_matches[0], etree._Element):
        return front_matches[0]

    matches = root.xpath(".//*[local-name()='castList'][1]")
    if matches and isinstance(matches[0], etree._Element):
        return matches[0]
    return None


def _local_name(element: etree._Element) -> str:
    return etree.QName(element).localname


def _first_direct_child(element: etree._Element, name: str) -> etree._Element | None:
    for child in element:
        if _local_name(child) == name:
            return child
    return None


def _direct_children(element: etree._Element, name: str) -> list[etree._Element]:
    return [child for child in element if _local_name(child) == name]


def _render_cast_list_items(cast_list: etree._Element) -> list[str]:
    lines: list[str] = []
    for child in cast_list:
        tag = _local_name(child)
        if tag == "castItem":
            lines.append(_render_cast_item(child))
        elif tag == "castGroup":
            lines.extend(_render_cast_group(child))
    return lines


def _render_cast_group(group: etree._Element) -> list[str]:
    lines: list[str] = []
    head = _first_direct_child(group, "head")
    if head is not None:
        lines.append(rf"\item[] \textbf{{{_normalize_inline(_render_inline(head))}}}")

    for child in group:
        if _local_name(child) == "castItem":
            lines.append(_render_cast_item(child))
    return lines


def _render_cast_item(cast_item: etree._Element) -> str:
    role = _first_direct_child(cast_item, "role")
    label = _normalize_inline(_render_inline(role)) if role is not None else ""

    details: list[str] = []
    for role_desc in _direct_children(cast_item, "roleDesc"):
        detail = _normalize_inline(_render_inline(role_desc))
        if detail:
            details.append(detail)
    for actor in _direct_children(cast_item, "actor"):
        detail = _normalize_inline(_render_inline(actor))
        if detail:
            details.append(detail)

    if label:
        detail_text = " -- ".join(details)
        return rf"\item[{label}] {detail_text}".rstrip()

    content = _normalize_inline(_render_inline(cast_item))
    if content:
        return rf"\item[] {content}"
    return "% DRAMATIS PERSONAE: empty castItem omitted."


def _render_inline(element: etree._Element | None) -> str:
    if element is None:
        return ""

    parts: list[str] = [_render_text_chunk(element.text)]
    for child in element:
        parts.append(_render_inline_child(child))
        parts.append(_render_text_chunk(child.tail))
    return "".join(parts)


def _render_inline_child(element: etree._Element) -> str:
    tag = _local_name(element)
    if tag == "hi":
        return _render_hi(element)
    if tag == "note":
        return _render_note(element)
    if tag in {"role", "roleDesc", "actor", "persName", "head", "castItem"}:
        return _render_inline(element)

    content = _render_inline(element)
    if content:
        return content
    return f"% Unsupported inline TEI element <{tag}> omitted."


def _render_hi(element: etree._Element) -> str:
    content = _normalize_inline(_render_inline(element))
    rend = (element.get("rend") or "").strip().lower()
    if "italic" in rend:
        return rf"\emph{{{content}}}"
    if "bold" in rend:
        return rf"\textbf{{{content}}}"
    return content


def _render_note(element: etree._Element) -> str:
    content = _normalize_inline(_render_inline(element))
    if not content:
        return ""
    return rf"\footnote{{{content}}}"


def _render_text_chunk(text: str | None) -> str:
    if not text:
        return ""
    return escape_latex_text(re.sub(r"\s+", " ", text))


def _normalize_inline(text: str) -> str:
    return re.sub(r" {2,}", " ", text).strip()
