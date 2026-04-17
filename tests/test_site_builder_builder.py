from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from lxml import html as lxml_html

from ets.site_builder.builder import build_static_site
from ets.site_builder.config import site_config_from_dict


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "fixtures" / "site_builder" / "minimal"
METOPES_MINIMAL = ROOT / "fixtures" / "metopes" / "minimal"
RUNTIME_ROOT = ROOT / "tests" / "_runtime"


def _runtime_dir(prefix: str) -> Path:
    target = RUNTIME_ROOT / f"{prefix}_{uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_builder_generates_index_and_secondary_pages() -> None:
    base_dir = _runtime_dir("site_builder")
    output_dir = base_dir / "site_with_notice"
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "site_subtitle": "Publication test",
            "dramatic_xml_dir": str(FIXTURE_ROOT / "dramatic"),
            "notice_xml_dir": str(FIXTURE_ROOT / "notices"),
            "output_dir": str(output_dir),
            "show_xml_download": True,
            "publish_notices": True,
            "include_metadata": True,
            "project_name": "ETS Site Builder",
        }
    )

    result = build_static_site(config)

    assert result.play_count == 2
    assert result.notice_count == 1
    assert (output_dir / "index.html").exists()
    assert (output_dir / "plays" / "andromaque.html").exists()
    assert (output_dir / "plays" / "berenice.html").exists()
    assert (output_dir / "notices" / "andromaque-notice.html").exists()
    assert (output_dir / "xml" / "dramatic" / "andromaque.xml").exists()
    assert (output_dir / "xml" / "dramatic" / "berenice.xml").exists()
    assert len(result.generated_pages) >= 4


def test_builder_generates_cross_links_and_home_intro_from_explicit_mapping() -> None:
    base_dir = _runtime_dir("site_builder_links")
    output_dir = base_dir / "site_links"
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "site_subtitle": "Publication test",
            "dramatic_xml_dir": str(FIXTURE_ROOT / "dramatic"),
            "notice_xml_dir": str(FIXTURE_ROOT / "notices"),
            "output_dir": str(output_dir),
            "publish_notices": True,
            "homepage_intro": "Bienvenue sur l'edition de demonstration.",
            "play_notice_map": {"andromaque": "andromaque-notice"},
        }
    )

    result = build_static_site(config)

    assert result.play_count == 2
    assert result.notice_count == 1
    home_html = (output_dir / "index.html").read_text(encoding="utf-8")
    play_html = (output_dir / "plays" / "andromaque.html").read_text(encoding="utf-8")
    notice_html = (output_dir / "notices" / "andromaque-notice.html").read_text(encoding="utf-8")

    assert "Bienvenue sur l&#x27;edition de demonstration." in home_html
    assert 'class="home-overview"' in home_html
    assert "../notices/andromaque-notice.html" in play_html
    assert "../plays/andromaque.html" in notice_html
    assert "Pour qui sont ces serpents" in play_html
    assert 'class="play-structure-nav"' in play_html

    doc = lxml_html.document_fromstring(play_html)
    assert len(doc.xpath("//main/nav")) == 1
    assert doc.xpath("//main/nav//div[contains(@class, 'play-structure-nav')]")
    assert not doc.xpath("//section//aside[contains(@class, 'play-structure-nav')]")
    assert doc.xpath("//section[@id='contenu-editorial' and contains(@class, 'dramatic-content')]")
    assert doc.xpath("//main/nav//details[contains(@class, 'nav-details')]")
    assert doc.xpath("//main/nav//ul[contains(@class, 'site-nav') and contains(@class, 'nested')]")
    assert "IM Fell DW Pica" in play_html
    assert ".vers-container" in play_html
    assert "#container {" not in play_html

    nav_targets = doc.xpath("//main/nav//div[contains(@class, 'play-structure-nav')]//a/@href")
    assert nav_targets
    for href in nav_targets:
        assert href.startswith("#")
        anchor_id = href[1:]
        assert doc.xpath(f"//*[@id='{anchor_id}']")


