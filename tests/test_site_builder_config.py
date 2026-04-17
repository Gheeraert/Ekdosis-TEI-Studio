from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from ets.site_builder.config import load_site_config, site_config_from_dict
from ets.site_builder.manifest import build_site_manifest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = ROOT / "tests" / "_runtime"


def _runtime_dir(prefix: str) -> Path:
    target = RUNTIME_ROOT / f"{prefix}_{uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_site_config_from_dict_normalizes_paths_and_defaults() -> None:
    base = _runtime_dir("site_builder_config")
    config = site_config_from_dict(
        {
            "site_title": "ETS Config Demo",
            "dramatic_xml_dir": "fixtures/site_builder/minimal/dramatic",
            "output_dir": "out/site",
        },
        base_dir=ROOT,
    )

    assert config.site_title == "ETS Config Demo"
    assert config.site_subtitle == ""
    assert config.dramatic_xml_dir == (ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic").resolve()
    assert config.notice_xml_dir is None
    assert config.output_dir == (ROOT / "out" / "site").resolve()
    assert config.assets.logo_files == ()
    assert config.assets.asset_directories == ()
    assert config.play_notice_map == ()
    assert config.homepage_intro == ""
    assert config.homepage_sections == ()
    assert config.general_notice_slug == ""


def test_site_config_loads_from_json_and_resolves_relative_paths() -> None:
    base = _runtime_dir("site_builder_config_json")
    config_path = base / "publication.json"
    payload = {
        "site_title": "ETS Config JSON",
        "site_subtitle": "Edition test",
        "dramatic_xml_dir": "../../../fixtures/site_builder/minimal/dramatic",
        "notice_xml_dir": "../../../fixtures/metopes/minimal",
        "output_dir": "site_output",
        "assets": {
            "logos": ["../../../fixtures/site_builder/minimal/dramatic/andromaque.xml"],
            "directories": ["../../../fixtures/metopes/minimal"],
        },
        "homepage_intro": "Corpus de démonstration.",
    }
    config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    config = load_site_config(config_path)

    assert config.site_title == "ETS Config JSON"
    assert config.notice_xml_dir == (ROOT / "fixtures" / "metopes" / "minimal").resolve()
    assert config.output_dir == (base / "site_output").resolve()
    assert config.assets.logo_files
    assert config.assets.logo_files[0].name == "andromaque.xml"
    assert config.homepage_intro == "Corpus de démonstration."


def test_site_config_supports_explicit_play_notice_mapping() -> None:
    config = site_config_from_dict(
        {
            "site_title": "ETS Config Mapping",
            "dramatic_xml_dir": str(ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic"),
            "notice_xml_dir": str(ROOT / "fixtures" / "site_builder" / "minimal" / "notices"),
            "output_dir": str(ROOT / "tests" / "_runtime" / "site_builder_config_mapping"),
            "play_notice_map": {
                "Andromaque": "andromaque-notice",
            },
        }
    )
    manifest = build_site_manifest(config)

    assert config.play_notice_map == (("andromaque", "andromaque-notice"),)
    assert manifest.notices
    assert manifest.notices[0].related_play_slug == "andromaque"


def test_site_config_supports_general_notice_and_homepage_sections() -> None:
    config = site_config_from_dict(
        {
            "site_title": "ETS Editorial",
            "dramatic_xml_dir": str(ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic"),
            "notice_xml_dir": str(ROOT / "fixtures" / "metopes" / "minimal"),
            "output_dir": str(ROOT / "tests" / "_runtime" / "site_builder_config_editorial"),
            "general_notice_slug": "Bibliographie",
            "homepage_sections": [
                {
                    "title": "Cadre scientifique",
                    "paragraphs": [
                        "Edition produite dans un cadre collectif.",
                        "Validation continue par l'equipe editoriale.",
                    ],
                }
            ],
        }
    )

    assert config.general_notice_slug == "bibliographie"
    assert len(config.homepage_sections) == 1
    assert config.homepage_sections[0].title == "Cadre scientifique"
    assert config.homepage_sections[0].paragraphs == (
        "Edition produite dans un cadre collectif.",
        "Validation continue par l'equipe editoriale.",
    )


def test_site_config_invalid_required_fields_fail_cleanly() -> None:
    with pytest.raises(ValueError, match="site_title"):
        site_config_from_dict(
            {
                "site_title": "   ",
                "dramatic_xml_dir": ".",
                "output_dir": "out/site",
            }
        )

    with pytest.raises(ValueError, match="dramatic_xml_dir"):
        site_config_from_dict(
            {
                "site_title": "ETS",
                "dramatic_xml_dir": "   ",
                "output_dir": "out/site",
            }
        )


def test_site_config_invalid_play_notice_map_fails_cleanly() -> None:
    with pytest.raises(ValueError, match="play_notice_map"):
        site_config_from_dict(
            {
                "site_title": "ETS",
                "dramatic_xml_dir": ".",
                "output_dir": "out/site",
                "play_notice_map": ["not-a-dict"],
            }
        )


def test_site_config_invalid_homepage_sections_fail_cleanly() -> None:
    with pytest.raises(ValueError, match="homepage_sections"):
        site_config_from_dict(
            {
                "site_title": "ETS",
                "dramatic_xml_dir": ".",
                "output_dir": "out/site",
                "homepage_sections": {"title": "not-a-list"},
            }
        )
