from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import urlparse

from .models import (
    BibliographyBlock,
    BibliographyEntry,
    Block,
    BoldRun,
    CapsRun,
    FootnoteDefinition,
    FootnoteRefRun,
    HeadingBlock,
    InlineRun,
    ItalicRun,
    LinkRun,
    ListBlock,
    MarkdownDiagnostic,
    MarkdownDocument,
    MarkdownParseResult,
    ParagraphBlock,
    QuoteBlock,
    RuleBlock,
    SmallCapsRun,
    SubRun,
    SupRun,
    TextRun,
    UnderlineRun,
)


_HEADING_RE = re.compile(r"^(#{1,4})\s+(.*)$")
_UNORDERED_LIST_RE = re.compile(r"^[-*]\s+(.+)$")
_ORDERED_LIST_RE = re.compile(r"^\d+\.\s+(.+)$")
_FOOTNOTE_DEF_RE = re.compile(r"^\[\^([A-Za-z0-9_-]+)\]:(.*)$")

_CUSTOM_TAGS: tuple[tuple[str, str, type[InlineRun]], ...] = (
    ("[caps]", "[/caps]", CapsRun),
    ("[sup]", "[/sup]", SupRun),
    ("[sub]", "[/sub]", SubRun),
    ("[sc]", "[/sc]", SmallCapsRun),
    ("[u]", "[/u]", UnderlineRun),
)


@dataclass
class _InlineParseState:
    diagnostics: list[MarkdownDiagnostic]
    refs: list[str]


def _append_text_run(runs: list[InlineRun], text: str) -> None:
    if not text:
        return
    if runs and isinstance(runs[-1], TextRun):
        runs[-1] = TextRun(runs[-1].text + text)
    else:
        runs.append(TextRun(text))


def _find_marker(text: str, marker: str, start: int) -> int:
    return text.find(marker, start)


def _is_valid_link_target(target: str) -> bool:
    cleaned = target.strip()
    if not cleaned or any(char.isspace() for char in cleaned):
        return False
    if cleaned.startswith(("#", "/", "./", "../")):
        return True
    parsed = urlparse(cleaned)
    if parsed.scheme in {"http", "https", "mailto"} and parsed.netloc:
        return True
    if parsed.scheme and parsed.path:
        return True
    return False


