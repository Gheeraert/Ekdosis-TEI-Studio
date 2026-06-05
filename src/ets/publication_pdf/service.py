from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ets.application.editorial_notice_import import EditorialNoticeImportService, PreparedPublicationConfig
from ets.application.site_publication_config import SitePublicationDialogConfig

from .assembler import build_publication_pdf_master
from .compiler import PublicationPdfCompileResult, compile_publication_pdf


@dataclass(frozen=True)
class PublicationPdfMasterBuildResult:
    master_path: Path
    prepared_config: SitePublicationDialogConfig
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class PublicationPdfBuildResult:
    master_result: PublicationPdfMasterBuildResult
    compile_result: PublicationPdfCompileResult
    ok: bool
    pdf_path: Path | None
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


def build_publication_pdf_master_from_prepared_config(
    prepared_config: SitePublicationDialogConfig,
    build_dir: str | Path,
    *,
    warnings: tuple[str, ...] = (),
) -> PublicationPdfMasterBuildResult:
    master_path = build_publication_pdf_master(prepared_config, build_dir)
    return PublicationPdfMasterBuildResult(
        master_path=master_path,
        prepared_config=prepared_config,
        warnings=warnings,
    )


def build_and_compile_publication_pdf_from_prepared_config(
    prepared_config: SitePublicationDialogConfig,
    build_dir: str | Path,
    *,
    warnings: tuple[str, ...] = (),
    engine: str = "xelatex",
    runs: int = 2,
    timeout_seconds: int = 120,
) -> PublicationPdfBuildResult:
    master_result = build_publication_pdf_master_from_prepared_config(
        prepared_config,
        build_dir,
        warnings=warnings,
    )
    compile_result = compile_publication_pdf(
        master_result.master_path,
        engine=engine,
        runs=runs,
        timeout_seconds=timeout_seconds,
    )
    return PublicationPdfBuildResult(
        master_result=master_result,
        compile_result=compile_result,
        ok=compile_result.ok,
        pdf_path=compile_result.pdf_path if compile_result.ok else None,
        warnings=master_result.warnings,
    )


def build_and_compile_publication_pdf_from_dialog_config(
    config: SitePublicationDialogConfig,
    build_dir: str | Path,
    *,
    editorial_import_service: EditorialPublicationConfigPreparer | None = None,
    engine: str = "xelatex",
    runs: int = 2,
    timeout_seconds: int = 120,
) -> PublicationPdfBuildResult:
    service = editorial_import_service or EditorialNoticeImportService()
    prepared = service.prepare_dialog_config_for_publication(config)
    return build_and_compile_publication_pdf_from_prepared_config(
        prepared.config,
        build_dir,
        warnings=prepared.warnings,
        engine=engine,
        runs=runs,
        timeout_seconds=timeout_seconds,
    )
