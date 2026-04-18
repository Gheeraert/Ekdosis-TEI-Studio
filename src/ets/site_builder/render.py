from __future__ import annotations

import html
import re

from lxml import etree, html as lxml_html

from ets.html import HtmlExportOptions, render_html_export_from_tei

from .models import (
    HomePageSection,
    NavigationItem,
    NoticeDocument,
    NoticeEntry,
    NoticeSection,
    PlayEntry,
    PlayNavigation,
    SiteManifest,
)
from .play_navigation import extract_play_navigation, index_play_navigation


NOTE_REF_PATTERN = re.compile(r'<sup class="note-ref"><a href="#note-([^"]+)">\[([^\]]+)\]</a></sup>')


def _asset_prefix(current_href: str) -> str:
    path = current_href.strip("/")
    if not path or "/" not in path:
        return ""
    depth = len(path.split("/")) - 1
    return "../" * depth


def _kind_class(kind: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "-", kind.lower()).strip("-") or "item"


def _href_without_hash(href: str) -> str:
    return href.split("#", maxsplit=1)[0]


def _contains_descendant_for_page(item: NavigationItem, current_href: str) -> bool:
    for child in item.children:
        if child.href and _href_without_hash(child.href) == current_href:
            return True
        if _contains_descendant_for_page(child, current_href):
            return True
    return False


def _nav_item_contains_current(item: NavigationItem, current_href: str) -> bool:
    if item.href == current_href:
        return True
    # Keep high-level play branches open on play pages, but do not auto-open
    # every act/scene branch when current_href has no hash.
    if item.kind in {"plays_group", "play_group"} and _contains_descendant_for_page(item, current_href):
        return True
    return any(_nav_item_contains_current(child, current_href) for child in item.children)


def _nav_label_html(item: NavigationItem, current_href: str) -> str:
    escaped_label = html.escape(item.label)
    if not item.href:
        return f'<span class="nav-label">{escaped_label}</span>'

    current_attr = ""
    if item.href == current_href and item.kind not in {"act", "scene"}:
        current_attr = ' aria-current="page"'
    href = item.href
    if href and not href.startswith(("#", "/", "http://", "https://")):
        href = f"{_asset_prefix(current_href)}{href}"
    escaped_href = html.escape(href, quote=True)
    return f'<a href="{escaped_href}"{current_attr}>{escaped_label}</a>'


def _nav_item_html(item: NavigationItem, current_href: str) -> str:
    kind_class = _kind_class(item.kind)
    if not item.children:
        return f'<li class="nav-item nav-kind-{kind_class}">{_nav_label_html(item, current_href)}</li>'

    child_items = "".join(_nav_item_html(child, current_href) for child in item.children)
    open_attr = " open" if _nav_item_contains_current(item, current_href) else ""
    return (
        f'<li class="nav-item nav-kind-{kind_class} nav-branch">'
        f'<details class="nav-details"{open_attr}>'
        f'<summary class="nav-summary">{_nav_label_html(item, current_href)}</summary>'
        f'<ul class="site-nav nested">{child_items}</ul>'
        f"</details></li>"
    )


def _nav_html(manifest: SiteManifest, current_href: str) -> str:
    items = "".join(_nav_item_html(item, current_href) for item in manifest.navigation)
    return f'<ul class="site-nav">{items}</ul>'


def _branding_html(manifest: SiteManifest, current_href: str) -> str:
    logos = manifest.config.assets.logo_files
    if not logos:
        return ""
    prefix = _asset_prefix(current_href)
    images = "".join(
        (
            f'<img src="{html.escape(prefix + "assets/logos/" + logo.name, quote=True)}" '
            f'alt="{html.escape(manifest.config.site_title)}" loading="lazy">'
        )
        for logo in logos
    )
    return f'<div class="branding" aria-label="Identite visuelle">{images}</div>'


