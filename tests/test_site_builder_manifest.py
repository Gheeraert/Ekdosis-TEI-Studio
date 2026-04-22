from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

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


def _runtime_dir(prefix: str) -> Path:
    target = ROOT / "tests" / "_runtime" / f"{prefix}_{uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


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
    assert any(item.kind == "piece_notice" for item in flat_nav)
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
    assert any(child.kind == "piece_notice" for child in andromaque_branch.children)
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


def test_manifest_maps_prefixed_notice_slug_under_play_branch() -> None:
    runtime_dir = ROOT / "tests" / "_runtime" / "site_builder_manifest_notice_prefix_mapping"
    dramatic_dir = runtime_dir / "dramatic"
    notice_dir = runtime_dir / "notices"
    dramatic_dir.mkdir(parents=True, exist_ok=True)
    notice_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic" / "andromaque.xml", dramatic_dir / "andromaque.xml")
    shutil.copy2(
        ROOT / "fixtures" / "site_builder" / "minimal" / "notices" / "andromaque-notice.xml",
        notice_dir / "notice-andromaque.xml",
    )

    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(dramatic_dir),
            "notice_xml_dir": str(notice_dir),
            "output_dir": str(runtime_dir / "out"),
            "publish_notices": True,
        }
    )

    manifest = build_site_manifest(config)

    plays_group = next(item for item in manifest.navigation if item.kind == "plays_group")
    andromaque_branch = next(item for item in plays_group.children if item.label == "Andromaque")
    assert andromaque_branch.children
    assert andromaque_branch.children[0].kind == "piece_notice"
    assert andromaque_branch.children[0].href == "notices/andromaque-notice.html"
    assert not any(item.kind == "notices_group" for item in manifest.navigation)


def test_manifest_play_navigation_respects_editorial_front_matter_order_for_unites_editoriales() -> None:
    runtime = _runtime_dir("site_builder_manifest_unites_editoriales")
    dramatic_dir = runtime / "dramatic"
    notice_dir = runtime / "notices"
    dramatic_dir.mkdir(parents=True, exist_ok=True)
    notice_dir.mkdir(parents=True, exist_ok=True)

    fixtures_dir = ROOT / "fixtures" / "site_builder" / "unites_editoriales"
    shutil.copy2(fixtures_dir / "piece.xml", dramatic_dir / "piece.xml")
    shutil.copy2(fixtures_dir / "notice.xml", notice_dir / "notice.xml")
    preface_source = next(fixtures_dir.glob("pr*face.xml"))
    shutil.copy2(preface_source, notice_dir / "preface.xml")

    play_slug = "la-thebaide-ou-les-freres-ennemis"
    notice_slug = "alexandre-le-grand-notice-extrait-de-fixture"
    preface_slug = "mithridate-preface-fixture-tei-simplifiee"

    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(dramatic_dir),
            "notice_xml_dir": str(notice_dir),
            "output_dir": str(runtime / "out"),
            "publish_notices": True,
            "play_notice_map": {play_slug: notice_slug},
            "play_preface_map": {play_slug: [preface_slug]},
        }
    )

    manifest = build_site_manifest(config)

    assert len(manifest.plays) == 1
    assert len(manifest.notices) == 2
    assert any(entry.slug == preface_slug and entry.editorial_role == "author_preface" for entry in manifest.notices)

    play_structure = next(item for item in manifest.play_navigation if item.play_slug == play_slug)
    assert play_structure.front_items
    assert [item.kind for item in play_structure.front_items[:3]] == [
        "piece_notice",
        "author_preface",
        "dramatis_personae",
    ]
    assert play_structure.front_items[0].href == f"notices/{notice_slug}.html"
    assert play_structure.front_items[1].href == f"notices/{preface_slug}.html"
    assert play_structure.front_items[2].anchor_id
    assert play_structure.front_items[2].href == (
        f"plays/{play_slug}.html#{play_structure.front_items[2].anchor_id}"
    )
    assert play_structure.dramatis_personae

    plays_group = next(item for item in manifest.navigation if item.kind == "plays_group")
    play_branch = next(item for item in plays_group.children if item.label == play_structure.play_title)

    # Canonical order: notice -> preface -> dramatis -> acts -> scenes
    assert [child.kind for child in play_branch.children[:3]] == [
        "piece_notice",
        "author_preface",
        "dramatis_personae",
    ]
    assert play_branch.children[3].kind == "act"
    assert play_branch.children[3].children
    assert play_branch.children[3].children[0].kind == "scene"

    flat_nav = _flatten_navigation(manifest.navigation)
    preface_nodes = [
        item
        for item in flat_nav
        if item.href == f"notices/{preface_slug}.html"
    ]
    assert len(preface_nodes) == 1
    assert preface_nodes[0].kind == "author_preface"


