from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from ets.site_builder.builder import build_static_site
from ets.site_builder.config import site_config_from_dict
from ets.site_builder.extractors import extract_notice_entry
from ets.site_builder.manifest import build_site_manifest
from ets.site_builder.models import NavigationItem, SiteManifest
from ets.site_builder.render import render_notice_page


ROOT = Path(__file__).resolve().parents[1]
DRAMATIC_FIXTURES = ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic"
REALISTIC_NOTICES = ROOT / "fixtures" / "metopes" / "realistic"
RUNTIME_ROOT = ROOT / "tests" / "_runtime"


def _runtime_dir(prefix: str) -> Path:
    target = RUNTIME_ROOT / f"{prefix}_{uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _find_notice(manifest: SiteManifest, slug: str):
    return next(notice for notice in manifest.notices if notice.slug == slug)


def _has_node_kind_recursive(sections, node_kind: str) -> bool:
    for section in sections:
        if section.node_kind == node_kind:
            return True
        if _has_node_kind_recursive(section.children, node_kind):
            return True
    return False


def test_realistic_master_volume_manifest_shape_and_local_xinclude_resolution() -> None:
    config = site_config_from_dict(
        {
            "site_title": "ETS Realistic",
            "dramatic_xml_dir": str(DRAMATIC_FIXTURES),
            "notice_xml_dir": str(REALISTIC_NOTICES),
            "output_dir": str(ROOT / "tests" / "_runtime" / "site_builder_realistic_manifest"),
            "publish_notices": True,
            "resolve_notice_xincludes": True,
        }
    )

    manifest = build_site_manifest(config)
    master = _find_notice(manifest, "heraldique-et-papaute")
    document = master.document

    assert document is not None
    assert master.notice_kind == "master_volume"
    assert document.sections
    assert document.toc
    assert any(path.name == "Ch01_Introduction.xml" for path in document.included_documents)
    assert _has_node_kind_recursive(document.sections, "included_document")
    assert any("Could not resolve xi:include" in warning for warning in document.include_warnings)
    assert any(page.output_relpath == "notices/heraldique-et-papaute.html" for page in manifest.pages)
    assert any(item.kind == "notice_volume" for item in manifest.navigation)


def test_realistic_standalone_notice_extraction_and_rendering() -> None:
    notice = extract_notice_entry(REALISTIC_NOTICES / "Ch01_Introduction.xml")
    config = site_config_from_dict(
        {
            "site_title": "ETS Realistic",
            "dramatic_xml_dir": str(DRAMATIC_FIXTURES),
            "notice_xml_dir": str(REALISTIC_NOTICES),
            "output_dir": str(ROOT / "tests" / "_runtime" / "site_builder_realistic_render"),
            "publish_notices": True,
        }
    )
    manifest = SiteManifest(
        config=config,
        notices=(notice,),
        navigation=(
            NavigationItem(label="Accueil", href="index.html", kind="index"),
            NavigationItem(label=notice.title, href=f"notices/{notice.slug}.html", kind="notice"),
        ),
    )

    html_page = render_notice_page(manifest, notice)

    assert notice.notice_kind == "standalone"
    assert notice.title == "Introduction"
    assert notice.document is not None
    assert notice.document.front_title_page
    assert notice.document.notes
    assert 'class="notice-title-block"' in html_page
    assert 'class="notice-front"' in html_page
    assert "<em>" in html_page
    assert 'class="note-ref"' in html_page
    assert 'class="notice-notes"' in html_page


def test_realistic_publication_build_links_output_tree_and_downloads() -> None:
    base_dir = _runtime_dir("site_builder_realistic_build")
    output_dir = base_dir / "site"
    logo = base_dir / "logo-realistic.txt"
    logo.write_text("ETS", encoding="utf-8")
    assets_dir = base_dir / "brand"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "palette.txt").write_text("bleu", encoding="utf-8")

    config = site_config_from_dict(
        {
            "site_title": "ETS Realistic",
            "site_subtitle": "Validation integration",
            "dramatic_xml_dir": str(DRAMATIC_FIXTURES),
            "notice_xml_dir": str(REALISTIC_NOTICES),
            "output_dir": str(output_dir),
            "show_xml_download": True,
            "publish_notices": True,
            "play_notice_map": {"andromaque": "introduction"},
            "assets": {
                "logos": [str(logo)],
                "directories": [str(assets_dir)],
            },
        }
    )

    result = build_static_site(config)

    assert result.play_count == 2
    assert result.notice_count == 2

    assert (output_dir / "index.html").exists()
    assert (output_dir / "plays" / "andromaque.html").exists()
    assert (output_dir / "notices" / "introduction.html").exists()
    assert (output_dir / "notices" / "heraldique-et-papaute.html").exists()

    play_html = (output_dir / "plays" / "andromaque.html").read_text(encoding="utf-8")
    intro_notice_html = (output_dir / "notices" / "introduction.html").read_text(encoding="utf-8")
    master_notice_html = (output_dir / "notices" / "heraldique-et-papaute.html").read_text(encoding="utf-8")
    home_html = (output_dir / "index.html").read_text(encoding="utf-8")

    assert "../notices/introduction.html" in play_html
    assert 'class="play-structure-nav"' in play_html
    assert 'class="play-reading-layout"' not in play_html
    assert 'id="contenu-editorial"' in play_html
    assert "IM Fell DW Pica" in play_html
    assert "../plays/andromaque.html" in intro_notice_html
    assert "Sommaire" in master_notice_html
    assert "notice-toc" in master_notice_html
    assert 'src="assets/logos/logo-realistic.txt"' in home_html

    assert (output_dir / "xml" / "dramatic" / "andromaque.xml").exists()
    assert (output_dir / "xml" / "dramatic" / "berenice.xml").exists()
    assert (output_dir / "xml" / "notices" / "introduction.xml").exists()
    assert (output_dir / "xml" / "notices" / "heraldique-et-papaute.xml").exists()
    assert (output_dir / "assets" / "logos" / "logo-realistic.txt").exists()
    assert (output_dir / "assets" / "brand" / "palette.txt").exists()

    relpaths = {path.relative_to(output_dir).as_posix() for path in result.generated_pages}
    assert relpaths == {
        "index.html",
        "plays/andromaque.html",
        "plays/berenice.html",
        "notices/introduction.html",
        "notices/heraldique-et-papaute.html",
    }