def _layout(
    manifest: SiteManifest,
    *,
    page_title: str,
    current_href: str,
    content_html: str,
    head_extra_html: str = "",
) -> str:
    return f"""<!doctype html>
<html lang=\"fr\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{html.escape(page_title)}</title>
  {head_extra_html}
  <style>
    html {{ scroll-behavior: smooth; }}
    body {{ font-family: Georgia, 'Times New Roman', serif; margin: 0; color: #1f2328; line-height: 1.5; }}
    header {{ padding: 1rem 1.25rem; border-bottom: 1px solid #d5d7da; background: #f8f9fb; }}
    main {{ display: grid; grid-template-columns: 280px 1fr; gap: 1rem; min-height: 100vh; }}
    nav {{ border-right: 1px solid #eceef1; padding: 1rem 1.25rem; }}
    nav ul {{ margin: 0; padding-left: 1.1rem; }}
    nav li {{ margin: 0.35rem 0; }}
    .site-nav {{ margin-bottom: 1rem; }}
    .site-nav.nested {{ margin-top: 0.35rem; }}
    .nav-item > a, .nav-summary a {{ color: #1e3a5f; text-decoration: none; }}
    .nav-item > a:hover, .nav-summary a:hover {{ text-decoration: underline; }}
    .nav-label {{ color: #2d3d51; font-weight: 600; }}
    .nav-summary {{ cursor: pointer; }}
    .nav-summary::marker {{ color: #66778c; }}
    .nav-summary a[aria-current="page"], .nav-item > a[aria-current="page"] {{ font-weight: 700; }}

    .home-overview {{ margin-bottom: 1.4rem; }}
    .home-overview h2 {{ margin-bottom: 0.45rem; }}
    .home-overview .home-project {{ margin: 0.25rem 0 0.55rem; color: #304257; }}
    .home-overview dl {{ margin: 0; display: grid; grid-template-columns: 180px 1fr; gap: 0.35rem 0.9rem; }}
    .home-overview dt {{ font-weight: 600; color: #304257; }}
    .home-overview dd {{ margin: 0; color: #2e3946; }}
    .home-editorial-section {{ margin: 1.1rem 0 1.35rem; }}
    .home-editorial-section h3 {{ margin-bottom: 0.45rem; }}
    .home-editorial-section p {{ margin: 0.4rem 0; }}
    .home-plays {{ margin-top: 1.3rem; }}
    .home-play-list {{ margin: 0.45rem 0 0; padding-left: 1.15rem; }}
    .home-play-list li {{ margin: 0.45rem 0; }}
    .home-play-links {{ color: #3f5065; font-size: 0.95rem; }}
    .home-general-notice {{ margin: 1rem 0 1.25rem; padding: 0.85rem 1rem; border: 1px solid #dce4ed; border-radius: 6px; background: #f8fafc; }}
    section {{ padding: 1rem 1.25rem 2.5rem; max-width: 980px; }}
    .meta {{ color: #505a67; }}
    .dramatic-content {{ min-width: 0; max-width: 980px; }}
    .dramatic-anchor {{ display: block; height: 0; margin: 0; padding: 0; }}
    .branding {{ margin-top: 0.65rem; display: flex; gap: 0.65rem; align-items: center; flex-wrap: wrap; }}
    .branding img {{ max-height: 54px; width: auto; border: 1px solid #dfe4eb; background: #fff; padding: 0.2rem; border-radius: 4px; }}

    .notice-title-block {{ margin: 0.2rem 0 1rem; padding-bottom: 0.7rem; border-bottom: 1px solid #dde3ea; }}
    .notice-title-block h2 {{ margin: 0 0 0.4rem; }}
    .notice-subtitle {{ margin: 0.1rem 0 0.4rem; color: #4e6177; font-style: italic; }}
    .notice-byline {{ margin: 0; color: #3f4d5d; }}

    .notice-meta {{ margin: 1rem 0 1.2rem; padding: 0.85rem 1rem; background: #f8fafc; border: 1px solid #dce4ed; border-radius: 6px; }}
    .notice-meta dl {{ margin: 0; display: grid; grid-template-columns: 180px 1fr; gap: 0.35rem 0.9rem; }}
    .notice-meta dt {{ font-weight: 600; color: #304257; }}
    .notice-meta dd {{ margin: 0; color: #2e3946; }}

    .notice-front {{ margin: 1rem 0 1.2rem; color: #435365; }}

    .notice-toc {{ margin: 1.2rem 0 1.8rem; padding: 0.9rem 1rem; border: 1px solid #dbe2eb; border-radius: 6px; background: #fcfdff; }}
    .notice-toc h3 {{ margin: 0 0 0.6rem; }}
    .notice-toc ul {{ margin: 0.25rem 0 0.3rem; padding-left: 1.2rem; }}
    .notice-toc li {{ margin: 0.22rem 0; }}
    .toc-label {{ display: inline-block; min-width: 3.9rem; margin-right: 0.35rem; color: #5d6c80; font-size: 0.86rem; text-transform: uppercase; letter-spacing: 0.03em; }}

    .notice-section {{ margin: 1.8rem 0; }}
    .notice-group {{ margin: 2rem 0; padding: 0.7rem 0.9rem 0.8rem; border-left: 4px solid #8ca7c7; background: #f8fbff; }}
    .notice-included-document {{ margin: 1.2rem 0 1.6rem; padding: 0.95rem 1rem; border: 1px solid #d7dfea; border-radius: 6px; background: #ffffff; }}
    .notice-included-document .doc-meta {{ margin: 0.35rem 0 0.8rem; color: #4c5a6b; font-size: 0.93rem; }}
    .notice-section h3, .notice-section h4, .notice-section h5 {{ margin: 0 0 0.65rem; line-height: 1.28; }}
    .notice-section p {{ margin: 0.6rem 0; }}

    .note-ref a {{ text-decoration: none; }}
    .notice-notes {{ margin-top: 2.4rem; padding-top: 1rem; border-top: 1px solid #dde3ea; }}
    .notice-notes h3 {{ margin-top: 0; }}
    .notice-notes ol {{ padding-left: 1.4rem; }}
    .notice-notes li {{ margin: 0.4rem 0; }}
    .note-backlink {{ margin-left: 0.45rem; text-decoration: none; }}

    @media (prefers-reduced-motion: reduce) {{
      html {{ scroll-behavior: auto; }}
    }}

    @media (min-width: 901px) {{
      nav {{
        position: sticky;
        top: 1rem;
        align-self: start;
        max-height: calc(100vh - 2rem);
        overflow: auto;
      }}
    }}

    @media (max-width: 900px) {{
      main {{ grid-template-columns: 1fr; }}
      nav {{
        position: static;
        max-height: none;
        overflow: visible;
        border-right: none;
        border-bottom: 1px solid #eceef1;
      }}
      .notice-meta dl {{ grid-template-columns: 1fr; }}
      .notice-meta dt {{ margin-top: 0.25rem; }}
      .home-overview dl {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(manifest.config.site_title)}</h1>
    <p>{html.escape(manifest.config.site_subtitle)}</p>
    {_branding_html(manifest, current_href)}
  </header>
  <main>
    <nav aria-label=\"Navigation principale\">{_nav_html(manifest, current_href=current_href)}</nav>
    <section>{content_html}</section>
  </main>
</body>
</html>
"""

