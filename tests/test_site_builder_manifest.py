from __future__ import annotations

from pathlib import Path

from ets.site_builder.config import site_config_from_dict
from ets.site_builder.manifest import build_site_manifest


ROOT = Path(__file__).resolve().parents[1]


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
    assert any(item.kind == "play" for item in manifest.navigation)
    assert any(item.kind == "notice" for item in manifest.navigation)
    assert any(page.kind == "notice" for page in manifest.pages)
    assert {play.slug for play in manifest.plays} == {"andromaque", "berenice"}
    assert manifest.notices[0].slug == "andromaque-notice"
    assert manifest.notices[0].related_play_slug == "andromaque"
