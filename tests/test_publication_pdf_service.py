from __future__ import annotations

from pathlib import Path

from ets.application import SitePublicationDialogConfig, SitePublicationDialogPlayConfig
from ets.application.editorial_notice_import import PreparedPublicationConfig
from ets.publication_pdf import (
    PublicationPdfMasterBuildResult,
    build_publication_pdf_master_from_dialog_config,
    build_publication_pdf_master_from_prepared_config,
)


class _FakeEditorialImportService:
    def __init__(self, prepared: PreparedPublicationConfig) -> None:
        self.prepared = prepared
        self.calls: list[SitePublicationDialogConfig] = []

    def prepare_dialog_config_for_publication(self, config: SitePublicationDialogConfig) -> PreparedPublicationConfig:
        self.calls.append(config)
        return self.prepared


def _write_tei(path: Path, *, body: str = "<p>Contenu editorial.</p>", front: str = "") -> Path:
    path.write_text(
        f"""<?xml version="1.0" encoding="utf-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <front>{front}</front>
    <body>{body}</body>
  </text>
</TEI>
""",
        encoding="utf-8",
    )
    return path


def _dramatic_body(line: str = "Vers dramatique.") -> str:
    return f"""
      <div type="act" n="1">
        <head>ACTE I</head>
        <div type="scene" n="1">
          <head>SCENE I</head>
          <sp>
            <speaker>ALPHA</speaker>
            <l n="1">{line}</l>
          </sp>
        </div>
      </div>
    """


def _prepared_xml_config(tmp_path: Path, *, intro_text: str = "Introduction preparee.") -> SitePublicationDialogConfig:
    intro = _write_tei(tmp_path / "intro.xml", body=f"<p>{intro_text}</p>")
    dramatic = _write_tei(
        tmp_path / "piece.xml",
        body=_dramatic_body(),
        front="<castList><castItem><role>ALPHA</role></castItem></castList>",
    )
    notice = _write_tei(tmp_path / "notice.xml", body="<p>Notice preparee.</p>")
    preface = _write_tei(tmp_path / "preface.xml", body="<p>Preface preparee.</p>")
    return SitePublicationDialogConfig(
        author_name="Auteur",
        corpus_title="Corpus",
        output_dir=tmp_path / "site",
        general_intro_tei=intro,
        plays=(
            SitePublicationDialogPlayConfig(
                play_slug="piece",
                dramatic_xml_path=dramatic,
                notice_xml_path=notice,
                preface_xml_path=preface,
            ),
        ),
    )


def test_service_prepares_dialog_config_then_builds_master(tmp_path: Path) -> None:
    raw_config = SitePublicationDialogConfig(
        corpus_title="Config brute",
        output_dir=tmp_path / "site",
        general_intro_tei=tmp_path / "intro.docx",
        plays=(),
    )
    prepared_config = _prepared_xml_config(tmp_path, intro_text="Introduction issue de la config preparee.")
    fake_service = _FakeEditorialImportService(
        PreparedPublicationConfig(config=prepared_config, warnings=("Avertissement controle.",))
    )

    result = build_publication_pdf_master_from_dialog_config(
        raw_config,
        tmp_path / "build",
        editorial_import_service=fake_service,
    )

    assert isinstance(result, PublicationPdfMasterBuildResult)
    assert fake_service.calls == [raw_config]
    assert result.master_path == (tmp_path / "build" / "master.tex").resolve()
    assert result.master_path.exists()
    assert result.prepared_config == prepared_config
    assert result.warnings == ("Avertissement controle.",)
    master_text = result.master_path.read_text(encoding="utf-8")
    assert "Introduction issue de la config preparee." in master_text
    assert "Config brute" not in master_text


def test_service_accepts_xml_config_without_real_pandoc(tmp_path: Path) -> None:
    config = _prepared_xml_config(tmp_path)

    result = build_publication_pdf_master_from_dialog_config(config, tmp_path / "build")

    assert result.master_path.exists()
    assert result.prepared_config.general_intro_tei == config.general_intro_tei.resolve()
    assert result.prepared_config.plays[0].notice_xml_path == config.plays[0].notice_xml_path.resolve()
    assert result.warnings == ()
    master_text = result.master_path.read_text(encoding="utf-8")
    assert "Introduction preparee." in master_text
    assert "Notice preparee." in master_text
    assert "Preface preparee." in master_text
    assert r"\speaker{ALPHA}" in master_text


def test_service_does_not_compile_latex_or_create_pdf(tmp_path: Path) -> None:
    config = _prepared_xml_config(tmp_path)

    result = build_publication_pdf_master_from_dialog_config(config, tmp_path / "build")

    assert result.master_path.name == "master.tex"
    assert not list((tmp_path / "build").glob("*.pdf"))


def test_service_builds_master_from_prepared_config_without_preparing_again(tmp_path: Path) -> None:
    prepared_config = _prepared_xml_config(tmp_path)

    result = build_publication_pdf_master_from_prepared_config(
        prepared_config,
        tmp_path / "prepared-build",
        warnings=("Warning deja prepare.",),
    )

    assert result.master_path == (tmp_path / "prepared-build" / "master.tex").resolve()
    assert result.master_path.exists()
    assert result.prepared_config == prepared_config
    assert result.warnings == ("Warning deja prepare.",)
