from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from ets.application import (
    SitePublicationDialogConfig,
    SitePublicationDialogPlayConfig,
    load_site_publication_dialog_config,
    save_site_publication_dialog_config,
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
        site_title="ETS publication",
        site_subtitle="Corpus",
        project_name="ETS",
        editor="Equipe",
        credits="Credits",
        homepage_intro="Intro",
        output_dir=(runtime / "site").resolve(),
        plays=(
            SitePublicationDialogPlayConfig(
                play_slug="andromaque",
                document_paths=((runtime / "andromaque_A1.xml").resolve(), (runtime / "andromaque_A2.xml").resolve()),
            ),
            SitePublicationDialogPlayConfig(
                play_slug="berenice",
                document_paths=((runtime / "berenice_A1.xml").resolve(),),
            ),
        ),
        play_order=("berenice", "andromaque"),
        master_notice=(runtime / "master_notice.xml").resolve(),
        additional_notices=((runtime / "notice_intro.xml").resolve(),),
        logo_paths=((runtime / "logo.png").resolve(),),
        asset_directories=((runtime / "assets").resolve(),),
        play_notice_map=(("andromaque", "master-notice"),),
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
    assert payload["version"] == 1
    assert payload["plays"][0]["play_slug"] == "andromaque"


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
                "version": 1,
                "identity": {"site_title": "ETS"},
                "plays": "not-a-list",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="plays"):
        load_site_publication_dialog_config(config_path)