def test_manifest_can_publish_preface_without_piece_notice() -> None:
    runtime = _runtime_dir("site_builder_manifest_preface_only")
    dramatic_dir = runtime / "dramatic"
    notice_dir = runtime / "notices"
    dramatic_dir.mkdir(parents=True, exist_ok=True)
    notice_dir.mkdir(parents=True, exist_ok=True)

    fixtures_dir = ROOT / "fixtures" / "site_builder" / "unites_editoriales"
    shutil.copy2(fixtures_dir / "piece.xml", dramatic_dir / "piece.xml")
    preface_source = next(fixtures_dir.glob("pr*face.xml"))
    shutil.copy2(preface_source, notice_dir / "preface.xml")

    play_slug = "la-thebaide-ou-les-freres-ennemis"
    preface_slug = "mithridate-preface-fixture-tei-simplifiee"

    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(dramatic_dir),
            "notice_xml_dir": str(notice_dir),
            "output_dir": str(runtime / "out"),
            "publish_notices": False,
            "publish_prefaces": True,
            "play_preface_map": {play_slug: [preface_slug]},
        }
    )

    manifest = build_site_manifest(config)
    assert all(entry.editorial_role == "author_preface" for entry in manifest.notices)
    play_structure = next(item for item in manifest.play_navigation if item.play_slug == play_slug)
    assert [item.kind for item in play_structure.front_items[:2]] == ["author_preface", "dramatis_personae"]


def test_manifest_uses_external_dramatis_source_in_priority() -> None:
    runtime = _runtime_dir("site_builder_manifest_external_dramatis")
    dramatic_dir = runtime / "dramatic"
    notice_dir = runtime / "notices"
    dramatis_dir = runtime / "dramatis"
    dramatic_dir.mkdir(parents=True, exist_ok=True)
    notice_dir.mkdir(parents=True, exist_ok=True)
    dramatis_dir.mkdir(parents=True, exist_ok=True)

    fixtures_dir = ROOT / "fixtures" / "site_builder" / "unites_editoriales"
    shutil.copy2(fixtures_dir / "piece.xml", dramatic_dir / "piece.xml")
    shutil.copy2(fixtures_dir / "notice.xml", notice_dir / "notice.xml")
    preface_source = next(fixtures_dir.glob("pr*face.xml"))
    shutil.copy2(preface_source, notice_dir / "preface.xml")

    external_dramatis = dramatis_dir / "dramatis-externe.xml"
    external_dramatis.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <front>
      <castList>
        <castItem>Personnage externe Alpha</castItem>
        <castItem>Personnage externe Beta</castItem>
      </castList>
    </front>
  </text>
</TEI>
""",
        encoding="utf-8",
    )

    play_slug = "la-thebaide-ou-les-freres-ennemis"
    notice_slug = "alexandre-le-grand-notice-extrait-de-fixture"
    preface_slug = "mithridate-preface-fixture-tei-simplifiee"

    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(dramatic_dir),
            "notice_xml_dir": str(notice_dir),
            "dramatis_xml_dir": str(dramatis_dir),
            "output_dir": str(runtime / "out"),
            "publish_notices": True,
            "publish_prefaces": True,
            "play_notice_map": {play_slug: notice_slug},
            "play_preface_map": {play_slug: [preface_slug]},
            "play_dramatis_map": {play_slug: "dramatis-externe"},
        }
    )

    manifest = build_site_manifest(config)
    play_structure = next(item for item in manifest.play_navigation if item.play_slug == play_slug)
    assert play_structure.dramatis_personae == ("Personnage externe Alpha", "Personnage externe Beta")


def test_manifest_keeps_home_notice_for_inline_render_but_excludes_it_from_pages_and_nav() -> None:
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic"),
            "notice_xml_dir": str(ROOT / "fixtures" / "metopes" / "minimal"),
            "output_dir": str(ROOT / "tests" / "_runtime" / "site_builder_manifest_home_notice_inline"),
            "publish_notices": True,
            "general_notice_slug": "bibliographie",
            "home_page_notice_slug": "introduction",
        }
    )

    manifest = build_site_manifest(config)
    flat_nav = _flatten_navigation(manifest.navigation)

    assert any(notice.slug == "introduction" for notice in manifest.notices)
    assert not any(page.source_slug == "introduction" for page in manifest.pages)
    assert not any(item.href == "notices/introduction.html" for item in flat_nav)
    assert any(page.source_slug == "bibliographie" for page in manifest.pages)

