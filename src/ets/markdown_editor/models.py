from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MarkdownDiagnostic:
    code: str
    message: str
    severity: str = "ERROR"
    line: int | None = None
    column: int | None = None


@dataclass(frozen=True)
class TextRun:
    text: str


@dataclass(frozen=True)
class ItalicRun:
    children: tuple["InlineRun", ...]


@dataclass(frozen=True)
class BoldRun:
    children: tuple["InlineRun", ...]


@dataclass(frozen=True)
class UnderlineRun:
    children: tuple["InlineRun", ...]


@dataclass(frozen=True)
class SupRun:
    children: tuple["InlineRun", ...]


@dataclass(frozen=True)
class SubRun:
    children: tuple["InlineRun", ...]


@dataclass(frozen=True)
class CapsRun:
    children: tuple["InlineRun", ...]


@dataclass(frozen=True)
class SmallCapsRun:
    children: tuple["InlineRun", ...]


@dataclass(frozen=True)
class LinkRun:
    children: tuple["InlineRun", ...]
    target: str


@dataclass(frozen=True)
class FootnoteRefRun:
    identifier: str


InlineRun = (
    TextRun
    | ItalicRun
    | BoldRun
    | UnderlineRun
    | SupRun
    | SubRun
    | CapsRun
    | SmallCapsRun
    | LinkRun
    | FootnoteRefRun
)


@dataclass(frozen=True)
class HeadingBlock:
    level: int
    runs: tuple[InlineRun, ...]
    line: int


@dataclass(frozen=True)
class ParagraphBlock:
    runs: tuple[InlineRun, ...]
    line: int


@dataclass(frozen=True)
class ListBlock:
    ordered: bool
    items: tuple[tuple[InlineRun, ...], ...]
    line: int


@dataclass(frozen=True)
class QuoteBlock:
    paragraphs: tuple[tuple[InlineRun, ...], ...]
    line: int


@dataclass(frozen=True)
class RuleBlock:
    line: int


@dataclass(frozen=True)
class BibliographyEntry:
    raw_text: str
    entry_id: str | None = None
    origin: str = "manual"
    source_type: str | None = None
    source_key: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class BibliographyBlock:
    entries: tuple[BibliographyEntry, ...]
    line: int


Block = HeadingBlock | ParagraphBlock | ListBlock | QuoteBlock | RuleBlock | BibliographyBlock


@dataclass(frozen=True)
class FootnoteDefinition:
    identifier: str
    runs: tuple[InlineRun, ...]
    raw_text: str
    line: int


@dataclass(frozen=True)
class MarkdownDocument:
    blocks: tuple[Block, ...]
    footnotes: dict[str, FootnoteDefinition]
    footnote_reference_order: tuple[str, ...] = ()


@dataclass(frozen=True)
class MarkdownParseResult:
    document: MarkdownDocument
    diagnostics: tuple[MarkdownDiagnostic, ...] = ()

    @property
    def has_errors(self) -> bool:
        return any(item.severity.upper() == "ERROR" for item in self.diagnostics)
