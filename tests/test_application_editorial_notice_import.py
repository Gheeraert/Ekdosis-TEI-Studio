from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4
import xml.etree.ElementTree as ET
import zipfile

import pytest

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


def _assert_root_div_type(tei_xml: str, expected: str) -> ET.Element:
    root = ET.fromstring(tei_xml)
    div = root.find(".//tei:text/tei:body/tei:div", TEI_NS)
    assert div is not None
    assert div.get("type") == expected
    return div


def _write_minimal_word_docx(
    target: Path,
    *,
    title: str,
    subtitle: str | None = None,
    body_paragraph: str = "Paragraphe de test.",
) -> None:
    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""
    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""
    document_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
"""
    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:qFormat/>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:basedOn w:val="Normal"/>
    <w:qFormat/>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Subtitle">
    <w:name w:val="Subtitle"/>
    <w:basedOn w:val="Normal"/>
    <w:qFormat/>
  </w:style>
</w:styles>
"""

    subtitle_paragraph = ""
    if subtitle is not None:
        subtitle_paragraph = (
            '<w:p><w:pPr><w:pStyle w:val="Subtitle"/></w:pPr><w:r><w:t xml:space="preserve">'
            f"{subtitle}"
            "</w:t></w:r></w:p>"
        )
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:pPr><w:pStyle w:val="Title"/></w:pPr><w:r><w:t xml:space="preserve">{title}</w:t></w:r></w:p>
    {subtitle_paragraph}
    <w:p><w:pPr><w:pStyle w:val="Normal"/></w:pPr><w:r><w:t xml:space="preserve">{body_paragraph}</w:t></w:r></w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""

    core_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties
  xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:dcterms="http://purl.org/dc/terms/"
  xmlns:dcmitype="http://purl.org/dc/dcmitype/"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>fixture</dc:title>
</cp:coreProperties>
"""
    app_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
  <Application>Ekdosis-TEI Studio tests</Application>
</Properties>
"""

    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", rels_xml)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/styles.xml", styles_xml)
        archive.writestr("word/_rels/document.xml.rels", document_rels_xml)
        archive.writestr("docProps/core.xml", core_xml)
        archive.writestr("docProps/app.xml", app_xml)


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


def test_notice_valid_minimal_docx_import_generates_tei() -> None:
    service, source = _service_for("notice_ok_minimal.json", source_name="notice_ok_minimal.docx")
    result = service.import_docx(source, source_kind=EditorialSourceKind.PLAY_NOTICE)

    assert result.report.status is ValidationStatus.VALID
    assert result.tei_xml is not None
    root = ET.fromstring(result.tei_xml)
    assert root.find(".//tei:div[@type='notice']", TEI_NS) is not None
    assert root.find(".//tei:head[@type='main']", TEI_NS) is not None


def test_docx_import_reads_title_and_subtitle_from_pandoc_meta() -> None:
    runtime = _runtime_dir("app_editorial_notice_import_meta")
    source = runtime / "notice_meta.docx"
    source.write_text("placeholder", encoding="utf-8")
    payload = {
        "meta": {
            "title": {"t": "MetaInlines", "c": [{"t": "Str", "c": "Titre"}, {"t": "Space"}, {"t": "Str", "c": "Meta"}]},
            "subtitle": {
                "t": "MetaInlines",
                "c": [{"t": "Str", "c": "Sous-titre"}, {"t": "Space"}, {"t": "Str", "c": "Meta"}],
            },
        },
        "blocks": [{"t": "Para", "c": [{"t": "Str", "c": "Contenu"}]}],
    }
    service = EditorialNoticeImportService(pandoc_bridge=_StubBridge({source.name: payload}))

    result = service.import_docx(source, source_kind=EditorialSourceKind.PLAY_NOTICE)

    assert result.report.status is ValidationStatus.VALID
    assert result.tei_xml is not None
    root = ET.fromstring(result.tei_xml)
    assert root.find(".//tei:head[@type='main']", TEI_NS) is not None
    assert root.find(".//tei:head[@type='main']", TEI_NS).text == "Titre Meta"  # type: ignore[union-attr]
    assert root.find(".//tei:head[@type='sub']", TEI_NS) is not None
    assert root.find(".//tei:head[@type='sub']", TEI_NS).text == "Sous-titre Meta"  # type: ignore[union-attr]


