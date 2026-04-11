from __future__ import annotations

from pathlib import Path

from ets.parser import load_config, parse_play


def test_parse_stable_fixture_markers() -> None:
    root = Path(__file__).resolve().parents[1]
    config = load_config(root / "fixtures" / "stable" / "config.json")
    text = (root / "fixtures" / "stable" / "input.txt").read_text(encoding="utf-8")

    play = parse_play(text, config)
    assert len(play.acts) == 1
    act = play.acts[0]
    assert len(act.scenes) == 1
    scene = act.scenes[0]

    assert scene.head_readings[config.reference_witness].startswith("SCENE")
    assert "ORESTE" in scene.cast_readings[config.reference_witness]
    assert "PYLADE" in scene.cast_readings[config.reference_witness]

    assert scene.speeches[0].speaker_readings[config.reference_witness] == "ORESTE."
    assert scene.speeches[1].speaker_readings[config.reference_witness] == "PYLADE"

    all_numbers = [line.number for speech in scene.speeches for line in speech.verses]
    assert "37.1" in all_numbers
    assert "37.2" in all_numbers
    assert "134.1" in all_numbers
    assert "134.2" in all_numbers
    assert all_numbers[-1] == "142"

    line_124 = next(line for speech in scene.speeches for line in speech.verses if line.number == "124")
    assert line_124.whole_line_variant is True
