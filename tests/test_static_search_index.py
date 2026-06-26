from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

from lxml import html as lxml_html

from ets.site_builder.builder import build_static_site
from ets.site_builder.config import site_config_from_dict
from ets.site_builder.models import SiteConfig


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "fixtures" / "site_builder" / "minimal"


def _write_tei(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Britannicus</title>
        <author>Jean Racine</author>
      </titleStmt>
      <publicationStmt><p>Test</p></publicationStmt>
      <sourceDesc><p>Test</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <div type="act" n="1" xml:id="acte-premier">
        <div type="scene" n="1" xml:id="scene-premiere">
          <sp>
            <speaker>AGRIPPINE</speaker>
            <l n="1" xml:id="A1S1L1">Quoi&#160;?   Tandis que Néron s'abandonne au sommeil</l>
            <l n="2">Faut-il que vous veniez attendre son réveil&#160;?</l>
          </sp>
        </div>
      </div>
    </body>
  </text>
</TEI>
""",
        encoding="utf-8",
    )


def _load(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_tei_without_xml_ids(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Britannicus</title>
        <author>Jean Racine</author>
      </titleStmt>
      <publicationStmt><p>Test</p></publicationStmt>
      <sourceDesc><p>Test</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <div type="act" n="1">
        <div type="scene" n="1">
          <sp>
            <speaker>AGRIPPINE</speaker>
            <l n="1">Premier vers sans xml:id</l>
          </sp>
        </div>
      </div>
    </body>
  </text>
</TEI>
""",
        encoding="utf-8",
    )


def _assert_search_html_links_resolve(output_dir: Path, entries: list[dict[str, object]]) -> None:
    parsed_pages: dict[str, lxml_html.HtmlElement] = {}
    for entry in entries:
        href = entry["html"]
        assert isinstance(href, str)
        parsed = urlsplit(href)
        assert parsed.path
        assert parsed.fragment
        page = parsed_pages.get(parsed.path)
        if page is None:
            page_path = output_dir / parsed.path
            page = lxml_html.document_fromstring(page_path.read_text(encoding="utf-8"))
            parsed_pages[parsed.path] = page
        fragment = unquote(parsed.fragment)
        assert page.xpath("//*[@id=$fragment]", fragment=fragment)


def test_builder_does_not_generate_static_search_index_by_default(tmp_path: Path) -> None:
    dramatic_dir = tmp_path / "dramatic"
    output_dir = tmp_path / "site"
    _write_tei(dramatic_dir / "britannicus.xml")

    build_static_site(
        SiteConfig(
            site_title="ETS sans index",
            dramatic_xml_dir=dramatic_dir,
            output_dir=output_dir,
            publish_notices=False,
        )
    )

    assert not (output_dir / "search" / "index.json").exists()
    assert not (output_dir / "search.html").exists()
    home_html = lxml_html.document_fromstring((output_dir / "index.html").read_text(encoding="utf-8"))
    home_source = (output_dir / "index.html").read_text(encoding="utf-8")
    play_source = (output_dir / "plays" / "britannicus.html").read_text(encoding="utf-8")
    play_html = lxml_html.document_fromstring(
        play_source
    )
    assert 'class="site-header-search"' not in home_source
    assert 'class="site-header-search"' not in play_source
    assert not home_html.xpath("//header[contains(@class, 'site-header')]//a[@href='search.html']")
    assert not home_html.xpath("//main/nav//a[@href='search.html' and normalize-space()='Recherche']")
    assert not play_html.xpath("//header[contains(@class, 'site-header')]//a[@href='../search.html']")
    assert not play_html.xpath("//main/nav//a[@href='../search.html' and normalize-space()='Recherche']")


