from __future__ import annotations

import json
from pathlib import Path

import pytest

from ets.domain import Character, EditionConfig, Witness
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




def test_load_config_keeps_legacy_editor_keys_and_optional_transcriber() -> None:
    config_path = RUNTIME_DIR / "config_loader_legacy_editor_keys.json"
    config_path.write_text(
        json.dumps(_config_payload_with_reference("Témoin de référence", "B"), ensure_ascii=False),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.editor == "Clémentine Gheeraert"
    assert config.transcriber == ""


def test_load_config_reads_scientific_editor_and_transcriber_keys() -> None:
    payload = _config_payload_with_reference("Témoin de référence", "B")
    payload.pop("Prénom de l'éditeur")
    payload.pop("Nom de l'éditeur (vous)")
    payload["Prénom de l'éditeur scientifique"] = "Caroline"
    payload["Nom de l'éditeur scientifique"] = "Labrune"
    payload["Prénom du transcripteur"] = "Jeanne"
    payload["Nom du transcripteur"] = "Martin"
    config_path = RUNTIME_DIR / "config_loader_scientific_editor_transcriber.json"
    config_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    config = load_config(config_path)

    assert config.editor == "Caroline Labrune"
    assert config.transcriber == "Jeanne Martin"

def test_cli_override_keeps_priority() -> None:
    config = load_config(ROOT / "fixtures" / "stable" / "config.json", reference_override=0)
    assert config.reference_witness == 0
    assert config.castlist_path == ""
    assert config.transcription_path == ""


def test_load_config_without_characters_keeps_legacy_compatibility() -> None:
    config_path = RUNTIME_DIR / "config_loader_without_characters.json"
    config_path.write_text(
        json.dumps(_config_payload_with_reference("Témoin de référence", "B"), ensure_ascii=False),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.characters == []


def test_load_config_reads_optional_personnages() -> None:
    payload = _config_payload_with_reference("Témoin de référence", "B")
    payload["Personnages"] = [
        {
            "id": "char001",
            "nom": "Hermione",
            "aliases": ["HERMIONNE.", "HERMIONE", "Hermione"],
        }
    ]
    config_path = RUNTIME_DIR / "config_loader_personnages.json"
    config_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    config = load_config(config_path)

    assert config.characters == [
        Character(
            id="char001",
            label="Hermione",
            aliases=["HERMIONNE.", "HERMIONE", "Hermione"],
        )
    ]


def test_load_config_reads_optional_characters_alias() -> None:
    payload = _config_payload_with_reference("Témoin de référence", "B")
    payload["characters"] = [
        {
            "id": "char002",
            "label": "Jocaste",
            "aliases": ["IOCASTE", "JOCASTE"],
        }
    ]
    config_path = RUNTIME_DIR / "config_loader_characters.json"
    config_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    config = load_config(config_path)

    assert config.characters == [
        Character(id="char002", label="Jocaste", aliases=["IOCASTE", "JOCASTE"])
    ]


def test_edition_config_loads_speaker_authority_personnages() -> None:
    payload = _config_payload_with_reference("reference_witness", "A")
    payload["Titre de la pièce"] = "Britannicus"
    payload["Personnages"] = [
        {"id": "nero", "nom": "Néron", "aliases": ["NERON", "NÉRON", "Neron."]},
        {"id": "junie", "nom": "Junie", "aliases": ["JUNIE", "IUNIE"]},
    ]
    config_path = RUNTIME_DIR / "config_loader_speaker_authority_personnages.json"
    config_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    config = load_config(config_path)

    assert config.characters == [
        Character(id="nero", label="Néron", aliases=["NERON", "NÉRON", "Neron."]),
        Character(id="junie", label="Junie", aliases=["JUNIE", "IUNIE"]),
    ]
    assert config.castlist_path == ""


def test_edition_config_loads_legacy_characters_as_speaker_authority() -> None:
    payload = _config_payload_with_reference("reference_witness", "A")
    payload["characters"] = [
        {"id": "nero", "label": "Néron", "aliases": ["NERON", "NÉRON"]},
    ]
    config_path = RUNTIME_DIR / "config_loader_legacy_characters_authority.json"
    config_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    config = load_config(config_path)

    assert config.characters == [
        Character(id="nero", label="Néron", aliases=["NERON", "NÉRON"])
    ]


def test_edition_config_reference_witness_loads_but_dump_does_not_serialize_currently() -> None:
    payload = _config_payload_with_reference("reference_witness", "A")
    config_path = RUNTIME_DIR / "config_loader_reference_witness_dump_contract.json"
    config_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    config = load_config(config_path)
    saved_path = save_config(config, RUNTIME_DIR / "reference_witness_dump_contract.json")
    saved_payload = json.loads(saved_path.read_text(encoding="utf-8"))

    assert config.reference_witness == 0
    assert "reference_witness" not in saved_payload
    assert "Témoin de référence" not in saved_payload


def test_edition_config_keeps_speaker_authority_distinct_from_castlist_path() -> None:
    payload = _config_payload_with_reference("reference_witness", "A")
    # Personnages is the speaker authority table; castlist_path is a separate
    # paratext/dramatis-personae source path.
    payload["Personnages"] = [
        {"id": "nero", "nom": "Néron", "aliases": ["NERON"]},
    ]
    payload["castlist_path"] = "paratexts/britannicus_castlist.xml"
    config_path = RUNTIME_DIR / "config_loader_authority_and_castlist_path.json"
    config_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    config = load_config(config_path)

    assert config.characters == [Character(id="nero", label="Néron", aliases=["NERON"])]
    assert config.castlist_path == "paratexts/britannicus_castlist.xml"


def test_load_config_reads_optional_castlist_path() -> None:
    payload = _config_payload_with_reference("Témoin de référence", "B")
    payload["castlist_path"] = "castlist.txt"
    config_path = RUNTIME_DIR / "config_loader_castlist_path.json"
    config_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    config = load_config(config_path)

    assert config.castlist_path == "castlist.txt"


def test_load_config_reads_optional_transcription_path() -> None:
    payload = _config_payload_with_reference("Témoin de référence", "B")
    payload["transcription_path"] = "Esther.txt"
    config_path = RUNTIME_DIR / "config_loader_transcription_path.json"
    config_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    config = load_config(config_path)

    assert config.transcription_path == "Esther.txt"


def _write_character_config(name: str, characters: list[dict[str, object]]) -> Path:
    payload = _config_payload_with_reference("Témoin de référence", "B")
    payload["Personnages"] = characters
    config_path = RUNTIME_DIR / name
    config_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return config_path


def test_load_config_rejects_character_with_empty_id() -> None:
    config_path = _write_character_config(
        "config_loader_character_empty_id.json",
        [{"id": " ", "nom": "Hermione", "aliases": []}],
    )

    with pytest.raises(ValueError, match="id is required"):
        load_config(config_path)


def test_load_config_rejects_character_with_empty_label() -> None:
    config_path = _write_character_config(
        "config_loader_character_empty_label.json",
        [{"id": "char001", "nom": " ", "aliases": []}],
    )

    with pytest.raises(ValueError, match="nom/label is required"):
        load_config(config_path)


def test_load_config_rejects_duplicate_character_ids() -> None:
    config_path = _write_character_config(
        "config_loader_character_duplicate_id.json",
        [
            {"id": "char001", "nom": "Hermione", "aliases": []},
            {"id": "char001", "nom": "Andromaque", "aliases": []},
        ],
    )

    with pytest.raises(ValueError, match="duplicate id"):
        load_config(config_path)


def test_load_config_rejects_character_id_starting_with_digit() -> None:
    config_path = _write_character_config(
        "config_loader_character_digit_id.json",
        [{"id": "1char", "nom": "Hermione", "aliases": []}],
    )

    with pytest.raises(ValueError, match="XML-compatible id"):
        load_config(config_path)


def test_load_config_rejects_character_id_containing_space() -> None:
    config_path = _write_character_config(
        "config_loader_character_space_id.json",
        [{"id": "char 001", "nom": "Hermione", "aliases": []}],
    )

    with pytest.raises(ValueError, match="XML-compatible id"):
        load_config(config_path)


def test_load_config_accepts_simple_character_id() -> None:
    config_path = _write_character_config(
        "config_loader_character_simple_id.json",
        [{"id": "char001", "nom": "Hermione", "aliases": []}],
    )

    config = load_config(config_path)

    assert config.characters == [Character(id="char001", label="Hermione", aliases=[])]


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
    assert payload["Prénom de l'éditeur scientifique"] == "Tony"
    assert payload["Nom de l'éditeur scientifique"] == "Gheeraert"
    assert payload["Prénom du transcripteur"] == ""
    assert payload["Nom du transcripteur"] == ""
    assert payload["Temoins"][0] == {"abbr": "A", "year": "1670", "desc": "Barbin"}
    assert "Numéro du vers de départ" not in payload
    assert "Numéro de l'acte" not in payload
    assert "Numéro de la scène" not in payload

    assert "reference_witness" not in payload
    assert "Témoin de référence" not in payload


    assert "castlist_path" not in payload
    assert "transcription_path" not in payload


def test_save_config_writes_characters_when_present() -> None:
    config = EditionConfig(
        title="Thebaide",
        author="Jean Racine",
        editor="Tony Gheeraert",
        witnesses=[Witness(siglum="A", year="1664", description="A")],
        reference_witness=0,
        characters=[Character(id="char001", label="Jocaste", aliases=["IOCASTE", "JOCASTE"])],
    )
    saved_path = save_config(config, RUNTIME_DIR / "canonique_personnages.json")
    payload = json.loads(saved_path.read_text(encoding="utf-8"))

    assert payload["Personnages"] == [
        {"id": "char001", "nom": "Jocaste", "aliases": ["IOCASTE", "JOCASTE"]}
    ]


def test_save_config_writes_castlist_path_when_present() -> None:
    config = EditionConfig(
        title="Phedre",
        author="Jean Racine",
        editor="Tony Gheeraert",
        witnesses=[Witness(siglum="A", year="1677", description="A")],
        reference_witness=0,
        castlist_path="castlist.txt",
    )
    saved_path = save_config(config, RUNTIME_DIR / "canonique_castlist_path.json")
    payload = json.loads(saved_path.read_text(encoding="utf-8"))

    assert payload["castlist_path"] == "castlist.txt"


def test_save_config_writes_transcription_path_when_present() -> None:
    config = EditionConfig(
        title="Esther",
        author="Jean Racine",
        editor="Tony Gheeraert",
        witnesses=[Witness(siglum="A", year="1689", description="A")],
        reference_witness=0,
        transcription_path="Esther.txt",
    )
    saved_path = save_config(config, RUNTIME_DIR / "canonique_transcription_path.json")
    payload = json.loads(saved_path.read_text(encoding="utf-8"))

    assert payload["transcription_path"] == "Esther.txt"


def test_load_config_after_save_remains_compatible() -> None:
    original = EditionConfig(
        title="Britannicus",
        author="Jean Racine",
        editor="Tony Gheeraert",
        witnesses=[Witness(siglum="A", year="1670", description="Barbin")],
        reference_witness=0,
        transcriber="Caroline Labrune",
    )
    path = save_config(original, RUNTIME_DIR / "saved.json")

    reloaded = load_config(path)
    assert reloaded.title == "Britannicus"
    assert reloaded.author == "Jean Racine"
    assert reloaded.editor == "Tony Gheeraert"
    assert reloaded.transcriber == "Caroline Labrune"
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