def _class_tokens(node: etree._Element) -> set[str]:
    class_attr = node.get("class") or ""
    return {token for token in class_attr.split() if token}


def _has_class(node: etree._Element, token: str) -> bool:
    return token in _class_tokens(node)


def _collect_title_blocks(
    body: etree._Element,
    *,
    base_token: str,
    wrapper_token: str,
) -> list[etree._Element]:
    blocks: list[etree._Element] = []
    for node in body.xpath(".//div[@class]"):
        if not isinstance(node, etree._Element):
            continue
        if _has_class(node, wrapper_token):
            blocks.append(node)
            continue
        if not _has_class(node, base_token):
            continue

        wrapped = False
        for ancestor in node.iterancestors(tag="div"):
            if isinstance(ancestor, etree._Element) and _has_class(ancestor, wrapper_token):
                wrapped = True
                break
        if wrapped:
            continue
        blocks.append(node)
    return blocks


def _play_navigation_for(manifest: SiteManifest, play: PlayEntry) -> PlayNavigation:
    by_slug = index_play_navigation(manifest.play_navigation)
    existing = by_slug.get(play.slug)
    if existing is not None:
        return existing
    try:
        return extract_play_navigation(play)
    except ValueError:
        return PlayNavigation(play_slug=play.slug, play_title=play.title, acts=())