def test_builder_generates_static_search_index_when_enabled_without_dts(tmp_path: Path) -> None:
    dramatic_dir = tmp_path / "dramatic"
    output_dir = tmp_path / "site"
    _write_tei(dramatic_dir / "britannicus.xml")

    build_static_site(
        SiteConfig(
            site_title="ETS avec index",
            dramatic_xml_dir=dramatic_dir,
            output_dir=output_dir,
            publish_notices=False,
            enable_search_index=True,
        )
    )

    index_path = output_dir / "search" / "index.json"
    search_page_path = output_dir / "search.html"
    raw_json = index_path.read_text(encoding="utf-8")
    search_html = search_page_path.read_text(encoding="utf-8")
    entries = _load(index_path)

    assert search_page_path.exists()
    assert "search/index.json" in search_html
    assert 'type="search"' in search_html
    assert "Lire dans le site" in search_html
    assert "Fragment TEI" in search_html
    assert "Navigation DTS" in search_html
    assert "innerHTML" not in search_html
    assert len(entries) == 2
    first = entries[0]
    assert first == {
        "piece": "Britannicus",
        "slug": "britannicus",
        "ref": "A1S1L1",
        "citeType": "line",
        "speaker": "AGRIPPINE",
        "label": "Acte 1, scène 1, vers 1",
        "text": "Quoi ? Tandis que Néron s'abandonne au sommeil",
        "html": "plays/britannicus.html#A1S1L1",
    }
    assert entries[1]["ref"] == "A1S1L2"
    assert entries[1]["speaker"] == "AGRIPPINE"
    assert entries[1]["text"] == "Faut-il que vous veniez attendre son réveil ?"
    assert "Néron" in raw_json
    assert "\\u00e9" not in raw_json
    assert "dts_document" not in first
    assert "dts_navigation" not in first
    assert not (output_dir / "api" / "dts").exists()

    home_source = (output_dir / "index.html").read_text(encoding="utf-8")
    play_source = (output_dir / "plays" / "britannicus.html").read_text(encoding="utf-8")
    home_html = lxml_html.document_fromstring(home_source)
    play_html = lxml_html.document_fromstring(
        play_source
    )
    assert 'class="site-header-search"' in home_source
    assert 'href="search.html"' in home_source
    assert 'class="site-header-search-icon" aria-hidden="true"' in home_source
    assert "Recherche" in home_source
    assert 'class="site-header-search"' in play_source
    assert 'href="../search.html"' in play_source
    assert home_html.xpath(
        "//header[contains(@class, 'site-header')]//a[@href='search.html' and .//span[normalize-space()='Recherche']]"
    )
    assert play_html.xpath(
        "//header[contains(@class, 'site-header')]//a[@href='../search.html' and .//span[normalize-space()='Recherche']]"
    )
    assert not home_html.xpath("//main/nav//a[@href='search.html' and normalize-space()='Recherche']")
    assert not play_html.xpath("//main/nav//a[@href='../search.html' and normalize-space()='Recherche']")
    assert play_html.xpath("//*[@id='A1S1L1']")
    _assert_search_html_links_resolve(output_dir, entries)


def test_builder_generates_static_search_index_with_dts_links_when_dts_is_enabled(tmp_path: Path) -> None:
    dramatic_dir = tmp_path / "dramatic"
    output_dir = tmp_path / "site"
    _write_tei(dramatic_dir / "britannicus.xml")

    build_static_site(
        SiteConfig(
            site_title="ETS avec index et DTS",
            dramatic_xml_dir=dramatic_dir,
            output_dir=output_dir,
            publish_notices=False,
            enable_dts=True,
            enable_search_index=True,
        )
    )

    entries = _load(output_dir / "search" / "index.json")

    assert entries[0]["dts_document"] == "api/dts/document/britannicus/A1S1L1.xml"
    assert entries[0]["dts_navigation"] == "api/dts/navigation/britannicus/A1S1L1.json"
    assert entries[1]["dts_document"] == "api/dts/document/britannicus/A1S1L2.xml"
    assert entries[1]["dts_navigation"] == "api/dts/navigation/britannicus/A1S1L2.json"
    assert (output_dir / "api" / "dts" / "index.json").exists()


def test_static_search_index_and_html_use_logical_line_anchor_without_xml_id(tmp_path: Path) -> None:
    dramatic_dir = tmp_path / "dramatic"
    output_dir = tmp_path / "site"
    _write_tei_without_xml_ids(dramatic_dir / "britannicus.xml")

    build_static_site(
        SiteConfig(
            site_title="ETS avec index sans xml:id",
            dramatic_xml_dir=dramatic_dir,
            output_dir=output_dir,
            publish_notices=False,
            enable_search_index=True,
        )
    )

    entries = _load(output_dir / "search" / "index.json")
    play_html = lxml_html.document_fromstring(
        (output_dir / "plays" / "britannicus.html").read_text(encoding="utf-8")
    )

    assert entries[0]["ref"] == "A1S1L1"
    assert entries[0]["html"] == "plays/britannicus.html#A1S1L1"
    assert play_html.xpath("//*[@id='A1S1L1']")
    _assert_search_html_links_resolve(output_dir, entries)


def test_static_search_navigation_link_is_relative_from_notice_pages(tmp_path: Path) -> None:
    output_dir = tmp_path / "site"
    config = site_config_from_dict(
        {
            "site_title": "ETS avec recherche et notice",
            "dramatic_xml_dir": str(FIXTURE_ROOT / "dramatic"),
            "notice_xml_dir": str(FIXTURE_ROOT / "notices"),
            "output_dir": str(output_dir),
            "publish_notices": True,
            "play_notice_map": {"andromaque": "andromaque-notice"},
            "enable_search_index": True,
        }
    )

    build_static_site(config)

    notice_html = lxml_html.document_fromstring(
        (output_dir / "notices" / "andromaque-notice.html").read_text(encoding="utf-8")
    )

    assert notice_html.xpath(
        "//header[contains(@class, 'site-header')]//a[@href='../search.html' and .//span[normalize-space()='Recherche']]"
    )
    assert not notice_html.xpath("//main/nav//a[@href='../search.html' and normalize-space()='Recherche']")
