from __future__ import annotations

from dataclasses import dataclass, field

SUPPORTED_ANCHOR_KINDS = {"line", "line_range", "stage"}
SUPPORTED_ANNOTATION_TYPES = {
    "explicative",
    "lexicale",
    "intertextuelle",
    "dramaturgique",
    "textuelle",
    "bibliographique",
}
SUPPORTED_ANNOTATION_STATUS = {"draft", "reviewed", "validated"}


@dataclass(frozen=True)
class AnnotationAnchor:
    kind: str
    act: str
    scene: str
    line: str | None = None
    start_line: str | None = None
    end_line: str | None = None
    stage_index: int | None = None


@dataclass(frozen=True)
class Annotation:
    id: str
    type: str
    anchor: AnnotationAnchor
    content: str
    resp: str | None = None
    status: str = "draft"
    keywords: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AnnotationCollection:
    version: int
    annotations: list[Annotation] = field(default_factory=list)


@dataclass(frozen=True)
class AnnotationDiagnostic:
    code: str
    message: str
    annotation_id: str | None = None
    field: str | None = None


class AnnotationValidationError(ValueError):
    def __init__(self, diagnostics: list[AnnotationDiagnostic]) -> None:
        self.diagnostics = diagnostics
        joined = "; ".join(d.message for d in diagnostics[:5])
        suffix = "" if len(diagnostics) <= 5 else f" (+{len(diagnostics) - 5} more)"
        super().__init__(f"Annotation validation failed: {joined}{suffix}")


class AnnotationTargetNotFoundError(LookupError):
    def __init__(self, diagnostics: list[AnnotationDiagnostic]) -> None:
        self.diagnostics = diagnostics
        joined = "; ".join(d.message for d in diagnostics[:5])
        suffix = "" if len(diagnostics) <= 5 else f" (+{len(diagnostics) - 5} more)"
        super().__init__(f"Annotation target resolution failed: {joined}{suffix}")
