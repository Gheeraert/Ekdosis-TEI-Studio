from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from ets.domain import Character, EditionConfig, Witness


_CHARACTER_ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")


def _pick(data: dict[str, Any], keys: list[str], default: Any = "") -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return default


def _resolve_reference_witness(raw: dict[str, Any], witnesses: list[Witness], reference_override: int | None) -> int:
    if reference_override is not None:
        return reference_override

    canonical_keys = [
        "Témoin de référence",
        "Temoin de référence",
        "Temoin de reference",
        "Reference witness",
        "reference_witness",
    ]
    legacy_keys = [
        "Témoin de base",
        "Temoin de base",
        "Témoin lemme",
        "Temoin lemme",
        "Lemme",
        "Lemme témoin",
    ]
    raw_value = _pick(raw, canonical_keys + legacy_keys, default=None)
    if raw_value is None or str(raw_value).strip() == "":
        # Final fallback only when there is no reference information in config.
        return len(witnesses) - 1

    sigla = [witness.siglum for witness in witnesses]
    raw_text = str(raw_value).strip()
    if raw_text in sigla:
        return sigla.index(raw_text)

    try:
        raw_index = int(raw_text)
    except ValueError as exc:
        raise ValueError(f"Invalid reference witness value: {raw_value!r}") from exc

    if 0 <= raw_index < len(witnesses):
        return raw_index
    if 1 <= raw_index <= len(witnesses):
        return raw_index - 1
    raise ValueError(f"reference_witness is out of range: {raw_index}")


def _split_person_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _load_characters(raw: dict[str, Any]) -> list[Character]:
    characters_raw = _pick(raw, ["Personnages", "characters"], [])
    if characters_raw is None:
        return []
    if not isinstance(characters_raw, list):
        raise ValueError("Invalid characters config: expected a list.")

    characters: list[Character] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(characters_raw):
        if not isinstance(item, dict):
            raise ValueError(f"Invalid characters config at index {index}: expected an object.")
        character_id = str(_pick(item, ["id"], "")).strip()
        label = str(_pick(item, ["nom", "label"], "")).strip()
        if not character_id:
            raise ValueError(f"Invalid character at index {index}: id is required.")
        if not _CHARACTER_ID_RE.fullmatch(character_id):
            raise ValueError(f"Invalid character id {character_id!r}: expected an XML-compatible id.")
        if character_id in seen_ids:
            raise ValueError(f"Invalid characters config: duplicate id {character_id!r}.")
        if not label:
            raise ValueError(f"Invalid character {character_id!r}: nom/label is required.")
        aliases_raw = _pick(item, ["aliases"], [])
        if aliases_raw is None:
            aliases_raw = []
        if not isinstance(aliases_raw, list):
            raise ValueError(f"Invalid aliases for character {character_id or index!r}: expected a list.")
        aliases = [str(alias).strip() for alias in aliases_raw if str(alias).strip()]
        seen_ids.add(character_id)
        characters.append(Character(id=character_id, label=label, aliases=aliases))
    return characters


def _canonical_config_payload(config: EditionConfig) -> dict[str, Any]:
    author_first, author_last = _split_person_name(config.author)
    editor_first, editor_last = _split_person_name(config.editor)
    transcriber_first, transcriber_last = _split_person_name(config.transcriber)
    payload = {
        "Prénom de l'auteur": author_first,
        "Nom de l'auteur": author_last,
        "Titre de la pièce": config.title,
        "Prénom de l'éditeur scientifique": editor_first,
        "Nom de l'éditeur scientifique": editor_last,
        "Prénom du transcripteur": transcriber_first,
        "Nom du transcripteur": transcriber_last,
        "Temoins": [
            {"abbr": witness.siglum, "year": witness.year, "desc": witness.description}
            for witness in config.witnesses
        ],
    }
    if config.characters:
        payload["Personnages"] = [
            {"id": character.id, "nom": character.label, "aliases": list(character.aliases)}
            for character in config.characters
        ]
    if config.transcription_path.strip():
        payload["transcription_path"] = config.transcription_path.strip()
    if config.castlist_path.strip():
        payload["castlist_path"] = config.castlist_path.strip()
    if config.play_id.strip():
        payload["play_id"] = config.play_id.strip()
    return payload


def load_config(path: str | Path, reference_override: int | None = None) -> EditionConfig:
    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))

    author_first = _pick(raw, ["Prénom de l'auteur"])
    author_last = _pick(raw, ["Nom de l'auteur"])
    title = _pick(raw, ["Titre de la pièce"])
    editor_first = _pick(
        raw,
        [
            "Prénom de l'éditeur scientifique",
            "Prénom de l'éditeur",
        ],
    )
    editor_last = _pick(
        raw,
        [
            "Nom de l'éditeur scientifique",
            "Nom de l'éditeur (vous)",
        ],
    )
    transcriber_first = _pick(raw, ["Prénom du transcripteur"], default="")
    transcriber_last = _pick(raw, ["Nom du transcripteur"], default="")

    witnesses_raw = _pick(raw, ["Temoins"], [])
    witnesses = [
        Witness(
            siglum=str(item.get("abbr", "")).strip(),
            year=str(item.get("year", "")).strip(),
            description=str(item.get("desc", "")).strip(),
        )
        for item in witnesses_raw
    ]
    if not witnesses:
        raise ValueError("No witnesses found in config.")

    reference_witness = _resolve_reference_witness(raw, witnesses, reference_override)

    if not 0 <= reference_witness < len(witnesses):
        raise ValueError("reference_witness is out of range.")

    author = f"{author_first} {author_last}".strip()
    editor = f"{editor_first} {editor_last}".strip()
    transcriber = f"{transcriber_first} {transcriber_last}".strip()
    characters = _load_characters(raw)
    transcription_path = str(_pick(raw, ["transcription_path"], "") or "").strip()
    castlist_path = str(_pick(raw, ["castlist_path"], "") or "").strip()
    play_id = str(_pick(raw, ["play_id", "Identifiant de la pièce"], "") or "").strip()
    return EditionConfig(
        title=title,
        author=author,
        editor=editor,
        witnesses=witnesses,
        reference_witness=reference_witness,
        transcriber=transcriber,
        characters=characters,
        transcription_path=transcription_path,
        castlist_path=castlist_path,
        play_id=play_id,
    )


def dump_config(config: EditionConfig) -> str:
    """Serialize an EditionConfig to canonical JSON format."""
    payload = _canonical_config_payload(config)
    return json.dumps(payload, ensure_ascii=False, indent=2)


def save_config(config: EditionConfig, path: str | Path) -> Path:
    """Save an EditionConfig to canonical JSON format and return resolved path."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dump_config(config), encoding="utf-8")
    return target.resolve()
