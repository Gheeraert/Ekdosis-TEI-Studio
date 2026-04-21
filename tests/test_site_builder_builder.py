from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from lxml import html as lxml_html

from ets.site_builder.builder import build_static_site
from ets.site_builder.config import site_config_from_dict
from ets.site_builder.extractors import extract_play_entry
from ets.site_builder.manifest import build_site_manifest
from ets.site_builder.models import (
    NavigationItem,
    PlayActNavigation,
    PlayNavigation,
    PlaySceneNavigation,
    SiteManifest,
)
from ets.site_builder.render import _nav_item_contains_current, render_play_page


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

    doc = lxml_html.document_fromstring(play_html)
    assert len(doc.xpath("//main/nav")) == 1
    assert not doc.xpath("//main/nav//*[contains(@class, 'play-structure-nav')]")
    assert doc.xpath("//section[@id='contenu-editorial' and contains(@class, 'dramatic-content')]")
    assert doc.xpath("//main/nav//details[contains(@class, 'nav-details')]")
    assert doc.xpath("//main/nav//ul[contains(@class, 'site-nav') and contains(@class, 'nested')]")
    assert doc.xpath("//main/nav//a[contains(normalize-space(.), 'Acte 1')]")
    assert doc.xpath("//main/nav//a[contains(@href, '#ets-nav-andromaque-scene-1')]")
    assert len(doc.xpath("//main/nav//li[contains(@class, 'nav-kind-plays_group')]/details[@open]")) == 1
    assert len(doc.xpath("//main/nav//li[contains(@class, 'nav-kind-play_group')]/details[@open]")) == 1
    assert not doc.xpath("//main/nav//li[contains(@class, 'nav-kind-act')]/details[@open]")
    assert "IM Fell DW Pica" in play_html
    assert ".vers-container" in play_html
    assert "#container {" not in play_html
    assert "scroll-behavior: smooth" in play_html
    assert "position: sticky" in play_html
    assert "prefers-reduced-motion: reduce" in play_html
    assert "hashchange" in play_html
    assert "closeSiblingActDetails" in play_html

    nav_targets = doc.xpath("//main/nav//a[starts-with(@href, '../plays/andromaque.html#')]/@href")
    assert nav_targets
    for href in nav_targets:
        anchor_id = href.split("#", maxsplit=1)[1]
        assert doc.xpath(f"//*[@id='{anchor_id}']")

    assert "Lecture" not in play_html
    assert "Lire" not in play_html
    assert "Dans la piece" not in play_html
    assert "Lire" not in home_html

    notice_doc = lxml_html.document_fromstring(notice_html)
    assert "Aller a la piece associee" not in notice_html
    assert not notice_doc.xpath("//section//a[starts-with(@href, '../plays/')]")


def test_builder_copies_branding_assets_and_references_logos() -> None:
    base_dir = _runtime_dir("site_builder_assets")
    output_dir = base_dir / "site_assets"
    dramatic_dir = base_dir / "dramatic"
    shutil.copytree(FIXTURE_ROOT / "dramatic", dramatic_dir)

    logos_dir = base_dir / "assets" / "logos"
    logos_dir.mkdir(parents=True, exist_ok=True)
    (logos_dir / "b-logo.png").write_text("PNG", encoding="utf-8")
    (logos_dir / "a-logo.svg").write_text("SVG", encoding="utf-8")
    (logos_dir / "c-logo.webp").write_text("WEBP", encoding="utf-8")
    (logos_dir / "ignored.txt").write_text("IGNORE", encoding="utf-8")

    asset_dir = base_dir / "brand"
    asset_dir.mkdir(parents=True, exist_ok=True)
    (asset_dir / "palette.txt").write_text("bleu", encoding="utf-8")

    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(dramatic_dir),
            "notice_xml_dir": str(FIXTURE_ROOT / "notices"),
            "output_dir": str(output_dir),
            "publish_notices": True,
            "assets": {
                "directories": [str(asset_dir)],
            },
        }
    )

    result = build_static_site(config)

    assert (output_dir / "assets" / "logos" / "a-logo.svg").exists()
    assert (output_dir / "assets" / "logos" / "b-logo.png").exists()
    assert (output_dir / "assets" / "logos" / "c-logo.webp").exists()
    assert not (output_dir / "assets" / "logos" / "ignored.txt").exists()
    assert (output_dir / "assets" / "brand" / "palette.txt").exists()
    assert any(path.name == "a-logo.svg" for path in result.copied_assets)
    assert any(path.name == "b-logo.png" for path in result.copied_assets)
    assert any(path.name == "c-logo.webp" for path in result.copied_assets)

    home_html = (output_dir / "index.html").read_text(encoding="utf-8")
    play_html = (output_dir / "plays" / "andromaque.html").read_text(encoding="utf-8")
    assert 'src="assets/logos/a-logo.svg"' in home_html
    assert 'src="assets/logos/b-logo.png"' in home_html
    assert 'src="assets/logos/c-logo.webp"' in home_html
    assert home_html.index("a-logo.svg") < home_html.index("b-logo.png") < home_html.index("c-logo.webp")
    assert 'src="../assets/logos/a-logo.svg"' in play_html
    assert 'src="../assets/logos/b-logo.png"' in play_html
    assert 'src="../assets/logos/c-logo.webp"' in play_html