def _parse_inline_runs(text: str, *, line: int, column_offset: int, state: _InlineParseState) -> tuple[InlineRun, ...]:
    runs: list[InlineRun] = []
    index = 0

    while index < len(text):
        if text.startswith("**", index):
            end = _find_marker(text, "**", index + 2)
            if end == -1:
                state.diagnostics.append(
                    MarkdownDiagnostic(
                        code="E_MD_BOLD_UNCLOSED",
                        message="Balise gras non fermée.",
                        line=line,
                        column=column_offset + index + 1,
                    )
                )
                _append_text_run(runs, text[index:])
                break
            content = text[index + 2 : end]
            children = _parse_inline_runs(
                content,
                line=line,
                column_offset=column_offset + index + 2,
                state=state,
            )
            runs.append(BoldRun(children))
            index = end + 2
            continue

        if text.startswith("*", index):
            end = _find_marker(text, "*", index + 1)
            if end == -1:
                state.diagnostics.append(
                    MarkdownDiagnostic(
                        code="E_MD_ITALIC_UNCLOSED",
                        message="Balise italique non fermée.",
                        line=line,
                        column=column_offset + index + 1,
                    )
                )
                _append_text_run(runs, text[index:])
                break
            content = text[index + 1 : end]
            children = _parse_inline_runs(
                content,
                line=line,
                column_offset=column_offset + index + 1,
                state=state,
            )
            runs.append(ItalicRun(children))
            index = end + 1
            continue

        matched_custom = False
        for opening, closing, run_cls in _CUSTOM_TAGS:
            if not text.startswith(opening, index):
                continue
            end = _find_marker(text, closing, index + len(opening))
            if end == -1:
                state.diagnostics.append(
                    MarkdownDiagnostic(
                        code="E_MD_CUSTOM_TAG_UNCLOSED",
                        message=f"Balise maison non fermée: {opening}",
                        line=line,
                        column=column_offset + index + 1,
                    )
                )
                _append_text_run(runs, text[index:])
                index = len(text)
                matched_custom = True
                break
            content = text[index + len(opening) : end]
            children = _parse_inline_runs(
                content,
                line=line,
                column_offset=column_offset + index + len(opening),
                state=state,
            )
            runs.append(run_cls(children))
            index = end + len(closing)
            matched_custom = True
            break
        if matched_custom:
            continue

        if text.startswith("[^", index):
            end = _find_marker(text, "]", index + 2)
            if end != -1:
                ref_id = text[index + 2 : end].strip()
                if ref_id:
                    runs.append(FootnoteRefRun(ref_id))
                    state.refs.append(ref_id)
                    index = end + 1
                    continue

        if text.startswith("[", index):
            close_bracket = _find_marker(text, "]", index + 1)
            if close_bracket != -1 and close_bracket + 1 < len(text) and text[close_bracket + 1] == "(":
                close_paren = _find_marker(text, ")", close_bracket + 2)
                if close_paren == -1:
                    state.diagnostics.append(
                        MarkdownDiagnostic(
                            code="E_MD_LINK_INVALID",
                            message="Lien Markdown invalide: parenthèse fermante manquante.",
                            line=line,
                            column=column_offset + index + 1,
                        )
                    )
                    _append_text_run(runs, text[index])
                    index += 1
                    continue
                label = text[index + 1 : close_bracket]
                target = text[close_bracket + 2 : close_paren].strip()
                if not _is_valid_link_target(target):
                    state.diagnostics.append(
                        MarkdownDiagnostic(
                            code="E_MD_LINK_INVALID",
                            message=f"Lien Markdown invalide: cible '{target}'.",
                            line=line,
                            column=column_offset + close_bracket + 2,
                        )
                    )
                children = _parse_inline_runs(
                    label,
                    line=line,
                    column_offset=column_offset + index + 1,
                    state=state,
                )
                runs.append(LinkRun(children=children, target=target))
                index = close_paren + 1
                continue

        next_index = index + 1
        while next_index < len(text):
            if text.startswith("**", next_index):
                break
            if text.startswith("*", next_index):
                break
            if text.startswith("[^", next_index):
                break
            if text.startswith("[", next_index):
                break
            if any(text.startswith(opening, next_index) for opening, _, _ in _CUSTOM_TAGS):
                break
            next_index += 1
        _append_text_run(runs, text[index:next_index])
        index = next_index

    return tuple(runs)


def _parse_inline(text: str, *, line: int) -> tuple[tuple[InlineRun, ...], list[MarkdownDiagnostic], list[str]]:
    diagnostics: list[MarkdownDiagnostic] = []
    refs: list[str] = []
    state = _InlineParseState(diagnostics=diagnostics, refs=refs)
    runs = _parse_inline_runs(text, line=line, column_offset=0, state=state)
    return runs, diagnostics, refs


