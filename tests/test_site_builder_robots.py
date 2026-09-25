from __future__ import annotations

from pathlib import Path

from ets.site_builder.builder import build_static_site
from ets.site_builder.models import SiteConfig


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


def test_builder_does_not_write_robots_txt_without_site_base_url(tmp_path: Path) -> None:
    dramatic_dir = tmp_path / "dramatic"
    output_dir = tmp_path / "site"
    _write_tei(dramatic_dir / "britannicus.xml")

    build_static_site(
        SiteConfig(
            site_title="ETS sans SEO",
            dramatic_xml_dir=dramatic_dir,
            output_dir=output_dir,
            publish_notices=False,
            publish_prefaces=False,
        )
    )

    assert not (output_dir / "robots.txt").exists()


def test_builder_writes_robots_txt_when_site_base_url_is_configured(tmp_path: Path) -> None:
    dramatic_dir = tmp_path / "dramatic"
    output_dir = tmp_path / "site"
    _write_tei(dramatic_dir / "britannicus.xml")

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

    robots_path = output_dir / "robots.txt"
    assert robots_path.exists()

    robots_text = robots_path.read_text(encoding="utf-8")
    assert "Sitemap: https://edition.example.org/sitemap.xml" in robots_text
    assert "Disallow: /xml/" in robots_text
    assert "Disallow: /api/dts/" in robots_text
    assert result.warnings == ()
