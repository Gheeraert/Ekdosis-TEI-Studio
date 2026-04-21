from __future__ import annotations

import json
from pathlib import Path

import pytest

from ets.core import run_pipeline


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _config(path: Path) -> None:
    payload = {
        "PrÃƒÂ©nom de l'auteur": "Jean",
        "Nom de l'auteur": "Racine",
        "Titre de la piÃƒÂ¨ce": "Test",
        "Nom de l'ÃƒÂ©diteur (vous)": "Editeur",
        "PrÃƒÂ©nom de l'ÃƒÂ©diteur": "Test",
        "Temoins": [
            {"abbr": "A", "year": "1667", "desc": "A"},
            {"abbr": "B", "year": "1671", "desc": "B"},
        ],
        "reference_witness": 0,
    }
    _write(path, json.dumps(payload))


def test_scene_change_does_not_reuse_previous_speaker() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = root / "tests" / "_runtime"
    config_path = runtime / "scene_speaker_reset_config.json"
    input_path = runtime / "scene_speaker_reset_input.txt"
    _config(config_path)
    _write(
        input_path,
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
                "Bonjour.",
                "Bonjour.",
                "",
                "###SCENE II###",
                "###SCENE II###",
                "",
                "##BETA##",
                "##BETA##",
                "",
                "Ceci doit ÃƒÂ©chouer sans locuteur.",
                "Ceci doit ÃƒÂ©chouer sans locuteur.",
            ]
        )
        + "\n",
    )

    with pytest.raises(ValueError, match="Verse found before speaker."):
        run_pipeline(input_path=input_path, config_path=config_path)


def test_open_shared_verse_can_only_cross_immediate_next_scene() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = root / "tests" / "_runtime"
    config_path = runtime / "scene_shared_limit_config.json"
    input_path = runtime / "scene_shared_limit_input.txt"
    _config(config_path)
    _write(
        input_path,
        "\n".join(
            [
                "####ACTE I####",
                "####ACTE I####",
                "",
                "###SCENE I###",
                "###SCENE I###",
                "",
                "##A##",
                "##A##",
                "",
                "#A#",
                "#A#",
                "",
                "Fin...***",
                "Fin...***",
                "",
                "###SCENE II###",
                "###SCENE II###",
                "",
                "##B##",
                "##B##",
                "",
                "#B#",
                "#B#",
                "",
                "Texte sans reprise.",
                "Texte sans reprise.",
                "",
                "###SCENE III###",
                "###SCENE III###",
                "",
                "##C##",
                "##C##",
                "",
                "#C#",
                "#C#",
                "",
                "***Cette reprise tardive ne doit pas continuer 1.x",
                "***Cette reprise tardive ne doit pas continuer 1.x",
            ]
        )
        + "\n",
    )

    xml = run_pipeline(input_path=input_path, config_path=config_path)
    assert 'n="3"' in xml
    assert 'n="1.2"' not in xml
