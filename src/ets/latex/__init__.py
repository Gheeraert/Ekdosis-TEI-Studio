from __future__ import annotations

from .ekdosis_from_tei import tei_to_ekdosis
from .standard_from_tei import tei_peritext_to_latex

__all__ = ["tei_peritext_to_latex", "tei_to_ekdosis"]
