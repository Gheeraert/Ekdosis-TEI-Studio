from __future__ import annotations

from .models import (
    BlockKind,
    ParagraphCategory,
    ParsedBlock,
    ParsedDocument,
    ValidationMessage,
    ValidationReport,
    ValidationSeverity,
)
from .pandoc_parser import inline_text
from .style_registry import WordStyleRegistry, normalize_style_name


class NoticeImportValidator:
    def __init__(self, style_registry: WordStyleRegistry | None = None) -> None:
        self._styles = style_registry or WordStyleRegistry()

    def validate(self, document: ParsedDocument) -> ValidationReport:
        messages: list[ValidationMessage] = []

        title_count = 0
        previous_heading_level = 0
        saw_bibliography = False
        saw_heading = False
        paragraph_categories: list[ParagraphCategory] = []
        empty_paragraph_count = 0

        for block in document.blocks:
            if block.kind is BlockKind.UNSUPPORTED:
                messages.append(
                    ValidationMessage(
                        severity=ValidationSeverity.ERROR,
                        code="FORBIDDEN_WORD_OBJECT",
                        message=f"Objet Word/Pandoc non pris en charge: {block.raw_type or 'inconnu'}.",
                        location=f"bloc {block.index}",
                        paragraph_index=block.index,
                    )
                )
                continue

            if block.kind is BlockKind.TABLE:
                if block.table_complex_reason:
                    messages.append(
                        ValidationMessage(
                            severity=ValidationSeverity.ERROR,
                            code="TABLE_COMPLEX",
                            message="Tableau non conforme: seules les tables simples sans fusion sont autorisees.",
                            location=f"bloc {block.index}",
                            paragraph_index=block.index,
                            suggestion="Supprimer les fusions et les structures de tableau complexes.",
                        )
                    )
                continue

            if block.kind is BlockKind.LIST:
                continue

            style_name = (block.style_name or "").strip()
            if block.kind is BlockKind.HEADING:
                category = self._heading_category(block)
                if category is None:
                    messages.append(
                        ValidationMessage(
                            severity=ValidationSeverity.ERROR,
                            code="UNKNOWN_PARAGRAPH_STYLE",
                            message=f"Style de titre non autorise: {style_name or 'inconnu'}.",
                            location=f"paragraphe {block.index}",
                            style_name=style_name or None,
                            paragraph_index=block.index,
                        )
                    )
                    continue
            else:
                resolution = self._styles.resolve_style_category(style_name or "Normal")
                if resolution is None:
                    messages.append(
                        ValidationMessage(
                            severity=ValidationSeverity.ERROR,
                            code="UNKNOWN_PARAGRAPH_STYLE",
                            message=f"Style de paragraphe non autorise: {style_name or 'inconnu'}.",
                            location=f"paragraphe {block.index}",
                            style_name=style_name or None,
                            paragraph_index=block.index,
                            suggestion="Utiliser un style Word autorise (Normal, Titre, Citation, etc.).",
                        )
                    )
                    continue
                category = resolution.category
                if resolution.warning:
                    messages.append(
                        ValidationMessage(
                            severity=ValidationSeverity.WARNING,
                            code="STYLE_TOLERATED",
                            message=f"Style tolere mais non recommande: {style_name}.",
                            location=f"paragraphe {block.index}",
                            style_name=style_name,
                            paragraph_index=block.index,
                        )
                    )

            if category is ParagraphCategory.DOC_TITLE:
                title_count += 1
            if category in {
                ParagraphCategory.HEADING_1,
                ParagraphCategory.HEADING_2,
                ParagraphCategory.HEADING_3,
                ParagraphCategory.HEADING_4,
            }:
                saw_heading = True
                current_level = _category_to_level(category)
                if current_level > previous_heading_level + 1 and previous_heading_level != 0:
                    messages.append(
                        ValidationMessage(
                            severity=ValidationSeverity.ERROR,
                            code="HEADING_LEVEL_SKIP",
                            message=(
                                "Saut hierarchique invalide: "
                                f"Titre {previous_heading_level} -> Titre {current_level}."
                            ),
                            location=f"paragraphe {block.index}",
                            paragraph_index=block.index,
                        )
                    )
                if previous_heading_level == 0 and current_level > 1:
                    messages.append(
                        ValidationMessage(
                            severity=ValidationSeverity.ERROR,
                            code="HEADING_LEVEL_SKIP",
                            message=f"Titre {current_level} sans niveau parent precedent.",
                            location=f"paragraphe {block.index}",
                            paragraph_index=block.index,
                        )
                    )
                previous_heading_level = current_level

            raw_text = inline_text(block.inlines).strip()
            if block.kind is BlockKind.PARAGRAPH:
                if not raw_text:
                    empty_paragraph_count += 1
                if category in {ParagraphCategory.PARA, ParagraphCategory.PARA_NOINDENT}:
                    paragraph_categories.append(category)
            if category in {
                ParagraphCategory.HEADING_1,
                ParagraphCategory.HEADING_2,
                ParagraphCategory.HEADING_3,
                ParagraphCategory.HEADING_4,
            } and normalize_style_name(raw_text) == "bibliographie":
                saw_bibliography = True

        if title_count == 0:
            messages.append(
                ValidationMessage(
                    severity=ValidationSeverity.ERROR,
                    code="MISSING_TITLE",
                    message="Absence de titre principal (style Titre/Title).",
                    suggestion="Ajouter un paragraphe en style Titre (ou Title).",
                )
            )
        elif title_count > 1:
            messages.append(
                ValidationMessage(
                    severity=ValidationSeverity.WARNING,
                    code="MULTIPLE_TITLES",
                    message=f"{title_count} titres principaux detectes.",
                )
            )

        if empty_paragraph_count > 0:
            messages.append(
                ValidationMessage(
                    severity=ValidationSeverity.WARNING,
                    code="EMPTY_PARAGRAPH_SERIES",
                    message=f"{empty_paragraph_count} paragraphe(s) vide(s) detecte(s).",
                )
            )

        if _is_irregular_noindent_mix(paragraph_categories):
            messages.append(
                ValidationMessage(
                    severity=ValidationSeverity.WARNING,
                    code="MIXED_NORMAL_NOINDENT",
                    message="Alternance peu coherente entre paragraphe normal et paragraphe sans retrait.",
                )
            )

        if saw_heading and not saw_bibliography:
            messages.append(
                ValidationMessage(
                    severity=ValidationSeverity.WARNING,
                    code="MISSING_BIBLIO_SECTION",
                    message="Rubrique Bibliographie absente.",
                )
            )

        return ValidationReport.from_messages(messages)

    def _heading_category(self, block: ParsedBlock) -> ParagraphCategory | None:
        if block.heading_level == 1:
            return ParagraphCategory.HEADING_1
        if block.heading_level == 2:
            return ParagraphCategory.HEADING_2
        if block.heading_level == 3:
            return ParagraphCategory.HEADING_3
        if block.heading_level == 4:
            return ParagraphCategory.HEADING_4
        return None


def _category_to_level(category: ParagraphCategory) -> int:
    if category is ParagraphCategory.HEADING_1:
        return 1
    if category is ParagraphCategory.HEADING_2:
        return 2
    if category is ParagraphCategory.HEADING_3:
        return 3
    if category is ParagraphCategory.HEADING_4:
        return 4
    return 0


def _is_irregular_noindent_mix(categories: list[ParagraphCategory]) -> bool:
    has_normal = any(cat is ParagraphCategory.PARA for cat in categories)
    has_noindent = any(cat is ParagraphCategory.PARA_NOINDENT for cat in categories)
    if not (has_normal and has_noindent):
        return False
    transitions = 0
    for left, right in zip(categories, categories[1:]):
        if left != right:
            transitions += 1
    return transitions >= 2
