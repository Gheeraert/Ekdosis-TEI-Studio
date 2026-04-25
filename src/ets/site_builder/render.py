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
    PlayFrontItemNavigation,
    PlayNavigation,
    SiteManifest,
)
from .play_navigation import index_play_navigation


NOTE_REF_PATTERN = re.compile(r'<sup class="note-ref"><a href="#note-([^"]+)">\[([^\]]+)\]</a></sup>')


SITE_CREDITS_TEXT = "Site réalisé avec TEI Studio dans le cadre de la Chaire d'Excellence en Edition numérique. 2026"
SITE_GITHUB_URL = "https://github.com/Gheeraert/Ekdosis-TEI-Studio"
SITE_GITHUB_LABEL = "GitHub du projet"
SITE_PURH_URL = "https://purh.univ-rouen.fr"
SITE_PURH_LABEL = "PURH"
SITE_CHAIR_URL = "https://ceen.hypotheses.org"
SITE_CHAIR_LABEL = "Site de la chaire"
AFFILIATION_BANNER_ALT = "Bannière d'affiliation de la Chaire d'Excellence en Edition numérique, de la Région Normandie, de l'Université de Rouen Normandie et des PURH"
AFFILIATION_BANNER_FILENAME = "banniere_affiliation.png"


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



def _affiliation_banner_src(current_href: str) -> str:
    return f"{_asset_prefix(current_href)}assets/logos/{AFFILIATION_BANNER_FILENAME}"



def _site_sidebar_html(current_href: str) -> str:
    return (
        '<section class="site-project-meta" aria-label="A propos du site">'
        '<h2>À propos du site</h2>'
        f'<p>{html.escape(SITE_CREDITS_TEXT)}</p>'
        '<p class="site-project-links">'
        f'<a href="{html.escape(SITE_PURH_URL, quote=True)}" target="_blank" rel="noopener noreferrer">'
        f'{html.escape(SITE_PURH_LABEL)}</a><br>'
        f'<a href="{html.escape(SITE_CHAIR_URL, quote=True)}" target="_blank" rel="noopener noreferrer">'
        f'{html.escape(SITE_CHAIR_LABEL)}</a><br>'
        f'<a href="{html.escape(SITE_GITHUB_URL, quote=True)}" target="_blank" rel="noopener noreferrer">'
        f'{html.escape(SITE_GITHUB_LABEL)}</a>'
        '</p>'
        f'<a class="site-project-banner-link" href="{html.escape(SITE_CHAIR_URL, quote=True)}" target="_blank" rel="noopener noreferrer">'
        f'<img class="site-project-banner" src="{html.escape(_affiliation_banner_src(current_href), quote=True)}" '
        f'alt="{html.escape(AFFILIATION_BANNER_ALT)}" loading="lazy"></a>'
        "</section>"
    )


def _site_footer_html(current_href: str) -> str:
    return (
        '<footer class="site-footer">'
        '<div class="site-footer-inner">'
        f'<a class="site-footer-logo-link" href="{html.escape(SITE_CHAIR_URL, quote=True)}" target="_blank" rel="noopener noreferrer">'
        f'<img class="site-footer-logo" src="{html.escape(_affiliation_banner_src(current_href), quote=True)}" '
        f'alt="{html.escape(AFFILIATION_BANNER_ALT)}" loading="lazy"></a>'
        '<div class="site-footer-text">'
        f'<p>{html.escape(SITE_CREDITS_TEXT)}</p>'
        '<p class="site-footer-links">'
        f'<a href="{html.escape(SITE_PURH_URL, quote=True)}" target="_blank" rel="noopener noreferrer">'
        f'{html.escape(SITE_PURH_LABEL)}</a> · '
        f'<a href="{html.escape(SITE_CHAIR_URL, quote=True)}" target="_blank" rel="noopener noreferrer">'
        f'{html.escape(SITE_CHAIR_LABEL)}</a> · '
        f'<a href="{html.escape(SITE_GITHUB_URL, quote=True)}" target="_blank" rel="noopener noreferrer">'
        f'{html.escape(SITE_GITHUB_LABEL)}</a>'
        '</p>'
        '</div>'
        '</div>'
        '</footer>'
    )


