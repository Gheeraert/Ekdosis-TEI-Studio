from __future__ import annotations

from dataclasses import dataclass, field

from ets.validation import ValidationDiagnostic


@dataclass(frozen=True)
class AppDiagnostic:
    level: str
    code: str
    message: str
    annotation_id: str | None = None
    annotation_field: str | None = None
    line_number: int | None = None
    block_index: int | None = None
    act: str | None = None
    scene: str | None = None
    speaker: str | None = None
    excerpt: str | None = None
    block_type: str | None = None
    token_counts: list[int] | None = None
    witness_labels: list[str] | None = None
    block_lines: list[str] | None = None

    @classmethod
    def from_validation(cls, diagnostic: ValidationDiagnostic) -> "AppDiagnostic":
        return cls(
            level=diagnostic.level.value,
            code=diagnostic.code,
            message=diagnostic.message,
            line_number=diagnostic.line_number,
            block_index=diagnostic.block_index,
            act=diagnostic.act,
            scene=diagnostic.scene,
            speaker=diagnostic.speaker,
            excerpt=diagnostic.excerpt,
            block_type=diagnostic.block_type,
            token_counts=diagnostic.token_counts,
            witness_labels=diagnostic.witness_labels,
            block_lines=diagnostic.block_lines,
        )


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    diagnostics: list[AppDiagnostic] = field(default_factory=list)
    message: str | None = None


@dataclass(frozen=True)
class GenerationResult:
    ok: bool
    tei_xml: str | None = None
    diagnostics: list[AppDiagnostic] = field(default_factory=list)
    message: str | None = None


@dataclass(frozen=True)
class HtmlResult:
    ok: bool
    html: str | None = None
    diagnostics: list[AppDiagnostic] = field(default_factory=list)
    message: str | None = None
