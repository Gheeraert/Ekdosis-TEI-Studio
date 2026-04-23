from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4
import xml.etree.ElementTree as ET

from ets.application import (
    EditorialNoticeImportService,
    EditorialSourceKind,
    SitePublicationDialogConfig,
    SitePublicationDialogPlayConfig,
)
from ets.application.editorial_notice_import.pandoc_bridge import PandocExecutionError, PandocNotFoundError
from ets.application.editorial_notice_import.models import ValidationStatus


ROOT = Path(__file__).resolve().parents[1]
FIXTURES_AST = ROOT / "fixtures" / "notice_import" / "pandoc_ast"
RUNTIME_ROOT = ROOT / "tests" / "_runtime"
TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def _runtime_dir(prefix: str) -> Path:
    target = RUNTIME_ROOT / f"{prefix}_{uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _load_ast(name: str) -> dict[str, object]:
    return json.loads((FIXTURES_AST / name).read_text(encoding="utf-8"))


class _StubBridge:
    def __init__(
        self,
        ast_by_name: dict[str, dict[str, object]],
        *,
        not_found: set[str] | None = None,
        unreadable: set[str] | None = None,
    ) -> None:
        self._ast_by_name = ast_by_name
        self._not_found = not_found or set()
        self._unreadable = unreadable or set()

    def load_docx_ast(self, source_path: Path) -> dict[str, object]:
        key = source_path.name
        if key in self._not_found:
            raise PandocNotFoundError("Pandoc executable not found.")
        if key in self._unreadable:
            raise PandocExecutionError("Document illisible.")
        if key not in self._ast_by_name:
            raise PandocExecutionError(f"No AST fixture bound for '{key}'.")
        return self._ast_by_name[key]


def _service_for(ast_fixture_name: str, *, source_name: str = "source.docx") -> tuple[EditorialNoticeImportService, Path]:
    runtime = _runtime_dir("app_editorial_notice_import")
    source = runtime / source_name
    source.write_text("placeholder", encoding="utf-8")
    bridge = _StubBridge({source.name: _load_ast(ast_fixture_name)})
    return EditorialNoticeImportService(pandoc_bridge=bridge), source


def _run_import(ast_fixture_name: str, *, source_kind: EditorialSourceKind) -> tuple[EditorialNoticeImportService, Path]:
    return _service_for(ast_fixture_name)


def test_notice_valid_minimal_docx_import_generates_tei() -> None:
    service, source = _service_for("notice_ok_minimal.json", source_name="notice_ok_minimal.docx")
    result = service.import_docx(source, source_kind=EditorialSourceKind.PLAY_NOTICE)

    assert result.report.status is ValidationStatus.VALID
    assert result.tei_xml is not None
    root = ET.fromstring(result.tei_xml)
    assert root.find(".//tei:div[@type='notice']", TEI_NS) is not None
    assert root.find(".//tei:head[@type='main']", TEI_NS) is not None


def test_notice_valid_rich_docx_import_keeps_supported_structures() -> None:
    service, source = _service_for("notice_ok_rich.json", source_name="notice_ok_rich.docx")
    result = service.import_docx(source, source_kind=EditorialSourceKind.PLAY_NOTICE)

    assert result.report.status is ValidationStatus.VALID_WITH_WARNINGS
    assert result.report.warning_count >= 1
    assert result.tei_xml is not None
    root = ET.fromstring(result.tei_xml)
    assert root.find(".//tei:list", TEI_NS) is not None
    assert root.find(".//tei:table", TEI_NS) is not None
    assert root.find(".//tei:note[@place='foot']", TEI_NS) is not None
    assert root.find(".//tei:hi[@rend='bold']", TEI_NS) is not None
    assert root.find(".//tei:hi[@rend='italic']", TEI_NS) is not None
    assert root.find(".//tei:hi[@rend='sup']", TEI_NS) is not None
    assert root.find(".//tei:hi[@rend='sub']", TEI_NS) is not None


