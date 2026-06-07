from __future__ import annotations

from dataclasses import dataclass
from os import PathLike
from pathlib import Path
import re

from lxml import etree

from .escaping import escape_latex_text
from .templates import wrap_standalone

TEI_NS = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI_NS}

_TRAILING_SPACE = "\uE000ETS_TRAILING_SPACE\uE000"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"


@dataclass
class _RenderContext:
    apparatus_policy: str = "full"
    apparatus_numbering_policy: str = "ekdosis"
    current_line_number: str | None = None
    line_number_printed: bool = False

    def for_line(self, line_number: str | None) -> "_RenderContext":
        return _RenderContext(
            apparatus_policy=self.apparatus_policy,
            apparatus_numbering_policy=self.apparatus_numbering_policy,
            current_line_number=_base_line_number(line_number),
            line_number_printed=False,
        )


def tei_to_ekdosis(
    xml_input: str | PathLike[str],
    *,
    standalone: bool = False,
    apparatus_policy: str = "full",
    apparatus_numbering_policy: str = "ekdosis",
) -> str:
    """Convert canonical ETS TEI XML to a minimal LaTeX-Ekdosis fragment.

    ``xml_input`` may be an XML string or a filesystem path. A string that starts
    with ``<`` is treated as XML; otherwise an existing path is read from disk.
    """
    root = _parse_xml_input(xml_input)
    if apparatus_numbering_policy not in {"ekdosis", "editorial"}:
        raise ValueError("apparatus_numbering_policy must be 'ekdosis' or 'editorial'.")

    context = _RenderContext(
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
        return wrap_standalone(fragment, witness_declarations=render_ekdosis_witness_declarations_from_root(root))
    return fragment


def render_ekdosis_witness_declarations(xml_input: str | PathLike[str]) -> str:
    root = _parse_xml_input(xml_input)
    return render_ekdosis_witness_declarations_from_root(root)


def render_ekdosis_witness_declarations_from_root(root: etree._Element) -> str:
    witnesses = root.findall(".//tei:teiHeader//tei:listWit//tei:witness", namespaces=NS)
    used_witness_ids = _used_witness_ids(root)
    if used_witness_ids and not witnesses:
        raise ValueError("Apparat critique present, mais aucun listWit n'est declare dans le teiHeader.")

    declarations: list[str] = []
    declared: dict[str, str] = {}
    for witness in witnesses:
        witness_id = (witness.get(XML_ID) or "").strip()
        if not witness_id:
            raise ValueError("Temoin sans xml:id dans le teiHeader/listWit.")
        text = " ".join("".join(witness.itertext()).split())
        short, description = _parse_witness_label(witness_id, text)
        declaration = (
            rf"\DeclareWitness{{{witness_id}}}"
            rf"{{{escape_latex_text(short)}}}"
            rf"{{{escape_latex_text(description)}}}"
        )
        declared[witness_id] = declaration
        declarations.append(declaration)

    missing = sorted(used_witness_ids - set(declared))
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Temoin(s) utilise(s) dans l'apparat mais absent(s) du teiHeader/listWit: {missing_text}.")
    return "\n".join(declarations)


def _parse_witness_label(witness_id: str, text: str) -> tuple[str, str]:
    pattern = rf"^\s*{re.escape(witness_id)}\s*\(([^)]+)\)\s*(.*)$"
    match = re.match(pattern, text)
    if match is None:
        match = re.match(r"^\s*\S+\s+\(([^)]+)\)\s*(.*)$", text)
    if match is None:
        raise ValueError(f"Temoin '{witness_id}' impossible a convertir en DeclareWitness: {text}")
    short = match.group(1).strip()
    description = match.group(2).strip()
    return short, description


def _used_witness_ids(root: etree._Element) -> set[str]:
    used: set[str] = set()
    for reading in root.findall(".//tei:app//tei:lem", namespaces=NS) + root.findall(
        ".//tei:app//tei:rdg",
        namespaces=NS,
    ):
        used.update(_witness_ids_from_wit(reading.get("wit", "")))
    return used


def _witness_ids_from_wit(value: str) -> set[str]:
    return {item.lstrip("#") for item in value.split() if item.strip()}


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
        return [_render_stage(element, context=context)]
    if tag == "head":
        return [f"\\stage{{{_render_inline(element, context=context).strip()}}}"]
    if tag == "l":
        return [_render_line(element, context=context)]
    if tag == "lg":
        return _render_lg(element, context=context)
    if tag == "note":
        return []
    if tag == "front":
        return []
    return [line for child in element for line in _render_block(child, context=context)]


def _render_div(element: etree._Element, *, context: _RenderContext) -> list[str]:
    div_type = element.get("type", "")
    lines: list[str] = []
    if div_type in {"act", "scene"}:
        depth = "2" if div_type == "act" else "3"
        number = element.get("n", "")
        lines.append(f"\\ekddiv{{type={div_type}, n={number}, depth={depth}}}")

    for child in element:
        lines.extend(_render_block(child, context=context))
    return lines


def _render_speech(element: etree._Element, *, context: _RenderContext) -> list[str]:
    speaker = element.find("./tei:speaker", namespaces=NS)
    speaker_text = _render_inline(speaker, context=context).strip() if speaker is not None else ""
    lines = [
        r"\begin{speech}",
        f"  \\speaker{{{speaker_text}}}",
        r"  \begin{ekdverse}",
    ]

    for child in element:
        if _local_name(child) == "speaker":
            continue
        for rendered in _render_block(child, context=context):
            lines.append(f"    {rendered}")

    lines.extend([r"  \end{ekdverse}", r"\end{speech}"])
    return lines


def _render_stage(element: etree._Element, *, context: _RenderContext) -> str:
    rendered = _render_inline(element, context=context).strip()
    if element.get("type") == "personnages":
        return f"\\stage{{{rendered}}}"
    return f"\\didas{{{rendered}}}"


def _render_lg(element: etree._Element, *, context: _RenderContext) -> list[str]:
    lines: list[str] = []
    if element.get("type") == "stanza":
        attrs = ["type=stanza"]
        if element.get("subtype"):
            attrs.append(f"subtype={element.get('subtype')}")
        if element.get("rhyme"):
            attrs.append(f"rhyme={element.get('rhyme')}")
        lines.append("% stanza " + " ".join(attrs))

    for child in element:
        if _local_name(child) == "l":
            lines.append(_render_line(child, context=context))
        else:
            lines.extend(_render_block(child, context=context))
    return lines


def _render_line(element: etree._Element, *, context: _RenderContext) -> str:
    number = element.get("n", "")
    line_context = context.for_line(number)
    content = _render_inline(element, context=line_context).strip()
    return f"\\vnum{{{number}}}{{{content}\\\\}}"


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
    # ``cert=low`` marks inspect/probable cases: keep them visible.
    return element.get("cert") != "low"


def _render_app(element: etree._Element, *, context: _RenderContext) -> str:
    if _should_hide_app(element, context.apparatus_policy):
        lemma = element.find("./tei:lem", namespaces=NS)
        return _render_inline(lemma, context=context) if lemma is not None else ""

    pieces: list[str] = [r"\app{"]
    has_trailing_space = False
    for child in element:
        tag = _local_name(child)
        if tag not in {"lem", "rdg"}:
            continue
        content, trailing_space = _render_reading(child, context=context)
        has_trailing_space = has_trailing_space or trailing_space
        wit = _format_wit(child.get("wit", ""))
        options = _reading_options(tag, wit, content, context)
        pieces.append(f"\\{tag}[{options}]{{{content}}}")
    pieces.append("}")
    if has_trailing_space:
        pieces.append(_TRAILING_SPACE)
    return "".join(pieces)


def _render_reading(element: etree._Element, *, context: _RenderContext) -> tuple[str, bool]:
    rendered = _render_inline(element, context=context)
    trailing_space = bool(rendered) and rendered[-1].isspace()
    return rendered.strip(), trailing_space


def _reading_options(tag: str, wit: str, content: str, context: _RenderContext) -> str:
    options: list[str] = [f"wit={{{wit}}}"]
    if tag == "lem" and context.apparatus_numbering_policy == "editorial":
        options.append("nonum")
        prefix = _next_editorial_apparatus_prefix(context)
        if prefix:
            options.append(f"alt={{{prefix}{content}}}")
    return ",".join(options)


def _next_editorial_apparatus_prefix(context: _RenderContext) -> str:
    if not context.current_line_number or context.line_number_printed:
        return ""
    context.line_number_printed = True
    return rf"\textbf{{{context.current_line_number}}}~"


def _base_line_number(value: str | None) -> str | None:
    if value is None:
        return None
    base = value.strip().split(".", 1)[0].strip()
    return base or None


def _format_wit(value: str) -> str:
    sigla = [item.lstrip("#") for item in value.split() if item.strip()]
    return ", ".join(sigla)


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
