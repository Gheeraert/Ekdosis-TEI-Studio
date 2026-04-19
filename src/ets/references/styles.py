from __future__ import annotations

from dataclasses import dataclass

from .models import CitationOccurrence, ReferenceRecord


@dataclass(frozen=True)
class PublicationStyle:
    style_id: str
    label: str
    description: str


STYLES: tuple[PublicationStyle, ...] = (
    PublicationStyle(
        style_id="default_preview",
        label="Aperçu par défaut",
        description="Style éditorial sobre pour lecture locale.",
    ),
    PublicationStyle(
        style_id="simple_note",
        label="Note simple",
        description="Entrées adaptées à un usage en note.",
    ),
    PublicationStyle(
        style_id="simple_author_date",
        label="Auteur-date simple",
        description="Entrées de type auteur (année).",
    ),
)


def get_style(style_id: str) -> PublicationStyle:
    for style in STYLES:
        if style.style_id == style_id:
            return style
    return STYLES[0]


def format_bibliography_entry(record: ReferenceRecord, style_id: str) -> str:
    author_part = ", ".join(record.authors).strip() or "Sans auteur"
    title_part = record.title.strip() or "Sans titre"
    date_part = (record.date or "s.d.").strip()
    publisher_part = (record.publisher or "").strip()
    container_part = (record.container_title or "").strip()

    if style_id == "simple_author_date":
        tail = f"{publisher_part}." if publisher_part else ""
        return f"{author_part} ({date_part}). {title_part}. {tail}".strip()

    if style_id == "simple_note":
        pieces = [author_part, title_part]
        if container_part:
            pieces.append(container_part)
        if publisher_part:
            pieces.append(publisher_part)
        pieces.append(date_part)
        return ", ".join(item for item in pieces if item).strip().rstrip(",") + "."

    default_parts = [author_part, title_part]
    if container_part:
        default_parts.append(container_part)
    if publisher_part:
        default_parts.append(publisher_part)
    default_parts.append(date_part)
    return ", ".join(item for item in default_parts if item).strip().rstrip(",") + "."


def format_inline_citation(record: ReferenceRecord, citation: CitationOccurrence, style_id: str) -> str:
    author = (record.authors[0] if record.authors else "s.a.").strip()
    date = (record.date or "s.d.").strip()
    locator = citation.locator.strip() if citation.locator else ""

    if style_id == "simple_author_date":
        core = f"{author}, {date}"
        return f"{core}, {locator}" if locator else core

    base = f"{author}, {record.title}"
    if locator:
        return f"{base}, {locator}"
    return base

