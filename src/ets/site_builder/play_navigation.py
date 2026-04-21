from __future__ import annotations

from pathlib import Path
import re
import unicodedata

from lxml import etree

from .models import (
    PlayActNavigation,
    PlayEntry,
    PlayFrontItemNavigation,
    PlayNavigation,
    PlaySceneNavigation,
)


XML_NS = "http://www.w3.org/XML/1998/namespace"


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip())
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_only = ascii_only.lower()
    ascii_only = re.sub(r"[^a-z0-9]+", "-", ascii_only)
    ascii_only = ascii_only.strip("-")
    return ascii_only or "section"


def _normalize_ws(value: str) -> str:
    return " ".join(value.split())


def _localname(node: etree._Element) -> str:
    if not isinstance(node.tag, str):
        return ""
    if "}" in node.tag:
        return node.tag.split("}", 1)[1]
    return node.tag


def _division_label(node: etree._Element, default_kind: str, position: int) -> str:
    number = (node.get("n") or "").strip()
    if default_kind == "act":
        base = "Acte"
    elif default_kind == "scene":
        base = "Scène"
    else:
        base = default_kind.capitalize()
    return f"{base} {number}" if number else f"{base} {position}"


def _reserve_anchor_id(base: str, used: set[str]) -> str:
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def _make_anchor_id(
    *,
    play_slug: str,
    kind: str,
    node: etree._Element,
    fallback: str,
    used: set[str],
) -> str:
    xml_id = (node.get(f"{{{XML_NS}}}id") or "").strip()
    token_source = xml_id or (node.get("n") or "").strip() or fallback
    token = _slugify(token_source)
    base = f"ets-nav-{_slugify(play_slug)}-{kind}-{token}"
    return _reserve_anchor_id(base, used)


def _canonical_inline_text(node: etree._Element) -> str:
    fragments: list[str] = []
    if node.text:
        fragments.append(node.text)
    for child in node:
        lname = _localname(child)
        if lname == "app":
            lem_nodes = child.xpath("./*[local-name()='lem'][1]")
            if lem_nodes and isinstance(lem_nodes[0], etree._Element):
                fragments.append(_canonical_inline_text(lem_nodes[0]))
            else:
                fallback = _normalize_ws(" ".join(child.itertext()))
                if fallback:
                    fragments.append(fallback)
            if child.tail:
                fragments.append(child.tail)
            continue
        fragments.append(_canonical_inline_text(child))
        if child.tail:
            fragments.append(child.tail)
    return "".join(fragments)


