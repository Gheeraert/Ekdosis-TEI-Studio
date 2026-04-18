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
    assert not any(item.kind == "play_page" for item in flat_nav)
    assert any(page.kind == "notice" for page in manifest.pages)
    assert {play.slug for play in manifest.plays} == {"andromaque", "berenice"}
    assert manifest.notices[0].slug == "andromaque-notice"
    assert manifest.notices[0].related_play_slug == "andromaque"
    assert manifest.play_navigation


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
    assert not any(child.kind == "play_page" for child in andromaque_branch.children)
    assert any(child.label == "Notice de pièce" for child in andromaque_branch.children)
    assert any(child.kind == "act" for child in andromaque_branch.children)
    assert any(scene.kind == "scene" for act in andromaque_branch.children for scene in act.children)


def test_manifest_navigation_includes_play_notice_acts_and_scenes() -> None:
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic"),
            "output_dir": str(ROOT / "tests" / "_runtime" / "site_builder_manifest_play_nav_consistency"),
            "publish_notices": False,
        }
    )

    manifest = build_site_manifest(config)
    assert manifest.play_navigation

    plays_group = next(item for item in manifest.navigation if item.kind == "plays_group")
    for play_structure in manifest.play_navigation:
        play_branch = next(item for item in plays_group.children if item.label == play_structure.play_title)
        assert not any(node.kind == "play_page" for node in play_branch.children)
        for act in play_structure.acts:
            act_node = next(node for node in play_branch.children if node.kind == "act" and node.label == act.label)
            assert act_node.href == f"plays/{play_structure.play_slug}.html#{act.anchor_id}"
            for scene in act.scenes:
                scene_node = next(
                    node
                    for node in act_node.children
                    if node.kind == "scene" and node.label == scene.label
                )
                assert scene_node.href == f"plays/{play_structure.play_slug}.html#{scene.anchor_id}"
