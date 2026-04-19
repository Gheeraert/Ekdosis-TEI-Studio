from __future__ import annotations

import html
import re
import unicodedata
from pathlib import Path

from lxml import etree

from .models import NoticeDocument, NoticeEntry, NoticeNote, NoticeSection, NoticeTocEntry, PlayEntry


XML_NS = "http://www.w3.org/XML/1998/namespace"
XI_NS = "http://www.w3.org/2001/XInclude"


class SiteBuilderExtractionError(ValueError):
    """Raised when an XML source cannot be extracted safely."""


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip())
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_only = ascii_only.lower()
    ascii_only = re.sub(r"[^a-z0-9]+", "-", ascii_only)
    ascii_only = ascii_only.strip("-")
    return ascii_only or "untitled"


def _first_text(tree: etree._ElementTree, expressions: tuple[str, ...]) -> str | None:
    for expr in expressions:
        values = tree.xpath(expr)
        if values is None:
            continue
        if isinstance(values, list):
            if not values:
                continue
            first = values[0]
        else:
            first = values
        if isinstance(first, etree._Element):
            text = " ".join(first.itertext()).strip()
        else:
            text = str(first).strip()
        if text:
            return text
    return None


def _collect_main_divisions(tree: etree._ElementTree) -> tuple[str, ...]:
    labels: list[str] = []
    for node in tree.xpath("//*[local-name()='text']/*[local-name()='body']//*[local-name()='div']"):
        div_type = (node.get("type") or "div").strip()
        div_n = (node.get("n") or "").strip()
        label = f"{div_type} {div_n}".strip()
        if label and label not in labels:
            labels.append(label)
    return tuple(labels)


def _has_text_body(tree: etree._ElementTree) -> bool:
    bodies = tree.xpath("//*[local-name()='text']/*[local-name()='body']")
    if not bodies:
        return False
    return bool(" ".join(bodies[0].itertext()).strip())


def _parse_tree(xml_path: Path) -> etree._ElementTree:
    try:
        parser = etree.XMLParser(recover=False, remove_blank_text=False)
        return etree.parse(str(xml_path), parser)
    except (OSError, etree.XMLSyntaxError) as exc:
        raise SiteBuilderExtractionError(f"Unable to parse XML file '{xml_path}': {exc}") from exc


def _fallback_slug(xml_path: Path, candidate: str | None) -> str:
    if candidate and candidate.strip():
        return _slugify(candidate)
    return _slugify(xml_path.stem)


def _derive_related_play_slug(slug: str) -> str | None:
    lowered = slug.lower()
    suffixes = ("-notice", "_notice", "-metopes", "-metope")
    for suffix in suffixes:
        if lowered.endswith(suffix):
            candidate = slug[: -len(suffix)]
            return _slugify(candidate) if candidate else None
    return None


def _localname(node: etree._Element) -> str:
    if not isinstance(node.tag, str):
        return ""
    if "}" in node.tag:
        return node.tag.split("}", 1)[1]
    return node.tag


def _normalize_ws(value: str) -> str:
    return " ".join(value.split())


def _extract_author_list(tree: etree._ElementTree) -> tuple[str, ...]:
    authors: list[str] = []
    for author in tree.xpath("//*[local-name()='teiHeader']//*[local-name()='titleStmt']/*[local-name()='author']"):
        if isinstance(author, etree._Element):
            text = _normalize_ws(" ".join(author.itertext()))
            if text and text not in authors:
                authors.append(text)
    return tuple(authors)


def _extract_titles(tree: etree._ElementTree) -> tuple[str, str | None]:
    title = _first_text(
        tree,
        (
            "string(//*[local-name()='teiHeader']//*[local-name()='titleStmt']/*[local-name()='title'][@type='main'][1])",
            "string(//*[local-name()='teiHeader']//*[local-name()='titleStmt']/*[local-name()='title'][1])",
            "string((//*[local-name()='text']/*[local-name()='front']//*[local-name()='div'][@type='titlePage']//*[local-name()='p'])[1])",
        ),
    )
    subtitle = _first_text(
        tree,
        (
            "string(//*[local-name()='teiHeader']//*[local-name()='titleStmt']/*[local-name()='title'][@type='sub'][1])",
            "string((//*[local-name()='teiHeader']//*[local-name()='titleStmt']/*[local-name()='title'])[2])",
        ),
    )
    return title or "", subtitle


def _collect_front_title_page(tree: etree._ElementTree) -> tuple[str, ...]:
    lines: list[str] = []
    nodes = tree.xpath(
        "//*[local-name()='text']/*[local-name()='front']//*[local-name()='div'][@type='titlePage']//*[local-name()='p']"
    )
    for node in nodes:
        if isinstance(node, etree._Element):
            text = _normalize_ws(" ".join(node.itertext()))
            if text:
                lines.append(text)
    return tuple(lines)