def test_builder_does_not_render_branding_when_assets_logos_folder_is_missing() -> None:
    base_dir = _runtime_dir("site_builder_assets_missing")
    output_dir = base_dir / "site_assets_missing"
    dramatic_dir = base_dir / "dramatic"
    shutil.copytree(FIXTURE_ROOT / "dramatic", dramatic_dir)

    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(dramatic_dir),
            "notice_xml_dir": str(FIXTURE_ROOT / "notices"),
            "output_dir": str(output_dir),
            "publish_notices": True,
        }
    )

    build_static_site(config)
    home_html = (output_dir / "index.html").read_text(encoding="utf-8")
    assert 'class="branding"' not in home_html


def test_builder_does_not_render_branding_when_assets_logos_folder_is_empty() -> None:
    base_dir = _runtime_dir("site_builder_assets_empty")
    output_dir = base_dir / "site_assets_empty"
    dramatic_dir = base_dir / "dramatic"
    shutil.copytree(FIXTURE_ROOT / "dramatic", dramatic_dir)
    (base_dir / "assets" / "logos").mkdir(parents=True, exist_ok=True)

    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(dramatic_dir),
            "notice_xml_dir": str(FIXTURE_ROOT / "notices"),
            "output_dir": str(output_dir),
            "publish_notices": True,
        }
    )

    build_static_site(config)
    home_html = (output_dir / "index.html").read_text(encoding="utf-8")
    assert 'class="branding"' not in home_html


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
    assert "Introduction générale" in home_html
    assert 'href="notices/bibliographie.html"' in home_html
    assert result.notice_count >= 2

    doc = lxml_html.document_fromstring(play_html)
    assert doc.xpath("//main/nav//a[@href='../notices/bibliographie.html']")
    assert doc.xpath("//main/nav//li[contains(@class, 'nav-kind-plays_group')]")
    assert not doc.xpath("//main/nav//*[normalize-space(.)='Lecture']")
    assert not doc.xpath("//main/nav//*[normalize-space(.)='Lire']")
    assert not doc.xpath("//main/nav//*[contains(normalize-space(.), 'Dans la piece')]")
    assert doc.xpath("//main/nav//a[@href='../notices/introduction.html']")
    assert doc.xpath("//main/nav//a[contains(., 'Acte 1')]")
    assert doc.xpath("//main/nav//a[contains(@href, '#ets-nav-andromaque-scene-1')]")
    andromaque_anchors = doc.xpath("//main/nav//a[starts-with(@href, '../plays/andromaque.html#')]/@href")
    assert andromaque_anchors
    for href in andromaque_anchors:
        assert doc.xpath(f"//*[@id='{href.split('#', maxsplit=1)[1]}']")


