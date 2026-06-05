from __future__ import annotations

from pathlib import Path

import pytest

from ets.latex import tei_to_ekdosis


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
    assert "\\newcommand{\\stage}[1]" in actual
    assert "\\SetLineation{lineation=none}" in actual
    assert "\\begin{document}\n\\begin{ekdosis}\n" in actual
    assert _read(fixture_dir / "expected.tex").strip() in actual
    assert actual.endswith("\\end{ekdosis}\n\\end{document}\n")


def test_standalone_lineation_does_not_number_stage_or_speaker_automatically() -> None:
    actual = tei_to_ekdosis(_tei_with_lines([("1", "Premier vers.")]), standalone=True)

    assert "\\SetLineation{lineation=none}" in actual
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
