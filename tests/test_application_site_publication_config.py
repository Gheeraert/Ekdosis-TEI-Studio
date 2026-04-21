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
                preface_xml_path=(runtime / "andromaque-preface.xml").resolve(),
                dramatis_xml_path=(runtime / "andromaque-dramatis.xml").resolve(),
            ),
            SitePublicationDialogPlayConfig(
                play_slug="berenice",
                dramatic_xml_path=(runtime / "berenice.xml").resolve(),
                notice_xml_path=None,
                preface_xml_path=None,
                dramatis_xml_path=None,
            ),
        ),
        play_order=("berenice", "andromaque"),
        logo_paths=((runtime / "logo.png").resolve(),),
        asset_directories=((runtime / "assets").resolve(),),
        show_xml_download=True,
        publish_notices=True,
        publish_prefaces=True,
        include_metadata=True,
        resolve_notice_xincludes=True,
    )

    written = save_site_publication_dialog_config(config, config_path)
    loaded = load_site_publication_dialog_config(written)

    assert written == config_path.resolve()
    assert loaded == config

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "ets.site_publication_dialog_config"
    assert payload["version"] == 3
    assert payload["metadata"]["author_name"] == "Jean Racine"
    assert payload["plays"][0]["dramatic_xml_path"].endswith("andromaque.xml")
    assert payload["plays"][0]["notice_xml_path"].endswith("andromaque-notice.xml")
    assert payload["plays"][0]["preface_xml_path"].endswith("andromaque-preface.xml")
    assert payload["plays"][0]["dramatis_xml_path"].endswith("andromaque-dramatis.xml")
    assert payload["options"]["publish_prefaces"] is True


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
                "version": 3,
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


def test_site_publication_request_mapping_supports_intro_notice_preface_and_dramatis() -> None:
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
                dramatic_xml_path=(ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic" / "andromaque.xml"),
                notice_xml_path=(ROOT / "fixtures" / "site_builder" / "minimal" / "notices" / "andromaque-notice.xml"),
                preface_xml_path=(ROOT / "fixtures" / "site_builder" / "unites_editoriales" / "préface.xml"),
                dramatis_xml_path=(runtime / "andromaque-dramatis.xml").resolve(),
            ),
            SitePublicationDialogPlayConfig(
                play_slug="berenice",
                dramatic_xml_path=(ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic" / "berenice.xml"),
                notice_xml_path=None,
                preface_xml_path=None,
                dramatis_xml_path=None,
            ),
        ),
        play_order=("berenice", "andromaque"),
    )
    config.home_page_tei.write_text("<TEI/>", encoding="utf-8")  # type: ignore[union-attr]
    config.general_intro_tei.write_text("<TEI/>", encoding="utf-8")  # type: ignore[union-attr]
    (runtime / "andromaque-dramatis.xml").write_text("<TEI/>", encoding="utf-8")

    request = site_publication_request_from_dialog_config(config)

    assert request.identity.site_title == "Théâtre complet"
    assert request.identity.site_subtitle == "Jean Racine"
    assert request.identity.editor == "Caroline Labrune"
    assert request.identity.project_name == "jean-racine-theatre-complet"
    assert request.play_order == ("berenice", "andromaque")
    assert len(request.plays) == 2
    assert request.plays[0].play_slug == "berenice"
    assert request.plays[1].play_slug == "andromaque"
    assert request.play_notice_map == (("andromaque", "andromaque-notice"),)
    assert request.play_preface_map == (("andromaque", ("mithridate-preface-fixture-tei-simplifiee",)),)
    assert request.play_dramatis_map == (("andromaque", "andromaque-dramatis"),)
    assert len(request.notices) == 4


@pytest.mark.parametrize(
    ("notice_name", "preface_name", "expected_notice_count", "expected_preface_count"),
    [
        ("andromaque-notice.xml", None, 1, 0),
        (None, "préface.xml", 0, 1),
        ("andromaque-notice.xml", "préface.xml", 1, 1),
        (None, None, 0, 0),
    ],
)
def test_site_publication_request_handles_notice_and_preface_independently(
    notice_name: str | None,
    preface_name: str | None,
    expected_notice_count: int,
    expected_preface_count: int,
) -> None:
    runtime = _runtime_dir("app_site_publication_config_notice_preface_matrix")
    notice_path = (
        (ROOT / "fixtures" / "site_builder" / "minimal" / "notices" / notice_name).resolve()
        if notice_name is not None
        else None
    )
    preface_path = (
        (ROOT / "fixtures" / "site_builder" / "unites_editoriales" / preface_name).resolve()
        if preface_name is not None
        else None
    )

    config = SitePublicationDialogConfig(
        author_name="Jean Racine",
        corpus_title="Théâtre complet",
        output_dir=(runtime / "site").resolve(),
        plays=(
            SitePublicationDialogPlayConfig(
                play_slug="andromaque",
                dramatic_xml_path=(ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic" / "andromaque.xml"),
                notice_xml_path=notice_path,
                preface_xml_path=preface_path,
                dramatis_xml_path=None,
            ),
        ),
    )

    request = site_publication_request_from_dialog_config(config)
    assert len(request.play_notice_map) == expected_notice_count
    assert len(request.play_preface_map) == expected_preface_count


def test_derive_corpus_slug_uses_author_and_two_title_words() -> None:
    assert derive_corpus_slug("Jean Racine", "Théâtre complet et fragments") == "jean-racine-theatre-complet"
