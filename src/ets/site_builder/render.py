from __future__ import annotations

import html

from .models import NoticeDocument, NoticeEntry, NoticeSection, NoticeTocEntry, PlayEntry, SiteManifest


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
<html lang=\"fr\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
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
    .notice-meta {{ margin: 1rem 0; padding: 0.75rem; background: #f8fafc; border-left: 4px solid #9aaeca; }}
    .notice-toc {{ margin: 1rem 0 1.5rem; padding: 0.75rem; border: 1px solid #e0e5eb; background: #fcfdff; }}
    .notice-toc ul {{ margin: 0.4rem 0 0; padding-left: 1.2rem; }}
    .notice-section {{ margin: 1.5rem 0; }}
    .notice-section h3, .notice-section h4, .notice-section h5 {{ margin-bottom: 0.6rem; }}
    .notice-notes {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #dde3ea; }}
    .notice-notes ol {{ padding-left: 1.4rem; }}
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
    <nav aria-label=\"Navigation principale\">{_nav_html(manifest, current_href=current_href)}</nav>
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


def _render_toc_entries(entries: tuple[NoticeTocEntry, ...]) -> str:
    if not entries:
        return ""
    blocks: list[str] = ["<ul>"]
    for entry in entries:
        blocks.append(
            f'<li><a href="#{html.escape(entry.entry_id, quote=True)}">{html.escape(entry.title)}</a>{_render_toc_entries(entry.children)}</li>'
        )
    blocks.append("</ul>")
    return "".join(blocks)


def _heading_for_level(level: int) -> str:
    if level <= 1:
        return "h3"
    if level == 2:
        return "h4"
    return "h5"


def _render_notice_section(section: NoticeSection) -> str:
    heading = _heading_for_level(section.level)
    chunks: list[str] = [
        f'<article class="notice-section level-{section.level}" id="{html.escape(section.section_id, quote=True)}">',
        f'<{heading}>{html.escape(section.title)}</{heading}>',
    ]
    chunks.extend(section.paragraphs)
    if section.items:
        chunks.append("<ul>")
        chunks.extend(f"<li>{item}</li>" for item in section.items)
        chunks.append("</ul>")
    for child in section.children:
        chunks.append(_render_notice_section(child))
    chunks.append("</article>")
    return "".join(chunks)


def _render_notice_document(notice: NoticeEntry, document: NoticeDocument) -> str:
    lines: list[str] = [f"<h2>{html.escape(notice.title)}</h2>"]
    if notice.subtitle:
        lines.append(f"<p class=\"meta\">{html.escape(notice.subtitle)}</p>")

    meta_lines: list[str] = []
    if notice.authors:
        meta_lines.append(f"<p><strong>Auteur(s):</strong> {html.escape(', '.join(notice.authors))}</p>")
    meta_lines.append(f"<p><strong>Type:</strong> {html.escape(document.text_type)}</p>")
    meta_lines.append(f"<p><strong>Modèle notice:</strong> {html.escape(document.notice_kind)}</p>")
    if document.related_play_slug:
        meta_lines.append(f"<p><strong>Pièce associée:</strong> {html.escape(document.related_play_slug)}</p>")
    if notice.xml_download_relpath:
        meta_lines.append(
            f'<p><a href="../{html.escape(notice.xml_download_relpath, quote=True)}" download>Télécharger le XML</a></p>'
        )
    lines.append(f'<div class="notice-meta">{"".join(meta_lines)}</div>')

    if document.front_title_page:
        lines.append("<div class=\"notice-front\">")
        lines.extend(f"<p>{html.escape(item)}</p>" for item in document.front_title_page)
        lines.append("</div>")

    if document.toc:
        lines.append("<div class=\"notice-toc\"><h3>Sommaire</h3>")
        lines.append(_render_toc_entries(document.toc))
        lines.append("</div>")

    if document.sections:
        lines.extend(_render_notice_section(section) for section in document.sections)
    else:
        lines.append("<p class=\"meta\">Aucune section textuelle détectée.</p>")

    if document.notes:
        lines.append("<section class=\"notice-notes\"><h3>Notes</h3><ol>")
        for note in document.notes:
            lines.append(
                f'<li id="note-{html.escape(note.note_id, quote=True)}"><strong>[{html.escape(note.label)}]</strong> {html.escape(note.text)}</li>'
            )
        lines.append("</ol></section>")

    if document.include_warnings:
        lines.append("<section class=\"notice-warnings\"><h3>Inclure (xi:include)</h3><ul>")
        lines.extend(f"<li>{html.escape(item)}</li>" for item in document.include_warnings)
        lines.append("</ul></section>")

    return "".join(lines)


def render_notice_page(manifest: SiteManifest, notice: NoticeEntry) -> str:
    if notice.document is not None:
        content = _render_notice_document(notice, notice.document)
    else:
        content = f"<h2>{html.escape(notice.title)}</h2><p class=\"meta\">Notice sans document structuré.</p>"
    return _layout(
        manifest,
        page_title=notice.title,
        current_href=f"notices/{notice.slug}.html",
        content_html=content,
    )