def _ensure_anchor_id(body: etree._Element, target: etree._Element | None, desired_id: str) -> None:
    if target is not None:
        existing_id = (target.get("id") or "").strip()
        if existing_id == desired_id:
            return
        if not existing_id:
            target.set("id", desired_id)
            return
        parent = target.getparent()
        anchor = etree.Element("div")
        anchor.set("id", desired_id)
        anchor.set("class", "dramatic-anchor")
        if parent is None:
            body.insert(0, anchor)
        else:
            parent.insert(parent.index(target), anchor)
        return

    anchor = etree.Element("div")
    anchor.set("id", desired_id)
    anchor.set("class", "dramatic-anchor")
    body.insert(0, anchor)


def _inject_play_anchors(body: etree._Element, play_navigation: PlayNavigation) -> None:
    act_headers = _collect_title_blocks(body, base_token="acte-titre", wrapper_token="acte-titre-sans-variation")
    scene_headers = _collect_title_blocks(body, base_token="scene-titre", wrapper_token="scene-titre-sans-variation")
    speakers = body.xpath(".//div[contains(@class, 'locuteur')]")
    acts = play_navigation.acts
    for index, act in enumerate(acts):
        target: etree._Element | None = None
        if index < len(act_headers):
            target = act_headers[index]
        elif act.start_speech_index < len(speakers):
            target = speakers[act.start_speech_index]
        elif len(body):
            target = body[0]
        _ensure_anchor_id(body, target, act.anchor_id)

    scene_index = 0
    for act in acts:
        for scene in act.scenes:
            target = None
            if scene_index < len(scene_headers):
                target = scene_headers[scene_index]
            elif scene.start_speech_index < len(speakers):
                target = speakers[scene.start_speech_index]
            elif len(body):
                target = body[0]
            _ensure_anchor_id(body, target, scene.anchor_id)
            scene_index += 1


def _dramatic_assets_from_export_doc(export_doc: etree._Element) -> str:
    chunks: list[str] = []
    for node in export_doc.xpath("/html/head/link | /html/head/style"):
        tag = etree.QName(node).localname.lower()
        if tag == "link":
            rel = (node.get("rel") or "").lower()
            if "stylesheet" not in rel:
                continue
            chunks.append(etree.tostring(node, encoding="unicode", method="html"))
            continue
        css_text = "".join(node.itertext())
        # Skip export-shell layout rules (container/menu/footer) but keep dramatic engine CSS.
        if "#container" in css_text and "#menu-lateral" in css_text:
            continue
        css_text = re.sub(r"(?<![-\w])html(?=\s*\{)", ".dramatic-content", css_text)
        css_text = re.sub(r"(?<![-\w])body(?=\s*\{)", ".dramatic-content", css_text)
        chunks.append(f"<style>{css_text}</style>")
    return "".join(chunks)


def _play_reading_html(play: PlayEntry, play_navigation: PlayNavigation) -> tuple[str, str]:
    try:
        parser = etree.XMLParser(recover=False, remove_blank_text=False)
        tei_tree = etree.parse(str(play.source_path), parser)
    except (OSError, etree.XMLSyntaxError):
        return '<article class="dramatic-content"></article>', ""

    tei_xml = etree.tostring(tei_tree.getroot(), encoding="unicode")
    export_html = render_html_export_from_tei(
        tei_xml,
        options=HtmlExportOptions(
            document_title=play.title,
            include_menu=False,
            include_header=False,
            include_footer=False,
        ),
    )
    doc = lxml_html.document_fromstring(export_html)
    asset_html = _dramatic_assets_from_export_doc(doc)
    sections = doc.xpath("//section[@id='contenu-editorial']")
    if not sections:
        return '<article class="dramatic-content"></article>', asset_html

    editorial = sections[0]
    existing_class = (editorial.get("class") or "").strip()
    class_parts = [part for part in existing_class.split() if part]
    if "dramatic-content" not in class_parts:
        class_parts.append("dramatic-content")
    editorial.set("class", " ".join(class_parts))
    _inject_play_anchors(editorial, play_navigation)
    dramatic_html = etree.tostring(editorial, encoding="unicode", method="html")
    return dramatic_html, asset_html


