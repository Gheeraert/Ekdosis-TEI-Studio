from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ets.site_builder.config import site_config_from_dict
from ets.site_builder.extractors import extract_notice_entry
from ets.site_builder.models import NavigationItem, SiteManifest
from ets.site_builder.render import render_notice_page


ROOT = Path(__file__).resolve().parents[1]
MINIMAL = ROOT / "fixtures" / "metopes" / "minimal"


def test_render_notice_page_outputs_structured_metopes_html() -> None:
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic"),
            "notice_xml_dir": str(MINIMAL),
            "output_dir": str(ROOT / "tests" / "_runtime" / "site_builder_render"),
            "show_xml_download": True,
        }
    )
    notice = extract_notice_entry(MINIMAL / "Ch01_Introduction_test.xml")
    notice = replace(notice, xml_download_relpath=f"xml/notices/{notice.slug}.xml")
    manifest = SiteManifest(
        config=config,
        notices=(notice,),
        navigation=(
            NavigationItem(label="Accueil", href="index.html", kind="index"),
            NavigationItem(label=notice.title, href=f"notices/{notice.slug}.html", kind="notice"),
        ),
    )

    html_page = render_notice_page(manifest, notice)

    assert "<h2>Introduction</h2>" in html_page
    assert "Sommaire" in html_page
    assert "<em>mise en forme italique</em>" in html_page
    assert "Notes" in html_page
    assert "Note de bas de page de démonstration." in html_page
    assert "Télécharger le XML" in html_page
    assert 'href="#doc-body"' in html_page
    assert 'id="doc-body"' in html_page


def test_render_notice_page_renders_lists_from_metopes_chapter() -> None:
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic"),
            "notice_xml_dir": str(MINIMAL),
            "output_dir": str(ROOT / "tests" / "_runtime" / "site_builder_render_lists"),
        }
    )
    notice = extract_notice_entry(MINIMAL / "Ch02_Sections_et_titres.xml")
    manifest = SiteManifest(
        config=config,
        notices=(notice,),
        navigation=(NavigationItem(label=notice.title, href=f"notices/{notice.slug}.html", kind="notice"),),
    )

    html_page = render_notice_page(manifest, notice)

    assert "Premier item" in html_page
    assert "Deuxième item" in html_page


def test_render_notice_page_nested_toc_for_master_volume() -> None:
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic"),
            "notice_xml_dir": str(MINIMAL),
            "output_dir": str(ROOT / "tests" / "_runtime" / "site_builder_render_master"),
        }
    )
    notice = extract_notice_entry(MINIMAL / "Metopes_Test_Book.xml")
    manifest = SiteManifest(
        config=config,
        notices=(notice,),
        navigation=(NavigationItem(label=notice.title, href=f"notices/{notice.slug}.html", kind="notice_volume"),),
    )

    html_page = render_notice_page(manifest, notice)

    assert "Sommaire" in html_page
    assert "notice-group" in html_page
    assert "notice-included-document" in html_page
    assert "Ch01_Introduction_test.xml" in html_page
    assert 'href="#grp1-introduction"' in html_page
