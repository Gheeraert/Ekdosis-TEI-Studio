from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from ets.core import run_pipeline

NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def _parse(xml_text: str) -> ET.Element:
    return ET.fromstring(xml_text)


def _line_numbers(root: ET.Element) -> list[str]:
    return [el.get("n", "") for el in root.findall(".//tei:l", NS)]


def _speakers(root: ET.Element) -> list[str]:
    return [el.text or "" for el in root.findall(".//tei:speaker", NS)]


def _line(root: ET.Element, n: str) -> ET.Element:
    line = root.find(f".//tei:l[@n='{n}']", NS)
    assert line is not None
    return line


def test_pipeline_generates_valid_minimal_tei_from_stable_fixture() -> None:
    root = Path(__file__).resolve().parents[1]
    xml_text = run_pipeline(
        input_path=root / "fixtures" / "stable" / "input.txt",
        config_path=root / "fixtures" / "stable" / "config.json",
    )

    generated = _parse(xml_text)
    assert generated.tag.endswith("TEI")

    assert generated.find(".//tei:div[@type='act']", NS) is not None
    assert generated.find(".//tei:div[@type='scene']", NS) is not None
    assert len(generated.findall(".//tei:witness", NS)) == 6

    numbers = _line_numbers(generated)
    assert numbers[0] == "1"
    assert "37.1" in numbers and "37.2" in numbers
    assert "134.1" in numbers and "134.2" in numbers
    assert numbers[-1] == "142"

    # Token-level collation: line 1 contains several token-column apparatus entries.
    line_1 = _line(generated, "1")
    assert len(line_1.findall("tei:app", NS)) >= 3

    # A stable literal line should remain literal with no apparatus.
    line_51 = _line(generated, "51")
    assert len(line_51.findall("tei:app", NS)) == 0

    # Whole-line marker line keeps explicit whole-line apparatus behavior.
    line_124 = _line(generated, "124")
    assert len(line_124.findall("tei:app", NS)) == 1


def test_pipeline_matches_stable_fixture_line_and_speaker_sequence() -> None:
    root = Path(__file__).resolve().parents[1]
    xml_text = run_pipeline(
        input_path=root / "fixtures" / "stable" / "input.txt",
        config_path=root / "fixtures" / "stable" / "config.json",
    )
    expected_xml = (root / "fixtures" / "stable" / "expected.xml").read_text(encoding="utf-8")

    generated_root = _parse(xml_text)
    expected_root = _parse(expected_xml)

    assert _line_numbers(generated_root) == _line_numbers(expected_root)
    assert _speakers(generated_root) == _speakers(expected_root)