def _play_nav_hash_sync_script() -> str:
    return """<script>
(() => {
  function findActDetailsForLink(link) {
    const actBranch = link.closest('li.nav-item.nav-kind-act.nav-branch');
    if (!actBranch) return null;
    return actBranch.querySelector(':scope > details.nav-details');
  }

  function closeSiblingActDetails(targetDetails) {
    const parentList = targetDetails.closest('ul');
    if (!parentList) return;
    parentList.querySelectorAll(':scope > li.nav-item.nav-kind-act.nav-branch > details.nav-details').forEach((details) => {
      details.open = details === targetDetails;
    });
  }

  function openParentDetails(link) {
    let details = link.closest('details.nav-details');
    while (details) {
      details.open = true;
      details = details.parentElement ? details.parentElement.closest('details.nav-details') : null;
    }
  }

  function closeAllActDetails(navRoot) {
    navRoot.querySelectorAll('li.nav-item.nav-kind-act.nav-branch > details.nav-details').forEach((details) => {
      details.open = false;
    });
  }

  function syncFromHash() {
    const navRoot = document.querySelector('main nav[aria-label="Navigation principale"]');
    if (!navRoot) return;
    const hash = window.location.hash || '';
    if (!hash) {
      closeAllActDetails(navRoot);
      return;
    }
    const escaped = (window.CSS && typeof window.CSS.escape === 'function') ? window.CSS.escape(hash) : hash.replace(/"/g, '\\"');
    const link = navRoot.querySelector('a[href$="' + escaped + '"]');
    if (!link) return;
    const actDetails = findActDetailsForLink(link);
    if (actDetails) {
      closeSiblingActDetails(actDetails);
      actDetails.open = true;
    }
    openParentDetails(link);
  }

  window.addEventListener('hashchange', syncFromHash);
  window.addEventListener('DOMContentLoaded', syncFromHash);
})();
</script>"""


def _homepage_sections(manifest: SiteManifest) -> tuple[HomePageSection, ...]:
    if manifest.config.homepage_sections:
        return manifest.config.homepage_sections
    if manifest.config.homepage_intro:
        return (HomePageSection(title="Presentation", paragraphs=(manifest.config.homepage_intro,)),)
    return ()


def _render_home_overview(manifest: SiteManifest) -> str:
    identity_rows: list[tuple[str, str]] = []
    if manifest.config.editor:
        identity_rows.append(("Responsable editorial", html.escape(manifest.config.editor)))
    if manifest.config.credits:
        identity_rows.append(("Soutiens et credits", html.escape(manifest.config.credits)))

    rows_html = ""
    if identity_rows:
        rows = "".join(f"<dt>{label}</dt><dd>{value}</dd>" for label, value in identity_rows)
        rows_html = f"<dl>{rows}</dl>"

    project_html = (
        f'<p class="home-project">{html.escape(manifest.config.project_name)}</p>'
        if manifest.config.project_name
        else ""
    )
    return f'<header class="home-overview"><h2>Accueil</h2>{project_html}{rows_html}</header>'


def _render_home_editorial_sections(manifest: SiteManifest) -> str:
    blocks: list[str] = []
    for section in _homepage_sections(manifest):
        paragraphs = "".join(f"<p>{html.escape(paragraph)}</p>" for paragraph in section.paragraphs)
        blocks.append(
            f'<article class="home-editorial-section"><h3>{html.escape(section.title)}</h3>{paragraphs}</article>'
        )
    return "".join(blocks)


def _render_home_play_list(manifest: SiteManifest) -> str:
    if not manifest.plays:
        return '<section class="home-plays" id="pieces"><h3>Pièces</h3><p class="meta">Aucune piece detectee.</p></section>'

    items = [f"<li><strong>{html.escape(play.title)}</strong></li>" for play in manifest.plays]
    return f'<section class="home-plays" id="pieces"><h3>Pièces</h3><ul class="home-play-list">{"".join(items)}</ul></section>'


def _render_home_general_notice(manifest: SiteManifest) -> str:
    if manifest.general_notice_slug is None:
        return ""
    for notice in manifest.notices:
        if notice.slug == manifest.general_notice_slug:
            return (
                f'<section class="home-general-notice">'
                f"<h3>Introduction générale</h3>"
                f'<p><a href="{html.escape(f"notices/{notice.slug}.html", quote=True)}">'
                f"{html.escape(notice.title)}</a></p>"
                f"</section>"
            )
    return ""


def render_home_page(manifest: SiteManifest) -> str:
    blocks: list[str] = [
        _render_home_overview(manifest),
        _render_home_editorial_sections(manifest),
        _render_home_general_notice(manifest),
        _render_home_play_list(manifest),
    ]
    content = "".join(blocks)
    return _layout(manifest, page_title=manifest.config.site_title, current_href="index.html", content_html=content)


