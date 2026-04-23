from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class EditorialSourceKind(str, Enum):
    HOME_PAGE = "home_page"
    GENERAL_INTRO = "general_intro"
    PLAY_NOTICE = "play_notice"
    PLAY_PREFACE = "play_preface"


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class ValidationStatus(str, Enum):
    VALID = "VALID"
    VALID_WITH_WARNINGS = "VALID_WITH_WARNINGS"
    INVALID = "INVALID"


@dataclass(frozen=True)
class ValidationMessage:
    severity: ValidationSeverity
    code: str
    message: str
    location: str | None = None
    style_name: str | None = None
    paragraph_index: int | None = None
    suggestion: str | None = None


@dataclass(frozen=True)
class ValidationReport:
    status: ValidationStatus
    messages: tuple[ValidationMessage, ...]

    @property
    def blocking_error_count(self) -> int:
        return sum(1 for item in self.messages if item.severity is ValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for item in self.messages if item.severity is ValidationSeverity.WARNING)

    @classmethod
    def from_messages(cls, messages: list[ValidationMessage] | tuple[ValidationMessage, ...]) -> ValidationReport:
        frozen_messages = tuple(messages)
        has_errors = any(item.severity is ValidationSeverity.ERROR for item in frozen_messages)
        has_warnings = any(item.severity is ValidationSeverity.WARNING for item in frozen_messages)
        if has_errors:
            status = ValidationStatus.INVALID
        elif has_warnings:
            status = ValidationStatus.VALID_WITH_WARNINGS
        else:
            status = ValidationStatus.VALID
        return cls(status=status, messages=frozen_messages)


class ParagraphCategory(str, Enum):
    DOC_TITLE = "DOC_TITLE"
    DOC_SUBTITLE = "DOC_SUBTITLE"
    HEADING_1 = "HEADING_1"
    HEADING_2 = "HEADING_2"
    HEADING_3 = "HEADING_3"
    HEADING_4 = "HEADING_4"
    PARA = "PARA"
    PARA_NOINDENT = "PARA_NOINDENT"
    BLOCK_QUOTE = "BLOCK_QUOTE"
    CAPTION = "CAPTION"


class InlineKind(str, Enum):
    TEXT = "text"
    ITALIC = "italic"
    BOLD = "bold"
    UNDERLINE = "underline"
    SMALLCAPS = "smallcaps"
    SUP = "sup"
    SUB = "sub"
    STRIKETHROUGH = "strikethrough"
    LINK = "link"
    NOTE = "note"


@dataclass(frozen=True)
class InlineNode:
    kind: InlineKind
    text: str = ""
    children: tuple["InlineNode", ...] = ()
    target: str | None = None


class BlockKind(str, Enum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    LIST = "list"
    TABLE = "table"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ParsedBlock:
    kind: BlockKind
    index: int
    style_name: str | None = None
    heading_level: int | None = None
    inlines: tuple[InlineNode, ...] = ()
    list_items: tuple[tuple[InlineNode, ...], ...] = ()
    ordered_list: bool = False
    table_rows: tuple[tuple[tuple[InlineNode, ...], ...], ...] = ()
    table_complex_reason: str | None = None
    raw_type: str | None = None


@dataclass(frozen=True)
class ParsedDocument:
    source_path: Path
    blocks: tuple[ParsedBlock, ...]


@dataclass(frozen=True)
class EditorialImportResult:
    source_path: Path
    source_kind: EditorialSourceKind
    report: ValidationReport
    tei_xml: str | None = None

