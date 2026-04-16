from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from ets.application import (
    SiteBuildRequest,
    SiteBuilderService,
    build_site_from_config_dict,
    build_site_from_config_file,
)


ROOT = Path(__file__).resolve().parents[1]
DRAMATIC_FIXTURES = ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic"
MINIMAL_NOTICES = ROOT / "fixtures" / "site_builder" / "minimal" / "notices"
REALISTIC_NOTICES = ROOT / "fixtures" / "metopes" / "realistic"
RUNTIME_ROOT = ROOT / "tests" / "_runtime"


def _runtime_dir(prefix: str) -> Path:
    target = RUNTIME_ROOT / f"{prefix}_{uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_site_builder_service_build_from_config_dict_success() -> None:
    base = _runtime_dir("app_site_builder_service_dict")
    output_dir = base / "site"

    result = build_site_from_config_dict(
        {
            "site_title": "ETS Service Build",
            "dramatic_xml_dir": str(DRAMATIC_FIXTURES),
            "notice_xml_dir": str(REALISTIC_NOTICES),
            "output_dir": str(output_dir),
            "publish_notices": True,
            "show_xml_download": True,
            "play_notice_map": {"andromaque": "introduction"},
        }
    )

    assert result.ok is True
    assert result.output_dir == output_dir.resolve()
    assert result.play_count == 2
    assert result.notice_count == 2
    assert "index.html" in result.generated_page_relpaths
    assert "plays/andromaque.html" in result.generated_page_relpaths
    assert "notices/introduction.html" in result.generated_page_relpaths
    assert (output_dir / "xml" / "notices" / "introduction.xml").exists()


def test_site_builder_service_build_from_config_file_success_and_deterministic_paths() -> None:
    base = _runtime_dir("app_site_builder_service_file")
    output_dir = base / "site"
    config_path = base / "site_config.json"
    config_path.write_text(
        json.dumps(
            {
                "site_title": "ETS Service File Build",
                "dramatic_xml_dir": str(DRAMATIC_FIXTURES),
                "notice_xml_dir": str(MINIMAL_NOTICES),
                "output_dir": str(output_dir),
                "publish_notices": True,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    result = build_site_from_config_file(config_path)

    assert result.ok is True
    assert result.generated_page_relpaths == (
        "index.html",
        "plays/andromaque.html",
        "plays/berenice.html",
        "notices/andromaque-notice.html",
    )


def test_site_builder_service_propagates_non_blocking_warnings() -> None:
    base = _runtime_dir("app_site_builder_service_warn")
    output_dir = base / "site"
    service = SiteBuilderService()

    result = service.build(
        SiteBuildRequest(
            source={
                "site_title": "ETS Service Warning Build",
                "dramatic_xml_dir": str(DRAMATIC_FIXTURES),
                "notice_xml_dir": str(MINIMAL_NOTICES),
                "output_dir": str(output_dir),
                "publish_notices": True,
                "play_notice_map": {"unknown-play": "andromaque-notice"},
            }
        )
    )

    assert result.ok is True
    assert any("unknown play slug" in warning for warning in result.warnings)
    assert (output_dir / "index.html").exists()


def test_site_builder_service_fails_cleanly_on_invalid_config() -> None:
    result = build_site_from_config_dict(
        {
            "site_title": "   ",
            "dramatic_xml_dir": str(DRAMATIC_FIXTURES),
            "output_dir": str(ROOT / "tests" / "_runtime" / "unused"),
        }
    )

    assert result.ok is False
    assert result.error_code == "E_SITE_CONFIG"
    assert result.error_detail is not None
    assert "site_title" in result.error_detail

