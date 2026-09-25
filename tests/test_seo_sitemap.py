from __future__ import annotations

from lxml import etree

from ets.seo import build_sitemap_xml

_SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"


def test_build_sitemap_xml_is_well_formed_and_lists_all_pages() -> None:
    xml_text = build_sitemap_xml(
        "https://edition.example.org",
        ["index.html", "plays/andromaque.html", "notices/introduction.html"],
    )

    root = etree.fromstring(xml_text.encode("utf-8"))
    locs = root.xpath("//sm:url/sm:loc/text()", namespaces={"sm": _SITEMAP_NAMESPACE})

    assert locs == [
        "https://edition.example.org/index.html",
        "https://edition.example.org/plays/andromaque.html",
        "https://edition.example.org/notices/introduction.html",
    ]


def test_build_sitemap_xml_handles_empty_page_list() -> None:
    xml_text = build_sitemap_xml("https://edition.example.org", [])

    root = etree.fromstring(xml_text.encode("utf-8"))
    assert root.xpath("//sm:url", namespaces={"sm": _SITEMAP_NAMESPACE}) == []


def test_build_sitemap_xml_escapes_special_characters_in_relpaths() -> None:
    xml_text = build_sitemap_xml("https://edition.example.org", ["plays/andromaque&fils.html"])

    root = etree.fromstring(xml_text.encode("utf-8"))
    locs = root.xpath("//sm:url/sm:loc/text()", namespaces={"sm": _SITEMAP_NAMESPACE})

    assert locs == ["https://edition.example.org/plays/andromaque&fils.html"]
    assert "&amp;" in xml_text
