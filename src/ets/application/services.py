from __future__ import annotations

from pathlib import Path
from typing import Any

from lxml import etree

from ets.annotations import (
    Annotation,
    AnnotationCollection,
    AnnotationTargetNotFoundError,
    AnnotationValidationError,
    create_annotation as _create_annotation,
    delete_annotation as _delete_annotation,
    inject_annotations_into_tei,
    load_annotations as _load_annotations,
    parse_annotations_payload,
    update_annotation as _update_annotation,
)
from ets.annotations import save_annotations as _save_annotations
from ets.core import run_pipeline_from_text
from ets.domain import EditionConfig
from ets.html import render_html_preview_from_tei
from ets.parser import load_config as _load_config
from ets.parser import save_config as _save_config
from ets.validation import InputValidationError, ValidationReport, validate_input_text

from .models import AppDiagnostic, GenerationResult, HtmlResult, ValidationResult
from .naming import build_default_basename


def _map_diagnostics(report: ValidationReport) -> list[AppDiagnostic]:
    return [AppDiagnostic.from_validation(item) for item in report.diagnostics]


def _has_error(diagnostics: list[AppDiagnostic]) -> bool:
    return any(item.level == "ERROR" for item in diagnostics)


def _single_diagnostic(code: str, message: str) -> list[AppDiagnostic]:
    return [AppDiagnostic(level="ERROR", code=code, message=message)]


def _map_annotation_diagnostics(
    diagnostics: list[object], default_code: str, default_message: str
) -> list[AppDiagnostic]:
    mapped: list[AppDiagnostic] = []
    for item in diagnostics:
        code = getattr(item, "code", default_code)
        message = getattr(item, "message", default_message)
        annotation_id = getattr(item, "annotation_id", None)
        annotation_field = getattr(item, "field", None)
        mapped.append(
            AppDiagnostic(
                level="ERROR",
                code=code,
                message=message,
                annotation_id=annotation_id,
                annotation_field=annotation_field,
            )
        )
    if mapped:
        return mapped
    return _single_diagnostic(default_code, default_message)


def load_config(config_path: str | Path) -> EditionConfig:
    """Load an EditionConfig from a JSON path."""
    return _load_config(config_path)


def save_config(config: EditionConfig, output_path: str | Path) -> Path:
    """Save config as canonical JSON and return resolved path."""
    return _save_config(config, output_path)


def validate_text(text: str, config: EditionConfig) -> ValidationResult:
    """Run input-level transcription validation only (pre-parse checks)."""
    report = validate_input_text(text, len(config.witnesses), witness_sigla=[w.siglum for w in config.witnesses])
    diagnostics = _map_diagnostics(report)
    if _has_error(diagnostics):
        return ValidationResult(ok=False, diagnostics=diagnostics, message="Input validation failed.")
    return ValidationResult(ok=True, diagnostics=diagnostics, message="Input validation successful.")


def generate_tei_from_text(text: str, config: EditionConfig) -> GenerationResult:
    """Generate TEI XML from in-memory transcription text."""
    validation = validate_text(text, config)
    if not validation.ok:
        return GenerationResult(ok=False, tei_xml=None, diagnostics=validation.diagnostics, message=validation.message)

    try:
        tei_xml = run_pipeline_from_text(text, config, validate_input=False)
    except InputValidationError as exc:
        diagnostics = [AppDiagnostic.from_validation(item) for item in exc.diagnostics]
        return GenerationResult(ok=False, tei_xml=None, diagnostics=diagnostics, message=str(exc))
    except ValueError as exc:
        return GenerationResult(
            ok=False,
            tei_xml=None,
            diagnostics=_single_diagnostic("E_PIPELINE", str(exc)),
            message=str(exc),
        )
    return GenerationResult(ok=True, tei_xml=tei_xml, diagnostics=validation.diagnostics, message="TEI generation successful.")


