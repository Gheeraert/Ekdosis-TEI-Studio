from __future__ import annotations

import html
import re

from .models import NoticeDocument, NoticeEntry, NoticeSection, PlayEntry, SiteManifest


NOTE_REF_PATTERN = re.compile(r'<sup class="note-ref"><a href="#note-([^"]+)">\[([^\]]+)\]</a></sup>')


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
    body {{ font-family: Georgia, 'Times New Roman', serif; margin: 0; color: #1f2328; line-height: 1.5; }}
    header {{ padding: 1rem 1.25rem; border-bottom: 1px solid #d5d7da; background: #f8f9fb; }}
    main {{ display: grid; grid-template-columns: 280px 1fr; gap: 1rem; min-height: 100vh; }}
    nav {{ border-right: 1px solid #eceef1; padding: 1rem 1.25rem; }}
    nav ul {{ margin: 0; padding-left: 1.1rem; }}
    nav li {{ margin: 0.4rem 0; }}
    section {{ padding: 1rem 1.25rem 2.5rem; max-width: 980px; }}
    .meta {{ color: #505a67; }}

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

    @media (max-width: 900px) {{
      main {{ grid-template-columns: 1fr; }}
      nav {{ border-right: none; border-bottom: 1px solid #eceef1; }}
      .notice-meta dl {{ grid-template-columns: 1fr; }}
      .notice-meta dt {{ margin-top: 0.25rem; }}
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
    intro_block = (
        f"<p>{html.escape(manifest.config.homepage_intro)}</p>"
        if manifest.config.homepage_intro
        else ""
    )
    content = (
        f"<h2>Accueil</h2>"
        f"<p>{html.escape(manifest.config.project_name)}</p>"
        f"{intro_block}"
        f"<h3>Pieces</h3><ul>{play_items}</ul>"
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
        lines.append(f"<h3>Divisions reperees</h3><ul>{division_items}</ul>")
    if manifest.config.show_xml_download and play.xml_download_relpath:
        lines.append(
            f'<p><a href="../{html.escape(play.xml_download_relpath, quote=True)}" download>Telecharger le XML</a></p>'
        )
    notice = _notice_for_play(manifest, play.slug)
    if notice is not None:
        lines.append(
            f'<p><a href="../notices/{html.escape(notice.slug, quote=True)}.html">Lire la notice savante associee</a></p>'
        )
    if manifest.config.credits:
        lines.append(f'<p class="meta">{html.escape(manifest.config.credits)}</p>')
    return _layout(
        manifest,
        page_title=play.title,
        current_href=f"plays/{play.slug}.html",
        content_html="".join(lines),
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
        rows.append(("Piece associee", html.escape(document.related_play_slug)))
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


def _render_notice_document(notice: NoticeEntry, document: NoticeDocument) -> str:
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
        content = _render_notice_document(notice, notice.document)
    else:
        content = f'<h2>{html.escape(notice.title)}</h2><p class="meta">Notice sans document structure.</p>'
    return _layout(
        manifest,
        page_title=notice.title,
        current_href=f"notices/{notice.slug}.html",
        content_html=content,
    )
