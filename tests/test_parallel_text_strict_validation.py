from __future__ import annotations

import json
from pathlib import Path

import pytest

from ets.core import run_pipeline


def _write_runtime_file(path: Path, content: str) -> None:
    path.parent.mkdir(exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _runtime_config(path: Path) -> None:
    payload = {
        "PrÃƒÂ©nom de l'auteur": "Jean",
        "Nom de l'auteur": "Racine",
        "Titre de la piÃƒÂ¨ce": "Andromaque",
        "Nom de l'ÃƒÂ©diteur (vous)": "Gheeraert",
        "PrÃƒÂ©nom de l'ÃƒÂ©diteur": "ClÃƒÂ©mentine",
        "Temoins": [
            {"abbr": "A", "year": "1667", "desc": "A"},
            {"abbr": "B", "year": "1671", "desc": "B"},
        ],
        "reference_witness": 0,
    }
    _write_runtime_file(path, json.dumps(payload))


def test_strict_validation_blocks_on_act_head_token_mismatch() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = root / "tests" / "_runtime"
    config_path = runtime / "strict_head_config.json"
    input_path = runtime / "strict_head_input.txt"
    _runtime_config(config_path)
    _write_runtime_file(
        input_path,
        "\n".join(
            [
                "####ACTE I####",
                "####ACTE####",
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
                "bonjour",
                "bonjour",
            ]
        ),
    )
    with pytest.raises(ValueError, match=r"Token count mismatch in collatable parallel block .*type=act_head.*block=0"):
        run_pipeline(input_path=input_path, config_path=config_path)


def test_strict_validation_blocks_on_cast_token_mismatch() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = root / "tests" / "_runtime"
    config_path = runtime / "strict_cast_config.json"
    input_path = runtime / "strict_cast_input.txt"
    _runtime_config(config_path)
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
                "##ALPHA## ##BETA##",
                "##ALPHA##",
                "",
                "#ALPHA#",
                "#ALPHA#",
                "",
                "bonjour",
                "bonjour",
            ]
        ),
    )
    with pytest.raises(ValueError, match=r"Token count mismatch in collatable parallel block .*type=cast.*block=2"):
        run_pipeline(input_path=input_path, config_path=config_path)
