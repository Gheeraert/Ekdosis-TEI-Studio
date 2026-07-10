"""Tests for ets.web.config_builder — in-memory EditionConfig construction."""

from __future__ import annotations

import json

import pytest

from ets.domain import EditionConfig, Witness
from ets.web.config_builder import config_from_dict, config_from_form


# ── Helpers ──────────────────────────────────────────────────────────────────

_TEMOINS_2 = [
    {"abbr": "A", "year": "1670", "desc": "Édition princeps"},
    {"abbr": "B", "year": "1676", "desc": "Collective"},
]

_MINIMAL_RAW = {
    "Prénom de l'auteur": "Jean",
    "Nom de l'auteur": "Racine",
    "Titre de la pièce": "Britannicus",
    "Prénom de l'éditeur scientifique": "Caroline",
    "Nom de l'éditeur scientifique": "Labrune",
    "Prénom du transcripteur": "",
    "Nom du transcripteur": "",
    "Temoins": _TEMOINS_2,
}


# ── config_from_dict ─────────────────────────────────────────────────────────

def test_config_from_dict_title_author_editor() -> None:
    cfg = config_from_dict(_MINIMAL_RAW)
    assert cfg.title == "Britannicus"
    assert cfg.author == "Jean Racine"
    assert cfg.editor == "Caroline Labrune"


def test_config_from_dict_transcriber_empty() -> None:
    cfg = config_from_dict(_MINIMAL_RAW)
    assert cfg.transcriber == ""


def test_config_from_dict_witnesses() -> None:
    cfg = config_from_dict(_MINIMAL_RAW)
    assert len(cfg.witnesses) == 2
    assert cfg.witnesses[0] == Witness(siglum="A", year="1670", description="Édition princeps")
    assert cfg.witnesses[1] == Witness(siglum="B", year="1676", description="Collective")


def test_config_from_dict_preserves_witness_kind() -> None:
    raw = {
        **_MINIMAL_RAW,
        "Temoins": [
            {"abbr": "A", "year": "1670", "desc": "A", "kind": "documentary"},
            {"abbr": "E", "year": "1670-Reg.", "desc": "Regularized", "kind": "editorial"},
        ],
    }

    cfg = config_from_dict(raw)

    assert [witness.kind for witness in cfg.witnesses] == ["documentary", "editorial"]


def test_config_from_dict_rejects_invalid_witness_kind() -> None:
    raw = {
        **_MINIMAL_RAW,
        "Temoins": [
            {"abbr": "E", "year": "1670-Reg.", "desc": "Regularized", "kind": "regularized"},
        ],
    }

    with pytest.raises(ValueError, match="Unsupported witness kind"):
        config_from_dict(raw)


def test_config_from_dict_reference_witness_defaults_to_last() -> None:
    cfg = config_from_dict(_MINIMAL_RAW)
    assert cfg.reference_witness == 1  # last witness


def test_config_from_dict_reference_witness_by_siglum() -> None:
    raw = {**_MINIMAL_RAW, "Témoin de référence": "A"}
    cfg = config_from_dict(raw)
    assert cfg.reference_witness == 0


def test_config_from_dict_reference_witness_by_lemme() -> None:
    raw = {**_MINIMAL_RAW, "Lemme": "A"}
    cfg = config_from_dict(raw)
    assert cfg.reference_witness == 0


def test_config_from_dict_reference_witness_by_lemme_temoin() -> None:
    raw = {**_MINIMAL_RAW, "Lemme témoin": "A"}
    cfg = config_from_dict(raw)
    assert cfg.reference_witness == 0


def test_config_from_dict_castlist_path_is_cleared() -> None:
    raw = {**_MINIMAL_RAW, "castlist_path": "castlist2.txt"}
    cfg = config_from_dict(raw)
    assert cfg.castlist_path == ""


def test_config_from_dict_transcription_path_is_cleared() -> None:
    raw = {**_MINIMAL_RAW, "transcription_path": "scene1.txt"}
    cfg = config_from_dict(raw)
    assert cfg.transcription_path == ""