def _render_children_inline(node: etree._Element, notes: dict[str, NoticeNote], note_order: list[str]) -> str:
    fragments: list[str] = []
    if node.text:
        fragments.append(html.escape(node.text))

    for child in node:
        name = _localname(child)
        if name == "hi":
            inner = _render_children_inline(child, notes, note_order)
            rend = (child.get("rend") or "").lower()
            if "italic" in rend:
                fragments.append(f"<em>{inner}</em>")
            elif rend in {"sup", "super"}:
                fragments.append(f"<sup>{inner}</sup>")
            elif rend in {"sub", "subscript"}:
                fragments.append(f"<sub>{inner}</sub>")
            else:
                css = f"hi-{html.escape(rend)}" if rend else "hi"
                fragments.append(f'<span class="{css}">{inner}</span>')
        elif name == "ref":
            inner = _render_children_inline(child, notes, note_order)
            target = html.escape(child.get("target") or "#", quote=True)
            fragments.append(f'<a href="{target}">{inner}</a>')
        elif name == "note":
            note_id = child.get(f"{{{XML_NS}}}id") or f"n{len(notes) + 1}"
            label = (child.get("n") or str(len(notes) + 1)).strip() or str(len(notes) + 1)
            note_text = _normalize_ws(" ".join(child.itertext()))
            if note_id not in notes:
                notes[note_id] = NoticeNote(note_id=note_id, label=label, text=note_text)
                note_order.append(note_id)
            fragments.append(
                f'<sup class="note-ref"><a href="#note-{html.escape(note_id, quote=True)}">[{html.escape(label)}]</a></sup>'
            )
        else:
            fragments.append(_render_children_inline(child, notes, note_order))

        if child.tail:
            fragments.append(html.escape(child.tail))

    return "".join(fragments)


def _is_safe_local_href(href: str) -> bool:
    cleaned = href.strip()
    if not cleaned:
        return False
    lowered = cleaned.lower()
    if lowered.startswith(("http://", "https://", "ftp://", "file://", "data:")):
        return False
    if ":" in cleaned and not re.match(r"^[A-Za-z]:[\\/]", cleaned):
        return False
    return True


def _anchor_from_title(title: str, fallback: str) -> str:
    slug = _slugify(title)
    return slug if slug and slug != "untitled" else fallback


def _extract_section_from_div(
    node: etree._Element,
    *,
    level: int,
    node_kind: str,
    path_token: str,
    notes: dict[str, NoticeNote],
    note_order: list[str],
) -> NoticeSection:
    title = _normalize_ws(" ".join(node.xpath("./*[local-name()='head'][1]//text()")))
    if not title:
        title = (node.get("type") or "section").strip() or "section"

    xml_id = node.get(f"{{{XML_NS}}}id")
    anchor = _anchor_from_title(title, fallback=f"{path_token}-section")
    section_id = _slugify(xml_id) if xml_id else f"{path_token}-{anchor}"

    paragraphs: list[str] = []
    items: list[str] = []
    children: list[NoticeSection] = []

    div_index = 0
    for child in node:
        name = _localname(child)
        if name == "head":
            continue
        if name == "p":
            html_text = _render_children_inline(child, notes, note_order)
            if html_text.strip():
                paragraphs.append(f"<p>{html_text}</p>")
        elif name == "list":
            for item in child.xpath("./*[local-name()='item']"):
                if isinstance(item, etree._Element):
                    item_html = _render_children_inline(item, notes, note_order)
                    if item_html.strip():
                        items.append(item_html)
        elif name == "div":
            div_index += 1
            children.append(
                _extract_section_from_div(
                    child,
                    level=level + 1,
                    node_kind="section",
                    path_token=f"{path_token}-s{div_index}",
                    notes=notes,
                    note_order=note_order,
                )
            )

    return NoticeSection(
        section_id=section_id,
        title=title,
        kind=(node.get("type") or "div").strip() or "div",
        level=level,
        node_kind=node_kind,
        paragraphs=tuple(paragraphs),
        items=tuple(items),
        children=tuple(children),
    )


