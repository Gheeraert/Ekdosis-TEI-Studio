from __future__ import annotations

from os import PathLike
from pathlib import Path
import re

from lxml import etree

from .escaping import escape_latex_text


def tei_peritext_to_latex(xml_input: str | PathLike[str]) -> str:
    """Convert editorial/peritextual TEI into a standard LaTeX fragment.

    This converter intentionally returns only a body fragment: no preamble, no
    document environment, and no user-facing export file. The future publication
    PDF master owns chapter-level structure, so a root ``head type="main"`` is
    ignored to avoid duplicate titles. Nested ``div`` headings are rendered as
    unnumbered sections.
    """
    root = _parse_xml_input(xml_input)
    body = _first_element(root, ".//*[local-name()='text']/*[local-name()='body']")
    if body is None:
        return ""

    blocks = _render_child_blocks(body, div_level=0)
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


def _first_element(root: etree._Element, expression: str) -> etree._Element | None:
    matches = root.xpath(expression)
    if matches and isinstance(matches[0], etree._Element):
        return matches[0]
    return None


def _local_name(element: etree._Element) -> str:
    return etree.QName(element).localname


def _render_child_blocks(element: etree._Element, *, div_level: int) -> list[str]:
    blocks: list[str] = []
    if element.text and element.text.strip():
        blocks.append(_normalize_inline(_render_text_chunk(element.text)))
    for child in element:
        rendered = _render_block(child, div_level=div_level)
        if rendered:
            blocks.append(rendered)
        if child.tail and child.tail.strip():
            blocks.append(_normalize_inline(_render_text_chunk(child.tail)))
    return blocks


def _render_block(element: etree._Element, *, div_level: int) -> str:
    tag = _local_name(element)
    if tag == "div":
        return _render_div(element, div_level=div_level)
    if tag == "head":
        return _render_head(element, div_level=max(div_level, 1))
    if tag == "p":
        return _render_paragraph(element)
    if tag == "quote":
        return _render_quote(element, div_level=div_level)
    if tag == "list":
        return _render_list(element, div_level=div_level)
    if tag == "listBibl":
        return _render_list_bibl(element)
    if tag == "bibl":
        return _normalize_inline(_render_inline(element))
    if tag == "table":
        return _render_table(element)

    content = _normalize_inline(_render_inline(element))
    if not content:
        return f"% Unsupported TEI element <{tag}> omitted."
    return f"% Unsupported TEI element <{tag}> rendered as plain content.\n{content}"


def _render_div(element: etree._Element, *, div_level: int) -> str:
    blocks: list[str] = []
    for child in element:
        if _local_name(child) == "head":
            rendered = _render_div_head(child, div_level=div_level)
        else:
            child_level = div_level + 1 if _local_name(child) == "div" else div_level
            rendered = _render_block(child, div_level=child_level)
        if rendered:
            blocks.append(rendered)
    return "\n\n".join(blocks)


def _render_div_head(element: etree._Element, *, div_level: int) -> str:
    head_type = (element.get("type") or "").strip().lower()
    if div_level == 0 and head_type == "main":
        return ""
    if head_type == "sub":
        command = "subsection" if div_level <= 1 else "subsubsection"
    else:
        command = _section_command(max(div_level, 1))
    return rf"\{command}*{{{_normalize_inline(_render_inline(element))}}}"


def _render_head(element: etree._Element, *, div_level: int) -> str:
    return rf"\{_section_command(div_level)}*{{{_normalize_inline(_render_inline(element))}}}"


def _section_command(div_level: int) -> str:
    if div_level <= 1:
        return "section"
    if div_level == 2:
        return "subsection"
    return "subsubsection"


def _render_paragraph(element: etree._Element) -> str:
    content = _normalize_inline(_render_inline(element))
    if not content:
        return ""
    if (element.get("rend") or "").strip().lower() == "noindent":
        return rf"\noindent {content}"
    return content


def _render_quote(element: etree._Element, *, div_level: int) -> str:
    blocks = _render_child_blocks(element, div_level=div_level)
    if not blocks:
        content = _normalize_inline(_render_inline(element))
        blocks = [content] if content else []
    inner = "\n\n".join(blocks)
    return "\\begin{quote}\n" + inner + "\n\\end{quote}"


def _render_list(element: etree._Element, *, div_level: int) -> str:
    env = "enumerate" if (element.get("type") or "").strip().lower() == "ordered" else "itemize"
    items = [
        _render_item(child, div_level=div_level)
        for child in element
        if _local_name(child) == "item"
    ]
    return f"\\begin{{{env}}}\n" + "\n".join(items) + f"\n\\end{{{env}}}"


def _render_item(element: etree._Element, *, div_level: int) -> str:
    block_child_names = {"div", "p", "quote", "list", "listBibl", "table"}
    child_blocks = [
        _render_block(child, div_level=div_level)
        for child in element
        if _local_name(child) in block_child_names
    ]
    content = "\n\n".join(block for block in child_blocks if block.strip())
    inline = _normalize_inline(_render_inline(element))
    if content:
        return "\\item " + content
    return "\\item " + inline


def _render_list_bibl(element: etree._Element) -> str:
    items = [
        "\\item " + _normalize_inline(_render_inline(child))
        for child in element
        if _local_name(child) == "bibl"
    ]
    return "\\begin{itemize}\n" + "\n".join(items) + "\n\\end{itemize}"


def _render_table(element: etree._Element) -> str:
    rows = [
        child
        for child in element
        if _local_name(child) == "row"
    ]
    if not rows:
        return "% TABLE: unsupported empty table omitted."

    rendered_rows: list[list[str]] = []
    column_count = 0
    for row in rows:
        cells = [
            _normalize_inline(_render_inline(cell))
            for cell in row
            if _local_name(cell) == "cell"
        ]
        column_count = max(column_count, len(cells))
        rendered_rows.append(cells)

    if column_count == 0:
        return "% TABLE: unsupported table without cells omitted."

    spec = "|" + "|".join("l" for _ in range(column_count)) + "|"
    lines = [rf"\begin{{tabular}}{{{spec}}}", r"\hline"]
    for cells in rendered_rows:
        padded = cells + [""] * (column_count - len(cells))
        lines.append(" & ".join(padded) + r" \\")
        lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    return "\n".join(lines)


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
    if tag == "ref":
        return _render_ref(element)
    if tag in {"p", "item", "bibl", "cell", "head"}:
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
    if "underline" in rend:
        return rf"\underline{{{content}}}"
    if "smallcaps" in rend:
        return rf"\textsc{{{content}}}"
    if rend in {"sup", "super"}:
        return rf"\textsuperscript{{{content}}}"
    if rend in {"sub", "subscript"}:
        return rf"\textsubscript{{{content}}}"
    return content


def _render_note(element: etree._Element) -> str:
    content = _normalize_inline(_render_inline(element))
    if not content:
        return ""
    if (element.get("place") or "").strip().lower() == "foot":
        return rf"\footnote{{{content}}}"
    return rf"\footnote{{{content}}}"


def _render_ref(element: etree._Element) -> str:
    content = _normalize_inline(_render_inline(element))
    target = (element.get("target") or "").strip()
    if not target:
        return content
    return rf"{content}\footnote{{URL: {escape_latex_text(target)}}}"


def _render_text_chunk(text: str | None) -> str:
    if not text:
        return ""
    return escape_latex_text(re.sub(r"\s+", " ", text))


def _normalize_inline(text: str) -> str:
    return re.sub(r" {2,}", " ", text).strip()
