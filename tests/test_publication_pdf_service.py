from __future__ import annotations

from pathlib import Path

from ets.application import SitePublicationDialogConfig, SitePublicationDialogPlayConfig
from ets.application.editorial_notice_import import PreparedPublicationConfig
from ets.publication_pdf.compiler import PublicationPdfCompileResult
from ets.publication_pdf import (
    PublicationPdfBuildResult,
    PublicationPdfMasterBuildResult,
    build_and_compile_publication_pdf_from_dialog_config,
    build_and_compile_publication_pdf_from_prepared_config,
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
    assert "Introduction issue de la config preparee." not in master_text
    assert str(prepared_config.general_intro_tei.resolve()) in master_text  # type: ignore[union-attr]
    assert "Config brute" not in master_text


def test_master_build_from_dialog_config_cleans_up_prepared_temp_root(tmp_path: Path) -> None:
    raw_config = SitePublicationDialogConfig(
        corpus_title="Config brute",
        output_dir=tmp_path / "site",
        plays=(),
    )
    prepared_config = _prepared_xml_config(tmp_path)
    temp_root = tmp_path / "ets_notice_import_test"
    temp_root.mkdir()
    (temp_root / "notice_converti.xml").write_text("<TEI/>", encoding="utf-8")
    fake_service = _FakeEditorialImportService(
        PreparedPublicationConfig(config=prepared_config, temp_root=temp_root)
    )

    result = build_publication_pdf_master_from_dialog_config(
        raw_config,
        tmp_path / "build",
        editorial_import_service=fake_service,
    )

    assert result.master_path.exists()
    assert not temp_root.exists()


def test_service_accepts_xml_config_without_real_pandoc(tmp_path: Path) -> None:
    config = _prepared_xml_config(tmp_path)

    result = build_publication_pdf_master_from_dialog_config(config, tmp_path / "build")

    assert result.master_path.exists()
    assert result.prepared_config.general_intro_tei == config.general_intro_tei.resolve()
    assert result.prepared_config.plays[0].notice_xml_path == config.plays[0].notice_xml_path.resolve()
    assert result.warnings == ()
    master_text = result.master_path.read_text(encoding="utf-8")
    assert "Introduction preparee." not in master_text
    assert str(config.general_intro_tei.resolve()) in master_text  # type: ignore[union-attr]
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


def _compile_result(
    *,
    master_path: Path,
    ok: bool,
    pdf_path: Path | None = None,
    engine: str = "lualatex",
    returncode: int | None = 0,
) -> PublicationPdfCompileResult:
    return PublicationPdfCompileResult(
        ok=ok,
        master_path=master_path,
        pdf_path=pdf_path,
        engine=engine,
        command=(engine, "master.tex"),
        returncode=returncode,
        stdout="stdout",
        stderr="stderr",
        log_path=None,
        message="compile message",
    )


def test_build_and_compile_from_prepared_config_succeeds(
    tmp_path: Path,
    monkeypatch,
) -> None:
    prepared_config = _prepared_xml_config(tmp_path)
    calls: list[tuple[Path, str, int, int | None, int, int]] = []

    def _fake_compile(master_path, *, engine, runs, max_runs, stability_confirmations, timeout_seconds):
        resolved = Path(master_path).resolve()
        calls.append((resolved, engine, runs, max_runs, stability_confirmations, timeout_seconds))
        pdf_path = resolved.with_suffix(".pdf")
        pdf_path.write_text("pdf", encoding="utf-8")
        return _compile_result(master_path=resolved, ok=True, pdf_path=pdf_path, engine=engine)

    monkeypatch.setattr("ets.publication_pdf.service.compile_publication_pdf", _fake_compile)

    result = build_and_compile_publication_pdf_from_prepared_config(
        prepared_config,
        tmp_path / "compiled-build",
        warnings=("Warning transmis.",),
        engine="lualatex",
        runs=3,
        max_runs=12,
        stability_confirmations=2,
        timeout_seconds=30,
    )

    assert isinstance(result, PublicationPdfBuildResult)
    assert result.ok is True
    assert result.master_result.master_path.exists()
    assert result.pdf_path == (tmp_path / "compiled-build" / "master.pdf").resolve()
    assert result.compile_result.pdf_path == result.pdf_path
    assert result.warnings == ("Warning transmis.",)
    assert calls == [(result.master_result.master_path, "lualatex", 3, 12, 2, 30)]
    assert not (prepared_config.output_dir or Path()).exists()


def test_build_and_compile_from_prepared_config_preserves_failed_compile(
    tmp_path: Path,
    monkeypatch,
) -> None:
    prepared_config = _prepared_xml_config(tmp_path)
    calls: list[tuple[str, int, int | None, int]] = []

    def _fake_compile(master_path, *, engine, runs, max_runs, stability_confirmations, timeout_seconds):
        calls.append((engine, runs, max_runs, stability_confirmations))
        return _compile_result(
            master_path=Path(master_path).resolve(),
            ok=False,
            pdf_path=None,
            engine=engine,
            returncode=1,
        )

    monkeypatch.setattr("ets.publication_pdf.service.compile_publication_pdf", _fake_compile)

    result = build_and_compile_publication_pdf_from_prepared_config(prepared_config, tmp_path / "failed-build")

    assert calls == [("lualatex", 3, 12, 2)]
    assert result.ok is False
    assert result.pdf_path is None
    assert result.master_result.master_path.exists()
    assert result.compile_result.returncode == 1


def test_build_and_compile_from_dialog_config_prepares_once(
    tmp_path: Path,
    monkeypatch,
) -> None:
    raw_config = SitePublicationDialogConfig(corpus_title="Brut", output_dir=tmp_path / "site")
    prepared_config = _prepared_xml_config(tmp_path)
    fake_service = _FakeEditorialImportService(
        PreparedPublicationConfig(config=prepared_config, warnings=("Warning prepare.",))
    )
    calls: list[tuple[str, int, int | None, int]] = []

    def _fake_compile(master_path, *, engine, runs, max_runs, stability_confirmations, timeout_seconds):
        resolved = Path(master_path).resolve()
        calls.append((engine, runs, max_runs, stability_confirmations))
        pdf_path = resolved.with_suffix(".pdf")
        pdf_path.write_text("pdf", encoding="utf-8")
        return _compile_result(master_path=resolved, ok=True, pdf_path=pdf_path, engine=engine)

    monkeypatch.setattr("ets.publication_pdf.service.compile_publication_pdf", _fake_compile)

    result = build_and_compile_publication_pdf_from_dialog_config(
        raw_config,
        tmp_path / "dialog-build",
        editorial_import_service=fake_service,
        engine="pdflatex",
    )

    assert fake_service.calls == [raw_config]
    assert result.ok is True
    assert result.master_result.prepared_config == prepared_config
    assert result.warnings == ("Warning prepare.",)
    assert calls == [("pdflatex", 3, 12, 2)]


def test_build_and_compile_from_prepared_config_can_request_fixed_runs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    prepared_config = _prepared_xml_config(tmp_path)
    calls: list[tuple[int, int | None, int]] = []

    def _fake_compile(master_path, *, engine, runs, max_runs, stability_confirmations, timeout_seconds):
        resolved = Path(master_path).resolve()
        calls.append((runs, max_runs, stability_confirmations))
        pdf_path = resolved.with_suffix(".pdf")
        pdf_path.write_text("pdf", encoding="utf-8")
        return _compile_result(master_path=resolved, ok=True, pdf_path=pdf_path, engine=engine)

    monkeypatch.setattr("ets.publication_pdf.service.compile_publication_pdf", _fake_compile)

    result = build_and_compile_publication_pdf_from_prepared_config(
        prepared_config,
        tmp_path / "fixed-build",
        runs=4,
        max_runs=None,
    )

    assert result.ok is True
    assert calls == [(4, None, 2)]


def test_build_and_compile_from_prepared_config_does_not_publish_unstable_pdf(
    tmp_path: Path,
    monkeypatch,
) -> None:
    prepared_config = _prepared_xml_config(tmp_path)

    def _fake_compile(master_path, *, engine, runs, max_runs, stability_confirmations, timeout_seconds):
        resolved = Path(master_path).resolve()
        pdf_path = resolved.with_suffix(".pdf")
        pdf_path.write_text("diagnostic pdf", encoding="utf-8")
        return _compile_result(master_path=resolved, ok=False, pdf_path=pdf_path, engine=engine)

    monkeypatch.setattr("ets.publication_pdf.service.compile_publication_pdf", _fake_compile)

    result = build_and_compile_publication_pdf_from_prepared_config(prepared_config, tmp_path / "unstable-build")

    assert result.ok is False
    assert result.pdf_path is None
    assert result.compile_result.pdf_path == (tmp_path / "unstable-build" / "master.pdf").resolve()
