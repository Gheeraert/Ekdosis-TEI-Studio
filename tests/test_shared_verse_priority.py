from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from ets.core import run_pipeline

NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def test_shared_verse_three_segments_same_scene_from_fixture() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture_dir = root / "fixtures" / "shared_verse" / "thebaide_2_2"
    xml_text = run_pipeline(
        input_path=fixture_dir / "input.txt",
        config_path=fixture_dir / "config.json",
    )
    doc = ET.fromstring(xml_text)

    numbers = [el.get("n", "") for el in doc.findall(".//tei:l", NS)]
    assert "441.1" in numbers
    assert "441.2" in numbers
    assert "441.3" in numbers

    # Shared-verse continuity must survive speaker changes in the same scene.
    line_to_speaker: dict[str, str] = {}
    for sp in doc.findall(".//tei:sp", NS):
        speaker = "".join(sp.find("tei:speaker", NS).itertext()).strip()  # type: ignore[union-attr]
        for line in sp.findall("tei:l", NS):
            line_to_speaker[line.get("n", "")] = speaker
    assert line_to_speaker["441.1"].startswith("ANTIGONE")
    assert line_to_speaker["441.2"].startswith("OLYMPE")
    assert line_to_speaker["441.3"].startswith("ANTIGONE")


def test_shared_verse_two_segments_can_cross_successive_scenes() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime_dir = root / "tests" / "_runtime"
    runtime_dir.mkdir(exist_ok=True)

    config_path = runtime_dir / "shared_cross_scene_config.json"
    input_path = runtime_dir / "shared_cross_scene_input.txt"
    config_payload = {
        "PrÃ©nom de l'auteur": "Jean",
        "Nom de l'auteur": "Racine",
        "Titre de la piÃ¨ce": "Test",
        "NumÃ©ro de l'acte": "1",
        "NumÃ©ro de la scÃ¨ne": "1",
        "NumÃ©ro du vers de dÃ©part": 1,
        "Nom de l'Ã©diteur (vous)": "Editeur",
        "PrÃ©nom de l'Ã©diteur": "Test",
        "Temoins": [
            {"abbr": "A", "year": "1667", "desc": "A"},
            {"abbr": "B", "year": "1671", "desc": "B"},
        ],
        "reference_witness": 0,
    }
    config_path.write_text(json.dumps(config_payload), encoding="utf-8")
    input_path.write_text(
        "\n".join(
            [
                "####ACTE I####",
                "####ACTE I####",
                "",
                "###SCENE I###",
                "###SCENE I###",
                "",
                "##ALPHA##",
                "##ALPHA##",
                "",
                "#ALPHA#",
                "#ALPHA#",
                "",
                "Fin...***",
                "Fin...***",
                "",
                "###SCENE II###",
                "###SCENE II###",
                "",
                "##BETA##",
                "##BETA##",
                "",
                "#BETA#",
                "#BETA#",
                "",
                "***Suite.",
                "***Suite.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    xml_text = run_pipeline(input_path=input_path, config_path=config_path)
    doc = ET.fromstring(xml_text)

    scene_divs = doc.findall(".//tei:div[@type='scene']", NS)
    assert len(scene_divs) == 2

    scene_1_lines = [el.get("n", "") for el in scene_divs[0].findall(".//tei:l", NS)]
    scene_2_lines = [el.get("n", "") for el in scene_divs[1].findall(".//tei:l", NS)]
    assert "1.1" in scene_1_lines
    assert "1.2" in scene_2_lines

    scene_2_first_speaker = scene_divs[1].find(".//tei:sp/tei:speaker", NS)
    assert scene_2_first_speaker is not None
    assert "".join(scene_2_first_speaker.itertext()).strip().startswith("BETA")
