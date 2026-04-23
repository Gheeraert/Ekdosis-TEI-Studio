from __future__ import annotations

from .models import ValidationMessage, ValidationReport, ValidationSeverity, ValidationStatus


def format_validation_report(report: ValidationReport, *, title: str) -> str:
    status_label = _status_label(report.status)
    lines = [
        f"{title}",
        f"Statut: {status_label}",
        f"Erreurs bloquantes: {report.blocking_error_count}",
        f"Avertissements: {report.warning_count}",
    ]
    if report.messages:
        lines.append("")
        lines.append("Details:")
        for message in report.messages:
            lines.append(_format_message(message))
    return "\n".join(lines)


def _status_label(status: ValidationStatus) -> str:
    if status is ValidationStatus.VALID:
        return "Import conforme"
    if status is ValidationStatus.VALID_WITH_WARNINGS:
        return "Import conforme avec avertissements"
    return "Import refuse"


def _format_message(message: ValidationMessage) -> str:
    prefix = "Erreur" if message.severity is ValidationSeverity.ERROR else "Avertissement"
    core = f"- {prefix} [{message.code}] {message.message}"
    details: list[str] = []
    if message.location:
        details.append(message.location)
    if message.style_name:
        details.append(f"style={message.style_name}")
    if message.suggestion:
        details.append(f"suggestion={message.suggestion}")
    if details:
        return f"{core} ({'; '.join(details)})"
    return core