def generate_html_preview_from_tei(tei_xml: str) -> HtmlResult:
    """Generate preview HTML from TEI XML."""
    try:
        html = render_html_preview_from_tei(tei_xml)
    except (etree.LxmlError, ValueError, OSError) as exc:
        return HtmlResult(ok=False, html=None, diagnostics=_single_diagnostic("E_HTML_PREVIEW", str(exc)), message=str(exc))
    return HtmlResult(ok=True, html=html, message="HTML preview generation successful.")


def generate_html_preview_from_text(text: str, config: EditionConfig) -> HtmlResult:
    """Generate preview HTML from in-memory transcription text."""
    generation = generate_tei_from_text(text, config)
    if not generation.ok or generation.tei_xml is None:
        return HtmlResult(
            ok=False,
            html=None,
            diagnostics=generation.diagnostics,
            message=generation.message or "HTML preview generation failed.",
        )
    html_result = generate_html_preview_from_tei(generation.tei_xml)
    if not html_result.ok:
        return HtmlResult(
            ok=False,
            html=None,
            diagnostics=html_result.diagnostics,
            message=html_result.message,
        )
    return HtmlResult(ok=True, html=html_result.html, diagnostics=generation.diagnostics, message=html_result.message)


def export_tei(tei_xml: str, output_path: str | Path) -> Path:
    """Write TEI XML to disk and return the resolved path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tei_xml, encoding="utf-8")
    return path.resolve()


def export_html(html: str, output_path: str | Path) -> Path:
    """Write HTML output to disk and return the resolved path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path.resolve()


def suggest_output_basename(text: str, config: EditionConfig) -> str:
    """Suggest a default output basename like Title_A1_S1of4."""
    return build_default_basename(text, config)


def load_annotations(path: str | Path) -> AnnotationCollection:
    """Load annotations from JSON and validate their shape."""
    return _load_annotations(path)


def save_annotations(collection: AnnotationCollection, output_path: str | Path) -> Path:
    """Save annotations JSON and return resolved path."""
    return _save_annotations(collection, output_path)


def parse_annotation(payload: dict[str, Any]) -> Annotation:
    """Parse and validate a single annotation payload."""
    parsed = parse_annotations_payload({"version": 1, "annotations": [payload]})
    return parsed.annotations[0]


def create_annotation(collection: AnnotationCollection, annotation: Annotation) -> AnnotationCollection:
    """Create an annotation in an in-memory collection."""
    return _create_annotation(collection, annotation)


def update_annotation(collection: AnnotationCollection, annotation: Annotation) -> AnnotationCollection:
    """Update an annotation in an in-memory collection."""
    return _update_annotation(collection, annotation)


def delete_annotation(collection: AnnotationCollection, annotation_id: str) -> AnnotationCollection:
    """Delete an annotation in an in-memory collection."""
    return _delete_annotation(collection, annotation_id)


def enrich_tei_with_annotations(tei_xml: str, annotations: AnnotationCollection) -> GenerationResult:
    """Inject editorial annotations into generated TEI."""
    try:
        enriched = inject_annotations_into_tei(tei_xml, annotations)
    except AnnotationTargetNotFoundError as exc:
        return GenerationResult(
            ok=False,
            tei_xml=None,
            diagnostics=_map_annotation_diagnostics(
                exc.diagnostics,
                default_code="E_ANN_TARGET_NOT_FOUND",
                default_message=str(exc),
            ),
            message=str(exc),
        )
    except AnnotationValidationError as exc:
        return GenerationResult(
            ok=False,
            tei_xml=None,
            diagnostics=_map_annotation_diagnostics(
                exc.diagnostics,
                default_code="E_ANN_INVALID_JSON",
                default_message=str(exc),
            ),
            message=str(exc),
        )
    except ValueError as exc:
        return GenerationResult(
            ok=False,
            tei_xml=None,
            diagnostics=_single_diagnostic("E_ANN_ENRICHMENT", str(exc)),
            message=str(exc),
        )
    return GenerationResult(ok=True, tei_xml=enriched, message="TEI enrichment with annotations successful.")