def test_docx_import_root_div_type_depends_on_editorial_context() -> None:
    runtime = _runtime_dir("app_editorial_notice_import_root_kind")
    source = runtime / "source.docx"
    source.write_text("placeholder", encoding="utf-8")
    payload = _load_ast("notice_ok_minimal.json")
    service = EditorialNoticeImportService(pandoc_bridge=_StubBridge({source.name: payload}))

    expected_by_kind = {
        EditorialSourceKind.HOME_PAGE: "accueil",
        EditorialSourceKind.GENERAL_INTRO: "introduction-generale",
        EditorialSourceKind.PLAY_NOTICE: "notice",
        EditorialSourceKind.PLAY_PREFACE: "preface",
    }
    for source_kind, expected_root_type in expected_by_kind.items():
        result = service.import_docx(source, source_kind=source_kind)
        assert result.report.blocking_error_count == 0
        assert result.tei_xml is not None
        div = _assert_root_div_type(result.tei_xml, expected_root_type)
        xml_id = div.get("{http://www.w3.org/XML/1998/namespace}id")
        assert xml_id is not None
        assert xml_id.endswith(f"-{expected_root_type}")


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
    _assert_root_div_type(result.tei_xml, "preface")


def test_general_intro_valid_minimal_docx_import() -> None:
    service, source = _service_for("general_intro_ok_minimal.json", source_name="general_intro_ok_minimal.docx")
    result = service.import_docx(source, source_kind=EditorialSourceKind.GENERAL_INTRO)
    assert result.report.status is ValidationStatus.VALID
    assert result.tei_xml is not None
    _assert_root_div_type(result.tei_xml, "introduction-generale")


def test_home_page_valid_minimal_docx_import() -> None:
    service, source = _service_for("home_page_ok_minimal.json", source_name="home_page_ok_minimal.docx")
    result = service.import_docx(source, source_kind=EditorialSourceKind.HOME_PAGE)
    assert result.report.status is ValidationStatus.VALID
    assert result.tei_xml is not None
    _assert_root_div_type(result.tei_xml, "accueil")


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


def test_real_pandoc_docx_title_and_subtitle_are_imported_from_meta() -> None:
    if shutil.which("pandoc") is None:
        pytest.skip("pandoc is not available in this environment.")

    runtime = _runtime_dir("app_editorial_notice_import_real_docx")
    source = runtime / "real_title_subtitle.docx"
    _write_minimal_word_docx(
        source,
        title="Titre réel DOCX",
        subtitle="Sous-titre réel DOCX",
        body_paragraph="Contenu réel.",
    )

    raw = subprocess.run(
        ["pandoc", str(source), "-f", "docx+styles", "-t", "json"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    payload = json.loads(raw.stdout)
    assert "meta" in payload
    assert isinstance(payload["meta"], dict)
    assert "title" in payload["meta"]
    assert "subtitle" in payload["meta"]

    service = EditorialNoticeImportService()
    result = service.import_docx(source, source_kind=EditorialSourceKind.PLAY_NOTICE)

    assert result.report.status is ValidationStatus.VALID
    assert result.tei_xml is not None
    root = ET.fromstring(result.tei_xml)
    assert root.find(".//tei:head[@type='main']", TEI_NS) is not None
    assert root.find(".//tei:head[@type='main']", TEI_NS).text == "Titre réel DOCX"  # type: ignore[union-attr]
    assert root.find(".//tei:head[@type='sub']", TEI_NS) is not None
    assert root.find(".//tei:head[@type='sub']", TEI_NS).text == "Sous-titre réel DOCX"  # type: ignore[union-attr]


def test_xml_source_is_kept_without_docx_conversion() -> None:
    runtime = _runtime_dir("app_editorial_notice_import_xml_passthrough")
    source_xml = runtime / "already_tei.xml"
    source_xml.write_text(
        "<?xml version='1.0' encoding='utf-8'?><TEI xmlns='http://www.tei-c.org/ns/1.0'/>",
        encoding="utf-8",
    )
    service = EditorialNoticeImportService()

    result = service.inspect_source_for_ui(source_xml, source_kind=EditorialSourceKind.HOME_PAGE)

    assert result.report.status is ValidationStatus.VALID
    assert result.tei_xml is None


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
