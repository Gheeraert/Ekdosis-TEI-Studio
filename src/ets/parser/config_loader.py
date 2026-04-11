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


def load_config(path: str | Path, reference_override: int | None = None) -> EditionConfig:
    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))

    author_first = _pick(raw, ["Prénom de l'auteur", "PrÃ©nom de l'auteur"])
    author_last = _pick(raw, ["Nom de l'auteur"])
    title = _pick(raw, ["Titre de la pièce", "Titre de la piÃ¨ce"])
    editor_first = _pick(raw, ["Prénom de l'éditeur", "PrÃ©nom de l'Ã©diteur"])
    editor_last = _pick(raw, ["Nom de l'éditeur (vous)", "Nom de l'Ã©diteur (vous)"])
    start_line = int(_pick(raw, ["Numéro du vers de départ", "NumÃ©ro du vers de dÃ©part"], 1))
    act_number = str(_pick(raw, ["Numéro de l'acte", "NumÃ©ro de l'acte"], "1"))
    scene_number = str(_pick(raw, ["Numéro de la scène", "NumÃ©ro de la scÃ¨ne"], "1"))

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

    if reference_override is not None:
        reference_witness = reference_override
    else:
        reference_witness = len(witnesses) - 1

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
        start_line_number=start_line,
        act_number=act_number,
        scene_number=scene_number,
    )
