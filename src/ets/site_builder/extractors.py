from __future__ import annotations

import html
import re
import unicodedata
from copy import deepcopy
from pathlib import Path

from lxml import etree

from .models import (
    NoticeDocument,
    NoticeEntry,
    NoticeNote,
    NoticeSection,
    NoticeTocEntry,
    PlayEntry,
)


TEI_NS = "http://www.tei-c.org/ns/1.0"
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
    body = bodies[0]
    return bool(" ".join(body.itertext()).strip())


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


def _is_master_volume(tree: etree._ElementTree) -> bool:
    return bool(tree.xpath("//*[local-name()='text' and @type='book']"))


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
            fragments.append(f'<sup class="note-ref"><a href="#note-{html.escape(note_id, quote=True)}">[{html.escape(label)}]</a></sup>')
        else:
            fragments.append(_render_children_inline(child, notes, note_order))

        if child.tail:
            fragments.append(html.escape(child.tail))

    return "".join(fragments)


def _section_id(node: etree._Element, fallback: str) -> str:
    xml_id = node.get(f"{{{XML_NS}}}id")
    if xml_id:
        return _slugify(xml_id)
    return fallback


def _extract_section_from_div(
    node: etree._Element,
    *,
    level: int,
    fallback_id: str,
    notes: dict[str, NoticeNote],
    note_order: list[str],
) -> NoticeSection:
    title = _normalize_ws(" ".join(node.xpath("./*[local-name()='head'][1]//text()")))
    if not title:
        title = (node.get("type") or "section").strip() or "section"

    paragraphs: list[str] = []
    items: list[str] = []
    children: list[NoticeSection] = []

    child_index = 0
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
            child_index += 1
            children.append(
                _extract_section_from_div(
                    child,
                    level=level + 1,
                    fallback_id=f"{fallback_id}-{child_index}",
                    notes=notes,
                    note_order=note_order,
                )
            )

    return NoticeSection(
        section_id=_section_id(node, fallback_id),
        title=title,
        kind=(node.get("type") or "div").strip() or "div",
        level=level,
        paragraphs=tuple(paragraphs),
        items=tuple(items),
        children=tuple(children),
    )


