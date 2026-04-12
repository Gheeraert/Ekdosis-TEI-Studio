from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from ets.core import run_pipeline

NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def test_pipeline_handles_two_successive_scenes_in_same_act() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture_dir = root / "fixtures" / "known_issues" / "andromaque_scenes_3_et_4"
    runtime_dir = root / "tests" / "_runtime"
    runtime_dir.mkdir(exist_ok=True)

    combined_input = runtime_dir / "combined_scene3_scene4.txt"
    combined_input.write_text(
        "\n\n".join(
            [
                _read(fixture_dir / "input_scene3.txt"),
                _read(fixture_dir / "input_scene4.txt"),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    output_path = runtime_dir / "combined_scene3_scene4.xml"
    xml_text = run_pipeline(
        input_path=combined_input,
        config_path=fixture_dir / "config_scene3.json",
    )
    output_path.write_text(xml_text, encoding="utf-8")

    root_xml = ET.fromstring(xml_text)
    acts = root_xml.findall(".//tei:body/tei:div[@type='act']", NS)
    assert len(acts) == 1

    scenes = acts[0].findall("./tei:div[@type='scene']", NS)
    assert len(scenes) == 2

    cast_1 = scenes[0].find("tei:stage[@type='personnages']", NS)
    cast_2 = scenes[1].find("tei:stage[@type='personnages']", NS)
    assert cast_1 is not None and cast_2 is not None
    assert "PH" in "".join(cast_1.itertext())
    assert "ANDROMAQ" in "".join(cast_2.itertext())

    first_speaker_scene_2 = scenes[1].find("./tei:sp/tei:speaker", NS)
    assert first_speaker_scene_2 is not None
    assert "PYRRH" in "".join(first_speaker_scene_2.itertext())

    lines_scene_1 = scenes[0].findall(".//tei:l", NS)
    lines_scene_2 = scenes[1].findall(".//tei:l", NS)
    assert lines_scene_1 and lines_scene_2
    assert lines_scene_1[-1].get("n") != lines_scene_2[0].get("n")
    assert lines_scene_2[0].get("n") != "1"