def test_builder_copies_branding_assets_and_references_logos() -> None:
    base_dir = _runtime_dir("site_builder_assets")
    output_dir = base_dir / "site_assets"
    logo_file = base_dir / "logo-ets.txt"
    logo_file.write_text("LOGO", encoding="utf-8")
    asset_dir = base_dir / "brand"
    asset_dir.mkdir(parents=True, exist_ok=True)
    (asset_dir / "palette.txt").write_text("bleu", encoding="utf-8")

    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(FIXTURE_ROOT / "dramatic"),
            "notice_xml_dir": str(FIXTURE_ROOT / "notices"),
            "output_dir": str(output_dir),
            "publish_notices": True,
            "assets": {
                "logos": [str(logo_file)],
                "directories": [str(asset_dir)],
            },
        }
    )

    result = build_static_site(config)

    assert (output_dir / "assets" / "logos" / "logo-ets.txt").exists()
    assert (output_dir / "assets" / "brand" / "palette.txt").exists()
    assert any(path.name == "logo-ets.txt" for path in result.copied_assets)

    home_html = (output_dir / "index.html").read_text(encoding="utf-8")
    play_html = (output_dir / "plays" / "andromaque.html").read_text(encoding="utf-8")
    assert 'src="assets/logos/logo-ets.txt"' in home_html
    assert 'src="../assets/logos/logo-ets.txt"' in play_html


def test_builder_warns_on_invalid_mapping_without_failing() -> None:
    base_dir = _runtime_dir("site_builder_invalid_mapping")
    output_dir = base_dir / "site_invalid_mapping"
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(FIXTURE_ROOT / "dramatic"),
            "notice_xml_dir": str(FIXTURE_ROOT / "notices"),
            "output_dir": str(output_dir),
            "publish_notices": True,
            "play_notice_map": {
                "unknown-play": "andromaque-notice",
                "andromaque": "unknown-notice",
            },
        }
    )

    result = build_static_site(config)

    assert (output_dir / "index.html").exists()
    assert result.play_count == 2
    assert any("unknown play slug" in warning for warning in result.warnings)
    assert any("notice slug not found" in warning for warning in result.warnings)


def test_builder_handles_missing_notice_directory_without_failure() -> None:
    base_dir = _runtime_dir("site_builder")
    dramatic_dir = base_dir / "dramatic_only"
    dramatic_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FIXTURE_ROOT / "dramatic" / "andromaque.xml", dramatic_dir / "andromaque.xml")

    output_dir = base_dir / "site_without_notice"
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(dramatic_dir),
            "notice_xml_dir": str(base_dir / "missing_notices"),
            "output_dir": str(output_dir),
            "show_xml_download": False,
            "publish_notices": True,
        }
    )

    result = build_static_site(config)

    assert result.play_count == 1
    assert result.notice_count == 0
    assert (output_dir / "index.html").exists()
    assert (output_dir / "plays" / "andromaque.html").exists()


def test_builder_cleans_output_directory_before_regeneration() -> None:
    base_dir = _runtime_dir("site_builder")
    output_dir = base_dir / "site_cleaned"
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(FIXTURE_ROOT / "dramatic"),
            "notice_xml_dir": str(FIXTURE_ROOT / "notices"),
            "output_dir": str(output_dir),
            "publish_notices": True,
        }
    )

    first_result = build_static_site(config)
    stale_file = output_dir / "obsolete.txt"
    stale_file.write_text("stale", encoding="utf-8")

    second_result = build_static_site(config)

    assert first_result.play_count == second_result.play_count == 2
    assert not stale_file.exists()


