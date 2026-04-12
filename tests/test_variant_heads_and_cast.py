from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from ets.core import run_pipeline

NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def test_variant_fixture_collates_scene_head_cast_and_speaker_text_blocks() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture_dir = root / "fixtures" / "variant_head_and_cast"
    xml_text = run_pipeline(
        input_path=fixture_dir / "input_andromaque_3_3.txt",
        config_path=fixture_dir / "config_andromaque_3_3.json",
    )
    doc = ET.fromstring(xml_text)

    scene = doc.find(".//tei:div[@type='scene']", NS)
    assert scene is not None

    scene_head = scene.find("./tei:head", NS)
    assert scene_head is not None
    # No variant expected here in fixture, but still handled by collated text rendering.
    assert "".join(scene_head.itertext()).startswith("SCENE")

    cast = scene.find("./tei:stage[@type='personnages']", NS)
    assert cast is not None
    cast_app = cast.find("./tei:app", NS)
    assert cast_app is not None
    assert cast_app.find("./tei:lem", NS) is not None
    assert len(cast_app.findall("./tei:rdg", NS)) >= 1

    speaker = scene.find(".//tei:sp/tei:speaker", NS)
    assert speaker is not None
    speaker_app = speaker.find("./tei:app", NS)
    assert speaker_app is not None
    assert speaker_app.find("./tei:lem", NS) is not None
