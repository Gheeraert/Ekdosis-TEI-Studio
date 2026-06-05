from __future__ import annotations

from pathlib import Path

from ets.application import SitePublicationDialogConfig, SitePublicationDialogPlayConfig
from ets.publication_pdf import build_publication_pdf_master


def _write_xml(path: Path, body: str = "<p>Document source.</p>", front: str = "") -> Path:
    path.write_text(
        f"""<?xml version="1.0" encoding="utf-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <front>
      {front}
    </front>
    <body>
      {body}
    </body>
  </text>
</TEI>
""",
        encoding="utf-8",
    )
    return path


def _dramatic_body(speaker: str, line: str) -> str:
    return f"""
      <div type="act" n="1">
        <head>ACTE I</head>
        <div type="scene" n="1">
          <head>SCENE I</head>
          <sp>
            <speaker>{speaker}</speaker>
            <l n="1">{line}</l>
          </sp>
        </div>
      </div>
    """


def _config(tmp_path: Path) -> SitePublicationDialogConfig:
    home = _write_xml(tmp_path / "home_page.xml", "<p>Texte reserve a la page accueil.</p>")
    intro = _write_xml(tmp_path / "general_intro.xml", "<p>Introduction generale convertie.</p>")
    play_a = _write_xml(
        tmp_path / "a_dramatic.xml",
        body=_dramatic_body("ORESTE", "Je parle pour Andromaque."),
        front="<castList><castItem><role>Front Andromaque</role></castItem></castList>",
    )
    notice_a = _write_xml(tmp_path / "a_notice.xml", '<p>Notice avec <hi rend="italic">italique</hi>.</p>')
    preface_a = _write_xml(tmp_path / "a_preface.xml", "<p>Preface convertie.</p>")
    dramatis_a = _write_xml(
        tmp_path / "a_dramatis.xml",
        front="<castList><castItem><role>Dramatis externe Alpha</role></castItem></castList>",
    )
    play_b = _write_xml(
        tmp_path / "b_dramatic.xml",
        body=_dramatic_body("BERENICE", "Je parle pour Berenice."),
        front="<castList><castItem><role>Front Berenice</role></castItem></castList>",
    )
    play_c = _write_xml(tmp_path / "c_dramatic.xml", body=_dramatic_body("TITUS", "Je parle sans castList."))

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
            SitePublicationDialogPlayConfig(
                play_slug="sans-castlist",
                dramatic_xml_path=play_c,
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


def test_master_contains_ekdosis_support_preamble(tmp_path: Path) -> None:
    master_text = build_publication_pdf_master(_config(tmp_path), tmp_path / "build").read_text(encoding="utf-8")

    assert r"\usepackage[teiexport, divs=ekdosis, poetry=verse]{ekdosis}" in master_text
    assert r"\SetLineation{" in master_text
    assert "lineation=none" in master_text
    assert "modulo" in master_text
    assert "vmodulo=0" in master_text
    assert r"\newcommand{\stage}" in master_text
    assert r"\newenvironment{speech}" in master_text
    assert r"\newcommand{\speaker}" in master_text
    assert r"\cs_new_protected:Npn \vnum" in master_text


def test_master_excludes_home_page_and_includes_general_intro(tmp_path: Path) -> None:
    config = _config(tmp_path)

    master_text = build_publication_pdf_master(config, tmp_path / "build").read_text(encoding="utf-8")

    assert str(config.home_page_tei.resolve()) not in master_text  # type: ignore[union-attr]
    assert "Texte reserve a la page accueil." not in master_text
    assert "% GENERAL INTRO:" in master_text
    assert str(config.general_intro_tei.resolve()) in master_text  # type: ignore[union-attr]
    assert "Introduction generale convertie." in master_text


def test_master_inserts_notice_and_preface_latex_fragments(tmp_path: Path) -> None:
    master_text = build_publication_pdf_master(_config(tmp_path), tmp_path / "build").read_text(encoding="utf-8")

    assert "% NOTICE:" in master_text
    assert r"Notice avec \emph{italique}." in master_text
    assert "% PREFACE:" in master_text
    assert "Preface convertie." in master_text


def test_master_orders_plays_from_config(tmp_path: Path) -> None:
    master_text = build_publication_pdf_master(_config(tmp_path), tmp_path / "build").read_text(encoding="utf-8")

    assert master_text.index("% PLAY: andromaque") < master_text.index("% PLAY: berenice")
    assert master_text.index("% PLAY: berenice") < master_text.index("% PLAY: sans-castlist")


def test_master_orders_play_front_matter_before_dramatic_text(tmp_path: Path) -> None:
    master_text = build_publication_pdf_master(_config(tmp_path), tmp_path / "build").read_text(encoding="utf-8")

    notice = master_text.index("% NOTICE:")
    preface = master_text.index("% PREFACE:")
    dramatis = master_text.index("% DRAMATIS PERSONAE:")
    dramatic = master_text.index("% DRAMATIC TEXT:")

    assert notice < preface < dramatis < dramatic
    assert r"Notice avec \emph{italique}." in master_text[notice:preface]
    assert "Preface convertie." in master_text[preface:dramatis]
    assert "Dramatis externe Alpha" in master_text[dramatis:dramatic]
    assert "\\begin{speech}" in master_text[dramatic:]


def test_master_omits_absent_notice_and_preface_placeholders(tmp_path: Path) -> None:
    master_text = build_publication_pdf_master(_config(tmp_path), tmp_path / "build").read_text(encoding="utf-8")
    second_play_text = master_text[master_text.index("% PLAY: berenice") :]

    assert "% NOTICE:" not in second_play_text
    assert "% PREFACE:" not in second_play_text
    assert "% DRAMATIS PERSONAE: front of" in second_play_text
    assert "% DRAMATIC TEXT:" in second_play_text


def test_master_uses_external_dramatis_before_dramatic_front(tmp_path: Path) -> None:
    master_text = build_publication_pdf_master(_config(tmp_path), tmp_path / "build").read_text(encoding="utf-8")
    play_text = master_text[master_text.index("% PLAY: andromaque") : master_text.index("% PLAY: berenice")]

    assert "% DRAMATIS PERSONAE:" in play_text
    assert "Dramatis externe Alpha" in play_text
    assert "Front Andromaque" not in play_text


def test_master_uses_dramatic_front_castlist_when_no_external_dramatis(tmp_path: Path) -> None:
    master_text = build_publication_pdf_master(_config(tmp_path), tmp_path / "build").read_text(encoding="utf-8")
    play_text = master_text[master_text.index("% PLAY: berenice") : master_text.index("% PLAY: sans-castlist")]

    assert "% DRAMATIS PERSONAE: front of" in play_text
    assert "\\item[Front Berenice]" in play_text


def test_master_keeps_stable_comment_when_no_castlist_is_found(tmp_path: Path) -> None:
    master_text = build_publication_pdf_master(_config(tmp_path), tmp_path / "build").read_text(encoding="utf-8")
    play_text = master_text[master_text.index("% PLAY: sans-castlist") :]

    assert "% DRAMATIS PERSONAE: front of" in play_text
    assert "% DRAMATIS PERSONAE: no castList found." in play_text
    assert "% DRAMATIC TEXT:" in play_text


def test_master_inserts_dramatic_ekdosis_fragment_and_removes_placeholder(tmp_path: Path) -> None:
    master_text = build_publication_pdf_master(_config(tmp_path), tmp_path / "build").read_text(encoding="utf-8")

    assert "% DRAMATIC TEXT:" in master_text
    assert r"\begin{ekdosis}" in master_text
    assert r"\end{ekdosis}" in master_text
    assert r"\speaker{ORESTE}" in master_text
    assert r"\vnum{1}{Je parle pour Andromaque.\\}" in master_text
    assert "Placeholder: conversion TEI dramatique vers LaTeX-Ekdosis a venir." not in master_text


def test_master_does_not_embed_standalone_latex_documents(tmp_path: Path) -> None:
    master_text = build_publication_pdf_master(_config(tmp_path), tmp_path / "build").read_text(encoding="utf-8")

    assert master_text.count(r"\documentclass") == 1
    assert master_text.count(r"\begin{document}") == 1
    assert master_text.count(r"\end{document}") == 1


def test_master_does_not_duplicate_front_castlist_in_dramatic_text_section(tmp_path: Path) -> None:
    master_text = build_publication_pdf_master(_config(tmp_path), tmp_path / "build").read_text(encoding="utf-8")
    play_text = master_text[master_text.index("% PLAY: berenice") : master_text.index("% PLAY: sans-castlist")]
    dramatic_text = play_text[play_text.index("% DRAMATIC TEXT:") :]

    assert "Front Berenice" in play_text
    assert "Front Berenice" not in dramatic_text
    assert r"\speaker{BERENICE}" in dramatic_text
