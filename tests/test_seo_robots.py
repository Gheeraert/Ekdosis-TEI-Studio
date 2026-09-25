from __future__ import annotations

from ets.seo import build_robots_txt, robots_txt_url_path


def test_build_robots_txt_returns_empty_without_base_url() -> None:
    assert build_robots_txt(None) == ""


def test_build_robots_txt_includes_sitemap_directive() -> None:
    robots_text = build_robots_txt("https://edition.example.org")

    assert "Sitemap: https://edition.example.org/sitemap.xml" in robots_text
    assert robots_text.startswith("User-agent: *\n")


def test_build_robots_txt_disallows_raw_export_directories_by_default() -> None:
    robots_text = build_robots_txt("https://edition.example.org")

    assert "Disallow: /xml/" in robots_text
    assert "Disallow: /txt/" in robots_text
    assert "Disallow: /downloads/" in robots_text
    assert "Disallow: /api/dts/" in robots_text
    assert "Disallow: /search/index.json" in robots_text


def test_build_robots_txt_honors_custom_disallowed_paths() -> None:
    robots_text = build_robots_txt("https://edition.example.org", disallowed_paths=["/private/"])

    assert "Disallow: /private/" in robots_text
    assert "Disallow: /xml/" not in robots_text


def test_robots_txt_url_path_is_empty_at_domain_root() -> None:
    assert robots_txt_url_path("https://edition.example.org") == ""


def test_robots_txt_url_path_reports_subdirectory() -> None:
    assert robots_txt_url_path("https://example.org/corpus") == "/corpus"


def test_build_robots_txt_prefixes_disallow_rules_under_a_subdirectory() -> None:
    robots_text = build_robots_txt("https://example.org/corpus")

    assert "Disallow: /corpus/xml/" in robots_text
    assert "Disallow: /corpus/api/dts/" in robots_text
    # unprefixed rules must not appear: they would target the wrong host path
    assert "Disallow: /xml/" not in robots_text
    assert "Sitemap: https://example.org/corpus/sitemap.xml" in robots_text