def test_preface_valid_minimal_docx_import() -> None:
    service, source = _service_for("preface_ok_minimal.json", source_name="preface_ok_minimal.docx")
    result = service.import_docx(source, source_kind=EditorialSourceKind.PLAY_PREFACE)
    assert result.report.status is ValidationStatus.VALID
    assert result.tei_xml is not None


def test_general_intro_valid_minimal_docx_import() -> None:
    service, source = _service_for("general_intro_ok_minimal.json", source_name="general_intro_ok_minimal.docx")
    result = service.import_docx(source, source_kind=EditorialSourceKind.GENERAL_INTRO)
    assert result.report.status is ValidationStatus.VALID
    assert result.tei_xml is not None


def test_home_page_valid_minimal_docx_import() -> None:
    service, source = _service_for("home_page_ok_minimal.json", source_name="home_page_ok_minimal.docx")
    result = service.import_docx(source, source_kind=EditorialSourceKind.HOME_PAGE)
    assert result.report.status is ValidationStatus.VALID
    assert result.tei_xml is not None


def test_docx_import_maps_smallcaps() -> None:
    service, source = _service_for("notice_ok_smallcaps.json", source_name="notice_ok_smallcaps.docx")
    result = service.import_docx(source, source_kind=EditorialSourceKind.PLAY_NOTICE)
    assert result.report.status is ValidationStatus.VALID
    assert result.tei_xml is not None
    root = ET.fromstring(result.tei_xml)
    assert root.find(".//tei:hi[@rend='smallcaps']", TEI_NS) is not None


def test_docx_import_maps_noindent_style() -> None:
    service, source = _service_for("notice_ok_noindent.json", source_name="notice_ok_noindent.docx")
    result = service.import_docx(source, source_kind=EditorialSourceKind.PLAY_NOTICE)
    assert result.report.status is ValidationStatus.VALID
    assert result.tei_xml is not None
    root = ET.fromstring(result.tei_xml)
    assert root.find(".//tei:p[@rend='noindent']", TEI_NS) is not None


def test_docx_import_maps_bibliography_section() -> None:
    service, source = _service_for("notice_ok_biblio.json", source_name="notice_ok_biblio.docx")
    result = service.import_docx(source, source_kind=EditorialSourceKind.PLAY_NOTICE)
    assert result.report.status is ValidationStatus.VALID
    assert result.tei_xml is not None
    root = ET.fromstring(result.tei_xml)
    assert root.find(".//tei:listBibl", TEI_NS) is not None
    assert len(root.findall(".//tei:listBibl/tei:bibl", TEI_NS)) == 2


def test_docx_import_accepts_simple_table() -> None:
    service, source = _service_for("notice_ok_table_simple.json", source_name="notice_ok_table_simple.docx")
    result = service.import_docx(source, source_kind=EditorialSourceKind.PLAY_NOTICE)
    assert result.report.status is ValidationStatus.VALID
    assert result.tei_xml is not None
    root = ET.fromstring(result.tei_xml)
    assert len(root.findall(".//tei:table/tei:row", TEI_NS)) >= 2


def test_docx_import_rejects_unknown_style() -> None:
    service, source = _service_for("notice_bad_unknown_style.json", source_name="notice_bad_unknown_style.docx")
    result = service.import_docx(source, source_kind=EditorialSourceKind.PLAY_NOTICE)
    assert result.report.status is ValidationStatus.INVALID
    codes = {message.code for message in result.report.messages}
    assert "UNKNOWN_PARAGRAPH_STYLE" in codes


def test_docx_import_rejects_heading_level_jump() -> None:
    service, source = _service_for("notice_bad_heading_jump.json", source_name="notice_bad_heading_jump.docx")
    result = service.import_docx(source, source_kind=EditorialSourceKind.PLAY_NOTICE)
    assert result.report.status is ValidationStatus.INVALID
    codes = {message.code for message in result.report.messages}
    assert "HEADING_LEVEL_SKIP" in codes


def test_docx_import_rejects_complex_table() -> None:
    service, source = _service_for("notice_bad_table_complex.json", source_name="notice_bad_table_complex.docx")
    result = service.import_docx(source, source_kind=EditorialSourceKind.PLAY_NOTICE)
    assert result.report.status is ValidationStatus.INVALID
    codes = {message.code for message in result.report.messages}
    assert "TABLE_COMPLEX" in codes


