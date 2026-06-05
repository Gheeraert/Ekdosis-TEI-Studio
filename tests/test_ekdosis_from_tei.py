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
    assert "\\begin{document}\n\\begin{ekdosis}\n" in actual
    assert _read(fixture_dir / "expected.tex").strip() in actual
    assert actual.endswith("\\end{ekdosis}\n\\end{document}\n")
