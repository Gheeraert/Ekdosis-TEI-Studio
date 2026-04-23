from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .models import ParagraphCategory


def normalize_style_name(style_name: str) -> str:
    normalized = unicodedata.normalize("NFKD", style_name.strip())
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower()
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered.strip()


@dataclass(frozen=True)
class StyleResolution:
    category: ParagraphCategory
    warning: bool = False


class WordStyleRegistry:
    def __init__(self) -> None:
        self._allowed_map: dict[str, StyleResolution] = {}
        self._install_defaults()

    def _register(
        self,
        names: tuple[str, ...],
        category: ParagraphCategory,
        *,
        warning: bool = False,
    ) -> None:
        resolution = StyleResolution(category=category, warning=warning)
        for name in names:
            self._allowed_map[normalize_style_name(name)] = resolution

    def _install_defaults(self) -> None:
        self._register(("Titre", "Title"), ParagraphCategory.DOC_TITLE)
        self._register(("Sous-titre", "Sous titre", "Subtitle"), ParagraphCategory.DOC_SUBTITLE)
        self._register(("Titre 1", "Heading 1"), ParagraphCategory.HEADING_1)
        self._register(("Titre 2", "Heading 2"), ParagraphCategory.HEADING_2)
        self._register(("Titre 3", "Heading 3"), ParagraphCategory.HEADING_3)
        self._register(("Titre 4", "Heading 4"), ParagraphCategory.HEADING_4)
        self._register(("Normal",), ParagraphCategory.PARA)
        self._register(
            (
                "Sans espacement",
                "Sans retrait",
                "No Spacing",
                "No Indent",
                "NoIndent",
            ),
            ParagraphCategory.PARA_NOINDENT,
        )
        self._register(("Citation", "Quote"), ParagraphCategory.BLOCK_QUOTE)
        self._register(("Légende", "Legende", "Caption"), ParagraphCategory.CAPTION)

        self._register(("Body Text", "Corps de texte"), ParagraphCategory.PARA, warning=True)
        self._register(("List Paragraph",), ParagraphCategory.PARA, warning=True)

    def resolve_style_category(self, style_name: str) -> StyleResolution | None:
        key = normalize_style_name(style_name)
        return self._allowed_map.get(key)

