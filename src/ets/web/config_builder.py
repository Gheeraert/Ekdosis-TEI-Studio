"""Build EditionConfig from web form data or a raw ETS JSON dict.

Mirrors the logic of ets.parser.config_loader but works entirely in memory —
no file I/O, no castlist resolution (not applicable in web mode).
"""

from __future__ import annotations

import json
from typing import Any

from ets.domain import EditionConfig, Witness
from ets.parser.config_loader import _load_characters


def _pick(data: dict[str, Any], keys: list[str], default: Any = "") -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return default


def _resolve_reference_witness(raw: dict[str, Any], witnesses: list[Witness]) -> int:
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
    ]
    raw_value = _pick(raw, canonical_keys + legacy_keys, default=None)
    if raw_value is None or str(raw_value).strip() == "":
        return len(witnesses) - 1

    sigla = [w.siglum for w in witnesses]
    raw_text = str(raw_value).strip()
    if raw_text in sigla:
        return sigla.index(raw_text)

    try:
        raw_index = int(raw_text)
    except ValueError as exc:
        raise ValueError(f"Témoin de référence invalide : {raw_value!r}") from exc

    if 0 <= raw_index < len(witnesses):
        return raw_index
    if 1 <= raw_index <= len(witnesses):
        return raw_index - 1
    raise ValueError(f"Index de témoin de référence hors limites : {raw_index}")


def _witnesses_from_raw(witnesses_raw: list[Any]) -> list[Witness]:
    witnesses: list[Witness] = []
    for i, item in enumerate(witnesses_raw):
        if not isinstance(item, dict):
            raise ValueError(f"Témoin #{i + 1} : un objet JSON est attendu.")
        abbr = str(item.get("abbr", "")).strip()
        year = str(item.get("year", "")).strip()
        desc = str(item.get("desc", "")).strip()
        if not abbr:
            raise ValueError(f"Témoin #{i + 1} : le sigle (abbr) est requis.")
        witnesses.append(Witness(siglum=abbr, year=year, description=desc))
    return witnesses


def config_from_dict(raw: dict[str, Any]) -> EditionConfig:
    """Build an EditionConfig from a raw ETS JSON dict.

    Accepts the same keys as the existing config files (French labels).
    castlist_path and transcription_path are always cleared: local file
    paths have no meaning in web mode.
    """
    author_first = _pick(raw, ["Prénom de l'auteur"])
    author_last = _pick(raw, ["Nom de l'auteur"])
    title = _pick(raw, ["Titre de la pièce"])
    editor_first = _pick(raw, [
        "Prénom de l'éditeur scientifique",
        "Prénom de l'éditeur",
    ])
    editor_last = _pick(raw, [
        "Nom de l'éditeur scientifique",
        "Nom de l'éditeur (vous)",
    ])
    transcriber_first = _pick(raw, ["Prénom du transcripteur"], default="")
    transcriber_last = _pick(raw, ["Nom du transcripteur"], default="")

    witnesses_raw = _pick(raw, ["Temoins"], [])
    if not isinstance(witnesses_raw, list) or not witnesses_raw:
        raise ValueError("Au moins un témoin est requis (clé « Temoins »).")

    witnesses = _witnesses_from_raw(witnesses_raw)
    reference_witness = _resolve_reference_witness(raw, witnesses)

    title = str(title).strip()
    if not title:
        raise ValueError("Le titre de la pièce est requis.")

    author = f"{author_first} {author_last}".strip()
    editor = f"{editor_first} {editor_last}".strip()
    transcriber = f"{transcriber_first} {transcriber_last}".strip()
    characters = _load_characters(raw)

    return EditionConfig(
        title=title,
        author=author,
        editor=editor,
        witnesses=witnesses,
        reference_witness=reference_witness,
        transcriber=transcriber,
        characters=characters,
        castlist_path="",
        transcription_path="",
    )


def config_from_form(form: Any) -> EditionConfig:
    """Build an EditionConfig from HTML form data (ImmutableMultiDict or plain dict)."""
    titre = form.get("titre", "").strip()
    auteur_prenom = form.get("auteur_prenom", "").strip()
    auteur_nom = form.get("auteur_nom", "").strip()
    editeur_prenom = form.get("editeur_prenom", "").strip()
    editeur_nom = form.get("editeur_nom", "").strip()
    transcripteur_prenom = form.get("transcripteur_prenom", "").strip()
    transcripteur_nom = form.get("transcripteur_nom", "").strip()
    temoins_json_raw = form.get("temoins_json", "").strip()
    temoin_reference_raw = form.get("temoin_reference", "").strip()

    if not titre:
        raise ValueError("Le titre de la pièce est requis.")
    if not temoins_json_raw:
        raise ValueError("La liste des témoins (JSON) est requise.")

    try:
        temoins_raw = json.loads(temoins_json_raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON des témoins invalide : {exc}") from exc

    if not isinstance(temoins_raw, list) or not temoins_raw:
        raise ValueError("La liste des témoins doit être un tableau JSON non vide.")

    witnesses = _witnesses_from_raw(temoins_raw)

    if temoin_reference_raw:
        sigla = [w.siglum for w in witnesses]
        if temoin_reference_raw in sigla:
            reference_witness = sigla.index(temoin_reference_raw)
        else:
            try:
                idx = int(temoin_reference_raw)
            except ValueError:
                known = ", ".join(sigla)
                raise ValueError(
                    f"Témoin de référence invalide : {temoin_reference_raw!r} "
                    f"n'est ni un sigle connu ({known}) ni un entier."
                )
            if 0 <= idx < len(witnesses):
                reference_witness = idx
            elif 1 <= idx <= len(witnesses):
                reference_witness = idx - 1
            else:
                raise ValueError(
                    f"Index de témoin de référence hors limites : {idx} "
                    f"(attendu entre 0 et {len(witnesses) - 1})."
                )
    else:
        reference_witness = len(witnesses) - 1

    author = f"{auteur_prenom} {auteur_nom}".strip()
    editor = f"{editeur_prenom} {editeur_nom}".strip()
    transcriber = f"{transcripteur_prenom} {transcripteur_nom}".strip()

    return EditionConfig(
        title=titre,
        author=author,
        editor=editor,
        witnesses=witnesses,
        reference_witness=reference_witness,
        transcriber=transcriber,
        castlist_path="",
        transcription_path="",
    )