def _layout(
    manifest: SiteManifest,
    *,
    page_title: str,
    current_href: str,
    content_html: str,
    head_extra_html: str = "",
    section_class: str = "content-shell",
) -> str:
    return f"""<!doctype html>
<html lang=\"fr\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{html.escape(page_title)}</title>
  {head_extra_html}
  <script>
    (() => {{
      const themeStorageKey = "ets-theme";
      const fontStorageKey = "ets-font-scale";
      const minFontScale = 90;
      const maxFontScale = 200;
      const defaultFontScale = 100;
      const root = document.documentElement;
      const savedTheme = window.localStorage.getItem(themeStorageKey);
      const parsedFontScale = Number.parseInt(window.localStorage.getItem(fontStorageKey) || "", 10);
      const initialFontScale = Number.isFinite(parsedFontScale)
        ? Math.min(maxFontScale, Math.max(minFontScale, parsedFontScale))
        : defaultFontScale;

      root.style.fontSize = `${{initialFontScale}}%`;

      if (savedTheme === "light" || savedTheme === "dark") {{
        root.dataset.theme = savedTheme;
        return;
      }}
      const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
      root.dataset.theme = prefersDark ? "dark" : "light";
    }})();
  </script>
  <style>
    :root {{
      color-scheme: light;
      --font-body: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Palatino, "Times New Roman", serif;
      --font-ui: "Avenir Next", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      --bg: #f5f1e8;
      --bg-panel: #fdfaf4;
      --bg-soft: #f3ece0;
      --ink: #2d2620;
      --ink-muted: #5d5249;
      --accent: #6d2f38;
      --accent-soft: #8a4a54;
      --line: #d8cbb7;
      --header-bg: #12100f;
      --header-ink: #f3ece0;
      --header-muted: #d6c8b3;
      --focus: #a8783a;
      --shadow-soft: 0 1px 0 rgba(46, 34, 24, 0.04);
      --site-header-offset: 96px;
    }}
    html[data-theme="dark"] {{
      color-scheme: dark;
      --bg: #181412;
      --bg-panel: #221c18;
      --bg-soft: #2b231e;
      --ink: #ede2cf;
      --ink-muted: #c8b79f;
      --accent: #c1878f;
      --accent-soft: #ddb0b6;
      --line: #4f4237;
      --header-bg: #0e0b0a;
      --header-ink: #f1e6d1;
      --header-muted: #cdbda6;
      --focus: #c99a59;
      --shadow-soft: 0 1px 0 rgba(0, 0, 0, 0.25);
    }}
    html {{
     font-size: 100%;
     scroll-behavior: smooth;
     scroll-padding-top: calc(var(--site-header-offset) + 1rem);
    }}
    body {{ margin: 0; background: var(--bg); color: var(--ink); line-height: 1.6; font-family: var(--font-body); }}
    a {{ color: var(--accent); text-underline-offset: 0.14em; }}
    a:hover {{ color: var(--accent-soft); }}
    a:focus-visible, button:focus-visible, summary:focus-visible {{
      outline: 2px solid var(--focus);
      outline-offset: 2px;
    }}
    .site-header {{
      position: sticky;
      top: 0;
      z-index: 1500;
      background: var(--header-bg);
      color: var(--header-ink);
      border-bottom: 1px solid #000;
    }}
    .site-header-inner {{
      max-width: 1320px;
      margin: 0 auto;
      padding: 1rem 1rem 0.85rem;
      display: grid;
      grid-template-columns: 250px 960px;
      justify-content: start;
      gap: 0.45rem 0.75rem;
      align-items: start;
    }}
    .site-header-title {{
      grid-column: 1;
      min-width: max-content;
    }}
    .site-header-branding {{
      grid-column: 2;
      justify-self: end;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 0.35rem;
      min-width: 0;
    }}
    .site-author {{
      margin: 0 0 0.2rem;
      color: var(--header-ink);
      font-family: var(--font-ui);
      font-size: 1.3rem;
      font-weight: 600;
      letter-spacing: 0.01em;
    }}

    .site-header h1 {{
      margin: 0;
      font-weight: 600;
      letter-spacing: 0.01em;
      font-size: clamp(1.8rem, 3vw, 2.35rem);
      white-space: nowrap;
    }}
    .header-controls {{
      display: flex;
      justify-content: flex-end;
      gap: 0.35rem;
      flex-wrap: wrap;
    }}
    .theme-toggle {{
      position: static;
      align-self: flex-end;
      border: 1px solid rgba(243, 236, 224, 0.32);
      background: var(--header-bg);
      color: var(--header-ink);
      font-family: var(--font-ui);
      font-size: 0.76rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      padding: 0.3rem 0.52rem;
      cursor: pointer;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.18);
    }}
    .theme-toggle:hover {{
      border-color: rgba(243, 236, 224, 0.6);
    }}
    .theme-toggle:disabled {{
      opacity: 0.45;
      cursor: default;
      box-shadow: none;
    }}
    main {{ display: grid; grid-template-columns: 250px minmax(0, 1fr); gap: 0.75rem; min-height: calc(100vh - 4.8rem); padding: 0.85rem 1rem 1.4rem; max-width: 1320px; margin: 0 auto; }}
    nav {{ border: 1px solid var(--line); background: var(--bg-soft); padding: 0.9rem 0.95rem; box-shadow: var(--shadow-soft); box-sizing: border-box; width: 100%; min-width: 0; align-self: start; }}
    nav ul {{ margin: 0; padding-left: 1.1rem; }}
    nav li {{ margin: 0.35rem 0; }}
    .site-nav {{ margin-bottom: 1rem; }}
    .site-nav.nested {{ margin-top: 0.35rem; }}
    .nav-item > a, .nav-summary a {{ color: var(--ink); text-decoration: none; }}
    .nav-item > a:hover, .nav-summary a:hover {{ color: var(--accent); text-decoration: underline; }}
    .nav-label {{ color: var(--ink); font-weight: 600; font-family: var(--font-ui); font-size: 0.92rem; letter-spacing: 0.02em; text-transform: uppercase; }}
    .nav-item.nav-kind-play_group .nav-label,
    .nav-item.nav-kind-play_group > a,
    .nav-item.nav-kind-play_group .nav-summary a {{
      text-transform: none;
      letter-spacing: 0;
      font-family: var(--font-body);
      font-weight: 700;
    }}
    .nav-summary {{ cursor: pointer; }}
    .nav-summary::marker {{ color: var(--ink-muted); }}
    .nav-summary a[aria-current="page"], .nav-item > a[aria-current="page"] {{ font-weight: 700; color: var(--accent); }}

    .home-overview {{ margin-bottom: 1.4rem; }}
    .home-overview h2 {{ margin-bottom: 0.45rem; }}
    .home-overview .home-project {{ margin: 0.25rem 0 0.55rem; color: var(--ink-muted); font-style: italic; }}
    .home-overview dl {{ margin: 0; display: grid; grid-template-columns: 180px 1fr; gap: 0.35rem 0.9rem; }}
    .home-overview dt {{ font-weight: 600; color: var(--ink-muted); }}
    .home-overview dd {{ margin: 0; color: var(--ink); }}
    .home-editorial-section {{ margin: 1.1rem 0 1.35rem; }}
    .home-editorial-section h3 {{ margin-bottom: 0.45rem; }}
    .home-editorial-section p {{ margin: 0.4rem 0; }}
    .home-plays {{ margin-top: 1.3rem; }}
    .home-play-list {{ margin: 0.45rem 0 0; padding-left: 1.15rem; }}
    .home-play-list li {{ margin: 0.45rem 0; }}
    .home-play-links {{ color: var(--ink-muted); font-size: 0.95rem; }}
    .home-general-notice {{ margin: 1rem 0 1.25rem; padding: 0.85rem 1rem; border: 1px solid var(--line); background: var(--bg-soft); }}
    .home-page-notice {{ margin: 1.15rem 0 1.6rem; }}
    .notice-layout {{ display: block; }}
    .notice-toc.notice-toc-aside {{
      margin: 0 0 1.1rem;
      padding: 0.65rem 0.8rem;
      background: color-mix(in oklab, var(--bg-soft) 72%, var(--bg-panel));
      border-color: color-mix(in oklab, var(--line) 82%, var(--accent) 18%);
    }}
    .notice-toc.notice-toc-aside h3 {{
      margin: 0 0 0.4rem;
      font-size: 0.95rem;
      letter-spacing: 0.01em;
      color: var(--ink-muted);
    }}
    .notice-content {{ min-width: 0; }}
    .content-shell {{ padding: 1rem 1.2rem 2.5rem; max-width: 960px; background: var(--bg-panel); border: 1px solid var(--line); box-shadow: var(--shadow-soft); min-width: 0; }}
    .content-shell [id] {{
      /* décalage de l'arrivée des ancres sinon masquées par bandeau */
      scroll-margin-top: calc(var(--site-header-offset) + 0.2rem);
    }}
    .content-shell-play {{
      padding: 0.55rem 0.1rem 2.5rem;
      max-width: 980px;
      background: transparent;
      border: none;
      box-shadow: none;
    }}
    .meta {{ color: var(--ink-muted); font-family: var(--font-ui); font-size: 0.94rem; }}
    .play-author {{
      margin: 0.1rem 0 0.2rem;
      font-family: var(--font-ui);
      font-size: 1.45rem;
      font-weight: 600;
      letter-spacing: 0.01em;
      color: var(--ink);
    }}

    .content-shell-play > h2 {{ margin: 0.05rem 0 0.6rem; }}
    .content-shell-play .meta {{ margin: 0.2rem 0 0.35rem; }}
    .dramatic-content {{
      min-width: 0;
      max-width: none;
      margin: 0;
      background: transparent;
      color: var(--ink);
      font-family: var(--font-body);
    }}
    .content-shell-play .dramatic-content {{
      --ets-speaker-offset: 11rem;
      --ets-heading-offset: 11rem;
      --ets-cast-offset: 9rem;
      --ets-stage-offset: 9rem;
      --ets-tirade-offset: 1rem;
      --ets-verse-offset: 5rem;
      --ets-verse-num-left: -4.5rem;
      --ets-verse-num-width: 4rem;
      --ets-verse-decale: 14rem;
    }}
    .content-shell-play .dramatic-content .acte-titre,
    .content-shell-play .dramatic-content .acte-titre-sans-variation,
    .content-shell-play .dramatic-content .scene-titre,
    .content-shell-play .dramatic-content .scene-titre-sans-variation {{
      width: auto;
      max-width: calc(100% - var(--ets-heading-offset));
      margin-left: var(--ets-heading-offset);
      margin-right: 0;
      margin-bottom: 1.05rem;
      padding: 0 0.2rem;
      text-align: left;
      white-space: normal;
      overflow-wrap: anywhere;
      box-sizing: border-box;
    }}
    .content-shell-play .dramatic-content .personnages {{
      width: auto;
      max-width: calc(100% - var(--ets-cast-offset));
      margin-left: var(--ets-cast-offset);
      margin-right: 0;
      margin-bottom: 1.05rem;
      padding: 0 0.2rem;
      text-align: left;
      white-space: normal;
      overflow-wrap: anywhere;
      box-sizing: border-box;
    }}
    .content-shell-play .dramatic-content .locuteur {{
      max-width: calc(100% - var(--ets-speaker-offset));
      margin-left: var(--ets-speaker-offset);
      margin-right: 0;
      margin-bottom: 0.45rem;
      padding-left: 0.2rem;
      padding-right: 0.2rem;
      text-align: left;
      white-space: normal;
      overflow-wrap: anywhere;
      box-sizing: border-box;
    }}
    .content-shell-play .dramatic-content .tirade {{
      margin-left: var(--ets-tirade-offset);
    }}
    .content-shell-play .dramatic-content .didascalie,
    .content-shell-play .dramatic-content .notes {{
      margin-left: var(--ets-stage-offset);
    }}
    .content-shell-play .dramatic-content .vers-container {{
      margin-left: var(--ets-verse-offset);
      margin-bottom: 0.35rem;
      padding-left: 0;
      line-height: 1.3;
    }}
    .content-shell-play .dramatic-content .num-vers {{
      left: var(--ets-verse-num-left);
      width: var(--ets-verse-num-width);
      text-align: right;
      color: var(--ink-muted);
      font-size: 0.82em;
    }}
    .content-shell-play .dramatic-content .vers-decale {{ margin-left: var(--ets-verse-decale); }}
    .content-shell-play .dramatic-content .notes {{
      margin-top: 1.8rem;
      padding-top: 0.75rem;
      border-top-color: var(--line);
    }}
    .content-shell-play .dramatic-content .note-call a {{ color: var(--accent); }}
    .content-shell-play .dramatic-content .note-call a:hover,
    .content-shell-play .dramatic-content .note-call a:focus {{ border-bottom-color: var(--accent); }}
    .content-shell-play .dramatic-content .didascalie,
    .content-shell-play .dramatic-content .didascalie em,
    .content-shell-play .dramatic-content .didas-implicites-label,
    .content-shell-play .dramatic-content .stage-implicite::after {{
     color: var(--ets-stage-ink);
}}
    .content-shell-play .dramatic-content {{
      --ets-tooltip-bg: var(--bg-panel);
      --ets-tooltip-ink: var(--ink);
      --ets-tooltip-border: var(--line);
      --ets-tooltip-shadow: 0 10px 24px rgba(46, 34, 24, 0.16);
      --ets-stage-ink: #6d6258;
    }}
    
    html[data-theme="dark"] .content-shell-play .dramatic-content {{
      --ets-tooltip-shadow: 0 12px 28px rgba(0, 0, 0, 0.42);
      --ets-stage-ink: #d8c8bb;
    }}
    
    .content-shell-play .dramatic-content .variation {{
      position: relative;
      border-bottom-color: color-mix(in oklab, var(--accent) 50%, var(--ink-muted));
    }}
    
    
    .content-shell-play .dramatic-content .variation::after {{
      background: var(--ets-tooltip-bg);
      color: var(--ets-tooltip-ink);
      border: 1px solid var(--ets-tooltip-border);
      box-shadow: var(--ets-tooltip-shadow);
      border-radius: 8px;
      padding: 0.55em 0.7em;
      line-height: 1.35;
      max-width: min(50rem, calc(100vw - 4rem));
      z-index: 1000;
      overflow-wrap: break-word;
      white-space: pre-line;
      pointer-events: none;
    }}
    
    .content-shell-play .dramatic-content .variation:hover::after {{
      display: block;
    }}

    .dramatis-personae-block {{
      margin: 0.15rem 0 1rem;
      padding: 0.75rem 0.9rem 0.8rem;
      border: 1px solid var(--line);
      background: var(--bg-soft);
    }}
    .dramatis-personae-block h3 {{
      margin: 0 0 0.45rem;
      font-family: var(--font-ui);
      letter-spacing: 0.02em;
      text-transform: uppercase;
      font-size: 0.92rem;
      color: var(--ink-muted);
    }}
    .dramatis-personae-block ul {{
      margin: 0;
      padding-left: 1.2rem;
    }}
    .dramatis-personae-block li {{
      margin: 0.2rem 0;
    }}

    .dramatic-anchor {{ display: block; height: 0; margin: 0; padding: 0; }}
    .branding {{
      margin-top: 0.15rem;
      display: flex;
      justify-content: flex-end;
      gap: 0.35rem 0.5rem;
      align-items: center;
      flex-wrap: wrap;
      max-width: 100%;
    }}
    .branding img {{
      display: block;
      max-height: 28px;
      max-width: 120px;
      width: auto;
      border: 1px solid rgba(243, 236, 224, 0.35);
      background: rgba(255, 255, 255, 0.94);
      padding: 0.1rem;
      box-sizing: border-box;
    }}

    .notice-title-block {{ margin: 0.2rem 0 1rem; padding-bottom: 0.7rem; border-bottom: 1px solid var(--line); }}
    .notice-title-block h2 {{ margin: 0 0 0.4rem; }}
    .notice-subtitle {{ margin: 0.1rem 0 0.4rem; color: var(--ink-muted); font-style: italic; }}
    .notice-byline {{ margin: 0; color: var(--ink-muted); }}

    .notice-meta {{ margin: 1rem 0 1.2rem; padding: 0.85rem 1rem; background: var(--bg-soft); border: 1px solid var(--line); }}
    .notice-meta dl {{ margin: 0; display: grid; grid-template-columns: 180px 1fr; gap: 0.35rem 0.9rem; }}
    .notice-meta dt {{ font-weight: 600; color: var(--ink-muted); }}
    .notice-meta dd {{ margin: 0; color: var(--ink); }}

    .notice-front {{ margin: 1rem 0 1.2rem; color: var(--ink-muted); }}

    .notice-toc {{ margin: 1.2rem 0 1.8rem; padding: 0.9rem 1rem; border: 1px solid var(--line); background: var(--bg-soft); }}
    .notice-toc h3 {{ margin: 0 0 0.6rem; }}
    .notice-toc ul {{ margin: 0.25rem 0 0.3rem; padding-left: 1.2rem; }}
    .notice-toc li {{ margin: 0.22rem 0; }}
    .toc-label {{ display: inline-block; min-width: 3.9rem; margin-right: 0.35rem; color: var(--ink-muted); font-size: 0.86rem; text-transform: uppercase; letter-spacing: 0.03em; font-family: var(--font-ui); }}

    .notice-section {{ margin: 1.8rem 0; }}
    .notice-group {{ margin: 2rem 0; padding: 0.7rem 0.9rem 0.8rem; border-left: 4px solid var(--accent); background: var(--bg-soft); }}
    .notice-included-document {{ margin: 1.2rem 0 1.6rem; padding: 0.95rem 1rem; border: 1px solid var(--line); background: var(--bg-panel); }}
    .notice-included-document .doc-meta {{ margin: 0.35rem 0 0.8rem; color: var(--ink-muted); font-size: 0.93rem; }}
    .notice-section h3, .notice-section h4, .notice-section h5 {{ margin: 0 0 0.65rem; line-height: 1.28; }}
    .notice-section p {{ margin: 0.6rem 0; }}

    .note-ref a {{ text-decoration: none; }}
    .notice-notes {{ margin-top: 2.4rem; padding-top: 1rem; border-top: 1px solid var(--line); }}
    .notice-notes h3 {{ margin-top: 0; }}
    .notice-notes ol {{ padding-left: 1.4rem; }}
    .notice-notes li {{ margin: 0.4rem 0; }}
    .note-backlink {{ margin-left: 0.45rem; text-decoration: none; }}


    .site-project-meta {{
      margin-top: 10rem;
      padding-top: 1rem;
      border-top: 1px solid var(--line);
    }}
    .site-project-meta h2 {{
      margin: 0 0 0.45rem;
      font-family: var(--font-ui);
      font-size: 0.95rem;
      letter-spacing: 0.01em;
      color: var(--ink-muted);
    }}
    .site-project-meta p {{
      margin: 0.45rem 0;
      font-size: 0.94rem;
      color: var(--ink);
    }}
    .site-project-meta a {{
      font-family: var(--font-ui);
      font-size: 0.92rem;
    }}
    .site-project-links {{
      line-height: 1.75;
    }}
    .site-project-banner {{
      display: block;
      width: 100%;
      max-width: 100%;
      height: auto;
      margin-top: 0.7rem;
      border: 1px solid var(--line);
      background: transparent;
      box-sizing: border-box;
      border: none;
    }}

    .site-footer {{
      max-width: 1320px;
      margin: 0 auto 1.2rem;
      padding: 0 1rem;
    }}
    .site-footer-inner {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      padding: 0.85rem 1rem;
      border: 1px solid var(--line);
      background: var(--bg-soft);
      box-shadow: var(--shadow-soft);
    }}
    .site-footer-logo {{
      display: block;
      width: min(280px, 38vw);
      max-width: 100%;
      height: auto;
      flex: 0 0 auto;
      border: 1px solid var(--line);
      background: transparent;
      box-sizing: border-box;
      border: none;
    }}
    .site-footer-text {{
      margin: 0;
      color: var(--ink);
      font-size: 0.95rem;
    }}
    .site-footer-text p {{
      margin: 0.2rem 0;
    }}
    .site-footer-links a {{
      font-family: var(--font-ui);
    }}
    .site-project-banner-link:focus-visible,
    .site-footer-logo-link:focus-visible {{
      outline: 2px solid var(--focus);
      outline-offset: 3px;
}}

    @media (prefers-reduced-motion: reduce) {{
      html {{ scroll-behavior: auto; }}
    }}

    @media (min-width: 901px) {{
      nav {{
        position: sticky;
        top: calc(var(--site-header-offset) + 0.75rem);
        align-self: start;
        max-height: calc(100vh - var(--site-header-offset) - 1.5rem);
        overflow: auto;
      }}
      .notice-layout {{
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(220px, 280px);
        gap: 1rem;
        align-items: start;
      }}
      .notice-layout .notice-toc.notice-toc-aside {{
        order: 2;
        position: sticky;
        top: 0.8rem;
        max-height: calc(100vh - 2.2rem);
        overflow: auto;
      }}
      .notice-layout .notice-content {{
        order: 1;
      }}
    }}

    @media (max-width: 900px) {{
      .site-header-inner {{
        grid-template-columns: 1fr;
        padding: 0.85rem 1rem 0.75rem;
      }}
      .site-header-title {{
        grid-column: 1;
        min-width: 0;
      }}
      .site-header-branding {{
        grid-column: 1;
        width: 100%;
        justify-self: stretch;
        align-items: flex-start;
        margin-top: 0.15rem;
      }}
      .branding {{
        justify-content: flex-start;
        gap: 0.3rem 0.45rem;
      }}
      .branding img {{
        max-height: 22px;
        max-width: 100px;
      }}
      .site-header h1 {{
        white-space: normal;
      }}
      main {{ grid-template-columns: 1fr; }}
      nav {{
        position: static;
        max-height: none;
        overflow: visible;
        border-right: 1px solid var(--line);
      }}
      .content-shell {{ padding: 1rem; }}
      .content-shell-play {{ padding: 0.45rem 0 2rem; }}
      .content-shell-play .dramatic-content {{
        --ets-speaker-offset: 2.6rem;
        --ets-heading-offset: 2.35rem;
        --ets-cast-offset: 2.3rem;
        --ets-stage-offset: 2.25rem;
        --ets-tirade-offset: 0.35rem;
        --ets-verse-offset: 2.55rem;
        --ets-verse-num-left: -2.3rem;
        --ets-verse-num-width: 2.2rem;
        --ets-verse-decale: 1.3rem;
      }}
      .content-shell-play .dramatic-content .acte-titre,
      .content-shell-play .dramatic-content .acte-titre-sans-variation,
      .content-shell-play .dramatic-content .scene-titre,
      .content-shell-play .dramatic-content .scene-titre-sans-variation {{
        max-width: calc(100% - var(--ets-heading-offset));
        margin-left: var(--ets-heading-offset);
      }}
      .content-shell-play .dramatic-content .personnages {{
        max-width: calc(100% - var(--ets-cast-offset));
        margin-left: var(--ets-cast-offset);
      }}
      .notice-meta dl {{ grid-template-columns: 1fr; }}
      .notice-meta dt {{ margin-top: 0.25rem; }}
      .header-controls {{
        justify-content: flex-start;
      }}
      .theme-toggle {{
        align-self: flex-start;
        font-size: 0.72rem;
        padding: 0.28rem 0.46rem;
      }}

      .site-footer-inner {{
        flex-direction: column;
        align-items: flex-start;
      }}
      .site-footer-logo {{
        width: min(100%, 340px);
      }}
      .home-overview dl {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header class="site-header">
    <div class="site-header-inner">
      <div class="site-header-title">
        <p class="site-author">{html.escape(manifest.config.site_subtitle)}</p>
        <h1>{html.escape(manifest.config.site_title)}</h1>
      </div>
      <div class="site-header-branding">
        <div class="header-controls">
          <button class="theme-toggle" type="button" data-font-decrease aria-label="Retrecir le texte">A−</button>
          <button class="theme-toggle" type="button" data-font-increase aria-label="Agrandir le texte">A+</button>
          <button class="theme-toggle" type="button" data-theme-toggle aria-label="Basculer le theme">Mode sombre</button>
        </div>
        {_branding_html(manifest, current_href)}
      </div>
    </div>
  </header>
  <main>
    <nav aria-label=\"Navigation principale\">{_nav_html(manifest, current_href=current_href)}{_site_sidebar_html(current_href)}</nav>
    <section class="{html.escape(section_class, quote=True)}">{content_html}</section>
  </main>
  {_site_footer_html(current_href)}
  <script>
    (() => {{
      const themeStorageKey = "ets-theme";
      const fontStorageKey = "ets-font-scale";
      const minFontScale = 90;
      const maxFontScale = 200;
      const defaultFontScale = 100;
      const stepFontScale = 5;
      const root = document.documentElement;
      const header = document.querySelector(".site-header");
      const themeButton = document.querySelector("[data-theme-toggle]");
      const decreaseButton = document.querySelector("[data-font-decrease]");
      const increaseButton = document.querySelector("[data-font-increase]");
      if (!themeButton && !decreaseButton && !increaseButton) return;

      function clampFontScale(value) {{
        return Math.min(maxFontScale, Math.max(minFontScale, value));
      }}

      function syncHeaderOffset() {{
        if (!header) return;
        const headerHeight = Math.ceil(header.getBoundingClientRect().height);
        root.style.setProperty("--site-header-offset", `${{headerHeight}}px`);
      }}

      function currentFontScale() {{
        const parsed = Number.parseInt(window.localStorage.getItem(fontStorageKey) || root.style.fontSize || "", 10);
        return Number.isFinite(parsed) ? clampFontScale(parsed) : defaultFontScale;
      }}

      function applyFontScale(value) {{
        const nextValue = clampFontScale(value);
        root.style.fontSize = `${{nextValue}}%`;
        window.localStorage.setItem(fontStorageKey, String(nextValue));
        syncHeaderOffset();
        refreshLabels(nextValue);
      }}

      function refreshLabels(fontScale) {{
        if (themeButton) {{
          themeButton.textContent = root.dataset.theme === "dark" ? "Mode clair" : "Mode sombre";
        }}
        if (decreaseButton) {{
          decreaseButton.disabled = fontScale <= minFontScale;
        }}
        if (increaseButton) {{
          increaseButton.disabled = fontScale >= maxFontScale;
        }}
      }}

      syncHeaderOffset();
      window.addEventListener("resize", syncHeaderOffset);
      window.addEventListener("load", syncHeaderOffset);

      if (themeButton) {{
        themeButton.addEventListener("click", () => {{
          root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
          window.localStorage.setItem(themeStorageKey, root.dataset.theme);
          syncHeaderOffset();
          refreshLabels(currentFontScale());
        }});
      }}

      if (decreaseButton) {{
        decreaseButton.addEventListener("click", () => {{
          applyFontScale(currentFontScale() - stepFontScale);
        }});
      }}

      if (increaseButton) {{
        increaseButton.addEventListener("click", () => {{
          applyFontScale(currentFontScale() + stepFontScale);
        }});
      }}

      refreshLabels(currentFontScale());
    }})();
  </script>
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
    return PlayNavigation(play_slug=play.slug, play_title=play.title)


def _front_item_by_kind(play_navigation: PlayNavigation, kind: str) -> PlayFrontItemNavigation | None:
    for item in play_navigation.front_items:
        if item.kind == kind:
            return item
    return None


def _render_dramatis_personae(play_navigation: PlayNavigation) -> str:
    if not play_navigation.dramatis_personae:
        return ""
    front_item = _front_item_by_kind(play_navigation, "dramatis_personae")
    if front_item is None or not front_item.anchor_id:
        return ""
    entries = "".join(f"<li>{html.escape(item)}</li>" for item in play_navigation.dramatis_personae)
    return (
        f'<section class="dramatis-personae-block" id="{html.escape(front_item.anchor_id, quote=True)}">'
        f"<h3>Personnages</h3>"
        f"<ul>{entries}</ul>"
        f"</section>"
    )


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


def _notice_by_slug(manifest: SiteManifest, slug: str) -> NoticeEntry | None:
    for notice in manifest.notices:
        if notice.slug == slug:
            return notice
    return None


def _render_home_page_notice(manifest: SiteManifest) -> str:
    slug = (manifest.config.home_page_notice_slug or "").strip()
    if not slug:
        return ""

    notice = _notice_by_slug(manifest, slug)
    if notice is None or notice.document is None:
        return ""

    return (
        '<section class="home-page-notice" id="home-notice">'
        + _render_notice_document(
            manifest,
            notice,
            notice.document,
            display_mode="editorial_light",
            download_href_prefix="",
            show_toc_labels=False,
        )
        + "</section>"
    )


def render_home_page(manifest: SiteManifest) -> str:
    if manifest.config.home_page_notice_slug:
        blocks = [_render_home_page_notice(manifest)]
    else:
        blocks = [
            _render_home_overview(manifest),
            _render_home_editorial_sections(manifest),
            _render_home_page_notice(manifest),
            _render_home_general_notice(manifest),
            _render_home_play_list(manifest),
        ]
    content = "".join(blocks)
    return _layout(manifest, page_title=manifest.config.site_title, current_href="index.html", content_html=content)


def render_play_page(manifest: SiteManifest, play: PlayEntry) -> str:
    lines: list[str] = []

    if play.author:
        lines.append(f'<p class="play-author">{html.escape(play.author)}</p>')

    lines.append(f"<h2>{html.escape(play.title)}</h2>")

    if manifest.config.include_metadata:
        lines.append(f'<p class="meta">Type: {html.escape(play.document_type)}</p>')
    if manifest.config.show_xml_download and play.xml_download_relpath:
        lines.append(
            f'<p><a href="../{html.escape(play.xml_download_relpath, quote=True)}" download>Telecharger le XML</a></p>'
        )
    if manifest.config.credits:
        lines.append(f'<p class="meta">{html.escape(manifest.config.credits)}</p>')

    play_navigation = _play_navigation_for(manifest, play)
    lines.append(_render_dramatis_personae(play_navigation))
    dramatic_html, dramatic_assets = _play_reading_html(play, play_navigation)
    lines.append(dramatic_html)
    head_extras = f"{dramatic_assets}{_play_nav_hash_sync_script()}"

    return _layout(
        manifest,
        page_title=play.title,
        current_href=f"plays/{play.slug}.html",
        content_html="".join(lines),
        head_extra_html=head_extras,
        section_class="content-shell content-shell-play",
    )


def _toc_label(section: NoticeSection) -> str:
    if section.node_kind == "group":
        return "Part"
    if section.node_kind == "included_document":
        return "Doc"
    return "Sec"


def _render_toc_from_sections(sections: tuple[NoticeSection, ...], *, show_labels: bool = True) -> str:
    if not sections:
        return ""
    chunks: list[str] = ["<ul>"]
    for section in sections:
        label_html = f'<span class="toc-label">{_toc_label(section)}</span>' if show_labels else ""
        chunks.append(
            f'<li class="toc-item toc-kind-{html.escape(section.node_kind, quote=True)}">'
            f"{label_html}"
            f'<a href="#{html.escape(section.section_id, quote=True)}">{html.escape(section.title)}</a>'
            f'{_render_toc_from_sections(section.children, show_labels=show_labels)}</li>'
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


def _render_metadata_block(
    notice: NoticeEntry,
    document: NoticeDocument,
    *,
    download_href_prefix: str = "../",
) -> str:
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
                f'<a href="{html.escape(download_href_prefix + notice.xml_download_relpath, quote=True)}" download>'
                f"Telecharger le XML</a>",
            )
        )

    if not rows:
        return ""

    chunks: list[str] = ["<section class=\"notice-meta\" aria-label=\"Metadonnees\"><dl>"]
    for label, value in rows:
        chunks.append(f"<dt>{label}</dt><dd>{value}</dd>")
    chunks.append("</dl></section>")
    return "".join(chunks)


def _render_notice_document(
    manifest: SiteManifest,
    notice: NoticeEntry,
    document: NoticeDocument,
    *,
    display_mode: str = "full",
    download_href_prefix: str = "../",
    show_toc_labels: bool = True,
) -> str:
    ref_counts: dict[str, int] = {}
    first_refs: dict[str, str] = {}
    is_editorial_light = display_mode == "editorial_light"

    lines: list[str] = []
    if not is_editorial_light:
        lines.append(_render_title_block(notice, document))
    if not is_editorial_light:
        lines.append(_render_metadata_block(notice, document, download_href_prefix=download_href_prefix))
    if document.front_title_page:
        front_class = "notice-front" if not is_editorial_light else "notice-front notice-front-light"
        lines.append(f'<div class="{front_class}">')
        lines.extend(f"<p>{html.escape(item)}</p>" for item in document.front_title_page)
        lines.append("</div>")

    if document.sections and is_editorial_light:
        lines.append('<div class="notice-layout">')
        lines.append('<nav class="notice-toc notice-toc-aside" aria-label="Sommaire de lecture"><h3>Sommaire</h3>')
        lines.append(_render_toc_from_sections(document.sections, show_labels=show_toc_labels))
        lines.append("</nav>")
        lines.append('<div class="notice-content">')
        lines.extend(
            _render_notice_section(section, ref_counts=ref_counts, first_refs=first_refs)
            for section in document.sections
        )
        lines.append("</div></div>")
    elif document.sections:
        lines.append('<nav class="notice-toc" aria-label="Sommaire de la notice"><h3>Sommaire</h3>')
        lines.append(_render_toc_from_sections(document.sections, show_labels=show_toc_labels))
        lines.append("</nav>")
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

    if document.include_warnings and not is_editorial_light:
        lines.append('<section class="notice-warnings"><h3>xi:include</h3><ul>')
        lines.extend(f"<li>{html.escape(item)}</li>" for item in document.include_warnings)
        lines.append("</ul></section>")

    return "".join(lines)


def render_notice_page(manifest: SiteManifest, notice: NoticeEntry) -> str:
    if notice.document is not None:
        content = (
            f'<h2 class="editorial-reading-title">{html.escape(notice.title)}</h2>'
            + _render_notice_document(
                manifest,
                notice,
                notice.document,
                display_mode="editorial_light",
                show_toc_labels=False,
            )
        )
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

