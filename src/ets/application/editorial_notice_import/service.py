from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from uuid import uuid4
import xml.etree.ElementTree as ET

from ..site_publication_config import SitePublicationDialogConfig, SitePublicationDialogPlayConfig
from .models import (
    EditorialImportResult,
    EditorialSourceKind,
    ValidationMessage,
    ValidationReport,
    ValidationSeverity,
)
from .pandoc_bridge import PandocBridge, PandocExecutionError, PandocNotFoundError
from .pandoc_parser import parse_pandoc_document
from .reporting import format_validation_report
from .tei_builder import NoticeTeiBuilder
from .validator import NoticeImportValidator


@dataclass(frozen=True)
class PreparedPublicationConfig:
    config: SitePublicationDialogConfig
    warnings: tuple[str, ...] = ()


class EditorialNoticeImportService:
    def __init__(
        self,
        *,
        pandoc_bridge: PandocBridge | None = None,
        validator: NoticeImportValidator | None = None,
        tei_builder: NoticeTeiBuilder | None = None,
    ) -> None:
        self._bridge = pandoc_bridge or PandocBridge()
        self._validator = validator or NoticeImportValidator()
        self._builder = tei_builder or NoticeTeiBuilder()

    def inspect_source_for_ui(self, source_path: Path, *, source_kind: EditorialSourceKind) -> EditorialImportResult:
        suffix = source_path.suffix.lower()
        if suffix == ".xml":
            report = self._validate_xml(source_path)
            return EditorialImportResult(source_path=source_path.resolve(), source_kind=source_kind, report=report)
        if suffix == ".docx":
            return self.import_docx(source_path, source_kind=source_kind)
        report = ValidationReport.from_messages(
            [
                ValidationMessage(
                    severity=ValidationSeverity.ERROR,
                    code="UNSUPPORTED_SOURCE_FORMAT",
                    message=f"Format non pris en charge: '{source_path.suffix}'.",
                    suggestion="Choisir un fichier .xml ou .docx.",
                )
            ]
        )
        return EditorialImportResult(source_path=source_path.resolve(), source_kind=source_kind, report=report)

    def import_docx(self, source_path: Path, *, source_kind: EditorialSourceKind) -> EditorialImportResult:
        if not source_path.exists() or not source_path.is_file():
            report = ValidationReport.from_messages(
                [
                    ValidationMessage(
                        severity=ValidationSeverity.ERROR,
                        code="DOCX_UNREADABLE",
                        message=f"Fichier DOCX introuvable: {source_path}.",
                    )
                ]
            )
            return EditorialImportResult(source_path=source_path.resolve(), source_kind=source_kind, report=report)

        try:
            ast_payload = self._bridge.load_docx_ast(source_path)
            parsed_document = parse_pandoc_document(source_path, ast_payload)
            report = self._validator.validate(parsed_document)
            if report.blocking_error_count > 0:
                return EditorialImportResult(source_path=source_path.resolve(), source_kind=source_kind, report=report)
            tei_xml = self._builder.build_document_xml(parsed_document, source_kind=source_kind)
            return EditorialImportResult(
                source_path=source_path.resolve(),
                source_kind=source_kind,
                report=report,
                tei_xml=tei_xml,
            )
        except PandocNotFoundError as exc:
            report = ValidationReport.from_messages(
                [
                    ValidationMessage(
                        severity=ValidationSeverity.ERROR,
                        code="PANDOC_NOT_AVAILABLE",
                        message=str(exc) or "Pandoc est introuvable sur cette machine.",
                        suggestion="Installer pandoc puis relancer l'import DOCX.",
                    )
                ]
            )
            return EditorialImportResult(source_path=source_path.resolve(), source_kind=source_kind, report=report)
        except PandocExecutionError as exc:
            report = ValidationReport.from_messages(
                [
                    ValidationMessage(
                        severity=ValidationSeverity.ERROR,
                        code="DOCX_UNREADABLE",
                        message=f"Echec de lecture du DOCX via pandoc: {exc}",
                    )
                ]
            )
            return EditorialImportResult(source_path=source_path.resolve(), source_kind=source_kind, report=report)
        except ValueError as exc:
            report = ValidationReport.from_messages(
                [
                    ValidationMessage(
                        severity=ValidationSeverity.ERROR,
                        code="DOCX_UNREADABLE",
                        message=f"DOCX invalide ou illisible: {exc}",
                    )
                ]
            )
            return EditorialImportResult(source_path=source_path.resolve(), source_kind=source_kind, report=report)

    def prepare_dialog_config_for_publication(self, config: SitePublicationDialogConfig) -> PreparedPublicationConfig:
        temp_root = _create_temp_root(config)
        warnings: list[str] = []

        home_page_tei = self._prepare_single_source(
            config.home_page_tei,
            source_kind=EditorialSourceKind.HOME_PAGE,
            temp_root=temp_root,
            warnings=warnings,
        )
        general_intro_tei = self._prepare_single_source(
            config.general_intro_tei,
            source_kind=EditorialSourceKind.GENERAL_INTRO,
            temp_root=temp_root,
            warnings=warnings,
        )

        plays: list[SitePublicationDialogPlayConfig] = []
        for play in config.plays:
            notice_xml_path = self._prepare_single_source(
                play.notice_xml_path,
                source_kind=EditorialSourceKind.PLAY_NOTICE,
                temp_root=temp_root,
                warnings=warnings,
            )
            preface_xml_path = self._prepare_single_source(
                play.preface_xml_path,
                source_kind=EditorialSourceKind.PLAY_PREFACE,
                temp_root=temp_root,
                warnings=warnings,
            )
            plays.append(
                SitePublicationDialogPlayConfig(
                    play_slug=play.play_slug,
                    dramatic_xml_path=play.dramatic_xml_path,
                    notice_xml_path=notice_xml_path,
                    preface_xml_path=preface_xml_path,
                    dramatis_xml_path=play.dramatis_xml_path,
                )
            )

        prepared = replace(
            config,
            home_page_tei=home_page_tei,
            general_intro_tei=general_intro_tei,
            plays=tuple(plays),
        )
        return PreparedPublicationConfig(config=prepared, warnings=tuple(warnings))

    def _prepare_single_source(
        self,
        source_path: Path | None,
        *,
        source_kind: EditorialSourceKind,
        temp_root: Path,
        warnings: list[str],
    ) -> Path | None:
        if source_path is None:
            return None
        result = self.inspect_source_for_ui(source_path.resolve(), source_kind=source_kind)
        if result.report.blocking_error_count > 0:
            raise ValueError(
                format_validation_report(
                    result.report,
                    title=_source_kind_label(source_kind, source_path),
                )
            )
        if result.report.warning_count > 0:
            warnings.append(
                format_validation_report(
                    result.report,
                    title=_source_kind_label(source_kind, source_path),
                )
            )
        if source_path.suffix.lower() == ".xml":
            return source_path.resolve()
        if result.tei_xml is None:
            raise ValueError(
                f"Conversion DOCX -> TEI impossible pour '{source_path}'. Aucune sortie XML generee."
            )
        target = _write_temp_tei_file(temp_root, source_path=source_path, source_kind=source_kind, tei_xml=result.tei_xml)
        return target

    def _validate_xml(self, source_path: Path) -> ValidationReport:
        if not source_path.exists() or not source_path.is_file():
            return ValidationReport.from_messages(
                [
                    ValidationMessage(
                        severity=ValidationSeverity.ERROR,
                        code="XML_UNREADABLE",
                        message=f"Fichier XML introuvable: {source_path}.",
                    )
                ]
            )
        try:
            ET.parse(source_path)
        except (ET.ParseError, OSError) as exc:
            return ValidationReport.from_messages(
                [
                    ValidationMessage(
                        severity=ValidationSeverity.ERROR,
                        code="XML_UNREADABLE",
                        message=f"XML illisible: {exc}",
                    )
                ]
            )
        return ValidationReport.from_messages([])


