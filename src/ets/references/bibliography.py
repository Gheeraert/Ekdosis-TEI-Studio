from __future__ import annotations

import re
from dataclasses import dataclass

from .models import BibliographyEntry, BibliographyState, CitationOccurrence, ReferenceRecord
from .styles import format_bibliography_entry

_CITATION_PATTERN = re.compile(r"\{\{CITE:(?P<body>[^}]+)\}\}")


@dataclass(frozen=True)
class CitationTokenData:
    reference_id: str
    locator: str | None = None
    prefix: str | None = None
    suffix: str | None = None
    mode: str = "note"


def build_citation_token(
    reference_id: str,
    *,
    locator: str = "",
    prefix: str = "",
    suffix: str = "",
    mode: str = "note",
) -> str:
    safe_reference_id = _escape_token_part(reference_id.strip())
    parts = [safe_reference_id]
    if locator.strip():
        parts.append(f"locator={_escape_token_part(locator.strip())}")
    if prefix.strip():
        parts.append(f"prefix={_escape_token_part(prefix.strip())}")
    if suffix.strip():
        parts.append(f"suffix={_escape_token_part(suffix.strip())}")
    if mode.strip() and mode.strip() != "note":
        parts.append(f"mode={_escape_token_part(mode.strip())}")
    return "{{CITE:" + "|".join(parts) + "}}"


def parse_citation_token(token: str) -> CitationTokenData | None:
    match = _CITATION_PATTERN.fullmatch(token.strip())
    if not match:
        return None
    body = match.group("body")
    chunks = [item.strip() for item in _split_token_fields(body) if item.strip()]
    if not chunks:
        return None
    reference_id = _unescape_token_part(chunks[0])
    if not reference_id or "=" in reference_id:
        return None
    values: dict[str, str] = {}
    for item in chunks[1:]:
        if "=" not in item:
            continue
        key, value = item.split("=", maxsplit=1)
        values[key.strip().lower()] = _unescape_token_part(value.strip())
    return CitationTokenData(
        reference_id=reference_id,
        locator=values.get("locator") or None,
        prefix=values.get("prefix") or None,
        suffix=values.get("suffix") or None,
        mode=values.get("mode", "note"),
    )


def extract_citations(text: str, *, target_context: str | None = None) -> tuple[CitationOccurrence, ...]:
    found: list[CitationOccurrence] = []
    for index, match in enumerate(_CITATION_PATTERN.finditer(text), start=1):
        token = parse_citation_token(match.group(0))
        if token is None:
            continue
        found.append(
            CitationOccurrence(
                id=f"cit-{index}",
                reference_id=token.reference_id,
                locator=token.locator,
                prefix=token.prefix,
                suffix=token.suffix,
                citation_mode=token.mode,
                target_context=target_context,
            )
        )
    return tuple(found)


def build_bibliography_state(
    references_by_id: dict[str, ReferenceRecord],
    citations: tuple[CitationOccurrence, ...],
    *,
    style_id: str,
) -> BibliographyState:
    cited_ids: list[str] = []
    for citation in citations:
        if citation.reference_id in references_by_id and citation.reference_id not in cited_ids:
            cited_ids.append(citation.reference_id)
    entries = sorted(
        (
            BibliographyEntry(
                reference_id=ref_id,
                rendered=format_bibliography_entry(references_by_id[ref_id], style_id),
                sort_key=_sort_key(references_by_id[ref_id]),
            )
            for ref_id in cited_ids
        ),
        key=lambda item: item.sort_key,
    )
    return BibliographyState(
        style_id=style_id,
        generated_entries=tuple(entries),
        cited_reference_ids=tuple(cited_ids),
    )


def _sort_key(record: ReferenceRecord) -> str:
    author = record.authors[0].lower() if record.authors else "zzz"
    title = record.title.lower()
    date = (record.date or "zzzz").lower()
    return f"{author}|{date}|{title}"


def _split_token_fields(body: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    escaped = False
    for char in body:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "|":
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    parts.append("".join(current))
    return parts


def _escape_token_part(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|")


def _unescape_token_part(value: str) -> str:
    chars: list[str] = []
    escaped = False
    for char in value:
        if escaped:
            chars.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        chars.append(char)
    if escaped:
        chars.append("\\")
    return "".join(chars)
