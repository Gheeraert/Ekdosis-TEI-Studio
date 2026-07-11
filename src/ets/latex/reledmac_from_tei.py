from __future__ import annotations

from dataclasses import dataclass
from os import PathLike
from pathlib import Path
import re

from lxml import etree

from .escaping import escape_latex_text
from .reledmac_templates import render_reledmac_support_preamble

TEI_NS = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI_NS}
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
_TRAILING_SPACE = "\uE000ETS_TRAILING_SPACE\uE000"


@dataclass
class _Witness:
    witness_id: str
    siglum: str


@dataclass
class _RenderContext:
    witnesses: dict[str, _Witness]
    apparatus_policy: str = "full"
    apparatus_numbering_policy: str = "editorial"
    current_line_number: str | None = None
    line_number_printed: bool = False
    in_numbered_paragraph: bool = False

    def for_line(self, line_number: str | None) -> "_RenderContext":
        return _RenderContext(
            witnesses=self.witnesses,
            apparatus_policy=self.apparatus_policy,
            apparatus_numbering_policy=self.apparatus_numbering_policy,
            current_line_number=_base_line_number(line_number),
            line_number_printed=False,
            in_numbered_paragraph=True,
        )

    def for_critical_block(self) -> "_RenderContext":
        return _RenderContext(
            witnesses=self.witnesses,
            apparatus_policy=self.apparatus_policy,
            apparatus_numbering_policy=self.apparatus_numbering_policy,
            current_line_number=None,
            line_number_printed=False,
            in_numbered_paragraph=True,
        )


def tei_to_reledmac(
    xml_input: str | PathLike[str],
    *,
    standalone: bool = False,
    apparatus_policy: str = "full",
    apparatus_numbering_policy: str = "editorial",
) -> str:
    """Convert canonical ETS TEI XML to a LaTeX-Reledmac dramatic fragment."""
    if apparatus_numbering_policy != "editorial":
        raise ValueError("apparatus_numbering_policy must be 'editorial'.")

    root = _parse_xml_input(xml_input)
    witnesses = _collect_witnesses(root)
    context = _RenderContext(
        witnesses=witnesses,
        apparatus_policy=apparatus_policy,
        apparatus_numbering_policy=apparatus_numbering_policy,
    )
    body = root.find(".//tei:text/tei:body", namespaces=NS)
    if body is None:
        fragment = ""
    else:
        fragment = "\n".join(line for child in body for line in _render_block(child, context=context))
    fragment = _finalize_spacing(fragment).rstrip() + ("\n" if fragment else "")
    if standalone:
        return _wrap_standalone(fragment)
    return fragment


def _wrap_standalone(fragment: str) -> str:
    body = fragment.rstrip()
    return "\n".join(
        [
            r"\documentclass{book}",
            r"\usepackage{fontspec}",
            r"\usepackage[french]{babel}",
            r"\usepackage{csquotes}",
            render_reledmac_support_preamble().rstrip(),
            r"\begin{document}",
            body,
            r"\end{document}",
            "",
        ]
    )


def _collect_witnesses(root: etree._Element) -> dict[str, _Witness]:
    witness_elements = root.findall(".//tei:teiHeader//tei:listWit//tei:witness", namespaces=NS)
    used = _used_witness_ids(root)
    if used and not witness_elements:
        raise ValueError("Apparat critique present, mais aucun listWit n'est declare dans le teiHeader.")

    witnesses: dict[str, _Witness] = {}
    for witness in witness_elements:
        witness_id = (witness.get(XML_ID) or "").strip()
        if not witness_id:
            raise ValueError("Temoin sans xml:id dans le teiHeader/listWit.")
        witnesses[witness_id] = _Witness(witness_id=witness_id, siglum=witness_id)

    missing = sorted(used - set(witnesses))
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Temoin(s) utilise(s) dans l'apparat mais absent(s) du teiHeader/listWit: {missing_text}.")
    return witnesses


def _used_witness_ids(root: etree._Element) -> set[str]:
    used: set[str] = set()
    for reading in root.findall(".//tei:app//tei:lem", namespaces=NS) + root.findall(".//tei:app//tei:rdg", namespaces=NS):
        used.update(_witness_ids_from_wit(reading.get("wit", "")))
    return used


def _witness_ids_from_wit(value: str) -> list[str]:
    return [item.lstrip("#") for item in value.split() if item.strip()]


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


def _local_name(element: etree._Element) -> str:
    return etree.QName(element).localname


