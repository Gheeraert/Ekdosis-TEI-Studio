from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from ets.collation import collate_play
from ets.core import run_pipeline
from ets.domain import Character, EditionConfig, Witness
from ets.html import render_html_preview_from_tei
from ets.latex import tei_to_ekdosis
from ets.parser import parse_play
from ets.tei.generator import generate_tei_xml

NS = {"tei": "http://www.tei-c.org/ns/1.0"}
XML_NS = "http://www.w3.org/XML/1998/namespace"


def _config() -> EditionConfig:
    return EditionConfig(
        title="Britannicus",
        author="Jean Racine",
        editor="Editeur",
        witnesses=[
            Witness("A", "1670", "A"),
            Witness("B", "1671", "B"),
        ],
        reference_witness=0,
        characters=[
            Character(id="alpha", label="Alpha", aliases=["ALPHA"]),
            Character(id="beta", label="Beta", aliases=["BETA"]),
            Character(id="gamma", label="Gamma", aliases=["GAMMA"]),
        ],
        play_id="britannicus",
    )


def _block(first: str, second: str | None = None) -> list[str]:
    return [first, first if second is None else second]


def _tei_from_blocks(blocks: list[list[str]]) -> str:
    config = _config()
    text = "\n\n".join("\n".join(block) for block in blocks) + "\n"
    play = parse_play(text, config)
    collated = collate_play(play, [witness.siglum for witness in config.witnesses], config.reference_witness)
    return generate_tei_xml(collated, config)


def _base_blocks() -> list[list[str]]:
    return [
        _block("####ACTE I####"),
        _block("###SCENE I###"),
        _block("#ALPHA#"),
    ]


def _line(doc: ET.Element, number: str) -> ET.Element:
    line = doc.find(f".//tei:l[@n='{number}']", NS)
    assert line is not None
    return line


def _xml_id(element: ET.Element) -> str | None:
    return element.get(f"{{{XML_NS}}}id")


def _text(element: ET.Element) -> str:
    return "".join(element.itertext())


def _parts_by_number(doc: ET.Element) -> dict[str, str | None]:
    return {line.get("n", ""): line.get("part") for line in doc.findall(".//tei:l", NS)}


def _speaker_text(sp: ET.Element) -> str:
    speaker = sp.find("tei:speaker", NS)
    assert speaker is not None
    return _text(speaker).strip()


def test_shared_verse_two_fragments_get_initial_and_final_part() -> None:
    ordinary_lines = [_block(f"Vers ordinaire {index}.") for index in range(1, 20)]
    xml_text = _tei_from_blocks(
        [
            *_base_blocks(),
            *ordinary_lines,
            _block("Cause commune***", "Donne commune***"),
            _block("#BETA#"),
            _block("***fin du vers."),
        ]
    )
    doc = ET.fromstring(xml_text)
    line_20_1 = _line(doc, "20.1")
    line_20_2 = _line(doc, "20.2")

    assert line_20_1.get("part") == "I"
    assert line_20_2.get("part") == "F"
    assert _xml_id(line_20_1) == "britannicus-A1S1L20.1"
    assert _xml_id(line_20_2) == "britannicus-A1S1L20.2"
    assert "Cause" in _text(line_20_1)
    assert "fin du vers." in _text(line_20_2)

    speeches = doc.findall(".//tei:sp", NS)
    assert [sp.get("who") for sp in speeches] == ["#char-alpha", "#char-beta"]
    assert [_speaker_text(sp) for sp in speeches] == ["ALPHA", "BETA"]

    app = line_20_1.find("tei:app", NS)
    assert app is not None
    lemma = app.find("tei:lem", NS)
    rdg = app.find("tei:rdg", NS)
    assert lemma is not None
    assert rdg is not None
    assert lemma.get("wit") == "#A"
    assert rdg.get("wit") == "#B"
    assert _text(lemma) == "Cause "
    assert _text(rdg) == "Donne "

    html = render_html_preview_from_tei(xml_text)
    tex = tei_to_ekdosis(xml_text)
    assert 'part="I"' not in html
    assert 'part="F"' not in html
    assert "Cause" in html
    assert "fin du vers." in tex


