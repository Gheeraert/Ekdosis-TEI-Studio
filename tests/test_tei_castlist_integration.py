from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from ets.core import run_pipeline, run_pipeline_from_text
from ets.parser import load_config
from ets.validation import InputValidationError


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = ROOT / "tests" / "_runtime" / "castlist_integration"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
NS = {"tei": "http://www.tei-c.org/ns/1.0"}
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"


def _input_text() -> str:
    return "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "#THESEE#",
            "#THESEE#",
            "",
            "Je parle.",
            "Je parle.",
        ]
    )


def _config_payload(castlist_path: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "Prénom de l'auteur": "Jean",
        "Nom de l'auteur": "Racine",
        "Titre de la pièce": "Phedre",
        "Prénom de l'éditeur scientifique": "Test",
        "Nom de l'éditeur scientifique": "Editor",
        "Temoins": [
            {"abbr": "A", "year": "1677", "desc": "A"},
            {"abbr": "B", "year": "1687", "desc": "B"},
        ],
        "reference_witness": 0,
    }
    if castlist_path is not None:
        payload["castlist_path"] = castlist_path
    return payload


def _castlist_text() -> str:
    return "\n".join(
        [
            "%%castlist%%",
            "%%head%%",
            "Acteurs",
            "Acteurs",
            "%%fin_head%%",
            '%%cast id=thesee role="Thésée" desc="roi d’Athènes" aliases="THESEE|THESEE."%%',
            "Thésée, roi d’Athènes",
            "Thésée, Roi d’Athènes",
            "%%fin_cast%%",
            "%%setting%%",
            "La scène est à Trézène.",
            "La Scene est à Trézène.",
            "%%fin_setting%%",
            "%%fin_castlist%%",
        ]
    )


def _write_project(name: str, *, castlist_path: str | None = None, castlist_text: str | None = None) -> tuple[Path, Path]:
    project_dir = RUNTIME_DIR / name
    project_dir.mkdir(parents=True, exist_ok=True)
    input_path = project_dir / "input.txt"
    config_path = project_dir / "config.json"
    input_path.write_text(_input_text(), encoding="utf-8")
    config_path.write_text(json.dumps(_config_payload(castlist_path), ensure_ascii=False), encoding="utf-8")
    if castlist_path is not None and castlist_text is not None:
        (project_dir / castlist_path).write_text(castlist_text, encoding="utf-8")
    return input_path, config_path


def test_pipeline_without_castlist_path_has_no_dramatis_personae() -> None:
    input_path, config_path = _write_project("without_castlist")

    xml_text = run_pipeline(input_path=input_path, config_path=config_path)
    root = ET.fromstring(xml_text)

    assert root.find(".//tei:div[@type='dramatis-personae']", NS) is None
    assert root.find(".//tei:front", NS) is None


def test_pipeline_without_castlist_path_matches_previous_output() -> None:
    input_path, config_path = _write_project("without_castlist_equivalent")
    config = load_config(config_path)
    input_text = input_path.read_text(encoding="utf-8")

    from_pipeline = run_pipeline(input_path=input_path, config_path=config_path)
    from_text = run_pipeline_from_text(input_text, config)

    assert ET.tostring(ET.fromstring(from_pipeline), encoding="unicode") == ET.tostring(
        ET.fromstring(from_text),
        encoding="unicode",
    )


def test_pipeline_with_valid_castlist_inserts_front_before_body() -> None:
    input_path, config_path = _write_project(
        "with_castlist",
        castlist_path="castlist.txt",
        castlist_text=_castlist_text(),
    )

    xml_text = run_pipeline(input_path=input_path, config_path=config_path)
    root = ET.fromstring(xml_text)
    text = root.find("tei:text", NS)
    assert text is not None
    children = list(text)

    assert children[0].tag == "{http://www.tei-c.org/ns/1.0}front"
    assert children[1].tag == "{http://www.tei-c.org/ns/1.0}body"
    cast_div = root.find(".//tei:front/tei:div[@type='dramatis-personae']", NS)
    assert cast_div is not None
    cast_item = cast_div.find(".//tei:castItem", NS)
    assert cast_item is not None
    assert cast_item.attrib[XML_ID] == "thesee"
    assert cast_item.findtext("tei:role", namespaces=NS) == "Thésée"
    assert cast_item.findtext("tei:roleDesc", namespaces=NS) == "roi d’Athènes"
    assert cast_div.find("tei:stage[@type='setting']", NS) is not None
    assert root.find(".//tei:body/tei:div[@type='act']", NS) is not None


def test_pipeline_with_missing_castlist_file_raises_clear_error() -> None:
    input_path, config_path = _write_project("missing_castlist", castlist_path="missing.txt")

    with pytest.raises(FileNotFoundError, match="Castlist file not found"):
        run_pipeline(input_path=input_path, config_path=config_path)


def test_pipeline_with_invalid_castlist_raises_castlist_diagnostics() -> None:
    input_path, config_path = _write_project(
        "invalid_castlist",
        castlist_path="castlist.txt",
        castlist_text="\n".join(["%%castlist%%", "%%fin_castlist%%"]),
    )

    with pytest.raises(InputValidationError) as captured:
        run_pipeline(input_path=input_path, config_path=config_path)

    assert any(diagnostic.code == "E_CASTLIST_NO_CAST_ENTRY" for diagnostic in captured.value.diagnostics)
