from __future__ import annotations

from pathlib import Path

from ets.site_builder.config import site_config_from_dict
from ets.site_builder.manifest import build_site_manifest


ROOT = Path(__file__).resolve().parents[1]


def test_manifest_distinguishes_metopes_volume_and_standalone_notice() -> None:
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic"),
            "notice_xml_dir": str(ROOT / "fixtures" / "metopes" / "minimal"),
            "output_dir": str(ROOT / "tests" / "_runtime" / "site_builder_metopes_manifest"),
            "publish_notices": True,
            "resolve_notice_xincludes": True,
        }
    )

    manifest = build_site_manifest(config)

    kinds = {notice.notice_kind for notice in manifest.notices}
    nav_kinds = {item.kind for item in manifest.navigation if item.kind.startswith("notice")}
    page_kinds = {page.kind for page in manifest.pages if page.kind.startswith("notice")}

    assert "standalone" in kinds
    assert "master_volume" in kinds
    assert "notice" in nav_kinds
    assert "notice_volume" in nav_kinds
    assert "notice" in page_kinds
    assert "notice_volume" in page_kinds
