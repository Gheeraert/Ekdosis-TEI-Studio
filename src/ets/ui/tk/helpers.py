from __future__ import annotations

from ets.application import AppDiagnostic
from ets.domain import EditionConfig


def format_config_status(config: EditionConfig | None, config_path: str | None) -> str:
    if config is None:
        return "Configuration: aucune"
    origin = config_path if config_path else "(mémoire)"
    return (
        f"Configuration: {config.title} | témoins={len(config.witnesses)} | "
        f"réf={config.witnesses[config.reference_witness].siglum} | {origin}"
    )


def diagnostic_line_numbers(diagnostics: list[AppDiagnostic]) -> list[int]:
    numbers: list[int] = []
    seen: set[int] = set()
    for item in diagnostics:
        if item.line_number is None:
            continue
        if item.line_number in seen:
            continue
        seen.add(item.line_number)
        numbers.append(item.line_number)
    return sorted(numbers)

