from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

TEI_NS = "http://www.tei-c.org/ns/1.0"


def _tei(tag: str) -> str:
    return f"{{{TEI_NS}}}{tag}"


_PARAGRAPH_SPLIT_RE = re.compile(r"(?:\r?\n){2,}")
_SMALLCAPS_RE = re.compile(r"\[([^\[\]\n]+)\]\{\.smallcaps\}")
_LINK_RE = re.compile(r"\[([^\[\]\n]+)\]\((https?://[^\s)]+)\)")
_BOLD_RE = re.compile(r"\*\*([^*\n]+)\*\*")
_ITALIC_STAR_RE = re.compile(r"\*([^*\n]+)\*")
_ITALIC_UNDERSCORE_RE = re.compile(r"_([^_\n]+)_")
_SUPERSCRIPT_RE = re.compile(r"\^([^^\n]+)\^")
_SUBSCRIPT_RE = re.compile(r"~([^~\n]+)~")


@dataclass(frozen=True)
class MarkdownConversion:
    paragraphs: list[ET.Element]
    has_inline_markup: bool


def _append_text(parent: ET.Element, text: str) -> None:
    if not text:
        return
    if len(parent):
        last_child = parent[-1]
        last_child.tail = (last_child.tail or "") + text
        return
    parent.text = (parent.text or "") + text


def _split_paragraphs(content: str) -> list[str]:
    stripped = content.strip()
    if not stripped:
        return []
    return [paragraph for paragraph in _PARAGRAPH_SPLIT_RE.split(stripped) if paragraph]


def _parse_inline(paragraph_text: str) -> tuple[list[str | ET.Element], bool]:
    out: list[str | ET.Element] = []
    has_markup = False
    index = 0
    text = paragraph_text

    while index < len(text):
        matched = False
        for pattern_name, pattern in (
            ("smallcaps", _SMALLCAPS_RE),
            ("link", _LINK_RE),
            ("bold", _BOLD_RE),
            ("italic_star", _ITALIC_STAR_RE),
            ("italic_underscore", _ITALIC_UNDERSCORE_RE),
            ("superscript", _SUPERSCRIPT_RE),
            ("subscript", _SUBSCRIPT_RE),
        ):
            match = pattern.match(text, index)
            if match is None:
                continue

            element: ET.Element
            if pattern_name == "smallcaps":
                element = ET.Element(_tei("hi"), {"rend": "smallcaps"})
                element.text = match.group(1)
            elif pattern_name == "link":
                element = ET.Element(_tei("ref"), {"target": match.group(2)})
                element.text = match.group(1)
            elif pattern_name == "bold":
                element = ET.Element(_tei("hi"), {"rend": "bold"})
                element.text = match.group(1)
            elif pattern_name in {"italic_star", "italic_underscore"}:
                element = ET.Element(_tei("hi"), {"rend": "italic"})
                element.text = match.group(1)
            elif pattern_name == "superscript":
                element = ET.Element(_tei("hi"), {"rend": "superscript"})
                element.text = match.group(1)
            else:
                element = ET.Element(_tei("hi"), {"rend": "subscript"})
                element.text = match.group(1)

            out.append(element)
            has_markup = True
            index = match.end()
            matched = True
            break

        if matched:
            continue

        out.append(text[index])
        index += 1

    return out, has_markup


def convert_annotation_markdown(content: str) -> MarkdownConversion:
    paragraphs = _split_paragraphs(content)
    if not paragraphs:
        return MarkdownConversion(paragraphs=[], has_inline_markup=False)

    paragraph_nodes: list[ET.Element] = []
    has_inline_markup = False

    for paragraph_text in paragraphs:
        paragraph = ET.Element(_tei("p"))
        fragments, paragraph_has_markup = _parse_inline(paragraph_text)
        has_inline_markup = has_inline_markup or paragraph_has_markup
        for fragment in fragments:
            if isinstance(fragment, str):
                _append_text(paragraph, fragment)
            else:
                paragraph.append(fragment)
        paragraph_nodes.append(paragraph)

    return MarkdownConversion(paragraphs=paragraph_nodes, has_inline_markup=has_inline_markup)


def append_annotation_content(note: ET.Element, content: str) -> None:
    converted = convert_annotation_markdown(content)

    # Backward compatibility: keep existing flat text note content for plain,
    # single-paragraph notes with no supported markdown markup.
    if not converted.has_inline_markup and len(converted.paragraphs) <= 1:
        note.text = content
        return

    if not converted.paragraphs:
        note.text = content
        return

    for paragraph in converted.paragraphs:
        note.append(paragraph)