def _dedupe(values: list[str]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        token = _slugify(value)
        if not token or token in seen:
            continue
        seen.add(token)
        ordered.append(value)
    return tuple(ordered)


def _split_personae_text(raw_text: str) -> tuple[str, ...]:
    chunks = re.split(r"[;\n]+|,\s*", raw_text)
    cleaned: list[str] = []
    for chunk in chunks:
        token = _normalize_ws(chunk).strip(" .,:;")
        if token:
            cleaned.append(token)
    return _dedupe(cleaned)


def _extract_cast_list_personae(tree: etree._ElementTree) -> tuple[str, ...]:
    cast_lists = tree.xpath(
        "//*[local-name()='text']/*[local-name()='front']//*[local-name()='castList']"
    )
    for cast_list in cast_lists:
        if not isinstance(cast_list, etree._Element):
            continue
        entries: list[str] = []
        cast_items = cast_list.xpath(".//*[local-name()='castItem']")
        if cast_items:
            for cast_item in cast_items:
                if not isinstance(cast_item, etree._Element):
                    continue
                text = _normalize_ws(_canonical_inline_text(cast_item))
                if text:
                    entries.append(text)
        else:
            role_nodes = cast_list.xpath(".//*[local-name()='role']")
            for role_node in role_nodes:
                if not isinstance(role_node, etree._Element):
                    continue
                text = _normalize_ws(_canonical_inline_text(role_node))
                if text:
                    entries.append(text)

        if entries:
            return _dedupe(entries)

        fallback_text = _normalize_ws(_canonical_inline_text(cast_list))
        if fallback_text:
            return _split_personae_text(fallback_text)
    return ()


def _extract_stage_personae(body: etree._Element | None) -> tuple[str, ...]:
    if body is None:
        return ()
    stage_nodes = body.xpath(
        ".//*[local-name()='stage'"
        " and translate(@type,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='personnages']"
    )
    if not stage_nodes:
        return ()
    first_stage = stage_nodes[0]
    if not isinstance(first_stage, etree._Element):
        return ()
    stage_text = _normalize_ws(_canonical_inline_text(first_stage))
    if not stage_text:
        return ()
    return _split_personae_text(stage_text)


def _extract_dramatis_personae(tree: etree._ElementTree, body: etree._Element | None) -> tuple[str, ...]:
    cast_list_entries = _extract_cast_list_personae(tree)
    if cast_list_entries:
        return cast_list_entries
    return _extract_stage_personae(body)


def _parse_tree(path: Path) -> etree._ElementTree:
    parser = etree.XMLParser(recover=False, remove_blank_text=False)
    return etree.parse(str(path), parser)


def extract_play_navigation(
    play: PlayEntry,
    *,
    dramatis_source_path: Path | None = None,
) -> PlayNavigation:
    try:
        tree = _parse_tree(play.source_path)
    except (OSError, etree.XMLSyntaxError) as exc:
        raise ValueError(f"Unable to extract play navigation for '{play.source_path}': {exc}") from exc

    body_nodes = tree.xpath("//*[local-name()='text']/*[local-name()='body']")
    body = body_nodes[0] if body_nodes else None

    used_anchor_ids: set[str] = set()
    front_items: list[PlayFrontItemNavigation] = []

    dramatis_personae: tuple[str, ...] = ()
    if dramatis_source_path is not None:
        try:
            external_tree = _parse_tree(dramatis_source_path)
            external_body_nodes = external_tree.xpath("//*[local-name()='text']/*[local-name()='body']")
            external_body = external_body_nodes[0] if external_body_nodes else None
            dramatis_personae = _extract_dramatis_personae(external_tree, external_body)
        except (OSError, etree.XMLSyntaxError):
            dramatis_personae = ()
    if not dramatis_personae:
        dramatis_personae = _extract_dramatis_personae(tree, body)

    if dramatis_personae:
        dramatis_anchor = _reserve_anchor_id(
            f"ets-nav-{_slugify(play.slug)}-dramatis-personae",
            used_anchor_ids,
        )
        front_items.append(
            PlayFrontItemNavigation(
                kind="dramatis_personae",
                label="Personnages",
                href=f"plays/{play.slug}.html#{dramatis_anchor}",
                anchor_id=dramatis_anchor,
            )
        )

    if body is None:
        return PlayNavigation(
            play_slug=play.slug,
            play_title=play.title,
            front_items=tuple(front_items),
            dramatis_personae=dramatis_personae,
            acts=(),
        )

    acts: list[PlayActNavigation] = []
    speech_cursor = 0
    act_index = 0

    for node in body:
        if not isinstance(node.tag, str) or etree.QName(node).localname != "div":
            continue
        if (node.get("type") or "").strip().lower() != "act":
            continue

        act_index += 1
        act_label = _division_label(node, "act", act_index)
        act_anchor_id = _make_anchor_id(
            play_slug=play.slug,
            kind="act",
            node=node,
            fallback=str(act_index),
            used=used_anchor_ids,
        )
        act_start_speech_index = speech_cursor

        scenes: list[PlaySceneNavigation] = []
        scene_index = 0

        for scene_node in node:
            if not isinstance(scene_node.tag, str) or etree.QName(scene_node).localname != "div":
                continue
            if (scene_node.get("type") or "").strip().lower() != "scene":
                continue

            scene_index += 1
            scene_label = _division_label(scene_node, "scene", scene_index)
            scene_anchor_id = _make_anchor_id(
                play_slug=play.slug,
                kind="scene",
                node=scene_node,
                fallback=f"{act_index}-{scene_index}",
                used=used_anchor_ids,
            )
            scene_start_speech_index = speech_cursor
            scene_speeches = len(scene_node.xpath(".//*[local-name()='sp']"))
            speech_cursor += scene_speeches
            scenes.append(
                PlaySceneNavigation(
                    label=scene_label,
                    anchor_id=scene_anchor_id,
                    start_speech_index=scene_start_speech_index,
                )
            )

        if not scenes:
            speech_cursor += len(node.xpath(".//*[local-name()='sp']"))

        acts.append(
            PlayActNavigation(
                label=act_label,
                anchor_id=act_anchor_id,
                start_speech_index=act_start_speech_index,
                scenes=tuple(scenes),
            )
        )

    return PlayNavigation(
        play_slug=play.slug,
        play_title=play.title,
        front_items=tuple(front_items),
        dramatis_personae=dramatis_personae,
        acts=tuple(acts),
    )


def index_play_navigation(items: tuple[PlayNavigation, ...]) -> dict[str, PlayNavigation]:
    return {item.play_slug: item for item in items}