def _source_kind_label(source_kind: EditorialSourceKind, source_path: Path) -> str:
    labels = {
        EditorialSourceKind.HOME_PAGE: "Accueil",
        EditorialSourceKind.GENERAL_INTRO: "Introduction generale",
        EditorialSourceKind.PLAY_NOTICE: "Notice de piece",
        EditorialSourceKind.PLAY_PREFACE: "Preface de dramaturge",
    }
    label = labels.get(source_kind, "Contenu editorial")
    return f"{label}: {source_path.name}"


def _write_temp_tei_file(
    temp_root: Path,
    *,
    source_path: Path,
    source_kind: EditorialSourceKind,
    tei_xml: str,
) -> Path:
    safe_name = source_path.stem.replace(" ", "_")
    target = temp_root / f"{safe_name}_{source_kind.value}.xml"
    suffix = 2
    while target.exists():
        target = temp_root / f"{safe_name}_{source_kind.value}_{suffix}.xml"
        suffix += 1
    target.write_text(tei_xml, encoding="utf-8")
    return target.resolve()


def _create_temp_root(config: SitePublicationDialogConfig) -> Path:
    if config.output_dir is not None:
        base = config.output_dir.resolve().parent
    else:
        base = Path.cwd().resolve()
    base.mkdir(parents=True, exist_ok=True)
    target = (base / f"ets_notice_import_{uuid4().hex}").resolve()
    target.mkdir(parents=True, exist_ok=False)
    return target
