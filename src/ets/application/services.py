from __future__ import annotations

from pathlib import Path

from lxml import etree

from ets.core import run_pipeline_from_text
from ets.domain import EditionConfig
from ets.html import render_html_preview_from_tei
from ets.parser import load_config as _load_config
from ets.validation import InputValidationError, ValidationReport, validate_input_text

from .models import AppDiagnostic, GenerationResult, HtmlResult, ValidationResult


def _map_diagnostics(report: ValidationReport) -> list[AppDiagnostic]:
    return [AppDiagnostic.from_validation(item) for item in report.diagnostics]


def _has_error(diagnostics: list[AppDiagnostic]) -> bool:
    return any(item.level == "ERROR" for item in diagnostics)


def _single_diagnostic(code: str, message: str) -> list[AppDiagnostic]:
    return [AppDiagnostic(level="ERROR", code=code, message=message)]


def load_config(config_path: str | Path) -> EditionConfig:
    """Load an EditionConfig from a JSON path."""
    return _load_config(config_path)


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
