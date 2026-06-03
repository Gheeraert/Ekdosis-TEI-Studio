from __future__ import annotations

from ets.domain import EditionConfig
from ets.validation import ValidationReport

from .parser import _parse_castlist


def validate_castlist_text(text: str, config: EditionConfig) -> ValidationReport:
    _, diagnostics = _parse_castlist(text, len(config.witnesses))
    return ValidationReport(diagnostics=diagnostics)
