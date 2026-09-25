from __future__ import annotations

from pathlib import Path

from lxml import etree

from ets.site_builder.builder import build_static_site
from ets.site_builder.models import SiteConfig

_SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"


def _write_tei(path: Path, *, title: str = "Britannicus") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>{title}</title>
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
            <l>Tout m'afflige et me nuit, et conspire à me nuire.</l>
          </sp>
        </div>
      </div>
    </body>
  </text>
</TEI>
""",
        encoding="utf-8",
    )


def test_builder_does_not_write_sitemap_without_site_base_url(tmp_path: Path) -> None:
    dramatic_dir = tmp_path / "dramatic"
    output_dir = tmp_path / "site"
    _write_tei(dramatic_dir / "britannicus.xml")

    build_static_site(
        SiteConfig(
            site_title="ETS sans SEO",
            dramatic_xml_dir=dramatic_dir,
            output_dir=output_dir,
            publish_notices=False,
        )
    )

    assert not (output_dir / "sitemap.xml").exists()


def test_builder_writes_sitemap_when_site_base_url_is_configured(tmp_path: Path) -> None:
    dramatic_dir = tmp_path / "dramatic"
    output_dir = tmp_path / "site"
    _write_tei(dramatic_dir / "britannicus.xml")
    _write_tei(dramatic_dir / "andromaque.xml", title="Andromaque")

    result = build_static_site(
        SiteConfig(
            site_title="ETS avec SEO",
            dramatic_xml_dir=dramatic_dir,
            output_dir=output_dir,
            publish_notices=False,
            publish_prefaces=False,
            site_base_url="https://edition.example.org",
        )
    )

    sitemap_path = output_dir / "sitemap.xml"
    assert sitemap_path.exists()

    root = etree.fromstring(sitemap_path.read_bytes())
    locs = set(root.xpath("//sm:url/sm:loc/text()", namespaces={"sm": _SITEMAP_NAMESPACE}))

    assert locs == {
        "https://edition.example.org/index.html",
        "https://edition.example.org/plays/britannicus.html",
        "https://edition.example.org/plays/andromaque.html",
    }
    assert result.warnings == ()


def test_sitemap_excludes_search_and_dts_technical_pages(tmp_path: Path) -> None:
    dramatic_dir = tmp_path / "dramatic"
    output_dir = tmp_path / "site"
    _write_tei(dramatic_dir / "britannicus.xml")

    build_static_site(
        SiteConfig(
            site_title="ETS avec SEO",
            dramatic_xml_dir=dramatic_dir,
            output_dir=output_dir,
            publish_notices=False,
            site_base_url="https://edition.example.org",
            enable_dts=True,
            enable_search_index=True,
        )
    )

    sitemap_text = (output_dir / "sitemap.xml").read_text(encoding="utf-8")

    assert "search.html" not in sitemap_text
    assert "api-dts.html" not in sitemap_text
    assert "api/dts" not in sitemap_text
