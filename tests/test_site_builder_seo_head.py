from __future__ import annotations

from pathlib import Path

from lxml import html as lxml_html

from ets.site_builder.config import site_config_from_dict
from ets.site_builder.extractors import extract_play_entry, extract_notice_entry
from ets.site_builder.models import SiteManifest
from ets.site_builder.render import render_home_page, render_notice_page, render_play_page, render_search_page

ROOT = Path(__file__).resolve().parents[1]
DRAMATIC_DIR = ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic"
NOTICE_DIR = ROOT / "fixtures" / "metopes" / "minimal"


def _config(*, site_base_url: str | None = None, **overrides: object) -> object:
    payload = {
        "site_title": "ETS Demo",
        "dramatic_xml_dir": str(DRAMATIC_DIR),
        "output_dir": str(ROOT / "tests" / "_runtime" / "site_builder_seo_head"),
        **overrides,
    }
    if site_base_url is not None:
        payload["site_base_url"] = site_base_url
    return site_config_from_dict(payload)


def _play():
    xml_path = sorted(DRAMATIC_DIR.glob("*.xml"))[0]
    return extract_play_entry(xml_path)


def test_pages_have_no_canonical_link_without_site_base_url() -> None:
    config = _config()
    manifest = SiteManifest(config=config)

    html_page = render_home_page(manifest)

    assert "<link rel=\"canonical\"" not in html_page
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in html_page


def test_home_page_uses_homepage_intro_as_description() -> None:
    config = _config(homepage_intro="Corpus critique du théâtre classique français.")
    manifest = SiteManifest(config=config)

    html_page = render_home_page(manifest)

    assert (
        '<meta name="description" content="Corpus critique du théâtre classique français.">'
        in html_page
    )


def test_home_page_falls_back_to_generic_description() -> None:
    config = _config()
    manifest = SiteManifest(config=config)

    html_page = render_home_page(manifest)

    assert '<meta name="description" content="ETS Demo — édition critique numérique.">' in html_page


def test_canonical_link_uses_site_base_url_and_relpath() -> None:
    config = _config(site_base_url="https://edition.example.org/andromaque/")
    manifest = SiteManifest(config=config)

    html_page = render_home_page(manifest)

    assert (
        '<link rel="canonical" href="https://edition.example.org/andromaque/index.html">'
        in html_page
    )


def test_play_page_description_includes_title_and_author() -> None:
    config = _config()
    play = _play()
    manifest = SiteManifest(config=config, plays=(play,))

    html_page = render_play_page(manifest, play)

    if play.author:
        expected = f"{play.title}, {play.author} — édition critique numérique, ETS Demo."
    else:
        expected = f"{play.title} — édition critique numérique, ETS Demo."
    assert f'<meta name="description" content="{expected}">' in html_page


def test_play_page_canonical_uses_play_relpath() -> None:
    config = _config(site_base_url="https://edition.example.org")
    play = _play()
    manifest = SiteManifest(config=config, plays=(play,))

    html_page = render_play_page(manifest, play)

    assert (
        f'<link rel="canonical" href="https://edition.example.org/plays/{play.slug}.html">'
        in html_page
    )


def test_notice_page_description_and_canonical() -> None:
    config = _config(site_base_url="https://edition.example.org", notice_xml_dir=str(NOTICE_DIR))
    notice = extract_notice_entry(NOTICE_DIR / "Ch01_Introduction_test.xml")
    manifest = SiteManifest(config=config, notices=(notice,))

    html_page = render_notice_page(manifest, notice)

    assert f'<meta name="description" content="{notice.title} — notice, ETS Demo.">' in html_page
    assert (
        f'<link rel="canonical" href="https://edition.example.org/notices/{notice.slug}.html">'
        in html_page
    )


def test_search_page_has_generic_description() -> None:
    config = _config()
    manifest = SiteManifest(config=config)

    html_page = render_search_page(manifest)
    doc = lxml_html.document_fromstring(html_page)
    description = doc.xpath('string(//meta[@name="description"]/@content)')

    assert description == "Recherche dans l'édition — ETS Demo."


def test_long_homepage_intro_is_truncated_for_description() -> None:
    long_intro = "Une édition critique numérique du théâtre classique français. " * 5
    config = _config(homepage_intro=long_intro)
    manifest = SiteManifest(config=config)

    html_page = render_home_page(manifest)

    start = html_page.index('<meta name="description" content="') + len(
        '<meta name="description" content="'
    )
    end = html_page.index('">', start)
    description = html_page[start:end]

    assert len(description) <= 161
    assert description.endswith("…")
