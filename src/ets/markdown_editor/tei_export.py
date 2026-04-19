from __future__ import annotations

from dataclasses import dataclass
import xml.etree.ElementTree as ET

from .models import (
    BibliographyBlock,
    Block,
    BoldRun,
    CapsRun,
    FootnoteRefRun,
    HeadingBlock,
    InlineRun,
    ItalicRun,
    LinkRun,
    ListBlock,
    MarkdownDocument,
    ParagraphBlock,
    QuoteBlock,
    RuleBlock,
    SmallCapsRun,
    SubRun,
    SupRun,
    TextRun,
    UnderlineRun,
)


TEI_NS = "http://www.tei-c.org/ns/1.0"
ET.register_namespace("", TEI_NS)


def _tei(tag: str) -> str:
    return f"{{{TEI_NS}}}{tag}"


def _append_text(parent: ET.Element, last_child: ET.Element | None, text: str) -> None:
    if not text:
        return
    if last_child is None:
        parent.text = (parent.text or "") + text
        return
    last_child.tail = (last_child.tail or "") + text


@dataclass(frozen=True)
class _InlineExportContext:
    footnotes: dict[str, str]
    note_numbers: dict[str, int]


def _append_runs(parent: ET.Element, runs: tuple[InlineRun, ...], context: _InlineExportContext) -> None:
    last_child: ET.Element | None = None
    for run in runs:
        if isinstance(run, TextRun):
            _append_text(parent, last_child, run.text)
            continue

        if isinstance(run, ItalicRun):
            child = ET.SubElement(parent, _tei("hi"), {"rend": "italic"})
            _append_runs(child, run.children, context)
            last_child = child
            continue

        if isinstance(run, BoldRun):
            child = ET.SubElement(parent, _tei("hi"), {"rend": "bold"})
            _append_runs(child, run.children, context)
            last_child = child
            continue

        if isinstance(run, UnderlineRun):
            child = ET.SubElement(parent, _tei("hi"), {"rend": "underline"})
            _append_runs(child, run.children, context)
            last_child = child
            continue

        if isinstance(run, SupRun):
            child = ET.SubElement(parent, _tei("hi"), {"rend": "superscript"})
            _append_runs(child, run.children, context)
            last_child = child
            continue

        if isinstance(run, SubRun):
            child = ET.SubElement(parent, _tei("hi"), {"rend": "subscript"})
            _append_runs(child, run.children, context)
            last_child = child
            continue

        if isinstance(run, CapsRun):
            child = ET.SubElement(parent, _tei("hi"), {"rend": "caps"})
            _append_runs(child, run.children, context)
            last_child = child
            continue

        if isinstance(run, SmallCapsRun):
            child = ET.SubElement(parent, _tei("hi"), {"rend": "smallcaps"})
            _append_runs(child, run.children, context)
            last_child = child
            continue

        if isinstance(run, LinkRun):
            child = ET.SubElement(parent, _tei("ref"), {"target": run.target})
            _append_runs(child, run.children, context)
            last_child = child
            continue

        if isinstance(run, FootnoteRefRun):
            note_content = context.footnotes.get(run.identifier)
            if note_content is None:
                _append_text(parent, last_child, f"[^{run.identifier}]")
                continue
            attrs = {"place": "foot"}
            note_number = context.note_numbers.get(run.identifier)
            if note_number is not None:
                attrs["n"] = str(note_number)
            note = ET.SubElement(parent, _tei("note"), attrs)
            note.text = note_content
            last_child = note
            continue


def _append_block(parent: ET.Element, block: Block, context: _InlineExportContext) -> None:
    if isinstance(block, ParagraphBlock):
        paragraph = ET.SubElement(parent, _tei("p"))
        _append_runs(paragraph, block.runs, context)
        return

    if isinstance(block, ListBlock):
        attrs: dict[str, str] = {}
        if block.ordered:
            attrs["type"] = "ordered"
        listing = ET.SubElement(parent, _tei("list"), attrs)
        for item_runs in block.items:
            item = ET.SubElement(listing, _tei("item"))
            _append_runs(item, item_runs, context)
        return

    if isinstance(block, QuoteBlock):
        quote = ET.SubElement(parent, _tei("quote"))
        for paragraph_runs in block.paragraphs:
            paragraph = ET.SubElement(quote, _tei("p"))
            _append_runs(paragraph, paragraph_runs, context)
        return

    if isinstance(block, RuleBlock):
        ET.SubElement(parent, _tei("milestone"), {"unit": "separator"})
        return

    if isinstance(block, BibliographyBlock):
        list_bibl = ET.SubElement(parent, _tei("listBibl"))
        for entry in block.entries:
            bibl = ET.SubElement(list_bibl, _tei("bibl"))
            bibl.text = entry.raw_text
        return

    raise ValueError(f"Unsupported block type: {type(block)!r}")


def _build_notice_div(document: MarkdownDocument, *, notice_type: str) -> ET.Element:
    footnotes = {identifier: definition.raw_text for identifier, definition in document.footnotes.items()}
    note_numbers = {identifier: index + 1 for index, identifier in enumerate(document.footnote_reference_order)}
    context = _InlineExportContext(footnotes=footnotes, note_numbers=note_numbers)

    notice_div = ET.Element(_tei("div"), {"type": notice_type})
    section_stack: list[tuple[int, ET.Element]] = [(0, notice_div)]

    for block in document.blocks:
        if isinstance(block, HeadingBlock):
            while section_stack and section_stack[-1][0] >= block.level:
                section_stack.pop()
            parent = section_stack[-1][1] if section_stack else notice_div
            section = ET.SubElement(parent, _tei("div"), {"type": "section"})
            head = ET.SubElement(section, _tei("head"))
            _append_runs(head, block.runs, context)
            section_stack.append((block.level, section))
            continue

        container = section_stack[-1][1] if section_stack else notice_div
        _append_block(container, block, context)

    return notice_div


def export_tei_fragment(document: MarkdownDocument, *, notice_type: str = "notice") -> str:
    fragment = _build_notice_div(document, notice_type=notice_type)
    tree = ET.ElementTree(fragment)
    ET.indent(tree, "  ")
    return ET.tostring(fragment, encoding="unicode")


def export_tei_document(
    document: MarkdownDocument,
    *,
    title: str = "Notice éditoriale",
    author: str = "",
    editor: str = "",
    notice_type: str = "notice",
) -> str:
    tei = ET.Element(_tei("TEI"))
    tei_header = ET.SubElement(tei, _tei("teiHeader"))
    file_desc = ET.SubElement(tei_header, _tei("fileDesc"))
    title_stmt = ET.SubElement(file_desc, _tei("titleStmt"))
    ET.SubElement(title_stmt, _tei("title")).text = title
    if author:
        ET.SubElement(title_stmt, _tei("author")).text = author
    if editor:
        ET.SubElement(title_stmt, _tei("editor")).text = editor

    publication_stmt = ET.SubElement(file_desc, _tei("publicationStmt"))
    ET.SubElement(publication_stmt, _tei("p")).text = "Generated by Ekdosis TEI Studio v2 Markdown editor"
    source_desc = ET.SubElement(file_desc, _tei("sourceDesc"))
    ET.SubElement(source_desc, _tei("p")).text = "Born-digital Markdown editorial source."

    text = ET.SubElement(tei, _tei("text"))
    body = ET.SubElement(text, _tei("body"))
    body.append(_build_notice_div(document, notice_type=notice_type))

    tree = ET.ElementTree(tei)
    ET.indent(tree, "  ")
    return ET.tostring(tei, encoding="utf-8", xml_declaration=True).decode("utf-8")
