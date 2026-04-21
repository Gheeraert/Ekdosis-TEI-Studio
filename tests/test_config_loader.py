from __future__ import annotations

import json
from pathlib import Path

from ets.domain import EditionConfig, Witness
from ets.parser import load_config, save_config


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = ROOT / "tests" / "_runtime"
RUNTIME_DIR.mkdir(exist_ok=True)


def _config_payload_with_reference(reference_key: str, reference_value: str) -> dict[str, object]:
    return {
        "Prénom de l'auteur": "Jean",
        "Nom de l'auteur": "Racine",
        "Titre de la pièce": "Andromaque",
        "Prénom de l'éditeur": "Clémentine",
        "Nom de l'éditeur (vous)": "Gheeraert",
        "Temoins": [
            {"abbr": "A", "year": "1667", "desc": "A"},
            {"abbr": "B", "year": "1671", "desc": "B"},
            {"abbr": "F", "year": "2025", "desc": "F"},
        ],
        reference_key: reference_value,
    }


def test_load_config_uses_reference_from_canonical_key() -> None:
    config_path = RUNTIME_DIR / "config_loader_reference_canonical.json"
    config_path.write_text(
        json.dumps(_config_payload_with_reference("Témoin de référence", "B"), ensure_ascii=False),
        encoding="utf-8",
    )
    config = load_config(config_path)
    assert config.reference_witness == 1


def test_load_config_uses_legacy_fallback_key() -> None:
    config_path = RUNTIME_DIR / "config_loader_reference_legacy.json"
    config_path.write_text(
        json.dumps(_config_payload_with_reference("Lemme", "1"), ensure_ascii=False),
        encoding="utf-8",
    )
    config = load_config(config_path)
    assert config.reference_witness == 1


def test_cli_override_keeps_priority() -> None:
    config = load_config(ROOT / "fixtures" / "stable" / "config.json", reference_override=0)
    assert config.reference_witness == 0


def test_save_config_writes_canonical_json_without_reference_key() -> None:
    config = EditionConfig(
        title="Britannicus",
        author="Jean Racine",
        editor="Tony Gheeraert",
        witnesses=[
            Witness(siglum="A", year="1670", description="Barbin"),
            Witness(siglum="B", year="1676", description="Collective"),
        ],
        reference_witness=0,
    )
    saved_path = save_config(config, RUNTIME_DIR / "canonique.json")
    payload = json.loads(saved_path.read_text(encoding="utf-8"))

    assert payload["Prénom de l'auteur"] == "Jean"
    assert payload["Nom de l'auteur"] == "Racine"
    assert payload["Titre de la pièce"] == "Britannicus"
    assert payload["Prénom de l'éditeur"] == "Tony"
    assert payload["Nom de l'éditeur (vous)"] == "Gheeraert"
    assert payload["Temoins"][0] == {"abbr": "A", "year": "1670", "desc": "Barbin"}
    assert "Numéro du vers de départ" not in payload
    assert "Numéro de l'acte" not in payload
    assert "Numéro de la scène" not in payload

    assert "reference_witness" not in payload
    assert "Témoin de référence" not in payload


def test_load_config_after_save_remains_compatible() -> None:
    original = EditionConfig(
        title="Britannicus",
        author="Jean Racine",
        editor="Tony Gheeraert",
        witnesses=[Witness(siglum="A", year="1670", description="Barbin")],
        reference_witness=0,
    )
    path = save_config(original, RUNTIME_DIR / "saved.json")

    reloaded = load_config(path)
    assert reloaded.title == "Britannicus"
    assert reloaded.author == "Jean Racine"
    assert reloaded.editor == "Tony Gheeraert"
    assert len(reloaded.witnesses) == 1


def test_modify_existing_config_and_save() -> None:
    source = ROOT / "fixtures" / "stable" / "config.json"
    config = load_config(source)
    modified = EditionConfig(
        title="Britannicus (corrigé)",
        author=config.author,
        editor=config.editor,
        witnesses=config.witnesses,
        reference_witness=config.reference_witness,
    )
    saved = save_config(modified, RUNTIME_DIR / "modified.json")
    reloaded = load_config(saved)

    assert reloaded.title == "Britannicus (corrigé)"