def test_builder_sidebar_play_navigation_matches_manifest_play_navigation_without_local_block() -> None:
    base_dir = _runtime_dir("site_builder_nav_coherence")
    output_dir = base_dir / "site_nav_coherence"
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(FIXTURE_ROOT / "dramatic"),
            "output_dir": str(output_dir),
            "publish_notices": False,
        }
    )

    manifest = build_site_manifest(config)
    build_static_site(config)
    play_html = (output_dir / "plays" / "andromaque.html").read_text(encoding="utf-8")
    doc = lxml_html.document_fromstring(play_html)

    andromaque_structure = next(item for item in manifest.play_navigation if item.play_slug == "andromaque")
    expected_pairs = [
        (act.label, act.anchor_id) for act in andromaque_structure.acts
    ] + [
        (scene.label, scene.anchor_id) for act in andromaque_structure.acts for scene in act.scenes
    ]

    sidebar_pairs = [
        (node.text_content().strip(), node.get("href", "").split("#", maxsplit=1)[1])
        for node in doc.xpath("//main/nav//a[starts-with(@href, '../plays/andromaque.html#')]")
    ]
    assert sidebar_pairs == expected_pairs
    assert not doc.xpath("//main/nav//*[contains(@class, 'play-structure-nav')]")
    assert "Lecture" not in play_html
    assert "Lire" not in play_html
    assert "Dans la piece" not in play_html

    for _, anchor_id in expected_pairs:
        assert doc.xpath(f"//*[@id='{anchor_id}']")


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
    assert doc.xpath("//main/nav//a[@href='../notices/andromaque-notice.html']")
    assert doc.xpath("//main/nav//a[starts-with(@href, '../plays/andromaque.html#')]")
    assert not doc.xpath("//main/nav//*[contains(@class, 'play-structure-nav')]")
    assert doc.xpath("//section[@id='contenu-editorial' and contains(@class, 'dramatic-content')]")
    assert "IM Fell DW Pica" in play_html
    assert doc.xpath("//*[contains(@class, 'locuteur')]")
    assert doc.xpath("//*[contains(@class, 'vers-container')]")
    assert not doc.xpath("//*[contains(@class, 'play-reading-layout')]")
    assert not doc.xpath("//*[contains(., 'Divisions reperees')]")