def _looks_like_block_start(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped == "---" or stripped == ":::bibl":
        return True
    if stripped.startswith(">"):
        return True
    if _HEADING_RE.match(stripped):
        return True
    if _UNORDERED_LIST_RE.match(stripped):
        return True
    if _ORDERED_LIST_RE.match(stripped):
        return True
    if _FOOTNOTE_DEF_RE.match(stripped):
        return True
    return False


def _dedupe_ordered(values: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return tuple(ordered)


def parse_markdown(text: str) -> MarkdownParseResult:
    lines = text.splitlines()
    blocks: list[Block] = []
    diagnostics: list[MarkdownDiagnostic] = []
    footnotes: dict[str, FootnoteDefinition] = {}
    referenced_footnotes: list[str] = []
    previous_heading_level: int | None = None

    index = 0
    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()
        line_number = index + 1

        if not stripped:
            index += 1
            continue

        footnote_match = _FOOTNOTE_DEF_RE.match(stripped)
        if footnote_match:
            footnote_id = footnote_match.group(1).strip()
            content_lines = [footnote_match.group(2).lstrip()]
            lookahead = index + 1
            while lookahead < len(lines):
                next_line = lines[lookahead]
                if next_line.startswith("    ") or next_line.startswith("\t"):
                    content_lines.append(next_line.lstrip())
                    lookahead += 1
                    continue
                break
            raw_content = "\n".join(content_lines).strip()
            runs, inline_diagnostics, _ = _parse_inline(raw_content, line=line_number)
            diagnostics.extend(inline_diagnostics)
            if footnote_id in footnotes:
                diagnostics.append(
                    MarkdownDiagnostic(
                        code="E_MD_FOOTNOTE_DUPLICATE",
                        message=f"Définition de note en double: [^{footnote_id}].",
                        line=line_number,
                        column=1,
                    )
                )
            footnotes[footnote_id] = FootnoteDefinition(
                identifier=footnote_id,
                runs=runs,
                raw_text=raw_content,
                line=line_number,
            )
            index = lookahead
            continue

        if stripped == ":::bibl":
            bibliography_lines: list[str] = []
            start_line = line_number
            lookahead = index + 1
            closed = False
            while lookahead < len(lines):
                candidate = lines[lookahead].strip()
                if candidate == ":::":  # bloc fermant
                    closed = True
                    break
                bibliography_lines.append(lines[lookahead])
                lookahead += 1
            if not closed:
                diagnostics.append(
                    MarkdownDiagnostic(
                        code="E_MD_BIBL_UNCLOSED",
                        message="Bloc bibliographique :::bibl non fermé.",
                        line=start_line,
                        column=1,
                    )
                )
                index = lookahead
            else:
                index = lookahead + 1

            entries_raw: list[str] = []
            for bibl_line in bibliography_lines:
                candidate = bibl_line.strip()
                if not candidate:
                    continue
                if candidate.startswith("- "):
                    entries_raw.append(candidate[2:].strip())
                    continue
                if entries_raw:
                    entries_raw[-1] = f"{entries_raw[-1]} {candidate}"
                else:
                    entries_raw.append(candidate)
            entries = tuple(BibliographyEntry(raw_text=item) for item in entries_raw if item)
            blocks.append(BibliographyBlock(entries=entries, line=start_line))
            continue

        heading_match = _HEADING_RE.match(stripped)
        if heading_match:
            level = len(heading_match.group(1))
            title_text = heading_match.group(2).strip()
            runs, inline_diagnostics, refs = _parse_inline(title_text, line=line_number)
            diagnostics.extend(inline_diagnostics)
            referenced_footnotes.extend(refs)
            if previous_heading_level is not None and level > previous_heading_level + 1:
                diagnostics.append(
                    MarkdownDiagnostic(
                        code="W_MD_HEADING_JUMP",
                        message=f"Saut de niveau de titre incohérent: H{previous_heading_level} vers H{level}.",
                        severity="WARNING",
                        line=line_number,
                        column=1,
                    )
                )
            previous_heading_level = level
            blocks.append(HeadingBlock(level=level, runs=runs, line=line_number))
            index += 1
            continue

        if stripped == "---":
            blocks.append(RuleBlock(line=line_number))
            index += 1
            continue

        if stripped.startswith(">"):
            quote_lines: list[str] = []
            lookahead = index
            while lookahead < len(lines):
                candidate = lines[lookahead].strip()
                if not candidate.startswith(">"):
                    break
                content = candidate[1:].lstrip()
                quote_lines.append(content)
                lookahead += 1

            paragraphs: list[tuple[InlineRun, ...]] = []
            paragraph_buffer: list[str] = []
            for quote_line in quote_lines:
                if quote_line.strip():
                    paragraph_buffer.append(quote_line.strip())
                    continue
                if paragraph_buffer:
                    paragraph_text = " ".join(paragraph_buffer).strip()
                    runs, inline_diagnostics, refs = _parse_inline(paragraph_text, line=line_number)
                    diagnostics.extend(inline_diagnostics)
                    referenced_footnotes.extend(refs)
                    paragraphs.append(runs)
                    paragraph_buffer = []
            if paragraph_buffer:
                paragraph_text = " ".join(paragraph_buffer).strip()
                runs, inline_diagnostics, refs = _parse_inline(paragraph_text, line=line_number)
                diagnostics.extend(inline_diagnostics)
                referenced_footnotes.extend(refs)
                paragraphs.append(runs)

            blocks.append(QuoteBlock(paragraphs=tuple(paragraphs), line=line_number))
            index = lookahead
            continue

        unordered_match = _UNORDERED_LIST_RE.match(stripped)
        ordered_match = _ORDERED_LIST_RE.match(stripped)
        if unordered_match or ordered_match:
            ordered = ordered_match is not None
            lookahead = index
            items_raw: list[str] = []
            while lookahead < len(lines):
                candidate = lines[lookahead]
                stripped_candidate = candidate.strip()
                if not stripped_candidate:
                    break
                matcher = _ORDERED_LIST_RE if ordered else _UNORDERED_LIST_RE
                item_match = matcher.match(stripped_candidate)
                if item_match is not None:
                    items_raw.append(item_match.group(1).strip())
                    lookahead += 1
                    continue
                if (candidate.startswith("  ") or candidate.startswith("\t")) and items_raw:
                    continuation = stripped_candidate
                    items_raw[-1] = f"{items_raw[-1]} {continuation}"
                    lookahead += 1
                    continue
                break

            parsed_items: list[tuple[InlineRun, ...]] = []
            for item in items_raw:
                runs, inline_diagnostics, refs = _parse_inline(item, line=line_number)
                diagnostics.extend(inline_diagnostics)
                referenced_footnotes.extend(refs)
                parsed_items.append(runs)

            blocks.append(ListBlock(ordered=ordered, items=tuple(parsed_items), line=line_number))
            index = lookahead
            continue

        paragraph_lines: list[str] = [raw_line.strip()]
        lookahead = index + 1
        while lookahead < len(lines):
            candidate = lines[lookahead]
            if not candidate.strip():
                break
            if _looks_like_block_start(candidate):
                break
            paragraph_lines.append(candidate.strip())
            lookahead += 1
        paragraph_text = " ".join(paragraph_lines).strip()
        runs, inline_diagnostics, refs = _parse_inline(paragraph_text, line=line_number)
        diagnostics.extend(inline_diagnostics)
        referenced_footnotes.extend(refs)
        blocks.append(ParagraphBlock(runs=runs, line=line_number))
        index = lookahead

    reference_order = _dedupe_ordered(referenced_footnotes)
    for ref_id in reference_order:
        if ref_id not in footnotes:
            diagnostics.append(
                MarkdownDiagnostic(
                    code="E_MD_FOOTNOTE_UNDEFINED",
                    message=f"Appel de note sans définition: [^{ref_id}].",
                    line=None,
                    column=None,
                )
            )
    for footnote_id, definition in footnotes.items():
        if footnote_id not in reference_order:
            diagnostics.append(
                MarkdownDiagnostic(
                    code="W_MD_FOOTNOTE_ORPHAN",
                    message=f"Définition de note orpheline: [^{footnote_id}].",
                    severity="WARNING",
                    line=definition.line,
                    column=1,
                )
            )

    document = MarkdownDocument(
        blocks=tuple(blocks),
        footnotes=footnotes,
        footnote_reference_order=reference_order,
    )
    return MarkdownParseResult(document=document, diagnostics=tuple(diagnostics))