def _extract_text_sections(
    text_node: etree._Element,
    *,
    level: int,
    path_token: str,
    notes: dict[str, NoticeNote],
    note_order: list[str],
) -> tuple[NoticeSection, ...]:
    body_nodes = text_node.xpath("./*[local-name()='body']")
    if not body_nodes:
        return ()
    body = body_nodes[0]

    top_divs = body.xpath("./*[local-name()='div']")
    if top_divs:
        sections: list[NoticeSection] = []
        for index, div in enumerate(top_divs, start=1):
            if isinstance(div, etree._Element):
                sections.append(
                    _extract_section_from_div(
                        div,
                        level=level,
                        node_kind="section",
                        path_token=f"{path_token}-d{index}",
                        notes=notes,
                        note_order=note_order,
                    )
                )
        return tuple(sections)

    paragraphs: list[str] = []
    items: list[str] = []
    for child in body:
        name = _localname(child)
        if name == "p":
            html_text = _render_children_inline(child, notes, note_order)
            if html_text.strip():
                paragraphs.append(f"<p>{html_text}</p>")
        elif name == "list":
            for item in child.xpath("./*[local-name()='item']"):
                if isinstance(item, etree._Element):
                    item_html = _render_children_inline(item, notes, note_order)
                    if item_html.strip():
                        items.append(item_html)

    if not paragraphs and not items:
        return ()

    section_id = f"{path_token}-body"
    title = (text_node.get("type") or "notice").strip() or "notice"
    return (
        NoticeSection(
            section_id=section_id,
            title=title,
            kind="body",
            level=level,
            node_kind="section",
            paragraphs=tuple(paragraphs),
            items=tuple(items),
            children=(),
        ),
    )


def _extract_notice_core(
    tree: etree._ElementTree,
    *,
    source_path: Path,
    slug_seed: str | None,
    resolve_xincludes: bool,
) -> NoticeDocument:
    title, subtitle = _extract_titles(tree)
    authors = _extract_author_list(tree)
    text_type = _first_text(tree, ("string((//*[local-name()='text']/@type)[1])",)) or "notice"
    xml_id = _first_text(tree, ("string(/*/@xml:id)", "string(/*/@id)"))
    slug = _fallback_slug(source_path, slug_seed or xml_id or title)

    notes: dict[str, NoticeNote] = {}
    note_order: list[str] = []
    warnings: list[str] = []
    included_paths: list[Path] = []

    related = _first_text(
        tree,
        (
            "string((//*[local-name()='idno'][@type='play'])[1])",
            "string((//*[local-name()='idno'][@subtype='play'])[1])",
            "string((//*[local-name()='ref'][@type='play']/@target)[1])",
        ),
    )
    related_slug = _slugify(related) if related else _derive_related_play_slug(slug)

    is_master = bool(tree.xpath("//*[local-name()='text' and @type='book']"))

    def extract_included_document(
        include_node: etree._Element,
        *,
        level: int,
        path_token: str,
    ) -> NoticeSection | None:
        href = (include_node.get("href") or "").strip()
        if not resolve_xincludes:
            warnings.append(f"xi:include resolution disabled for '{href}' in '{source_path.name}'.")
            return None
        if not _is_safe_local_href(href):
            warnings.append(f"Skipped non-local xi:include href '{href}' in '{source_path.name}'.")
            return None

        include_path = (source_path.parent / href).resolve()
        if not include_path.exists() or not include_path.is_file():
            warnings.append(f"Could not resolve xi:include '{href}' from '{source_path.name}'.")
            return NoticeSection(
                section_id=f"{path_token}-missing",
                title=f"Include manquant: {href}",
                kind="missing_include",
                level=level,
                node_kind="included_document",
                source_path=include_path,
                paragraphs=(),
                items=(),
                children=(),
            )

        include_tree = _parse_tree(include_path)
        text_nodes = include_tree.xpath("//*[local-name()='text']")
        if not text_nodes:
            warnings.append(f"Included file '{href}' has no TEI text node.")
            return None

        included_doc = _extract_notice_core(
            include_tree,
            source_path=include_path,
            slug_seed=include_path.stem,
            resolve_xincludes=False,
        )
        included_paths.append(include_path)

        section_id = f"{path_token}-{_anchor_from_title(included_doc.title, include_path.stem)}"
        merged_warnings = list(included_doc.include_warnings)
        if merged_warnings:
            warnings.extend(merged_warnings)

        return NoticeSection(
            section_id=section_id,
            title=included_doc.title,
            kind="included_document",
            level=level,
            node_kind="included_document",
            subtitle=included_doc.subtitle,
            authors=included_doc.authors,
            text_type=included_doc.text_type,
            source_path=include_path,
            paragraphs=(),
            items=(),
            children=included_doc.sections,
        )

    def extract_group(node: etree._Element, *, level: int, path_token: str) -> NoticeSection:
        title = _normalize_ws(" ".join(node.xpath("./*[local-name()='head'][1]//text()")))
        if not title:
            title = (node.get("type") or "group").strip() or "group"

        group_anchor = _anchor_from_title(title, f"group-{path_token}")
        section_id = f"{path_token}-{group_anchor}"

        children: list[NoticeSection] = []
        group_index = 0
        include_index = 0

        for child in node:
            lname = _localname(child)
            if lname == "group":
                group_index += 1
                children.append(extract_group(child, level=level + 1, path_token=f"{path_token}-g{group_index}"))
            elif lname == "include" and child.tag.startswith("{" + XI_NS + "}"):
                include_index += 1
                included_node = extract_included_document(
                    child,
                    level=level + 1,
                    path_token=f"{path_token}-i{include_index}",
                )
                if included_node is not None:
                    children.append(included_node)
            elif lname == "text":
                children.extend(
                    _extract_text_sections(
                        child,
                        level=level + 1,
                        path_token=f"{path_token}-text",
                        notes=notes,
                        note_order=note_order,
                    )
                )

        return NoticeSection(
            section_id=section_id,
            title=title,
            kind=(node.get("type") or "group").strip() or "group",
            level=level,
            node_kind="group",
            children=tuple(children),
        )

    if is_master:
        text_nodes = tree.xpath("//*[local-name()='text' and @type='book'][1]")
        root_groups: list[NoticeSection] = []
        if text_nodes:
            top_groups = text_nodes[0].xpath("./*[local-name()='group']/*[local-name()='group']")
            if not top_groups:
                top_groups = text_nodes[0].xpath("./*[local-name()='group']")
            for idx, grp in enumerate(top_groups, start=1):
                if isinstance(grp, etree._Element):
                    root_groups.append(extract_group(grp, level=1, path_token=f"grp{idx}"))
        sections = tuple(root_groups)
        notice_kind = "master_volume"
        has_body = bool(sections)
    else:
        text_nodes = tree.xpath("//*[local-name()='text'][1]")
        sections = ()
        if text_nodes and isinstance(text_nodes[0], etree._Element):
            sections = _extract_text_sections(
                text_nodes[0],
                level=1,
                path_token="doc",
                notes=notes,
                note_order=note_order,
            )
        notice_kind = "standalone"
        has_body = _has_text_body(tree)

    front_title_page = _collect_front_title_page(tree)
    if not title and front_title_page:
        title = front_title_page[0]

    ordered_notes = tuple(notes[nid] for nid in note_order if nid in notes)

    def to_toc(section: NoticeSection) -> NoticeTocEntry:
        return NoticeTocEntry(
            entry_id=section.section_id,
            title=section.title,
            level=section.level,
            children=tuple(to_toc(child) for child in section.children),
        )

    return NoticeDocument(
        source_path=source_path.resolve(),
        slug=slug,
        title=title or source_path.stem,
        subtitle=subtitle,
        authors=authors,
        text_type=text_type,
        notice_kind=notice_kind,
        has_text_body=has_body,
        front_title_page=front_title_page,
        sections=sections,
        toc=tuple(to_toc(section) for section in sections),
        notes=ordered_notes,
        include_warnings=tuple(warnings),
        included_documents=tuple(included_paths),
        related_play_slug=related_slug,
    )