def test_builder_output_paths_are_deterministic() -> None:
    base_dir = _runtime_dir("site_builder_paths")
    output_dir = base_dir / "site_paths"
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(FIXTURE_ROOT / "dramatic"),
            "notice_xml_dir": str(FIXTURE_ROOT / "notices"),
            "output_dir": str(output_dir),
            "publish_notices": True,
        }
    )

    result = build_static_site(config)
    relpaths = {path.relative_to(output_dir).as_posix() for path in result.generated_pages}

    assert relpaths == {
        "index.html",
        "plays/andromaque.html",
        "plays/berenice.html",
        "notices/andromaque-notice.html",
    }


def test_builder_supports_general_notice_home_editorial_sections_and_hierarchical_navigation() -> None:
    base_dir = _runtime_dir("site_builder_general_notice")
    output_dir = base_dir / "site_general_notice"
    config = site_config_from_dict(
        {
            "site_title": "ETS Editorial Demo",
            "site_subtitle": "Structure editoriale",
            "dramatic_xml_dir": str(FIXTURE_ROOT / "dramatic"),
            "notice_xml_dir": str(METOPES_MINIMAL),
            "output_dir": str(output_dir),
            "publish_notices": True,
            "play_notice_map": {"andromaque": "introduction"},
            "general_notice_slug": "bibliographie",
            "homepage_sections": [
                {
                    "title": "Presentation du projet",
                    "paragraphs": [
                        "Edition numerique en cours de publication.",
                        "Corpus dramatique annote et collatable.",
                    ],
                },
                {
                    "title": "Cadre institutionnel",
                    "paragraphs": ["Soutien scientifique et institutionnel explicite."],
                },
            ],
        }
    )

    result = build_static_site(config)

    assert (output_dir / "notices" / "bibliographie.html").exists()
    assert (output_dir / "notices" / "introduction.html").exists()
    home_html = (output_dir / "index.html").read_text(encoding="utf-8")
    play_html = (output_dir / "plays" / "andromaque.html").read_text(encoding="utf-8")

    assert "Presentation du projet" in home_html
    assert "Cadre institutionnel" in home_html
    assert "Notice generale" in home_html
    assert 'href="notices/bibliographie.html"' in home_html
    assert result.notice_count >= 2

    doc = lxml_html.document_fromstring(play_html)
    assert doc.xpath("//main/nav//a[@href='../notices/bibliographie.html']")
    assert doc.xpath("//main/nav//span[contains(@class, 'nav-label') and contains(., 'Pieces')]")
    assert doc.xpath("//main/nav//a[contains(., 'Lecture')]")
    assert doc.xpath("//main/nav//a[contains(., 'Notice de piece')]")
    assert doc.xpath("//main/nav//a[contains(., 'Acte 1')]")
    assert doc.xpath("//main/nav//a[contains(., 'Scene 1')]")


def test_play_page_keeps_xml_download_and_embeds_transformed_text() -> None:
    base_dir = _runtime_dir("site_builder_play_reading")
    output_dir = base_dir / "site_play_reading"
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(FIXTURE_ROOT / "dramatic"),
            "notice_xml_dir": str(FIXTURE_ROOT / "notices"),
            "output_dir": str(output_dir),
            "show_xml_download": True,
            "publish_notices": True,
            "play_notice_map": {"andromaque": "andromaque-notice"},
        }
    )

    build_static_site(config)
    play_html = (output_dir / "plays" / "andromaque.html").read_text(encoding="utf-8")
    doc = lxml_html.document_fromstring(play_html)

    assert doc.xpath("//a[@href='../xml/dramatic/andromaque.xml' and @download]")
    assert doc.xpath("//a[@href='../notices/andromaque-notice.html']")
    assert doc.xpath("//main/nav//div[contains(@class, 'play-structure-nav')]")
    assert doc.xpath("//section[@id='contenu-editorial' and contains(@class, 'dramatic-content')]")
    assert "IM Fell DW Pica" in play_html
    assert doc.xpath("//*[contains(@class, 'locuteur')]")
    assert doc.xpath("//*[contains(@class, 'vers-container')]")
    assert not doc.xpath("//*[contains(@class, 'play-reading-layout')]")
    assert not doc.xpath("//*[contains(., 'Divisions reperees')]")
