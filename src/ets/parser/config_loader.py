from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ets.domain import EditionConfig, Witness


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
        "TÃ©moin de rÃ©fÃ©rence",
    ]
    legacy_keys = [
        "Témoin de base",
        "Temoin de base",
        "Témoin lemme",
        "Temoin lemme",
        "Lemme",
        "Lemme témoin",
        "TÃ©moin de base",
        "TÃ©moin lemme",
        "Lemme tÃ©moin",
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


def _canonical_config_payload(config: EditionConfig) -> dict[str, Any]:
    author_first, author_last = _split_person_name(config.author)
    editor_first, editor_last = _split_person_name(config.editor)
    return {
        "Prénom de l'auteur": author_first,
        "Nom de l'auteur": author_last,
        "Titre de la pièce": config.title,
        "Prénom de l'éditeur": editor_first,
        "Nom de l'éditeur (vous)": editor_last,
        "Temoins": [
            {"abbr": witness.siglum, "year": witness.year, "desc": witness.description}
            for witness in config.witnesses
        ],
    }


def load_config(path: str | Path, reference_override: int | None = None) -> EditionConfig:
    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))

    author_first = _pick(raw, ["Prénom de l'auteur", "PrÃ©nom de l'auteur", "PrÃƒÂ©nom de l'auteur"])
    author_last = _pick(raw, ["Nom de l'auteur"])
    title = _pick(raw, ["Titre de la pièce", "Titre de la piÃ¨ce", "Titre de la piÃƒÂ¨ce"])
    editor_first = _pick(raw, ["Prénom de l'éditeur", "PrÃ©nom de l'Ã©diteur", "PrÃƒÂ©nom de l'ÃƒÂ©diteur"])
    editor_last = _pick(raw, ["Nom de l'éditeur (vous)", "Nom de l'Ã©diteur (vous)", "Nom de l'ÃƒÂ©diteur (vous)"])

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
    return EditionConfig(
        title=title,
        author=author,
        editor=editor,
        witnesses=witnesses,
        reference_witness=reference_witness,
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