def _render_block(element: etree._Element, *, context: _RenderContext) -> list[str]:
    tag = _local_name(element)
    if tag == "div":
        return _render_div(element, context=context)
    if tag == "sp":
        return _render_speech(element, context=context)
    if tag == "stage":
        return _render_stage_block(element, context=context)
    if tag == "head":
        return _render_wrapped_block_if_needed(
            f"\\stage{{{_render_inline(element, context=_context_for_element(element, context=context)).strip()}}}",
            element,
        )
    if tag == "l":
        return _render_stanza([element], context=context)
    if tag == "lg":
        return _render_lg(element, context=context)
    if tag in {"note", "front"}:
        return []
    return [line for child in element for line in _render_block(child, context=context)]


def _render_div(element: etree._Element, *, context: _RenderContext) -> list[str]:
    div_type = element.get("type", "")
    lines: list[str] = []
    if div_type in {"act", "scene"}:
        head = element.find("./tei:head", namespaces=NS)
        title_context = _context_for_element(head, context=context)
        title = _render_inline(head, context=title_context).strip() if head is not None else element.get("n", "")
        macro = "PURHAct" if div_type == "act" else "PURHScene"
        lines.extend(_render_wrapped_block_if_needed(f"\\{macro}{{{title}}}", head))

    for child in element:
        if div_type in {"act", "scene"} and _local_name(child) == "head":
            continue
        lines.extend(_render_block(child, context=context))
    return lines


def _render_speech(element: etree._Element, *, context: _RenderContext) -> list[str]:
    speaker = element.find("./tei:speaker", namespaces=NS)
    speaker_context = _context_for_element(speaker, context=context)
    speaker_text = _render_inline(speaker, context=speaker_context).strip() if speaker is not None else ""
    lines = [r"\begin{speech}"]
    speaker_lines = _render_wrapped_block_if_needed(f"\\speaker{{{speaker_text}}}", speaker)
    lines.extend(f"  {line}" for line in speaker_lines)
    stanza_lines: list[etree._Element] = []

    def flush_stanza() -> None:
        nonlocal stanza_lines
        if stanza_lines:
            lines.extend(f"  {line}" for line in _render_stanza(stanza_lines, context=context))
            stanza_lines = []

    for child in element:
        tag = _local_name(child)
        if tag == "speaker":
            continue
        if tag == "l":
            stanza_lines.append(child)
            continue
        if tag == "lg" and child.get("type") == "stanza":
            flush_stanza()
            lines.extend(f"  {line}" for line in _render_lg(child, context=context))
            continue
        flush_stanza()
        for rendered in _render_block(child, context=context):
            lines.append(f"  {rendered}")
    flush_stanza()
    lines.append(r"\end{speech}")
    return lines


def _render_stage_block(element: etree._Element, *, context: _RenderContext) -> list[str]:
    rendered = _render_inline(element, context=_context_for_element(element, context=context)).strip()
    if element.get("type") == "personnages":
        return _render_wrapped_block_if_needed(f"\\stage{{{rendered}}}", element)
    return _render_wrapped_block_if_needed(f"\\didas{{{rendered}}}", element)


def _context_for_element(element: etree._Element | None, *, context: _RenderContext) -> _RenderContext:
    if element is not None and _contains_app(element):
        return context.for_critical_block()
    return context


def _contains_app(element: etree._Element) -> bool:
    if _local_name(element) == "app":
        return True
    return any(_contains_app(child) for child in element)


def _render_wrapped_block_if_needed(content: str, element: etree._Element | None) -> list[str]:
    if element is None or not _contains_app(element):
        return [content]
    return [
        r"\beginnumbering",
        r"\pstart",
        content,
        r"\pend",
        r"\endnumbering",
    ]


def _render_lg(element: etree._Element, *, context: _RenderContext) -> list[str]:
    lines = [child for child in element if _local_name(child) == "l"]
    if lines:
        return _render_stanza(lines, context=context)
    return [line for child in element for line in _render_block(child, context=context)]


def _render_stanza(elements: list[etree._Element], *, context: _RenderContext) -> list[str]:
    if not elements:
        return []
    lines = [r"\beginnumbering", r"\stanza"]
    for index, element in enumerate(elements):
        rendered = _render_line_content(element, context=context)
        terminator = r"\&" if index == len(elements) - 1 else "&"
        lines.append(f"{rendered}{terminator}")
    lines.append(r"\endnumbering")
    return lines


def _render_line_content(element: etree._Element, *, context: _RenderContext) -> str:
    number = element.get("n", "")
    line_context = context.for_line(number)
    content = _render_stanza_text(_render_inline(element, context=line_context).strip())
    prefix = r"\skipnumbering " if _is_shared_continuation(number) else ""
    return f"{prefix}\\PURHVerse{{{number}}}{{{content}}}"