def _extract_standalone_sections(
    text_node: etree._Element,
    notes: dict[str, NoticeNote],
    note_order: list[str],
) -> tuple[NoticeSection, ...]:
    body_nodes = text_node.xpath("./*[local-name()='body']")
    if not body_nodes:
        return ()
    body = body_nodes[0]

    sections: list[NoticeSection] = []
    top_divs = body.xpath("./*[local-name()='div']")
    if top_divs:
        for i, div in enumerate(top_divs, start=1):
            if isinstance(div, etree._Element):
                sections.append(
                    _extract_section_from_div(
                        div,
                        level=1,
                        fallback_id=f"sec-{i}",
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

    title = (text_node.get("type") or "notice").strip() or "notice"
    return (
        NoticeSection(
            section_id="body",
            title=title,
            kind="body",
            level=1,
            paragraphs=tuple(paragraphs),
            items=tuple(items),
            children=(),
        ),
    )


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


def _extract_text_from_include(include_path: Path) -> etree._Element | None:
    if not include_path.exists() or not include_path.is_file():
        return None
    include_tree = _parse_tree(include_path)
    text_nodes = include_tree.xpath("//*[local-name()='text']")
    if text_nodes:
        return deepcopy(text_nodes[0])
    root = include_tree.getroot()
    return deepcopy(root) if root is not None else None


def _resolve_local_xincludes(
    tree: etree._ElementTree,
    *,
    source_path: Path,
    enabled: bool,
) -> tuple[etree._ElementTree, tuple[str, ...], tuple[Path, ...]]:
    if not enabled:
        return tree, (), ()

    warnings: list[str] = []
    included: list[Path] = []
    pending = list(tree.xpath("//*[local-name()='include' and namespace-uri()=$ns]", ns=XI_NS))

    for include in pending:
        if not isinstance(include, etree._Element):
            continue
        href = (include.get("href") or "").strip()
        if not _is_safe_local_href(href):
            warnings.append(f"Skipped non-local xi:include href '{href}' in '{source_path.name}'.")
            continue

        resolved = (source_path.parent / href).resolve()
        extracted = _extract_text_from_include(resolved)
        if extracted is None:
            warnings.append(f"Could not resolve xi:include '{href}' from '{source_path.name}'.")
            continue

        parent = include.getparent()
        if parent is None:
            warnings.append(f"xi:include without parent ignored in '{source_path.name}'.")
            continue

        idx = parent.index(include)
        parent.remove(include)
        parent.insert(idx, extracted)
        included.append(resolved)

    return tree, tuple(warnings), tuple(included)


def _extract_sections_from_group(
    node: etree._Element,
    *,
    level: int,
    fallback_id: str,
    notes: dict[str, NoticeNote],
    note_order: list[str],
) -> NoticeSection:
    title = _normalize_ws(" ".join(node.xpath("./*[local-name()='head'][1]//text()")))
    if not title:
        text_titles = node.xpath("./*[local-name()='text']//*[local-name()='front']//*[local-name()='div'][@type='titlePage']//*[local-name()='p'][1]//text()")
        if text_titles:
            title = _normalize_ws(" ".join(text_titles))
    if not title:
        text_titles = node.xpath("./*[local-name()='text']//*[local-name()='body']//*[local-name()='head'][1]//text()")
        if text_titles:
            title = _normalize_ws(" ".join(text_titles))
    if not title:
        title = (node.get("type") or "group").strip() or "group"

    paragraphs: list[str] = []
    items: list[str] = []
    children: list[NoticeSection] = []

    direct_texts = node.xpath("./*[local-name()='text']")
    for text_node in direct_texts:
        if not isinstance(text_node, etree._Element):
            continue
        child_sections = _extract_standalone_sections(text_node, notes, note_order)
        for child in child_sections:
            paragraphs.extend(child.paragraphs)
            items.extend(child.items)
            children.extend(child.children)

    group_index = 0
    for child in node:
        if _localname(child) == "group":
            group_index += 1
            children.append(
                _extract_sections_from_group(
                    child,
                    level=level + 1,
                    fallback_id=f"{fallback_id}-{group_index}",
                    notes=notes,
                    note_order=note_order,
                )
            )

    return NoticeSection(
        section_id=_section_id(node, fallback_id),
        title=title,
        kind=(node.get("type") or "group").strip() or "group",
        level=level,
        paragraphs=tuple(paragraphs),
        items=tuple(items),
        children=tuple(children),
    )


def _build_toc_from_sections(sections: tuple[NoticeSection, ...]) -> tuple[NoticeTocEntry, ...]:
    def convert(section: NoticeSection) -> NoticeTocEntry:
        return NoticeTocEntry(
            entry_id=section.section_id,
            title=section.title,
            level=section.level,
            children=tuple(convert(child) for child in section.children),
        )

    return tuple(convert(section) for section in sections)


def extract_notice_document(xml_path: Path, *, resolve_xincludes: bool = True) -> NoticeDocument:
    tree = _parse_tree(xml_path)
    tree, include_warnings, included_documents = _resolve_local_xincludes(
        tree,
        source_path=xml_path,
        enabled=resolve_xincludes,
    )

    title, subtitle = _extract_titles(tree)
    authors = _extract_author_list(tree)
    text_type = _first_text(tree, ("string((//*[local-name()='text']/@type)[1])",)) or "notice"
    xml_id = _first_text(tree, ("string(/*/@xml:id)", "string(/*/@id)"))
    slug = _fallback_slug(xml_path, xml_id or title)

    notes: dict[str, NoticeNote] = {}
    note_order: list[str] = []

    is_master = _is_master_volume(tree)
    if is_master:
        root_groups = tree.xpath("//*[local-name()='text' and @type='book']/*[local-name()='group'][1]")
        sections: list[NoticeSection] = []
        if root_groups:
            root_group = root_groups[0]
            child_groups = root_group.xpath("./*[local-name()='group']")
            for i, child in enumerate(child_groups, start=1):
                if isinstance(child, etree._Element):
                    sections.append(
                        _extract_sections_from_group(
                            child,
                            level=1,
                            fallback_id=f"grp-{i}",
                            notes=notes,
                            note_order=note_order,
                        )
                    )
        notice_kind = "master_volume"
        has_body = bool(sections)
    else:
        text_nodes = tree.xpath("//*[local-name()='text'][1]")
        sections = []
        if text_nodes and isinstance(text_nodes[0], etree._Element):
            sections.extend(_extract_standalone_sections(text_nodes[0], notes, note_order))
        notice_kind = "standalone"
        has_body = _has_text_body(tree)

    ordered_notes = tuple(notes[note_id] for note_id in note_order if note_id in notes)
    front_title_page = _collect_front_title_page(tree)
    if not title and front_title_page:
        title = front_title_page[0]

    related = _first_text(
        tree,
        (
            "string((//*[local-name()='idno'][@type='play'])[1])",
            "string((//*[local-name()='idno'][@subtype='play'])[1])",
            "string((//*[local-name()='ref'][@type='play']/@target)[1])",
        ),
    )
    related_slug = _slugify(related) if related else _derive_related_play_slug(slug)

    sections_tuple = tuple(sections)
    return NoticeDocument(
        source_path=xml_path.resolve(),
        slug=slug,
        title=title or xml_path.stem,
        subtitle=subtitle,
        authors=authors,
        text_type=text_type,
        notice_kind=notice_kind,
        has_text_body=has_body,
        front_title_page=front_title_page,
        sections=sections_tuple,
        toc=_build_toc_from_sections(sections_tuple),
        notes=ordered_notes,
        include_warnings=include_warnings,
        included_documents=included_documents,
        related_play_slug=related_slug,
    )


def extract_play_entry(xml_path: Path) -> PlayEntry:
    tree = _parse_tree(xml_path)
    xml_id = _first_text(tree, ("string(/*/@xml:id)", "string(/*/@id)"))
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
    slug = _fallback_slug(xml_path, xml_id or title)
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