def test_docx_import_with_warnings_is_non_blocking() -> None:
    service, source = _service_for("notice_warn_non_blocking.json", source_name="notice_warn_non_blocking.docx")
    result = service.import_docx(source, source_kind=EditorialSourceKind.PLAY_NOTICE)
    assert result.report.status is ValidationStatus.VALID_WITH_WARNINGS
    assert result.report.warning_count > 0
    assert result.tei_xml is not None


def test_docx_import_handles_corrupted_or_unreadable_docx() -> None:
    runtime = _runtime_dir("app_editorial_notice_import_unreadable")
    source = runtime / "notice_corrupted.docx"
    source.write_text("placeholder", encoding="utf-8")
    bridge = _StubBridge({}, unreadable={source.name})
    service = EditorialNoticeImportService(pandoc_bridge=bridge)

    result = service.import_docx(source, source_kind=EditorialSourceKind.PLAY_NOTICE)
    assert result.report.status is ValidationStatus.INVALID
    codes = {message.code for message in result.report.messages}
    assert "DOCX_UNREADABLE" in codes


def test_docx_import_handles_missing_pandoc() -> None:
    runtime = _runtime_dir("app_editorial_notice_import_no_pandoc")
    source = runtime / "notice_missing_pandoc.docx"
    source.write_text("placeholder", encoding="utf-8")
    bridge = _StubBridge({}, not_found={source.name})
    service = EditorialNoticeImportService(pandoc_bridge=bridge)

    result = service.import_docx(source, source_kind=EditorialSourceKind.PLAY_NOTICE)
    assert result.report.status is ValidationStatus.INVALID
    codes = {message.code for message in result.report.messages}
    assert "PANDOC_NOT_AVAILABLE" in codes


def test_prepare_dialog_config_converts_docx_sources_but_keeps_xml_sources() -> None:
    runtime = _runtime_dir("app_editorial_notice_import_prepare")
    dramatic = runtime / "dramatic.xml"
    home_xml = runtime / "home.xml"
    dramatic.write_text("<xml/>", encoding="utf-8")
    home_xml.write_text("<xml/>", encoding="utf-8")

    notice_docx = runtime / "notice.docx"
    preface_docx = runtime / "preface.docx"
    intro_docx = runtime / "intro.docx"
    for path in (notice_docx, preface_docx, intro_docx):
        path.write_text("placeholder", encoding="utf-8")

    bridge = _StubBridge(
        {
            notice_docx.name: _load_ast("notice_ok_minimal.json"),
            preface_docx.name: _load_ast("preface_ok_minimal.json"),
            intro_docx.name: _load_ast("general_intro_ok_minimal.json"),
        }
    )
    service = EditorialNoticeImportService(pandoc_bridge=bridge)

    config = SitePublicationDialogConfig(
        corpus_title="Corpus test",
        output_dir=(runtime / "site").resolve(),
        home_page_tei=home_xml.resolve(),
        general_intro_tei=intro_docx.resolve(),
        plays=(
            SitePublicationDialogPlayConfig(
                play_slug="piece",
                dramatic_xml_path=dramatic.resolve(),
                notice_xml_path=notice_docx.resolve(),
                preface_xml_path=preface_docx.resolve(),
            ),
        ),
    )

    prepared = service.prepare_dialog_config_for_publication(config)
    output_config = prepared.config

    assert output_config.home_page_tei == home_xml.resolve()
    assert output_config.general_intro_tei is not None
    assert output_config.general_intro_tei.suffix == ".xml"
    assert output_config.plays[0].notice_xml_path is not None
    assert output_config.plays[0].notice_xml_path.suffix == ".xml"
    assert output_config.plays[0].preface_xml_path is not None
    assert output_config.plays[0].preface_xml_path.suffix == ".xml"
    assert output_config.plays[0].notice_xml_path != notice_docx.resolve()
    assert output_config.plays[0].preface_xml_path != preface_docx.resolve()