def test_web_load_desktop_config_preserves_speaker_authority() -> None:
    raw = {
        **_MINIMAL_RAW,
        "Personnages": [
            {"id": "nero", "nom": "Néron", "aliases": ["NERON", "NÉRON"]},
        ],
    }

    cfg = config_from_dict(raw)

    assert cfg.characters
    assert cfg.characters[0].id == "nero"
    assert cfg.characters[0].label == "Néron"
    assert cfg.characters[0].aliases == ["NERON", "NÉRON"]



def test_web_load_desktop_config_accepts_legacy_characters_authority() -> None:
    raw = {
        **_MINIMAL_RAW,
        "characters": [
            {"id": "nero", "label": "Néron", "aliases": ["NERON", "NÉRON"]},
        ],
    }

    cfg = config_from_dict(raw)

    assert cfg.characters
    assert cfg.characters[0].id == "nero"
    assert cfg.characters[0].label == "Néron"
    assert cfg.characters[0].aliases == ["NERON", "NÉRON"]

def test_config_from_dict_missing_title_raises() -> None:
    raw = {**_MINIMAL_RAW, "Titre de la pièce": ""}
    with pytest.raises(ValueError, match="titre"):
        config_from_dict(raw)


def test_config_from_dict_empty_witnesses_raises() -> None:
    raw = {**_MINIMAL_RAW, "Temoins": []}
    with pytest.raises(ValueError, match="[Tt]émoin"):
        config_from_dict(raw)


def test_config_from_dict_witness_missing_abbr_raises() -> None:
    raw = {**_MINIMAL_RAW, "Temoins": [{"year": "1670", "desc": "A"}]}
    with pytest.raises(ValueError, match="sigle"):
        config_from_dict(raw)


def test_config_from_dict_with_full_britannicus_json() -> None:
    """Round-trip test against the exact example JSON from the user spec."""
    raw = {
        "Prénom de l'auteur": "Jean",
        "Nom de l'auteur": "Racine",
        "Titre de la pièce": "Britannicus",
        "Prénom de l'éditeur scientifique": "Caroline",
        "Nom de l'éditeur scientifique": "Labrune",
        "Prénom du transcripteur": "",
        "Nom du transcripteur": "",
        "Temoins": [
            {"abbr": "A", "year": "1670", "desc": "Barbin, BNF cote RES YF 3208"},
            {"abbr": "B", "year": "1676", "desc": "Collective"},
            {"abbr": "C", "year": "1687", "desc": "Collective"},
            {"abbr": "D", "year": "1697", "desc": "Définitive"},
            {"abbr": "E", "year": "1670-Rég.", "desc": "Première édition régularisée"},
        ],
        "castlist_path": "castlist2.txt",
    }
    cfg = config_from_dict(raw)
    assert cfg.title == "Britannicus"
    assert cfg.author == "Jean Racine"
    assert len(cfg.witnesses) == 5
    assert cfg.witnesses[0].siglum == "A"
    assert cfg.witnesses[4].siglum == "E"
    assert cfg.reference_witness == 4  # last, no reference key in JSON
    assert cfg.castlist_path == ""     # cleared in web mode


# ── config_from_form ─────────────────────────────────────────────────────────

def test_config_from_form_basic() -> None:
    form = {
        "titre": "Andromaque",
        "auteur_prenom": "Jean",
        "auteur_nom": "Racine",
        "editeur_prenom": "Marie",
        "editeur_nom": "Dupont",
        "transcripteur_prenom": "",
        "transcripteur_nom": "",
        "temoins_json": json.dumps(_TEMOINS_2),
        "temoin_reference": "",
        "transcription": "",
    }
    cfg = config_from_form(form)
    assert cfg.title == "Andromaque"
    assert cfg.author == "Jean Racine"
    assert cfg.editor == "Marie Dupont"
    assert cfg.transcriber == ""


def test_config_from_form_temoins_as_witness_objects() -> None:
    form = {
        "titre": "Test",
        "auteur_prenom": "",
        "auteur_nom": "",
        "editeur_prenom": "",
        "editeur_nom": "",
        "transcripteur_prenom": "",
        "transcripteur_nom": "",
        "temoins_json": json.dumps(_TEMOINS_2),
        "temoin_reference": "",
        "transcription": "",
    }
    cfg = config_from_form(form)
    assert len(cfg.witnesses) == 2
    assert cfg.witnesses[0] == Witness(siglum="A", year="1670", description="Édition princeps")


