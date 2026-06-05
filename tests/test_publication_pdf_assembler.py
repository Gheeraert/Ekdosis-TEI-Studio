from __future__ import annotations

from pathlib import Path

from ets.application import SitePublicationDialogConfig, SitePublicationDialogPlayConfig
from ets.publication_pdf import build_publication_pdf_master


def _write_xml(path: Path) -> Path:
    path.write_text("<TEI/>", encoding="utf-8")
    return path


def _config(tmp_path: Path) -> SitePublicationDialogConfig:
    home = _write_xml(tmp_path / "home_page.xml")
    intro = _write_xml(tmp_path / "general_intro.xml")
    play_a = _write_xml(tmp_path / "a_dramatic.xml")
    notice_a = _write_xml(tmp_path / "a_notice.xml")
    preface_a = _write_xml(tmp_path / "a_preface.xml")
    dramatis_a = _write_xml(tmp_path / "a_dramatis.xml")
    play_b = _write_xml(tmp_path / "b_dramatic.xml")

    return SitePublicationDialogConfig(
        author_name="Jean Racine",
        corpus_title="Theatre complet",
        scientific_editor="Editor Test",
        home_page_tei=home,
        general_intro_tei=intro,
        plays=(
            SitePublicationDialogPlayConfig(
                play_slug="andromaque",
                dramatic_xml_path=play_a,
                notice_xml_path=notice_a,
                preface_xml_path=preface_a,
                dramatis_xml_path=dramatis_a,
            ),
            SitePublicationDialogPlayConfig(
                play_slug="berenice",
                dramatic_xml_path=play_b,
                notice_xml_path=None,
                preface_xml_path=None,
                dramatis_xml_path=None,
            ),
        ),
    )


def test_build_publication_pdf_master_creates_master_and_returns_resolved_path(tmp_path: Path) -> None:
    build_dir = tmp_path / "build"

    master_path = build_publication_pdf_master(_config(tmp_path), build_dir)

    assert master_path == (build_dir / "master.tex").resolve()
    assert master_path.exists()
    assert "\\documentclass{book}" in master_path.read_text(encoding="utf-8")


def test_master_excludes_home_page_and_includes_general_intro(tmp_path: Path) -> None:
    config = _config(tmp_path)

    master_text = build_publication_pdf_master(config, tmp_path / "build").read_text(encoding="utf-8")

    assert str(config.home_page_tei.resolve()) not in master_text  # type: ignore[union-attr]
    assert "% GENERAL INTRO:" in master_text
    assert str(config.general_intro_tei.resolve()) in master_text  # type: ignore[union-attr]


def test_master_orders_plays_from_config(tmp_path: Path) -> None:
    master_text = build_publication_pdf_master(_config(tmp_path), tmp_path / "build").read_text(encoding="utf-8")

    assert master_text.index("% PLAY: andromaque") < master_text.index("% PLAY: berenice")


def test_master_orders_play_front_matter_before_dramatic_text(tmp_path: Path) -> None:
    master_text = build_publication_pdf_master(_config(tmp_path), tmp_path / "build").read_text(encoding="utf-8")

    notice = master_text.index("% NOTICE:")
    preface = master_text.index("% PREFACE:")
    dramatis = master_text.index("% DRAMATIS PERSONAE:")
    dramatic = master_text.index("% DRAMATIC TEXT:")

    assert notice < preface < dramatis < dramatic


def test_master_omits_absent_notice_and_preface_placeholders(tmp_path: Path) -> None:
    master_text = build_publication_pdf_master(_config(tmp_path), tmp_path / "build").read_text(encoding="utf-8")
    second_play_text = master_text[master_text.index("% PLAY: berenice") :]

    assert "% NOTICE:" not in second_play_text
    assert "% PREFACE:" not in second_play_text
    assert "% DRAMATIS PERSONAE: front of" in second_play_text
    assert "% DRAMATIC TEXT:" in second_play_text
