from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lxml import etree

from ets.dts.document_fragments import encoded_reference
from ets.dts.models import DTSNavNode, DTSTeiIndex
from ets.dts.tei_index import index_tei


@dataclass(frozen=True)
class _LineSource:
    act: DTSNavNode
    scene: DTSNavNode
    line: DTSNavNode
    act_n: str
    scene_n: str
    line_n: str
    element: etree._Element


def _safe_target(output_root: Path, relative_path: Path) -> Path:
    root = output_root.resolve()
    target = (root / relative_path).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"output path escapes publication directory: {relative_path}") from exc
    return target


def _parse_source(source_path: Path) -> etree._ElementTree:
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    return etree.parse(str(source_path), parser)


def _normalize_space(value: str) -> str:
    return " ".join(value.split())


def _node_n(element: etree._Element, fallback: str) -> str:
    return str(element.get("n") or fallback).strip() or fallback


def _speaker_for_line(line: etree._Element) -> str | None:
    speech = next(
        (
            ancestor
            for ancestor in line.iterancestors()
            if etree.QName(ancestor).localname == "sp"
        ),
        None,
    )
    if speech is None:
        return None
    speakers: list[str] = []
    for child in speech:
        if etree.QName(child).localname != "speaker":
            continue
        text = _normalize_space("".join(child.itertext()))
        if text:
            speakers.append(text)
    if not speakers:
        return None
    return ", ".join(speakers)


def _line_sources(tree: etree._ElementTree, index: DTSTeiIndex) -> list[_LineSource]:
    sources: list[_LineSource] = []
    acts = tree.xpath(
        "//*[local-name()='text']/*[local-name()='body']/*[local-name()='div'][@type='act']"
    )
    for act_position, (act_node, act_element) in enumerate(zip(index.navigation, acts, strict=True), start=1):
        act_n = _node_n(act_element, str(act_position))
        scenes = act_element.xpath("./*[local-name()='div'][@type='scene']")
        for scene_position, (scene_node, scene_element) in enumerate(
            zip(act_node.children, scenes, strict=True),
            start=1,
        ):
            scene_n = _node_n(scene_element, str(scene_position))
            lines = scene_element.xpath(".//*[local-name()='l']")
            for line_position, (line_node, line_element) in enumerate(
                zip(scene_node.children, lines, strict=True),
                start=1,
            ):
                line_n = _node_n(line_element, str(line_position))
                sources.append(
                    _LineSource(
                        act=act_node,
                        scene=scene_node,
                        line=line_node,
                        act_n=act_n,
                        scene_n=scene_n,
                        line_n=line_n,
                        element=line_element,
                    )
                )
    return sources


def _line_entry(
    play: object,
    source: _LineSource,
    *,
    include_dts_links: bool,
) -> dict[str, Any]:
    slug = str(getattr(play, "slug", "")).strip()
    ref = source.line.identifier
    entry: dict[str, Any] = {
        "piece": str(getattr(play, "title", "") or slug),
        "slug": slug,
        "ref": ref,
        "citeType": "line",
        "speaker": _speaker_for_line(source.element),
        "label": f"Acte {source.act_n}, scène {source.scene_n}, vers {source.line_n}",
        "text": _normalize_space("".join(source.element.itertext())),
        "html": f"plays/{slug}.html#{encoded_reference(ref)}",
    }
    if include_dts_links:
        encoded_ref = encoded_reference(ref)
        entry["dts_document"] = f"api/dts/document/{slug}/{encoded_ref}.xml"
        entry["dts_navigation"] = f"api/dts/navigation/{slug}/{encoded_ref}.json"
    return entry


def _play_entries(play: object, *, include_dts_links: bool) -> list[dict[str, Any]]:
    source_path = Path(getattr(play, "source_path"))
    slug = str(getattr(play, "slug", "")).strip()
    index = index_tei(
        source_path,
        slug=slug,
        title=str(getattr(play, "title", "") or ""),
        author=getattr(play, "author", None),
    )
    tree = _parse_source(source_path)
    return [
        _line_entry(play, source, include_dts_links=include_dts_links)
        for source in _line_sources(tree, index)
    ]


def export_static_search_index(
    output_root: Path,
    plays: tuple[object, ...],
    *,
    include_dts_links: bool = False,
) -> tuple[str, ...]:
    warnings: list[str] = []
    entries: list[dict[str, Any]] = []
    for play in sorted(plays, key=lambda item: str(getattr(item, "slug", ""))):
        slug = str(getattr(play, "slug", "")).strip() or "unknown"
        try:
            entries.extend(_play_entries(play, include_dts_links=include_dts_links))
        except Exception as exc:
            warnings.append(f"Search index skipped for {slug}: {exc}")

    target = _safe_target(output_root, Path("search") / "index.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(entries, ensure_ascii=False, indent=2)
    target.write_text(f"{serialized}\n", encoding="utf-8")
    return tuple(warnings)