def render_play_page(manifest: SiteManifest, play: PlayEntry) -> str:
    lines = [f"<h2>{html.escape(play.title)}</h2>"]
    if manifest.config.include_metadata:
        if play.author:
            lines.append(f'<p class="meta">Auteur: {html.escape(play.author)}</p>')
        lines.append(f'<p class="meta">Type: {html.escape(play.document_type)}</p>')
    if manifest.config.show_xml_download and play.xml_download_relpath:
        lines.append(
            f'<p><a href="../{html.escape(play.xml_download_relpath, quote=True)}" download>Telecharger le XML</a></p>'
        )
    if manifest.config.credits:
        lines.append(f'<p class="meta">{html.escape(manifest.config.credits)}</p>')

    play_navigation = _play_navigation_for(manifest, play)
    dramatic_html, dramatic_assets = _play_reading_html(play, play_navigation)
    lines.append(dramatic_html)
    head_extras = f"{dramatic_assets}{_play_nav_hash_sync_script()}"

    return _layout(
        manifest,
        page_title=play.title,
        current_href=f"plays/{play.slug}.html",
        content_html="".join(lines),
        head_extra_html=head_extras,
    )


def _toc_label(section: NoticeSection) -> str:
    if section.node_kind == "group":
        return "Part"
    if section.node_kind == "included_document":
        return "Doc"
    return "Sec"


def _render_toc_from_sections(sections: tuple[NoticeSection, ...]) -> str:
    if not sections:
        return ""
    chunks: list[str] = ["<ul>"]
    for section in sections:
        chunks.append(
            f'<li class="toc-item toc-kind-{html.escape(section.node_kind, quote=True)}">'
            f'<span class="toc-label">{_toc_label(section)}</span>'
            f'<a href="#{html.escape(section.section_id, quote=True)}">{html.escape(section.title)}</a>'
            f'{_render_toc_from_sections(section.children)}</li>'
        )
    chunks.append("</ul>")
    return "".join(chunks)


def _heading_for_level(level: int) -> str:
    if level <= 1:
        return "h3"
    if level == 2:
        return "h4"
    return "h5"


