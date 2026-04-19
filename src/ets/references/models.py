from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ReferenceRecord:
    id: str
    origin: str
    source_key: str | None
    type: str
    title: str
    authors: tuple[str, ...]
    date: str | None = None
    publisher: str | None = None
    container_title: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    place: str | None = None
    url: str | None = None
    doi: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)
    normalized_data: dict[str, Any] = field(default_factory=dict)
    editor: str | None = None
    translator: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class CitationOccurrence:
    id: str
    reference_id: str
    locator: str | None = None
    prefix: str | None = None
    suffix: str | None = None
    citation_mode: str = "note"
    target_context: str | None = None


@dataclass(frozen=True)
class BibliographyEntry:
    reference_id: str
    rendered: str
    sort_key: str


@dataclass(frozen=True)
class BibliographyState:
    style_id: str
    generated_entries: tuple[BibliographyEntry, ...]
    cited_reference_ids: tuple[str, ...]


@dataclass(frozen=True)
class ImportDiagnostic:
    code: str
    message: str
    severity: str = "ERROR"


@dataclass(frozen=True)
class ImportResult:
    references: tuple[ReferenceRecord, ...]
    diagnostics: tuple[ImportDiagnostic, ...] = ()
    source_format: str = "unknown"

    @property
    def has_errors(self) -> bool:
        return any(item.severity.upper() == "ERROR" for item in self.diagnostics)

