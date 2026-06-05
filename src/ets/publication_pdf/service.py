from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ets.application.editorial_notice_import import EditorialNoticeImportService, PreparedPublicationConfig
from ets.application.site_publication_config import SitePublicationDialogConfig

from .assembler import build_publication_pdf_master


@dataclass(frozen=True)
class PublicationPdfMasterBuildResult:
    master_path: Path
    prepared_config: SitePublicationDialogConfig
    warnings: tuple[str, ...] = ()


class EditorialPublicationConfigPreparer(Protocol):
    def prepare_dialog_config_for_publication(self, config: SitePublicationDialogConfig) -> PreparedPublicationConfig:
        ...


def build_publication_pdf_master_from_dialog_config(
    config: SitePublicationDialogConfig,
    build_dir: str | Path,
    *,
    editorial_import_service: EditorialPublicationConfigPreparer | None = None,
) -> PublicationPdfMasterBuildResult:
    service = editorial_import_service or EditorialNoticeImportService()
    prepared = service.prepare_dialog_config_for_publication(config)
    master_path = build_publication_pdf_master(prepared.config, build_dir)
    return PublicationPdfMasterBuildResult(
        master_path=master_path,
        prepared_config=prepared.config,
        warnings=prepared.warnings,
    )