def extract_notice_document(xml_path: Path, *, resolve_xincludes: bool = True) -> NoticeDocument:
    tree = _parse_tree(xml_path)
    return _extract_notice_core(
        tree,
        source_path=xml_path,
        slug_seed=None,
        resolve_xincludes=resolve_xincludes,
    )


def extract_play_entry(xml_path: Path) -> PlayEntry:
    tree = _parse_tree(xml_path)
    title = _first_text(
        tree,
        (
            "string(//*[local-name()='teiHeader']//*[local-name()='titleStmt']/*[local-name()='title'][1])",
            "string((//*[local-name()='text']/*[local-name()='body']//*[local-name()='head'])[1])",
        ),
    )
    author = _first_text(
        tree,
        ("string(//*[local-name()='teiHeader']//*[local-name()='titleStmt']/*[local-name()='author'][1])",),
    )
    slug = _fallback_slug(xml_path, title)
    divisions = _collect_main_divisions(tree)
    return PlayEntry(
        source_path=xml_path.resolve(),
        slug=slug,
        title=title or xml_path.stem,
        author=author,
        document_type="dramatic_tei",
        main_divisions=divisions,
        has_text_body=_has_text_body(tree),
    )


def extract_notice_entry(xml_path: Path, *, resolve_xincludes: bool = True) -> NoticeEntry:
    document = extract_notice_document(xml_path, resolve_xincludes=resolve_xincludes)
    main_author = document.authors[0] if document.authors else None
    return NoticeEntry(
        source_path=document.source_path,
        slug=document.slug,
        title=document.title,
        subtitle=document.subtitle,
        author=main_author,
        authors=document.authors,
        document_type="metopes_notice",
        notice_kind=document.notice_kind,
        has_text_body=document.has_text_body,
        related_play_slug=document.related_play_slug,
        document=document,
    )
