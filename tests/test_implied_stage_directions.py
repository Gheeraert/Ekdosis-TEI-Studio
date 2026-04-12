from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from ets.core import run_pipeline

NS = {"tei": "http://www.tei-c.org/ns/1.0"}
XML_NS = "http://www.w3.org/XML/1998/namespace"


def _normalize_node_text(value: str | None) -> str:
    if value is None:
        return ""
    normalized = re.sub(r"\s+", " ", value).strip()
    return normalized


def _assert_xml_equivalent(actual: ET.Element, expected: ET.Element) -> None:
    assert actual.tag == expected.tag
    assert actual.attrib == expected.attrib
    assert _normalize_node_text(actual.text) == _normalize_node_text(expected.text)
    assert _normalize_node_text(actual.tail) == _normalize_node_text(expected.tail)

    actual_children = list(actual)
    expected_children = list(expected)
    assert len(actual_children) == len(expected_children)
    for a_child, e_child in zip(actual_children, expected_children):
        _assert_xml_equivalent(a_child, e_child)


def _write_runtime_file(path: Path, content: str) -> None:
    path.parent.mkdir(exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_runtime_config(path: Path) -> None:
    payload = {
        "PrÃ©nom de l'auteur": "Racine",
        "Nom de l'auteur": "Racine",
        "Titre de la piÃ¨ce": "BÃ©rÃ©nice",
        "NumÃ©ro de l'acte": "I",
        "NumÃ©ro de la scÃ¨ne": "1",
        "NumÃ©ro du vers de dÃ©part": 1,
        "Nom de l'Ã©diteur (vous)": "Gheeraert",
        "PrÃ©nom de l'Ã©diteur": "Tony",
        "Temoins": [
            {"abbr": "A", "year": "1671", "desc": "A"},
            {"abbr": "B", "year": "1676", "desc": "B"},
        ],
        "reference_witness": 0,
    }
    _write_runtime_file(path, json.dumps(payload))


def test_implied_stage_direction_fixture_matches_expected_xml() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture_dir = root / "fixtures" / "implied_stage_directions" / "berenice"
    xml_text = run_pipeline(
        input_path=fixture_dir / "input.txt",
        config_path=fixture_dir / "config.json",
    )
    actual = ET.fromstring(xml_text)
    expected = ET.fromstring((fixture_dir / "expected.xml").read_text(encoding="utf-8"))

    actual_scene = actual.find(".//tei:div[@type='scene']", NS)
    expected_scene = expected.find(".//tei:div[@type='scene']", NS)
    assert actual_scene is not None and expected_scene is not None
    _assert_xml_equivalent(actual_scene, expected_scene)

    speech = actual.find(".//tei:sp", NS)
    assert speech is not None

    implicit_stages = speech.findall("./tei:stage[@type='DI']", NS)
    assert len(implicit_stages) == 2
    assert implicit_stages[0].get(f"{{{XML_NS}}}id") == "implicite1"
    assert implicit_stages[1].get(f"{{{XML_NS}}}id") == "implicite2"
    assert implicit_stages[0].get("ana") == "#SET"
    assert implicit_stages[1].get("ana") == "#EVT"

    set_lines = [line.get("n", "") for line in implicit_stages[0].findall("./tei:l", NS)]
    evt_lines = [line.get("n", "") for line in implicit_stages[1].findall("./tei:l", NS)]
    assert set_lines == ["1", "2", "3", "4", "5", "6", "7", "8"]
    assert evt_lines == ["9"]

    # Line 10 remains a normal verse after implicit span closure and numbering is continuous.
    direct_lines = [line.get("n", "") for line in speech.findall("./tei:l", NS)]
    assert "10" in direct_lines
    all_numbers = [line.get("n", "") for line in actual.findall(".//tei:l", NS)]
    assert all_numbers == [str(i) for i in range(1, 11)]


def test_implied_stage_direction_close_without_open_fails() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = root / "tests" / "_runtime"
    config_path = runtime / "implicit_close_without_open_config.json"
    input_path = runtime / "implicit_close_without_open_input.txt"
    _write_runtime_config(config_path)
    _write_runtime_file(
        input_path,
        "\n".join(
            [
                "####ACTE I####",
                "####ACTE I####",
                "",
                "###SCENE I###",
                "###SCENE I###",
                "",
                "##ANTIOCHUS##",
                "##ANTIOCHUS##",
                "",
                "#ANTIOCHUS#",
                "#ANTIOCHUS#",
                "",
                "$$fin$$",
                "$$fin$$",
            ]
        )
        + "\n",
    )
    with pytest.raises(ValueError, match="Unexpected \\$\\$fin\\$\\$ without open implicit stage span."):
        run_pipeline(input_path=input_path, config_path=config_path)


def test_implied_stage_direction_unclosed_span_fails() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = root / "tests" / "_runtime"
    config_path = runtime / "implicit_unclosed_config.json"
    input_path = runtime / "implicit_unclosed_input.txt"
    _write_runtime_config(config_path)
    _write_runtime_file(
        input_path,
        "\n".join(
            [
                "####ACTE I####",
                "####ACTE I####",
                "",
                "###SCENE I###",
                "###SCENE I###",
                "",
                "##ANTIOCHUS##",
                "##ANTIOCHUS##",
                "",
                "#ANTIOCHUS#",
                "#ANTIOCHUS#",
                "",
                "$$SET$$",
                "$$SET$$",
                "",
                "Un vers dans le span",
                "Un vers dans le span",
            ]
        )
        + "\n",
    )
    with pytest.raises(ValueError, match="Unclosed implicit stage span at end of input."):
        run_pipeline(input_path=input_path, config_path=config_path)


def test_implied_stage_direction_nested_span_fails() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = root / "tests" / "_runtime"
    config_path = runtime / "implicit_nested_config.json"
    input_path = runtime / "implicit_nested_input.txt"
    _write_runtime_config(config_path)
    _write_runtime_file(
        input_path,
        "\n".join(
            [
                "####ACTE I####",
                "####ACTE I####",
                "",
                "###SCENE I###",
                "###SCENE I###",
                "",
                "##ANTIOCHUS##",
                "##ANTIOCHUS##",
                "",
                "#ANTIOCHUS#",
                "#ANTIOCHUS#",
                "",
                "$$SET$$",
                "$$SET$$",
                "",
                "$$EVT$$",
                "$$EVT$$",
            ]
        )
        + "\n",
    )
    with pytest.raises(ValueError, match="Nested implicit stage spans are unsupported."):
        run_pipeline(input_path=input_path, config_path=config_path)
