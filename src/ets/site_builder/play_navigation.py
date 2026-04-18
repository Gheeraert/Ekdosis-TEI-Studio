from __future__ import annotations

import re
import unicodedata

from lxml import etree

from .models import PlayActNavigation, PlayEntry, PlayNavigation, PlaySceneNavigation


XML_NS = "http://www.w3.org/XML/1998/namespace"


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip())
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_only = ascii_only.lower()
    ascii_only = re.sub(r"[^a-z0-9]+", "-", ascii_only)
    ascii_only = ascii_only.strip("-")
    return ascii_only or "section"


def _division_label(node: etree._Element, default_kind: str, position: int) -> str:
    number = (node.get("n") or "").strip()
    if default_kind == "act":
        base = "Acte"
    elif default_kind == "scene":
        base = "Scène"
    else:
        base = default_kind.capitalize()
    return f"{base} {number}" if number else f"{base} {position}"


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
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def extract_play_navigation(play: PlayEntry) -> PlayNavigation:
    try:
        parser = etree.XMLParser(recover=False, remove_blank_text=False)
        tree = etree.parse(str(play.source_path), parser)
    except (OSError, etree.XMLSyntaxError) as exc:
        raise ValueError(f"Unable to extract play navigation for '{play.source_path}': {exc}") from exc

    body_nodes = tree.xpath("//*[local-name()='text']/*[local-name()='body']")
    if not body_nodes:
        return PlayNavigation(play_slug=play.slug, play_title=play.title, acts=())
    body = body_nodes[0]

    used_anchor_ids: set[str] = set()
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

    return PlayNavigation(play_slug=play.slug, play_title=play.title, acts=tuple(acts))


def index_play_navigation(items: tuple[PlayNavigation, ...]) -> dict[str, PlayNavigation]:
    return {item.play_slug: item for item in items}