def test_config_from_form_preserves_witness_kind_from_json_textarea() -> None:
    form = {
        "titre": "Test",
        "auteur_prenom": "",
        "auteur_nom": "",
        "editeur_prenom": "",
        "editeur_nom": "",
        "transcripteur_prenom": "",
        "transcripteur_nom": "",
        "temoins_json": json.dumps([
            {"abbr": "A", "year": "1670", "desc": "A"},
            {"abbr": "E", "year": "1670-Reg.", "desc": "Regularized", "kind": "editorial"},
        ]),
        "temoin_reference": "",
        "transcription": "",
    }

    cfg = config_from_form(form)

    assert [witness.kind for witness in cfg.witnesses] == ["", "editorial"]


def test_config_from_form_reference_by_siglum() -> None:
    form = {
        "titre": "Test",
        "auteur_prenom": "",
        "auteur_nom": "",
        "editeur_prenom": "",
        "editeur_nom": "",
        "transcripteur_prenom": "",
        "transcripteur_nom": "",
        "temoins_json": json.dumps(_TEMOINS_2),
        "temoin_reference": "A",
        "transcription": "",
    }
    cfg = config_from_form(form)
    assert cfg.reference_witness == 0


def test_config_from_form_default_reference_is_last() -> None:
    form = {
        "titre": "Test",
        "auteur_prenom": "",
        "auteur_nom": "",
        "editeur_prenom": "",
        "editeur_nom": "",
        "transcripteur_prenom": "",
        "transcripteur_nom": "",
        "temoins_json": json.dumps(_TEMOINS_2),
        "temoin_reference": "",
        "transcription": "",
    }
    cfg = config_from_form(form)
    assert cfg.reference_witness == 1


def test_config_from_form_missing_titre_raises() -> None:
    form = {
        "titre": "",
        "temoins_json": json.dumps(_TEMOINS_2),
    }
    with pytest.raises(ValueError, match="titre"):
        config_from_form(form)


def test_config_from_form_invalid_json_raises() -> None:
    form = {
        "titre": "Test",
        "temoins_json": "pas du json",
    }
    with pytest.raises(ValueError, match="[Jj][Ss][Oo][Nn]"):
        config_from_form(form)


def _form_with_reference(ref: str) -> dict:
    return {
        "titre": "Test",
        "auteur_prenom": "",
        "auteur_nom": "",
        "editeur_prenom": "",
        "editeur_nom": "",
        "transcripteur_prenom": "",
        "transcripteur_nom": "",
        "temoins_json": json.dumps(_TEMOINS_2),
        "temoin_reference": ref,
    }


def test_config_from_form_reference_by_index_zero_based() -> None:
    cfg = config_from_form(_form_with_reference("0"))
    assert cfg.reference_witness == 0


def test_config_from_form_reference_unknown_siglum_raises() -> None:
    with pytest.raises(ValueError, match="[Ss]igle|invalide"):
        config_from_form(_form_with_reference("Z"))


def test_config_from_form_reference_non_numeric_non_siglum_raises() -> None:
    with pytest.raises(ValueError, match="invalide|entier"):
        config_from_form(_form_with_reference("pas-un-sigle"))


def test_config_from_form_reference_index_out_of_bounds_raises() -> None:
    with pytest.raises(ValueError, match="[Hh]ors limites|hors|invalide"):
        config_from_form(_form_with_reference("99"))


def test_config_from_form_castlist_path_always_empty() -> None:
    form = {
        "titre": "Test",
        "auteur_prenom": "",
        "auteur_nom": "",
        "editeur_prenom": "",
        "editeur_nom": "",
        "transcripteur_prenom": "",
        "transcripteur_nom": "",
        "temoins_json": json.dumps(_TEMOINS_2),
        "temoin_reference": "",
    }
    cfg = config_from_form(form)
    assert cfg.castlist_path == ""
