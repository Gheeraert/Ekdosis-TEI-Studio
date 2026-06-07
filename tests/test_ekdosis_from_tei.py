from __future__ import annotations

from pathlib import Path

import pytest

from ets.latex import tei_to_ekdosis
from ets.latex.ekdosis_from_tei import render_ekdosis_witness_declarations


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "fixtures" / "ekdosis_from_tei"


CASES = [
    "01_simple_line",
    "02_inline_app",
    "03_wit_multiple",
    "04_nbsp_ampersand",
    "05_speech_who_ignored",
    "06_stage",
    "07_italic",
    "08_italic_with_app",
    "09_lacuna",
    "10_shared_verse_decimal",
    "11_stanza_minimal",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _tei_with_lines(lines: list[tuple[str, str]]) -> str:
    rendered_lines = "\n".join(f'<l n="{number}">{text}</l>' for number, text in lines)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <div type="act" n="1">
        <head>ACTE I</head>
        <div type="scene" n="1">
          <head>SCENE I</head>
          <stage type="personnages">ALPHA, BETA.</stage>
          <sp>
            <speaker>ALPHA</speaker>
            {rendered_lines}
          </sp>
        </div>
      </div>
    </body>
  </text>
</TEI>
"""


def _tei_with_witnesses(*, witnesses: str, body_line: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Fixture Ekdosis</title></titleStmt>
      <publicationStmt><p>Publication test.</p></publicationStmt>
      <sourceDesc>
        {witnesses}
      </sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <div type="act" n="1">
        <head>ACTE I</head>
        <div type="scene" n="1">
          <head>SCENE I</head>
          <sp>
            <speaker>ALPHA</speaker>
            <l n="1">{body_line}</l>
          </sp>
        </div>
      </div>
    </body>
  </text>
</TEI>
"""


@pytest.mark.parametrize("case_name", CASES)
def test_tei_to_ekdosis_matches_minimal_fixture(case_name: str) -> None:
    fixture_dir = FIXTURE_ROOT / case_name

    actual = tei_to_ekdosis(fixture_dir / "input.xml")
    expected = _read(fixture_dir / "expected.tex")

    assert actual == expected


def test_tei_to_ekdosis_accepts_xml_string() -> None:
    fixture_dir = FIXTURE_ROOT / "01_simple_line"

    actual = tei_to_ekdosis(_read(fixture_dir / "input.xml"))

    assert actual == _read(fixture_dir / "expected.tex")


def test_tei_to_ekdosis_can_wrap_standalone_document() -> None:
    fixture_dir = FIXTURE_ROOT / "01_simple_line"

    actual = tei_to_ekdosis(fixture_dir / "input.xml", standalone=True)

    assert actual.startswith("\\documentclass{book}\n")
    assert "\\usepackage[teiexport, divs=ekdosis, poetry=verse]{ekdosis}" in actual
    assert r"\DeclareWitness{A}{1670}{Temoin A}" in actual
    assert r"\DeclareWitness{B}{1671}{Temoin B}" in actual
    assert actual.index(r"\DeclareWitness{A}{1670}") < actual.index(r"\begin{document}")
    assert "\\newcommand{\\stage}[1]" in actual
    assert "\\SetLineation{" in actual
    assert "lineation=none" in actual
    assert "vmodulo=0" in actual
    assert "\\begin{document}\n\\begin{ekdosis}\n" in actual
    assert _read(fixture_dir / "expected.tex").strip() in actual
    assert actual.endswith("\\end{ekdosis}\n\\end{document}\n")


def test_standalone_lineation_does_not_number_stage_or_speaker_automatically() -> None:
    actual = tei_to_ekdosis(_tei_with_lines([("1", "Premier vers.")]), standalone=True)

    assert "\\SetLineation{" in actual
    assert "lineation=none" in actual
    assert "vmodulo=0" in actual
    assert "\\stage{ACTE I}" in actual
    assert "\\stage{SCENE I}" in actual
    assert "\\stage{ALPHA, BETA.}" in actual
    assert "\\speaker{ALPHA}" in actual
    assert "\\vnum{1}{Premier vers.\\\\}" in actual


def test_standalone_vnum_macro_prints_only_multiples_of_five() -> None:
    actual = tei_to_ekdosis(
        _tei_with_lines([(str(number), f"Vers {number}.") for number in range(1, 13)]),
        standalone=True,
    )

    assert "\\int_mod:nn { \\l_tmpa_tl } { 5 }" in actual
    assert "\\makebox[0pt][r]{\\scriptsize \\l_tmpa_tl\\quad}" in actual
    for number in range(1, 13):
        assert f"\\vnum{{{number}}}{{Vers {number}.\\\\}}" in actual


def test_standalone_vnum_macro_treats_decimal_fragments_as_one_base_verse() -> None:
    actual = tei_to_ekdosis(
        _tei_with_lines(
            [
                ("10.1", "Debut du vers partage."),
                ("10.2", "Fin du vers partage."),
                ("11", "Vers suivant."),
            ]
        ),
        standalone=True,
    )

    assert "\\seq_set_split:Nnn \\l_ets_verse_number_parts_seq {.} {#1}" in actual
    assert "\\str_if_eq:VnF \\l_tmpb_tl {1}" in actual
    assert "\\vnum{10.1}{Debut du vers partage.\\\\}" in actual
    assert "\\vnum{10.2}{Fin du vers partage.\\\\}" in actual
    assert "\\vnum{11}{Vers suivant.\\\\}" in actual


def test_standalone_declares_witnesses_from_tei_header_listwit() -> None:
    xml = _tei_with_witnesses(
        witnesses="""
        <listWit>
          <witness xml:id="A">A (1669) Premiere edition.</witness>
          <witness xml:id="B">B (1676) Oeuvres de Racine.</witness>
        </listWit>
        """,
        body_line='Je <app><lem wit="#A">vois</lem><rdg wit="#B">voy</rdg></app> le jour.',
    )

    actual = tei_to_ekdosis(xml, standalone=True)

    assert r"\DeclareWitness{A}{1669}{Premiere edition.}" in actual
    assert r"\DeclareWitness{B}{1676}{Oeuvres de Racine.}" in actual
    assert r"\lem[wit={A}]{vois}" in actual
    assert r"\rdg[wit={B}]{voy}" in actual


def test_witness_declarations_reject_undeclared_wit() -> None:
    xml = _tei_with_witnesses(
        witnesses="""
        <listWit>
          <witness xml:id="A">A (1669) Premiere edition.</witness>
        </listWit>
        """,
        body_line='Je <app><lem wit="#A">vois</lem><rdg wit="#B">voy</rdg></app> le jour.',
    )

    with pytest.raises(ValueError, match="absent"):
        render_ekdosis_witness_declarations(xml)


def test_witness_declarations_reject_apparatus_without_listwit() -> None:
    xml = _tei_with_witnesses(
        witnesses="<p>Aucun temoin declare.</p>",
        body_line='Je <app><lem wit="#A">vois</lem><rdg wit="#B">voy</rdg></app> le jour.',
    )

    with pytest.raises(ValueError, match="listWit"):
        render_ekdosis_witness_declarations(xml)


def test_editorial_apparatus_numbering_injects_tei_line_numbers() -> None:
    xml = _tei_with_lines(
        [
            (
                "3",
                'Qu’errant dans le Palais sans suite <app><lem wit="#A">&amp; sans escorte</lem><rdg wit="#B">&amp; escorte</rdg></app>',
            ),
            (
                "27",
                'Rome depuis <app><lem wit="#A">trois</lem><rdg wit="#B">deux</rdg></app> ans par ses soins gouvernée',
            ),
        ]
    )

    actual = tei_to_ekdosis(xml, apparatus_numbering_policy="editorial")

    assert r"\lem[wit={A},nonum,alt={\textbf{3}~\& sans escorte}]{\& sans escorte}" in actual
    assert r"\lem[wit={A},nonum,alt={\textbf{27}~trois}]{trois}" in actual
    assert r"\rdg[wit={B}]{\& escorte}" in actual
    assert r"\rdg[wit={B}]{deux}" in actual


def test_editorial_apparatus_numbering_suppresses_repeated_number_on_same_line() -> None:
    xml = _tei_with_lines(
        [
            (
                "12",
                'Premier <app><lem wit="#A">mot</lem><rdg wit="#B">terme</rdg></app> et second <app><lem wit="#A">mot</lem><rdg wit="#B">terme</rdg></app>.',
            )
        ]
    )

    actual = tei_to_ekdosis(xml, apparatus_numbering_policy="editorial")

    assert actual.count(r"alt={\textbf{12}~mot}") == 1
    assert actual.count(r"\lem[wit={A},nonum") == 2