def test_shared_verse_three_fragments_get_initial_middle_final_part() -> None:
    xml_text = _tei_from_blocks(
        [
            *_base_blocks(),
            _block("debut***"),
            _block("#BETA#"),
            _block("***milieu***"),
            _block("#GAMMA#"),
            _block("***fin."),
        ]
    )
    doc = ET.fromstring(xml_text)

    assert _parts_by_number(doc) == {
        "1.1": "I",
        "1.2": "M",
        "1.3": "F",
    }


def test_shared_verse_part_sequences_are_independent_across_scenes() -> None:
    xml_text = _tei_from_blocks(
        [
            *_base_blocks(),
            _block("scene un***"),
            _block("#BETA#"),
            _block("***fin un."),
            _block("###SCENE II###"),
            _block("#ALPHA#"),
            _block("scene deux***"),
            _block("#BETA#"),
            _block("***fin deux."),
        ]
    )
    doc = ET.fromstring(xml_text)

    assert _parts_by_number(doc) == {
        "1.1": "I",
        "1.2": "F",
        "2.1": "I",
        "2.2": "F",
    }


def test_shared_verse_part_sequences_are_independent_across_acts() -> None:
    xml_text = _tei_from_blocks(
        [
            *_base_blocks(),
            _block("acte un***"),
            _block("#BETA#"),
            _block("***fin un."),
            _block("####ACTE II####"),
            _block("###SCENE I###"),
            _block("#ALPHA#"),
            _block("acte deux***"),
            _block("#BETA#"),
            _block("***fin deux."),
        ]
    )
    doc = ET.fromstring(xml_text)

    assert _parts_by_number(doc) == {
        "1.1": "I",
        "1.2": "F",
        "2.1": "I",
        "2.2": "F",
    }


def test_ordinary_verse_has_no_part_attribute() -> None:
    xml_text = _tei_from_blocks(
        [
            *_base_blocks(),
            _block("Vers ordinaire."),
        ]
    )
    doc = ET.fromstring(xml_text)

    assert _line(doc, "1").get("part") is None


def test_shared_verse_three_segments_same_scene_from_fixture() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture_dir = root / "fixtures" / "shared_verse" / "thebaide_2_2"
    xml_text = run_pipeline(
        input_path=fixture_dir / "input.txt",
        config_path=fixture_dir / "config.json",
    )
    doc = ET.fromstring(xml_text)

    numbers = [el.get("n", "") for el in doc.findall(".//tei:l", NS)]
    assert "2.1" in numbers
    assert "2.2" in numbers
    assert "2.3" in numbers

    # Shared-verse continuity must survive speaker changes in the same scene.
    line_to_speaker: dict[str, str] = {}
    for sp in doc.findall(".//tei:sp", NS):
        speaker = "".join(sp.find("tei:speaker", NS).itertext()).strip()  # type: ignore[union-attr]
        for line in sp.findall("tei:l", NS):
            line_to_speaker[line.get("n", "")] = speaker
    assert line_to_speaker["2.1"].startswith("ANTIGONE")
    assert line_to_speaker["2.2"].startswith("OLYMPE")
    assert line_to_speaker["2.3"].startswith("ANTIGONE")


def test_shared_verse_two_segments_can_cross_successive_scenes() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime_dir = root / "tests" / "_runtime"
    runtime_dir.mkdir(exist_ok=True)

    config_path = runtime_dir / "shared_cross_scene_config.json"
    input_path = runtime_dir / "shared_cross_scene_input.txt"
    config_payload = {
        "Prénom de l'auteur": "Jean",
        "Nom de l'auteur": "Racine",
        "Titre de la pièce": "Test",
        "Nom de l'éditeur (vous)": "Editeur",
        "Prénom de l'éditeur": "Test",
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
