from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from lxml import etree

from .models import NoticeEntry, PlayEntry


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


def extract_notice_entry(xml_path: Path) -> NoticeEntry:
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
    related = _first_text(
        tree,
        (
            "string((//*[local-name()='idno'][@type='play'])[1])",
            "string((//*[local-name()='idno'][@subtype='play'])[1])",
        ),
    )
    slug = _fallback_slug(xml_path, xml_id or title)
    related_slug = _slugify(related) if related else _derive_related_play_slug(slug)
    return NoticeEntry(
        source_path=xml_path.resolve(),
        slug=slug,
        title=title or xml_path.stem,
        author=author,
        document_type="metopes_notice",
        has_text_body=_has_text_body(tree),
        related_play_slug=related_slug,
    )
