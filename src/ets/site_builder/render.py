from __future__ import annotations

import html

from .models import NoticeEntry, PlayEntry, SiteManifest


def _nav_html(manifest: SiteManifest, current_href: str) -> str:
    items: list[str] = []
    for item in manifest.navigation:
        escaped_label = html.escape(item.label)
        escaped_href = html.escape(item.href, quote=True)
        current_attr = ' aria-current="page"' if item.href == current_href else ""
        items.append(f'<li><a href="{escaped_href}"{current_attr}>{escaped_label}</a></li>')
    return "<ul>" + "".join(items) + "</ul>"


def _layout(manifest: SiteManifest, *, page_title: str, current_href: str, content_html: str) -> str:
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(page_title)}</title>
  <style>
    body {{ font-family: Georgia, 'Times New Roman', serif; margin: 0; color: #1f2328; }}
    header {{ padding: 1rem 1.25rem; border-bottom: 1px solid #d5d7da; background: #f8f9fb; }}
    main {{ display: grid; grid-template-columns: 280px 1fr; gap: 1rem; min-height: 100vh; }}
    nav {{ border-right: 1px solid #eceef1; padding: 1rem 1.25rem; }}
    nav ul {{ margin: 0; padding-left: 1.1rem; }}
    nav li {{ margin: 0.4rem 0; }}
    section {{ padding: 1rem 1.25rem 2rem; }}
    .meta {{ color: #505a67; }}
    .placeholder {{ border-left: 4px solid #8ea3bf; padding: 0.75rem; background: #f5f8fc; }}
    @media (max-width: 900px) {{
      main {{ grid-template-columns: 1fr; }}
      nav {{ border-right: none; border-bottom: 1px solid #eceef1; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(manifest.config.site_title)}</h1>
    <p>{html.escape(manifest.config.site_subtitle)}</p>
  </header>
  <main>
    <nav aria-label="Navigation principale">{_nav_html(manifest, current_href=current_href)}</nav>
    <section>{content_html}</section>
  </main>
</body>
</html>
"""


def _notice_for_play(manifest: SiteManifest, play_slug: str) -> NoticeEntry | None:
    for notice in manifest.notices:
        if notice.related_play_slug == play_slug:
            return notice
    return None


def render_home_page(manifest: SiteManifest) -> str:
    play_items = "".join(
        f'<li><a href="{html.escape(f"plays/{play.slug}.html", quote=True)}">{html.escape(play.title)}</a></li>'
        for play in manifest.plays
    )
    notice_items = "".join(
        f'<li><a href="{html.escape(f"notices/{notice.slug}.html", quote=True)}">{html.escape(notice.title)}</a></li>'
        for notice in manifest.notices
    )
    notices_block = (
        f"<h3>Notices</h3><ul>{notice_items}</ul>"
        if manifest.config.publish_notices and manifest.notices
        else ""
    )
    content = (
        f"<h2>Accueil</h2>"
        f"<p>{html.escape(manifest.config.project_name)}</p>"
        f"<h3>Pièces</h3><ul>{play_items}</ul>"
        f"{notices_block}"
    )
    return _layout(manifest, page_title=manifest.config.site_title, current_href="index.html", content_html=content)


def render_play_page(manifest: SiteManifest, play: PlayEntry) -> str:
    lines = [f"<h2>{html.escape(play.title)}</h2>"]
    if manifest.config.include_metadata:
        if play.author:
            lines.append(f'<p class="meta">Auteur: {html.escape(play.author)}</p>')
        lines.append(f'<p class="meta">Type: {html.escape(play.document_type)}</p>')
    if play.main_divisions:
        division_items = "".join(f"<li>{html.escape(label)}</li>" for label in play.main_divisions)
        lines.append(f"<h3>Divisions repérées</h3><ul>{division_items}</ul>")
    if manifest.config.show_xml_download and play.xml_download_relpath:
        lines.append(
            f'<p><a href="../{html.escape(play.xml_download_relpath, quote=True)}" download>Télécharger le XML</a></p>'
        )
    notice = _notice_for_play(manifest, play.slug)
    if notice is not None:
        lines.append(
            f'<p><a href="../notices/{html.escape(notice.slug, quote=True)}.html">Lire la notice savante associée</a></p>'
        )
    if manifest.config.credits:
        lines.append(f'<p class="meta">{html.escape(manifest.config.credits)}</p>')
    return _layout(
        manifest,
        page_title=play.title,
        current_href=f"plays/{play.slug}.html",
        content_html="".join(lines),
    )


def render_notice_page(manifest: SiteManifest, notice: NoticeEntry) -> str:
    lines = [f"<h2>{html.escape(notice.title)}</h2>"]
    if manifest.config.include_metadata:
        if notice.author:
            lines.append(f'<p class="meta">Auteur: {html.escape(notice.author)}</p>')
        lines.append(f'<p class="meta">Type: {html.escape(notice.document_type)}</p>')
    if manifest.config.show_xml_download and notice.xml_download_relpath:
        lines.append(
            f'<p><a href="../{html.escape(notice.xml_download_relpath, quote=True)}" download>Télécharger le XML</a></p>'
        )
    lines.append(
        "<div class=\"placeholder\">"
        "Rendu notice dédié prévu (voie distincte Métopes -> HTML). "
        "Ce jalon publie une page autonome prête à recevoir la transformation."
        "</div>"
    )
    return _layout(
        manifest,
        page_title=notice.title,
        current_href=f"notices/{notice.slug}.html",
        content_html="".join(lines),
    )
