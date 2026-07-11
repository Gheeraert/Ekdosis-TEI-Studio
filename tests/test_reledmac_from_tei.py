from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from ets.latex.reledmac_from_tei import tei_to_reledmac


def _tei(body: str, *, witnesses: str | None = None) -> str:
    source_desc = witnesses or """
        <listWit>
          <witness xml:id="A">A (A) Premiere edition.</witness>
          <witness xml:id="B">B (B) Edition collective.</witness>
          <witness xml:id="C">C (C) Troisieme temoin.</witness>
        </listWit>
    """
    return f"""<?xml version="1.0" encoding="utf-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Fixture Reledmac</title></titleStmt>
      <publicationStmt><p>Publication test.</p></publicationStmt>
      <sourceDesc>{source_desc}</sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <body>{body}</body>
  </text>
</TEI>
"""


def _dramatic(lines: str, *, extra: str = "") -> str:
    return _tei(
        f"""
      <div type="act" n="1">
        <head>ACTE I</head>
        <div type="scene" n="1">
          <head>SCENE I</head>
          {extra}
          <sp>
            <speaker>ALPHA</speaker>
            {lines}
          </sp>
        </div>
      </div>
    """
    )


def test_simple_verse_without_apparatus() -> None:
    actual = tei_to_reledmac(_dramatic('<l n="1">Premier vers.</l>'))

    assert r"\PURHAct{ACTE I}" in actual
    assert r"\PURHScene{SCENE I}" in actual
    assert r"\speaker{ALPHA}" in actual
    assert r"\PURHVerse{1}{Premier vers.}\&" in actual
    assert r"\beginnumbering" in actual
    assert r"\endnumbering" in actual


def test_variant_with_one_reading() -> None:
    actual = tei_to_reledmac(_dramatic('<l n="1">Je <app><lem wit="#A">vois</lem><rdg wit="#B">voy</rdg></app>.</l>'))

    assert r"\edtext{vois}{\lemma{\textbf{1}~vois}\Afootnote[nonum]{A ; B voy}}" in actual


def test_variant_with_multiple_readings_preserves_order() -> None:
    actual = tei_to_reledmac(
        _dramatic('<l n="1"><app><lem wit="#A">Seigneur</lem><rdg wit="#B">Madame</rdg><rdg wit="#C">Cesar</rdg></app></l>')
    )

    assert r"A ; B Madame ; C Cesar" in actual


def test_lemma_witnesses_are_kept() -> None:
    actual = tei_to_reledmac(_dramatic('<l n="1"><app><lem wit="#A #B">Seigneur</lem><rdg wit="#C">Madame</rdg></app></l>'))

    assert r"A B ; C Madame" in actual
    assert "#" not in actual


def test_rdg_omission_is_rendered_as_om() -> None:
    actual = tei_to_reledmac(_dramatic('<l n="1"><app><lem wit="#A">Seigneur</lem><rdg wit="#B" type="omission"/></app></l>'))

    assert r"A ; B om." in actual


def test_lemma_omission_is_rendered_as_om_in_apparatus() -> None:
    actual = tei_to_reledmac(_dramatic('<l n="1"><app><lem wit="#A" type="omission"/><rdg wit="#B">Seigneur</rdg></app></l>'))

    assert r"\edtext{}{\lemma{\textbf{1}~om.}\Afootnote[nonum]{A ; B Seigneur}}" in actual


def test_italic_in_lemma_and_reading() -> None:
    actual = tei_to_reledmac(
        _dramatic(
            '<l n="1"><app><lem wit="#A"><hi rend="italic">Seigneur</hi></lem><rdg wit="#B"><hi rend="italic">Madame</hi></rdg></app></l>'
        )
    )

    assert r"\edtext{\emph{Seigneur}}" in actual
    assert r"B \emph{Madame}" in actual


def test_mixed_content_around_apparatus_is_preserved() -> None:
    actual = tei_to_reledmac(_dramatic('<l n="1">Je <app><lem wit="#A">vois</lem><rdg wit="#B">voy</rdg></app> le jour.</l>'))

    assert r"Je \edtext{vois}" in actual
    assert r"} le jour.}\&" in actual


def test_multiple_apparatus_same_verse_print_editorial_number_once() -> None:
    actual = tei_to_reledmac(
        _dramatic(
            '<l n="12">Premier <app><lem wit="#A">mot</lem><rdg wit="#B">terme</rdg></app> et second <app><lem wit="#A">jour</lem><rdg wit="#B">soir</rdg></app>.</l>'
        )
    )

    assert actual.count(r"\textbf{12}~") == 1
    assert r"\lemma{jour}" in actual


def test_apparatus_note_does_not_duplicate_lemma() -> None:
    actual = tei_to_reledmac(
        _dramatic('<l n="1"><app><lem wit="#A">augmenter</lem><rdg wit="#B">redoubler</rdg></app></l>')
    )

    assert r"\lemma{\textbf{1}~augmenter}\Afootnote[nonum]{A ; B redoubler}" in actual
    assert "augmenter] augmenter A" not in actual
    assert "augmenter A ; B redoubler" not in actual