def _decorate_note_refs(paragraph_html: str, ref_counts: dict[str, int], first_refs: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        note_id = match.group(1)
        label = match.group(2)
        count = ref_counts.get(note_id, 0) + 1
        ref_counts[note_id] = count
        ref_id = f"note-ref-{note_id}-{count}"
        if note_id not in first_refs:
            first_refs[note_id] = ref_id
        return (
            f'<sup id="{html.escape(ref_id, quote=True)}" class="note-ref">'
            f'<a href="#note-{html.escape(note_id, quote=True)}">[{html.escape(label)}]</a></sup>'
        )

    return NOTE_REF_PATTERN.sub(repl, paragraph_html)


def _render_notice_section(
    section: NoticeSection,
    *,
    ref_counts: dict[str, int],
    first_refs: dict[str, str],
) -> str:
    heading = _heading_for_level(section.level)
    if section.node_kind == "group":
        css = "notice-section notice-group"
        heading_tag = "h3" if section.level <= 1 else "h4"
    elif section.node_kind == "included_document":
        css = "notice-section notice-included-document"
        heading_tag = "h4" if section.level <= 2 else "h5"
    else:
        css = f"notice-section level-{section.level}"
        heading_tag = heading

    chunks: list[str] = [f'<article class="{css}" id="{html.escape(section.section_id, quote=True)}">']
    chunks.append(f'<{heading_tag}>{html.escape(section.title)}</{heading_tag}>')

    if section.node_kind == "included_document":
        meta_bits: list[str] = []
        if section.subtitle:
            meta_bits.append(html.escape(section.subtitle))
        if section.authors:
            meta_bits.append(f"auteur(s): {html.escape(', '.join(section.authors))}")
        if section.text_type:
            meta_bits.append(f"type: {html.escape(section.text_type)}")
        if meta_bits:
            chunks.append(f'<p class="doc-meta">{" | ".join(meta_bits)}</p>')

    chunks.extend(_decorate_note_refs(p, ref_counts, first_refs) for p in section.paragraphs)

    if section.items:
        chunks.append("<ul>")
        chunks.extend(f"<li>{item}</li>" for item in section.items)
        chunks.append("</ul>")

    for child in section.children:
        chunks.append(_render_notice_section(child, ref_counts=ref_counts, first_refs=first_refs))

    chunks.append("</article>")
    return "".join(chunks)


def _render_title_block(notice: NoticeEntry, document: NoticeDocument) -> str:
    lines: list[str] = ["<header class=\"notice-title-block\">", f"<h2>{html.escape(notice.title)}</h2>"]
    if notice.subtitle:
        lines.append(f'<p class="notice-subtitle">{html.escape(notice.subtitle)}</p>')
    if notice.authors:
        lines.append(f'<p class="notice-byline">{html.escape(", ".join(notice.authors))}</p>')
    lines.append("</header>")
    return "".join(lines)


def _render_metadata_block(notice: NoticeEntry, document: NoticeDocument) -> str:
    rows: list[tuple[str, str]] = []
    if notice.authors:
        rows.append(("Auteur(s)", html.escape(", ".join(notice.authors))))
    rows.append(("Type de texte", html.escape(document.text_type)))
    rows.append(("Modele", html.escape(document.notice_kind)))
    if document.related_play_slug:
        rows.append(("Pièce associée", html.escape(document.related_play_slug)))
    if document.notice_kind == "master_volume" and document.included_documents:
        rows.append(("Documents inclus", str(len(document.included_documents))))
    if notice.xml_download_relpath:
        rows.append(
            (
                "XML source",
                f'<a href="../{html.escape(notice.xml_download_relpath, quote=True)}" download>Telecharger le XML</a>',
            )
        )

    if not rows:
        return ""

    chunks: list[str] = ["<section class=\"notice-meta\" aria-label=\"Metadonnees\"><dl>"]
    for label, value in rows:
        chunks.append(f"<dt>{label}</dt><dd>{value}</dd>")
    chunks.append("</dl></section>")
    return "".join(chunks)


def _render_notice_document(manifest: SiteManifest, notice: NoticeEntry, document: NoticeDocument) -> str:
    ref_counts: dict[str, int] = {}
    first_refs: dict[str, str] = {}

    lines: list[str] = [_render_title_block(notice, document), _render_metadata_block(notice, document)]
    if document.front_title_page:
        lines.append("<div class=\"notice-front\">")
        lines.extend(f"<p>{html.escape(item)}</p>" for item in document.front_title_page)
        lines.append("</div>")

    if document.sections:
        lines.append('<nav class="notice-toc" aria-label="Sommaire de la notice"><h3>Sommaire</h3>')
        lines.append(_render_toc_from_sections(document.sections))
        lines.append("</nav>")

    if document.sections:
        lines.extend(
            _render_notice_section(section, ref_counts=ref_counts, first_refs=first_refs)
            for section in document.sections
        )
    else:
        lines.append('<p class="meta">Aucune section textuelle detectee.</p>')

    if document.notes:
        lines.append('<section class="notice-notes" aria-label="Notes de la notice"><h3>Notes</h3><ol>')
        for note in document.notes:
            backlink = ""
            first_ref = first_refs.get(note.note_id)
            if first_ref:
                backlink = f' <a class="note-backlink" href="#{html.escape(first_ref, quote=True)}" aria-label="Retour a l\'appel de note">↩</a>'
            lines.append(
                f'<li id="note-{html.escape(note.note_id, quote=True)}"><strong>[{html.escape(note.label)}]</strong> {html.escape(note.text)}{backlink}</li>'
            )
        lines.append("</ol></section>")

    if document.include_warnings:
        lines.append('<section class="notice-warnings"><h3>xi:include</h3><ul>')
        lines.extend(f"<li>{html.escape(item)}</li>" for item in document.include_warnings)
        lines.append("</ul></section>")

    return "".join(lines)


def render_notice_page(manifest: SiteManifest, notice: NoticeEntry) -> str:
    if notice.document is not None:
        content = _render_notice_document(manifest, notice, notice.document)
    else:
        content = (
            f'<h2>{html.escape(notice.title)}</h2>'
            '<p class="meta">Notice sans document structure.</p>'
        )
    return _layout(
        manifest,
        page_title=notice.title,
        current_href=f"notices/{notice.slug}.html",
        content_html=content,
    )
