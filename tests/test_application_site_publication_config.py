from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from ets.application import (
    SitePublicationDialogConfig,
    SitePublicationDialogPlayConfig,
    derive_corpus_slug,
    load_site_publication_dialog_config,
    save_site_publication_dialog_config,
    site_publication_request_from_dialog_config,
)


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = ROOT / "tests" / "_runtime"


def _runtime_dir(prefix: str) -> Path:
    target = RUNTIME_ROOT / f"{prefix}_{uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_site_publication_dialog_config_round_trip_json() -> None:
    runtime = _runtime_dir("app_site_publication_config_roundtrip")
    config_path = runtime / "publication_dialog.json"

    config = SitePublicationDialogConfig(
        author_name="Jean Racine",
        corpus_title="Théâtre complet",
        scientific_editor="Caroline Labrune",
        home_page_tei=(runtime / "accueil.xml").resolve(),
        general_intro_tei=(runtime / "introduction.xml").resolve(),
        output_dir=(runtime / "site").resolve(),
        plays=(
            SitePublicationDialogPlayConfig(
                play_slug="andromaque",
                dramatic_xml_path=(runtime / "andromaque.xml").resolve(),
                notice_xml_path=(runtime / "andromaque-notice.xml").resolve(),
            ),
            SitePublicationDialogPlayConfig(
                play_slug="berenice",
                dramatic_xml_path=(runtime / "berenice.xml").resolve(),
                notice_xml_path=None,
            ),
        ),
        play_order=("berenice", "andromaque"),
        logo_paths=((runtime / "logo.png").resolve(),),
        asset_directories=((runtime / "assets").resolve(),),
        show_xml_download=True,
        publish_notices=True,
        include_metadata=True,
        resolve_notice_xincludes=True,
    )

    written = save_site_publication_dialog_config(config, config_path)
    loaded = load_site_publication_dialog_config(written)

    assert written == config_path.resolve()
    assert loaded == config

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "ets.site_publication_dialog_config"
    assert payload["version"] == 2
    assert payload["metadata"]["author_name"] == "Jean Racine"
    assert payload["plays"][0]["dramatic_xml_path"].endswith("andromaque.xml")


def test_site_publication_dialog_config_invalid_json_fails_cleanly() -> None:
    runtime = _runtime_dir("app_site_publication_config_invalid_json")
    config_path = runtime / "invalid.json"
    config_path.write_text("{", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid publication dialog configuration JSON"):
        load_site_publication_dialog_config(config_path)


def test_site_publication_dialog_config_invalid_structure_fails_cleanly() -> None:
    runtime = _runtime_dir("app_site_publication_config_invalid_shape")
    config_path = runtime / "invalid_structure.json"
    config_path.write_text(
        json.dumps(
            {
                "schema": "ets.site_publication_dialog_config",
                "version": 2,
                "metadata": {"corpus_title": "ETS"},
                "plays": "not-a-list",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="plays"):
        load_site_publication_dialog_config(config_path)


def test_site_publication_dialog_config_rejects_multiple_documents_for_one_play() -> None:
    runtime = _runtime_dir("app_site_publication_config_legacy_multi_docs")
    config_path = runtime / "invalid_multi_docs.json"
    config_path.write_text(
        json.dumps(
            {
                "schema": "ets.site_publication_dialog_config",
                "version": 1,
                "identity": {"site_title": "ETS"},
                "plays": [
                    {
                        "play_slug": "andromaque",
                        "document_paths": [str((runtime / "A1.xml").resolve()), str((runtime / "A2.xml").resolve())],
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="exactly one dramatic XML file"):
        load_site_publication_dialog_config(config_path)


def test_site_publication_request_mapping_supports_intro_and_multiple_plays() -> None:
    runtime = _runtime_dir("app_site_publication_config_to_request")
    config = SitePublicationDialogConfig(
        author_name="Jean Racine",
        corpus_title="Théâtre complet",
        scientific_editor="Caroline Labrune",
        home_page_tei=(runtime / "accueil.xml").resolve(),
        general_intro_tei=(runtime / "introduction.xml").resolve(),
        output_dir=(runtime / "site").resolve(),
        plays=(
            SitePublicationDialogPlayConfig(
                play_slug="andromaque",
                dramatic_xml_path=(runtime / "andromaque.xml").resolve(),
                notice_xml_path=(runtime / "andromaque-notice.xml").resolve(),
            ),
            SitePublicationDialogPlayConfig(
                play_slug="berenice",
                dramatic_xml_path=(runtime / "berenice.xml").resolve(),
                notice_xml_path=None,
            ),
        ),
        play_order=("berenice", "andromaque"),
    )

    request = site_publication_request_from_dialog_config(config)

    assert request.identity.site_title == "Théâtre complet"
    assert request.identity.site_subtitle == "Jean Racine"
    assert request.identity.editor == "Caroline Labrune"
    assert request.identity.project_name == "jean-racine-theatre-complet"
    assert request.general_notice_slug == "introduction"
    assert request.play_order == ("berenice", "andromaque")
    assert len(request.plays) == 2
    assert request.plays[0].play_slug == "berenice"
    assert request.plays[0].related_notice_path is None
    assert request.plays[1].play_slug == "andromaque"
    assert request.plays[1].related_notice_path is not None
    assert len(request.notices) == 3


def test_derive_corpus_slug_uses_author_and_two_title_words() -> None:
    assert derive_corpus_slug("Jean Racine", "Théâtre complet et fragments") == "jean-racine-theatre-complet"
