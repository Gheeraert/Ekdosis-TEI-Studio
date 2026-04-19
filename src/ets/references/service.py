from __future__ import annotations

from pathlib import Path
from typing import Iterable
from uuid import uuid4

from .bibliography import build_bibliography_state, build_citation_token, extract_citations
from .importers import import_references
from .models import BibliographyState, CitationOccurrence, ImportResult, ReferenceRecord
from .styles import STYLES


class ReferencesService:
    def __init__(self) -> None:
        self._references: dict[str, ReferenceRecord] = {}
        self._style_id = STYLES[0].style_id

    @property
    def style_id(self) -> str:
        return self._style_id

    def set_style(self, style_id: str) -> None:
        known = {style.style_id for style in STYLES}
        self._style_id = style_id if style_id in known else STYLES[0].style_id

    def available_styles(self) -> tuple[str, ...]:
        return tuple(style.style_id for style in STYLES)

    def add_manual_reference(
        self,
        *,
        title: str,
        authors: Iterable[str],
        date: str = "",
        reference_type: str = "book",
        publisher: str = "",
        container_title: str = "",
        place: str = "",
        volume: str = "",
        issue: str = "",
        pages: str = "",
        url: str = "",
        doi: str = "",
        source_key: str = "",
        editor: str = "",
        translator: str = "",
        note: str = "",
    ) -> ReferenceRecord:
        reference = ReferenceRecord(
            id=f"ref-{uuid4().hex[:10]}",
            origin="manual",
            source_key=source_key.strip() or None,
            type=reference_type.strip() or "book",
            title=title.strip() or "Sans titre",
            authors=tuple(author.strip() for author in authors if author.strip()),
            date=date.strip() or None,
            publisher=publisher.strip() or None,
            container_title=container_title.strip() or None,
            volume=volume.strip() or None,
            issue=issue.strip() or None,
            pages=pages.strip() or None,
            place=place.strip() or None,
            url=url.strip() or None,
            doi=doi.strip() or None,
            raw_data={},
            normalized_data={},
            editor=editor.strip() or None,
            translator=translator.strip() or None,
            note=note.strip() or None,
        )
        self._references[reference.id] = reference
        return reference

    def import_from_file(self, path: str | Path) -> ImportResult:
        result = import_references(path)
        for reference in result.references:
            self._references[reference.id] = reference
        return result

    def all_references(self) -> tuple[ReferenceRecord, ...]:
        return tuple(
            sorted(
                self._references.values(),
                key=lambda ref: (
                    (ref.authors[0].lower() if ref.authors else "zzz"),
                    (ref.date or "zzzz"),
                    ref.title.lower(),
                ),
            )
        )

    def get_reference(self, reference_id: str) -> ReferenceRecord | None:
        return self._references.get(reference_id)

    def search_references(self, query: str) -> tuple[ReferenceRecord, ...]:
        q = query.strip().lower()
        if not q:
            return self.all_references()
        matches: list[ReferenceRecord] = []
        for ref in self._references.values():
            haystack = " ".join(
                (
                    ref.id,
                    ref.title,
                    " ".join(ref.authors),
                    ref.date or "",
                    ref.container_title or "",
                    ref.publisher or "",
                    ref.doi or "",
                    ref.url or "",
                )
            ).lower()
            if q in haystack:
                matches.append(ref)
        return tuple(
            sorted(
                matches,
                key=lambda ref: (
                    (ref.authors[0].lower() if ref.authors else "zzz"),
                    (ref.date or "zzzz"),
                    ref.title.lower(),
                ),
            )
        )

    def build_citation_token(
        self,
        reference_id: str,
        *,
        locator: str = "",
        prefix: str = "",
        suffix: str = "",
        mode: str = "note",
    ) -> str:
        if reference_id not in self._references:
            raise KeyError(f"Unknown reference id: {reference_id}")
        return build_citation_token(
            reference_id,
            locator=locator,
            prefix=prefix,
            suffix=suffix,
            mode=mode,
        )

    def extract_citations(self, text: str, *, target_context: str | None = None) -> tuple[CitationOccurrence, ...]:
        return extract_citations(text, target_context=target_context)

    def bibliography_from_text(self, text: str, *, target_context: str | None = None) -> BibliographyState:
        citations = self.extract_citations(text, target_context=target_context)
        return build_bibliography_state(self._references, citations, style_id=self._style_id)

    @staticmethod
    def bibliography_to_text(state: BibliographyState) -> str:
        if not state.generated_entries:
            return "Aucune référence citée pour le moment."
        lines: list[str] = []
        for index, entry in enumerate(state.generated_entries, start=1):
            lines.append(f"{index}. {entry.rendered}")
        return "\n".join(lines)

