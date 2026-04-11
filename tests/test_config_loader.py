from __future__ import annotations

import json
from pathlib import Path

from ets.parser import load_config


def test_load_config_uses_reference_from_canonical_key() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime_dir = root / "tests" / "_runtime"
    runtime_dir.mkdir(exist_ok=True)
    config_path = runtime_dir / "config_loader_reference_canonical.json"
    payload = {
        "PrÃ©nom de l'auteur": "Jean",
        "Nom de l'auteur": "Racine",
        "Titre de la piÃ¨ce": "Andromaque",
        "PrÃ©nom de l'Ã©diteur": "ClÃ©mentine",
        "Nom de l'Ã©diteur (vous)": "Gheeraert",
        "Temoins": [
            {"abbr": "A", "year": "1667", "desc": "A"},
            {"abbr": "B", "year": "1671", "desc": "B"},
            {"abbr": "F", "year": "2025", "desc": "F"},
        ],
        "reference_witness": "B",
    }
    config_path.write_text(json.dumps(payload), encoding="utf-8")
    config = load_config(config_path)
    assert config.reference_witness == 1


def test_load_config_uses_legacy_fallback_key() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime_dir = root / "tests" / "_runtime"
    runtime_dir.mkdir(exist_ok=True)
    config_path = runtime_dir / "config_loader_reference_legacy.json"
    payload = {
        "PrÃ©nom de l'auteur": "Jean",
        "Nom de l'auteur": "Racine",
        "Titre de la piÃ¨ce": "Andromaque",
        "PrÃ©nom de l'Ã©diteur": "ClÃ©mentine",
        "Nom de l'Ã©diteur (vous)": "Gheeraert",
        "Temoins": [
            {"abbr": "A", "year": "1667", "desc": "A"},
            {"abbr": "B", "year": "1671", "desc": "B"},
            {"abbr": "F", "year": "2025", "desc": "F"},
        ],
        "Lemme": "1",
    }
    config_path.write_text(json.dumps(payload), encoding="utf-8")
    config = load_config(config_path)
    assert config.reference_witness == 1


def test_cli_override_keeps_priority() -> None:
    root = Path(__file__).resolve().parents[1]
    config = load_config(root / "fixtures" / "stable" / "config.json", reference_override=0)
    assert config.reference_witness == 0
