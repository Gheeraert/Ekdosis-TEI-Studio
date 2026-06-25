from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from lxml import etree

from .models import DTSNavNode, DTSResource, DTSTeiIndex

XML_ID = "{http://www.w3.org/XML/1998/namespace}id"


class DTSTeiIndexError(ValueError):
    pass


def _normalized_text(value: str) -> str:
    return " ".join(value.split())


def _first_text(tree: etree._ElementTree, xpath: str) -> str:
    result = tree.xpath(xpath)
    if not result:
        return ""
    value = result[0]
    if isinstance(value, etree._Element):
        return _normalized_text("".join(value.itertext()))
    return _normalized_text(str(value))


def _fallback_slug(source_path: Path) -> str:
    normalized = unicodedata.normalize("NFKD", source_path.stem)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-") or "resource"


def _identifier(
    element: etree._Element,
    fallback: str,
    *,
    seen: set[str],
) -> str:
    candidate = (element.get(XML_ID) or fallback).strip() or fallback
    if candidate not in seen:
        seen.add(candidate)
        return candidate

    suffix = 2
    while f"{candidate}-{suffix}" in seen:
        suffix += 1
    unique = f"{candidate}-{suffix}"
    seen.add(unique)
    return unique


def _label(kind: str, number: str, identifier: str) -> str:
    if number:
        names = {"act": "Acte", "scene": "Scène", "line": "Vers"}
        return f"{names[kind]} {number}"
    return identifier


def index_tei(
    source_path: Path,
    *,
    slug: str | None = None,
    title: str | None = None,
    author: str | None = None,
) -> DTSTeiIndex:
    resolved_source = source_path.resolve()
    try:
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        tree = etree.parse(str(resolved_source), parser)
    except (OSError, etree.XMLSyntaxError) as exc:
        raise DTSTeiIndexError(f"unable to parse TEI: {exc}") from exc

    resolved_slug = (slug or "").strip() or _fallback_slug(resolved_source)
    resolved_title = (title or "").strip() or _first_text(
        tree,
        "(//*[local-name()='teiHeader']//*[local-name()='titleStmt']/*[local-name()='title'])[1]",
    )
    resolved_author = (author or "").strip() or _first_text(
        tree,
        "(//*[local-name()='teiHeader']//*[local-name()='titleStmt']/*[local-name()='author'])[1]",
    )
    resource = DTSResource(
        slug=resolved_slug,
        title=resolved_title or resolved_source.stem,
        author=resolved_author or None,
        source_path=resolved_source,
    )

    seen: set[str] = set()
    acts: list[DTSNavNode] = []
    act_elements = tree.xpath(
        "//*[local-name()='text']/*[local-name()='body']/*[local-name()='div'][@type='act']"
    )
    for act_position, act in enumerate(act_elements, start=1):
        act_n = (act.get("n") or str(act_position)).strip()
        logical_act_id = f"A{act_n}"
        act_id = _identifier(act, logical_act_id, seen=seen)
        scenes: list[DTSNavNode] = []
        scene_elements = act.xpath("./*[local-name()='div'][@type='scene']")
        for scene_position, scene in enumerate(scene_elements, start=1):
            scene_n = (scene.get("n") or str(scene_position)).strip()
            logical_scene_id = f"{logical_act_id}S{scene_n}"
            scene_id = _identifier(scene, logical_scene_id, seen=seen)
            lines: list[DTSNavNode] = []
            line_elements = scene.xpath(".//*[local-name()='l']")
            for line_position, line in enumerate(line_elements, start=1):
                line_n = (line.get("n") or str(line_position)).strip()
                line_id = _identifier(line, f"{logical_scene_id}L{line_n}", seen=seen)
                lines.append(
                    DTSNavNode(
                        identifier=line_id,
                        cite_type="line",
                        level=3,
                        parent=scene_id,
                        label=_label("line", line_n, line_id),
                    )
                )
            scenes.append(
                DTSNavNode(
                    identifier=scene_id,
                    cite_type="scene",
                    level=2,
                    parent=act_id,
                    label=_label("scene", scene_n, scene_id),
                    children=tuple(lines),
                )
            )
        acts.append(
            DTSNavNode(
                identifier=act_id,
                cite_type="act",
                level=1,
                parent=None,
                label=_label("act", act_n, act_id),
                children=tuple(scenes),
            )
        )

    return DTSTeiIndex(resource=resource, navigation=tuple(acts))
