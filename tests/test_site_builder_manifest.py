from __future__ import annotations

from pathlib import Path

from ets.site_builder.config import site_config_from_dict
from ets.site_builder.manifest import build_site_manifest
from ets.site_builder.models import NavigationItem


ROOT = Path(__file__).resolve().parents[1]


def _flatten_navigation(items: tuple[NavigationItem, ...]) -> tuple[NavigationItem, ...]:
    flattened: list[NavigationItem] = []
    for item in items:
        flattened.append(item)
        if item.children:
            flattened.extend(_flatten_navigation(item.children))
    return tuple(flattened)


def test_manifest_builds_navigation_and_notice_entries() -> None:
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "site_subtitle": "Publication test",
            "dramatic_xml_dir": str(ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic"),
            "notice_xml_dir": str(ROOT / "fixtures" / "site_builder" / "minimal" / "notices"),
            "output_dir": str(ROOT / "tests" / "_runtime" / "site_builder_manifest"),
            "show_xml_download": True,
            "publish_notices": True,
            "include_metadata": True,
            "project_name": "ETS Site Builder",
            "editor": "Equipe ETS",
            "credits": "Fixture tests",
        }
    )

    manifest = build_site_manifest(config)

    assert len(manifest.plays) == 2
    assert len(manifest.notices) == 1
    assert manifest.navigation
    flat_nav = _flatten_navigation(manifest.navigation)
    assert any(item.kind == "plays_group" for item in flat_nav)
    assert any(item.kind == "play_group" for item in flat_nav)
    assert any(item.kind == "notice" for item in flat_nav)
    assert any(item.kind == "act" for item in flat_nav)
    assert any(item.kind == "scene" for item in flat_nav)
    assert any(page.kind == "notice" for page in manifest.pages)
    assert {play.slug for play in manifest.plays} == {"andromaque", "berenice"}
    assert manifest.notices[0].slug == "andromaque-notice"
    assert manifest.notices[0].related_play_slug == "andromaque"


def test_manifest_reports_invalid_explicit_mapping_entries() -> None:
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "site_subtitle": "Publication test",
            "dramatic_xml_dir": str(ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic"),
            "notice_xml_dir": str(ROOT / "fixtures" / "site_builder" / "minimal" / "notices"),
            "output_dir": str(ROOT / "tests" / "_runtime" / "site_builder_manifest_invalid_map"),
            "publish_notices": True,
            "play_notice_map": {
                "missing-play": "andromaque-notice",
                "andromaque": "missing-notice",
            },
        }
    )

    manifest = build_site_manifest(config)

    assert any("unknown play slug" in warning for warning in manifest.warnings)
    assert any("notice slug not found" in warning for warning in manifest.warnings)


def test_manifest_supports_optional_general_notice_and_hierarchical_navigation() -> None:
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "site_subtitle": "Publication test",
            "dramatic_xml_dir": str(ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic"),
            "notice_xml_dir": str(ROOT / "fixtures" / "metopes" / "minimal"),
            "output_dir": str(ROOT / "tests" / "_runtime" / "site_builder_manifest_general_notice"),
            "publish_notices": True,
            "play_notice_map": {"andromaque": "introduction"},
            "general_notice_slug": "bibliographie",
        }
    )

    manifest = build_site_manifest(config)
    flat_nav = _flatten_navigation(manifest.navigation)

    assert manifest.general_notice_slug == "bibliographie"
    assert any(page.kind == "notice_general" and page.source_slug == "bibliographie" for page in manifest.pages)
    assert any(item.kind == "notice_general" for item in flat_nav)

    plays_group = next(item for item in manifest.navigation if item.kind == "plays_group")
    andromaque_branch = next(item for item in plays_group.children if item.label == "Andromaque")
    assert any(child.kind == "play_page" for child in andromaque_branch.children)
    assert any(child.label == "Notice de piece" for child in andromaque_branch.children)
    assert any(child.kind == "act" for child in andromaque_branch.children)