def test_play_anchor_injection_prefers_outer_title_wrappers_and_keeps_scene_alignment(
    monkeypatch,
) -> None:
    play = extract_play_entry(FIXTURE_ROOT / "dramatic" / "andromaque.xml")
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(FIXTURE_ROOT / "dramatic"),
            "output_dir": str(ROOT / "tests" / "_runtime" / "site_builder_nested_titles"),
            "publish_notices": False,
        }
    )
    play_navigation = PlayNavigation(
        play_slug=play.slug,
        play_title=play.title,
        acts=(
            PlayActNavigation(
                label="Acte 1",
                anchor_id="ets-nav-andromaque-act-1",
                start_speech_index=0,
                scenes=(
                    PlaySceneNavigation(
                        label="Scène 1",
                        anchor_id="ets-nav-andromaque-scene-1",
                        start_speech_index=0,
                    ),
                    PlaySceneNavigation(
                        label="Scène 2",
                        anchor_id="ets-nav-andromaque-scene-2",
                        start_speech_index=1,
                    ),
                ),
            ),
        ),
    )
    manifest = SiteManifest(
        config=config,
        plays=(play,),
        play_navigation=(play_navigation,),
        navigation=(
            NavigationItem(
                label="Pièces",
                href="",
                kind="plays_group",
                children=(
                    NavigationItem(
                        label=play.title,
                        href="",
                        kind="play_group",
                        children=(
                            NavigationItem(
                                label="Acte 1",
                                href=f"plays/{play.slug}.html#ets-nav-andromaque-act-1",
                                kind="act",
                                children=(
                                    NavigationItem(
                                        label="Scène 1",
                                        href=f"plays/{play.slug}.html#ets-nav-andromaque-scene-1",
                                        kind="scene",
                                    ),
                                    NavigationItem(
                                        label="Scène 2",
                                        href=f"plays/{play.slug}.html#ets-nav-andromaque-scene-2",
                                        kind="scene",
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )

    nested_export_html = """<!doctype html>
<html>
  <head></head>
  <body>
    <section id="contenu-editorial">
      <div class="acte-titre-sans-variation"><div class="acte-titre">Acte I</div></div>
      <div class="scene-titre-sans-variation"><div class="scene-titre">Scene 1</div></div>
      <div class="locuteur">ORESTE</div>
      <div class="scene-titre-sans-variation"><div class="scene-titre">Scene 2</div></div>
      <div class="locuteur">PYLADE</div>
    </section>
  </body>
</html>"""

    monkeypatch.setattr("ets.site_builder.render.render_html_export_from_tei", lambda *_args, **_kwargs: nested_export_html)

    play_html = render_play_page(manifest, play)
    doc = lxml_html.document_fromstring(play_html)

    assert doc.xpath("//div[contains(@class, 'acte-titre-sans-variation') and @id='ets-nav-andromaque-act-1']")
    assert doc.xpath("(//div[contains(@class, 'scene-titre-sans-variation')])[1][@id='ets-nav-andromaque-scene-1']")
    assert doc.xpath("(//div[contains(@class, 'scene-titre-sans-variation')])[2][@id='ets-nav-andromaque-scene-2']")
    assert not doc.xpath(
        "//div[contains(concat(' ', normalize-space(@class), ' '), ' scene-titre ') and @id='ets-nav-andromaque-scene-2']"
    )

    local_targets = doc.xpath("//main/nav//a[starts-with(@href, '../plays/andromaque.html#')]/@href")
    assert local_targets == [
        "../plays/andromaque.html#ets-nav-andromaque-act-1",
        "../plays/andromaque.html#ets-nav-andromaque-scene-1",
        "../plays/andromaque.html#ets-nav-andromaque-scene-2",
    ]
    for href in local_targets:
        assert doc.xpath(f"//*[@id='{href.split('#', maxsplit=1)[1]}']")


def test_nav_item_contains_current_keeps_play_group_open_without_auto_opening_all_acts() -> None:
    act_one = NavigationItem(
        label="Acte 1",
        href="plays/andromaque.html#acte-1",
        kind="act",
        children=(NavigationItem(label="Scène 1", href="plays/andromaque.html#scene-1", kind="scene"),),
    )
    act_two = NavigationItem(
        label="Acte 2",
        href="plays/andromaque.html#acte-2",
        kind="act",
        children=(NavigationItem(label="Scène 1", href="plays/andromaque.html#scene-2-1", kind="scene"),),
    )
    play_group = NavigationItem(
        label="Andromaque",
        href="",
        kind="play_group",
        children=(act_one, act_two),
    )

    assert _nav_item_contains_current(play_group, "plays/andromaque.html")
    assert not _nav_item_contains_current(act_one, "plays/andromaque.html")
    assert not _nav_item_contains_current(act_two, "plays/andromaque.html")


def test_builder_unites_editoriales_orders_notice_preface_dramatis_before_acts() -> None:
    base_dir = _runtime_dir("site_builder_unites_editoriales")
    dramatic_dir = base_dir / "dramatic"
    notice_dir = base_dir / "notices"
    output_dir = base_dir / "site"
    dramatic_dir.mkdir(parents=True, exist_ok=True)
    notice_dir.mkdir(parents=True, exist_ok=True)

    fixtures_dir = ROOT / "fixtures" / "site_builder" / "unites_editoriales"
    shutil.copy2(fixtures_dir / "piece.xml", dramatic_dir / "piece.xml")
    shutil.copy2(fixtures_dir / "notice.xml", notice_dir / "notice.xml")
    preface_source = next(fixtures_dir.glob("pr*face.xml"))
    shutil.copy2(preface_source, notice_dir / "preface.xml")

    play_slug = "la-thebaide-ou-les-freres-ennemis"
    notice_slug = "alexandre-le-grand-notice-extrait-de-fixture"
    preface_slug = "mithridate-preface-fixture-tei-simplifiee"

    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(dramatic_dir),
            "notice_xml_dir": str(notice_dir),
            "output_dir": str(output_dir),
            "publish_notices": True,
            "play_notice_map": {play_slug: notice_slug},
            "play_preface_map": {play_slug: [preface_slug]},
        }
    )

    manifest = build_site_manifest(config)
    result = build_static_site(config)
    assert result.play_count == 1
    assert result.notice_count == 2
    assert any(page.kind == "preface" and page.source_slug == preface_slug for page in manifest.pages)
    assert (output_dir / "notices" / f"{preface_slug}.html").exists()

    plays_group = next(item for item in manifest.navigation if item.kind == "plays_group")
    play_branch = next(item for item in plays_group.children if item.children)
    expected_top_level_hrefs = [f"../{child.href}" for child in play_branch.children]
    assert [child.kind for child in play_branch.children[:3]] == [
        "piece_notice",
        "author_preface",
        "dramatis_personae",
    ]

    play_html = (output_dir / "plays" / f"{play_slug}.html").read_text(encoding="utf-8")
    doc = lxml_html.document_fromstring(play_html)
    top_level_nodes = doc.xpath(
        "(//li[contains(@class, 'nav-kind-play_group')]//ul[contains(@class, 'site-nav') and contains(@class, 'nested')])[1]/li"
    )
    top_level_hrefs: list[str] = []
    for node in top_level_nodes:
        direct_link = node.xpath("./a/@href")
        if direct_link:
            top_level_hrefs.append(direct_link[0])
            continue
        summary_link = node.xpath("./details/summary//a/@href")
        if summary_link:
            top_level_hrefs.append(summary_link[0])

    assert top_level_hrefs[:3] == expected_top_level_hrefs[:3]
    assert top_level_hrefs[0] == f"../notices/{notice_slug}.html"
    assert top_level_hrefs[1] == f"../notices/{preface_slug}.html"
    assert not doc.xpath(
        f"//main/nav/ul[contains(@class, 'site-nav')]/li[contains(@class, 'nav-kind-preface') and .//a[@href='../notices/{preface_slug}.html']]"
    )

    dramatis_anchor_id = play_branch.children[2].href.split("#", maxsplit=1)[1]
    first_act_anchor_id = next(child.href for child in play_branch.children if child.kind == "act").split("#", maxsplit=1)[1]
    assert doc.xpath(f"//*[@id='{dramatis_anchor_id}']")
    assert doc.xpath(f"//*[@id='{first_act_anchor_id}']")
    assert play_html.index(f'id="{dramatis_anchor_id}"') < play_html.index(f'id="{first_act_anchor_id}"')


def test_builder_uses_external_dramatis_when_configured() -> None:
    base_dir = _runtime_dir("site_builder_external_dramatis")
    dramatic_dir = base_dir / "dramatic"
    notice_dir = base_dir / "notices"
    dramatis_dir = base_dir / "dramatis"
    output_dir = base_dir / "site"
    dramatic_dir.mkdir(parents=True, exist_ok=True)
    notice_dir.mkdir(parents=True, exist_ok=True)
    dramatis_dir.mkdir(parents=True, exist_ok=True)

    fixtures_dir = ROOT / "fixtures" / "site_builder" / "unites_editoriales"
    shutil.copy2(fixtures_dir / "piece.xml", dramatic_dir / "piece.xml")
    shutil.copy2(fixtures_dir / "notice.xml", notice_dir / "notice.xml")
    preface_source = next(fixtures_dir.glob("pr*face.xml"))
    shutil.copy2(preface_source, notice_dir / "preface.xml")

    (dramatis_dir / "dramatis-externe.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <front>
      <castList>
        <castItem>Personnage externe Alpha</castItem>
        <castItem>Personnage externe Beta</castItem>
      </castList>
    </front>
  </text>
</TEI>
""",
        encoding="utf-8",
    )

    play_slug = "la-thebaide-ou-les-freres-ennemis"
    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(dramatic_dir),
            "notice_xml_dir": str(notice_dir),
            "dramatis_xml_dir": str(dramatis_dir),
            "output_dir": str(output_dir),
            "publish_notices": True,
            "publish_prefaces": True,
            "play_notice_map": {play_slug: "alexandre-le-grand-notice-extrait-de-fixture"},
            "play_preface_map": {play_slug: ["mithridate-preface-fixture-tei-simplifiee"]},
            "play_dramatis_map": {play_slug: "dramatis-externe"},
        }
    )

    build_static_site(config)
    play_html = (output_dir / "plays" / f"{play_slug}.html").read_text(encoding="utf-8")
    doc = lxml_html.document_fromstring(play_html)
    assert doc.xpath("//section[contains(@class, 'dramatis-personae-block')]//li[text()='Personnage externe Alpha']")
    assert doc.xpath("//section[contains(@class, 'dramatis-personae-block')]//li[text()='Personnage externe Beta']")