def test_shared_verse_two_fragments_uses_skipnumbering() -> None:
    actual = tei_to_reledmac(_dramatic('<l n="20.1">Debut.</l><l n="20.2">Fin.</l>'))

    assert r"\PURHVerse{20.1}{Debut.}&" in actual
    assert r"\skipnumbering \PURHVerse{20.2}{Fin.}\&" in actual


def test_shared_verse_three_fragments() -> None:
    actual = tei_to_reledmac(_dramatic('<l n="30.1">Un.</l><l n="30.2">Deux.</l><l n="30.3">Trois.</l>'))

    assert r"\PURHVerse{30.1}{Un.}&" in actual
    assert r"\skipnumbering \PURHVerse{30.2}{Deux.}&" in actual
    assert r"\skipnumbering \PURHVerse{30.3}{Trois.}\&" in actual


def test_stage_speaker_personnages_act_scene_and_stanza() -> None:
    actual = tei_to_reledmac(
        _dramatic(
            '<lg type="stanza"><l n="1">Un.</l><l n="2">Deux.</l></lg>',
            extra='<stage type="personnages">ALPHA, BETA.</stage><stage>Il sort.</stage>',
        )
    )

    assert r"\stage{ALPHA, BETA.}" in actual
    assert r"\didas{Il sort.}" in actual
    assert r"\speaker{ALPHA}" in actual
    assert r"\PURHAct{ACTE I}" in actual
    assert r"\PURHScene{SCENE I}" in actual
    assert r"\stanza" in actual


def test_hide_minor_variants_but_keep_low_certainty() -> None:
    xml = _dramatic(
        '<l n="1"><app type="minor"><lem wit="#A">viens,</lem><rdg wit="#B">viens</rdg></app> '
        '<app type="minor" cert="low"><lem wit="#A">partir</lem><rdg wit="#B">mourir</rdg></app></l>'
    )

    actual = tei_to_reledmac(xml, apparatus_policy="hide_minor")

    assert "viens," in actual
    assert "B viens" not in actual
    assert r"\edtext{partir}" in actual
    assert "B mourir" in actual


def test_rejects_witness_used_but_absent_from_listwit() -> None:
    xml = _tei(
        '<sp><speaker>A</speaker><l n="1"><app><lem wit="#A">mot</lem><rdg wit="#B">terme</rdg></app></l></sp>',
        witnesses='<listWit><witness xml:id="A">A (A) Source.</witness></listWit>',
    )

    with pytest.raises(ValueError, match="absent"):
        tei_to_reledmac(xml)


def test_latex_escaping_and_no_ekdosis_commands() -> None:
    actual = tei_to_reledmac(_dramatic('<l n="1">A &amp; B_100 % sûr.</l>'))

    assert r"A \ampersand{} B\_100 \% sûr." in actual
    forbidden = [r"\usepackage{ekdosis}", r"\DeclareWitness", r"\begin{ekdosis}", r"\app", r"\lem[", r"\rdg[", r"\ekddiv"]
    assert not any(item in actual for item in forbidden)


def test_accepts_pathlike_input(tmp_path: Path) -> None:
    path = tmp_path / "input.xml"
    path.write_text(_dramatic('<l n="1">Depuis longtemps.</l>'), encoding="utf-8")

    assert r"\PURHVerse{1}{Depuis longtemps.}\&" in tei_to_reledmac(path)


def test_standalone_wraps_reledmac_document() -> None:
    actual = tei_to_reledmac(_dramatic('<l n="1">Premier vers.</l>'), standalone=True)

    assert actual.startswith(r"\documentclass{book}")
    assert r"\usepackage[" in actual
    assert r"]{reledmac}" in actual
    assert r"\begin{document}" in actual
    assert r"\end{document}" in actual


@pytest.mark.skipif(shutil.which("lualatex") is None or shutil.which("kpsewhich") is None, reason="LuaLaTeX not available")
def test_minimal_reledmac_document_compiles(tmp_path: Path) -> None:
    if subprocess.run(["kpsewhich", "reledmac.sty"], text=True, stdout=subprocess.PIPE).returncode != 0:
        pytest.skip("reledmac.sty not available")
    tex = tei_to_reledmac(
        _dramatic(
            '<stage>Il sort.</stage>'
            '<l n="1">Premier <app><lem wit="#A">mot</lem><rdg wit="#B">terme</rdg></app>.</l>'
            '<l n="2">Second vers.</l>'
            '<l n="5.1">Debut partage.</l>'
            '<l n="5.2">Fin partagee <app><lem wit="#A">ici</lem><rdg wit="#B" type="omission"/></app>.</l>'
        ),
        standalone=True,
    )
    (tmp_path / "master.tex").write_text(tex, encoding="utf-8")

    result = subprocess.run(
        ["lualatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "master.tex"],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=60,
    )

    assert result.returncode == 0, result.stdout
    assert (tmp_path / "master.pdf").exists()
