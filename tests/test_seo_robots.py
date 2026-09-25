from __future__ import annotations

from ets.seo import build_robots_txt


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