def _render_stanza_text(content: str) -> str:
    return content.replace(r"\&", r"\ampersand{}")


def _render_inline(element: etree._Element | None, *, context: _RenderContext) -> str:
    if element is None:
        return ""

    output: list[str] = [_render_text_chunk(element.text)]
    for child in element:
        output.append(_render_inline_child(child, context=context))
        output.append(_render_text_chunk(child.tail))
    return "".join(output)


def _render_inline_child(element: etree._Element, *, context: _RenderContext) -> str:
    tag = _local_name(element)
    if tag == "app":
        return _render_app(element, context=context)
    if tag == "hi" and element.get("rend") == "italic":
        return _render_italic(element, context=context)
    if tag == "note":
        return ""
    return _render_inline(element, context=context)


def _render_italic(element: etree._Element, *, context: _RenderContext) -> str:
    content = _render_inline(element, context=context)
    trailing = ""
    while content.endswith(_TRAILING_SPACE):
        content = content[: -len(_TRAILING_SPACE)]
        trailing += _TRAILING_SPACE
    return f"\\emph{{{content.strip()}}}{trailing}"


def _should_hide_app(element: etree._Element, apparatus_policy: str) -> bool:
    if apparatus_policy != "hide_minor":
        return False
    if element.get("type") != "minor":
        return False
    return element.get("cert") != "low"


def _render_app(element: etree._Element, *, context: _RenderContext) -> str:
    lemma = element.find("./tei:lem", namespaces=NS)
    if _should_hide_app(element, context.apparatus_policy):
        return _render_inline(lemma, context=context) if lemma is not None else ""
    if not context.in_numbered_paragraph:
        return _render_inline(lemma, context=context) if lemma is not None else ""

    lemma_text, trailing_space = _render_reading(lemma, context=context) if lemma is not None else ("", False)
    note = _apparatus_note(element, lemma_text=lemma_text, context=context)
    display_lemma = _next_editorial_apparatus_lemma(lemma_text, context)
    rendered = rf"\edtext{{{lemma_text}}}{{\lemma{{{display_lemma}}}\Afootnote[nonum]{{{note}}}}}"
    if trailing_space:
        rendered += _TRAILING_SPACE
    return rendered


def _apparatus_note(element: etree._Element, *, lemma_text: str, context: _RenderContext) -> str:
    entries: list[str] = []
    for child in element:
        tag = _local_name(child)
        if tag not in {"lem", "rdg"}:
            continue
        reading, _ = _render_reading(child, context=context)
        if _is_omission(child):
            reading = "om."
        sigla = _format_witnesses(child.get("wit", ""), context)
        if tag == "lem":
            entries.append(sigla.strip())
        else:
            entries.append(f"{sigla} {reading}".strip())
    return " ; ".join(entry for entry in entries if entry)


def _render_reading(element: etree._Element | None, *, context: _RenderContext) -> tuple[str, bool]:
    if element is None:
        return "", False
    if _is_omission(element):
        return "", False
    rendered = _render_inline(element, context=context)
    trailing_space = bool(rendered) and rendered[-1].isspace()
    return rendered.strip(), trailing_space


def _is_omission(element: etree._Element) -> bool:
    return element.get("type") == "omission"


def _format_witnesses(value: str, context: _RenderContext) -> str:
    sigla: list[str] = []
    for witness_id in _witness_ids_from_wit(value):
        witness = context.witnesses.get(witness_id)
        sigla.append(witness.siglum if witness is not None else witness_id)
    return " ".join(sigla)


def _next_editorial_apparatus_lemma(lemma_text: str, context: _RenderContext) -> str:
    if not context.current_line_number or context.line_number_printed:
        return lemma_text or "om."
    context.line_number_printed = True
    return rf"\textbf{{{context.current_line_number}}}~{lemma_text or 'om.'}"


def _base_line_number(value: str | None) -> str | None:
    if value is None:
        return None
    base = value.strip().split(".", 1)[0].strip()
    return base or None


def _is_shared_continuation(value: str | None) -> bool:
    if value is None or "." not in value:
        return False
    return value.split(".", 1)[1].strip() not in {"", "1"}


def _render_text_chunk(text: str | None) -> str:
    if not text:
        return ""
    if "\n" in text or "\r" in text:
        if not text.strip():
            return ""
        text = re.sub(r"\s+", " ", text.strip())
    return escape_latex_text(text)


def _finalize_spacing(text: str) -> str:
    return text.replace(_TRAILING_SPACE, " ")
