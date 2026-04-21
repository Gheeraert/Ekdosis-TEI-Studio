from __future__ import annotations

import re
import unicodedata
from dataclasses import replace
from pathlib import Path

from .extractors import SiteBuilderExtractionError, extract_notice_entry, extract_play_entry
from .models import (
    NavigationItem,
    NoticeEntry,
    PlayEntry,
    PlayFrontItemNavigation,
    PlayNavigation,
    SiteConfig,
    SiteManifest,
    SitePage,
)
from .play_navigation import extract_play_navigation


def _discover_xml_files(directory: Path) -> list[Path]:
    if not directory.exists() or not directory.is_dir():
        return []
    return sorted((path for path in directory.rglob("*.xml") if path.is_file()), key=lambda item: item.as_posix())


def _with_download_paths(
    config: SiteConfig,
    plays: list[PlayEntry],
    notices: list[NoticeEntry],
) -> tuple[list[PlayEntry], list[NoticeEntry]]:
    if not config.show_xml_download:
        return plays, notices

    mapped_plays = [replace(play, xml_download_relpath=f"xml/dramatic/{play.slug}.xml") for play in plays]
    mapped_notices = [replace(notice, xml_download_relpath=f"xml/notices/{notice.slug}.xml") for notice in notices]
    return mapped_plays, mapped_notices


def _normalize_identifier(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip())
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")


def _notice_slug_candidates(notice_slug: str) -> tuple[str, ...]:
    candidates: list[str] = []
    normalized = _normalize_identifier(notice_slug)
    if normalized:
        candidates.append(normalized)

    suffixes = ("-notice", "-metopes", "-metope", "-preface")
    prefixes = ("notice-", "metopes-", "metope-", "preface-")
    for suffix in suffixes:
        if normalized.endswith(suffix):
            trimmed = normalized[: -len(suffix)].strip("-")
            if trimmed:
                candidates.append(trimmed)
    for prefix in prefixes:
        if normalized.startswith(prefix):
            trimmed = normalized[len(prefix) :].strip("-")
            if trimmed:
                candidates.append(trimmed)
    return tuple(dict.fromkeys(candidates))


def _order_plays(plays: list[PlayEntry], *, play_order: tuple[str, ...], warnings: list[str]) -> list[PlayEntry]:
    if not play_order:
        return plays

    play_by_slug = {play.slug: play for play in plays}
    ordered: list[PlayEntry] = []
    seen: set[str] = set()

    for slug in play_order:
        target = play_by_slug.get(slug)
        if target is None:
            warnings.append(f"Configured play_order slug '{slug}' not found among detected plays.")
            continue
        ordered.append(target)
        seen.add(slug)

    for play in plays:
        if play.slug in seen:
            continue
        ordered.append(play)
    return ordered


def _associate_notices_with_plays(plays: list[PlayEntry], notices: list[NoticeEntry]) -> list[NoticeEntry]:
    play_slugs = {play.slug for play in plays}
    mapped: list[NoticeEntry] = []
    for notice in notices:
        related_slug = _normalize_identifier(notice.related_play_slug or "")
        if related_slug and related_slug in play_slugs:
            mapped.append(replace(notice, related_play_slug=related_slug))
            continue

        matched_slug: str | None = None
        for candidate in _notice_slug_candidates(notice.slug):
            if candidate in play_slugs:
                matched_slug = candidate
                break
        if matched_slug is not None:
            mapped.append(replace(notice, related_play_slug=matched_slug))
            continue

        mapped.append(replace(notice, related_play_slug=None))
    return mapped


def _apply_explicit_play_notice_map(
    notices: list[NoticeEntry],
    *,
    play_notice_map: tuple[tuple[str, str], ...],
    warnings: list[str],
) -> list[NoticeEntry]:
    if not play_notice_map:
        return notices

    notice_by_slug = {notice.slug: notice for notice in notices if notice.editorial_role != "author_preface"}
    mapped = list(notices)

    for play_slug, notice_slug in play_notice_map:
        target = notice_by_slug.get(notice_slug)
        if target is None:
            warnings.append(
                f"Configured play_notice_map entry '{play_slug} -> {notice_slug}' ignored: notice slug not found."
            )
            continue
        replaced = replace(target, related_play_slug=play_slug, editorial_role="notice")
        mapped = [replaced if item.slug == notice_slug else item for item in mapped]
        notice_by_slug[notice_slug] = replaced
    return mapped


def _apply_explicit_play_preface_map(
    notices: list[NoticeEntry],
    *,
    play_preface_map: tuple[tuple[str, tuple[str, ...]], ...],
    warnings: list[str],
) -> list[NoticeEntry]:
    if not play_preface_map:
        return notices

    by_slug = {notice.slug: notice for notice in notices}
    mapped = list(notices)

    for play_slug, preface_slugs in play_preface_map:
        for preface_slug in preface_slugs:
            target = by_slug.get(preface_slug)
            if target is None:
                warnings.append(
                    f"Configured play_preface_map entry '{play_slug} -> {preface_slug}' ignored: preface slug not found."
                )
                continue
            replaced = replace(target, related_play_slug=play_slug, editorial_role="author_preface")
            mapped = [replaced if item.slug == preface_slug else item for item in mapped]
            by_slug[preface_slug] = replaced
    return mapped


def _apply_general_notice_selection(
    notices: list[NoticeEntry],
    *,
    general_notice_slug: str,
    warnings: list[str],
) -> tuple[list[NoticeEntry], str | None]:
    if not general_notice_slug:
        return notices, None

    notice_by_slug = {notice.slug: notice for notice in notices if notice.editorial_role != "author_preface"}
    target = notice_by_slug.get(general_notice_slug)
    if target is None:
        warnings.append(f"Configured general_notice_slug '{general_notice_slug}' not found among detected notices.")
        return notices, None

    if target.related_play_slug is None:
        return notices, target.slug

    warnings.append(
        f"Configured general_notice_slug '{general_notice_slug}' overrides play association "
        f"('{target.related_play_slug}') for that notice."
    )
    updated = replace(target, related_play_slug=None)
    remapped = [updated if notice.slug == updated.slug else notice for notice in notices]
    return remapped, updated.slug


def _resolve_play_dramatis_sources(
    *,
    config: SiteConfig,
    plays: list[PlayEntry],
    warnings: list[str],
) -> dict[str, Path]:
    if not config.play_dramatis_map:
        return {}
    if config.dramatis_xml_dir is None:
        warnings.append("External dramatis mapping is configured but dramatis_xml_dir is not configured.")
        return {}

    by_slug = {
        _normalize_identifier(path.stem): path
        for path in _discover_xml_files(config.dramatis_xml_dir)
    }
    play_slugs = {play.slug for play in plays}
    resolved: dict[str, Path] = {}
    for play_slug, dramatis_slug in config.play_dramatis_map:
        if play_slug not in play_slugs:
            continue
        target = by_slug.get(dramatis_slug)
        if target is None:
            warnings.append(
                f"Configured play_dramatis_map entry '{play_slug} -> {dramatis_slug}' ignored: dramatis slug not found."
            )
            continue
        resolved[play_slug] = target
    return resolved


def _collect_play_navigation(
    plays: list[PlayEntry],
    warnings: list[str],
    *,
    play_dramatis_sources: dict[str, Path],
) -> tuple[PlayNavigation, ...]:
    structures: list[PlayNavigation] = []
    for play in plays:
        try:
            structures.append(
                extract_play_navigation(
                    play,
                    dramatis_source_path=play_dramatis_sources.get(play.slug),
                )
            )
        except ValueError as exc:
            warnings.append(str(exc))
            structures.append(PlayNavigation(play_slug=play.slug, play_title=play.title))
    return tuple(structures)


def _order_prefaces_for_play(
    prefaces: list[NoticeEntry],
    *,
    explicit_order: tuple[str, ...],
) -> list[NoticeEntry]:
    if not prefaces:
        return []
    ordered = sorted(prefaces, key=lambda entry: entry.slug)
    if not explicit_order:
        return ordered

    by_slug = {item.slug: item for item in ordered}
    result: list[NoticeEntry] = []
    seen: set[str] = set()
    for slug in explicit_order:
        target = by_slug.get(slug)
        if target is None:
            continue
        result.append(target)
        seen.add(slug)
    for item in ordered:
        if item.slug in seen:
            continue
        result.append(item)
    return result


def _compose_play_navigation(
    *,
    plays: list[PlayEntry],
    play_navigation: tuple[PlayNavigation, ...],
    notices: list[NoticeEntry],
    play_notice_map: tuple[tuple[str, str], ...],
    play_preface_map: tuple[tuple[str, tuple[str, ...]], ...],
) -> tuple[PlayNavigation, ...]:
    by_play_slug = {item.play_slug: item for item in play_navigation}

    notices_by_play: dict[str, list[NoticeEntry]] = {}
    prefaces_by_play: dict[str, list[NoticeEntry]] = {}
    notices_by_slug: dict[str, NoticeEntry] = {}
    prefaces_by_slug: dict[str, NoticeEntry] = {}
    for notice in notices:
        if notice.editorial_role == "author_preface":
            prefaces_by_slug[notice.slug] = notice
        else:
            notices_by_slug[notice.slug] = notice
        if not notice.related_play_slug:
            continue
        if notice.editorial_role == "author_preface":
            prefaces_by_play.setdefault(notice.related_play_slug, []).append(notice)
        else:
            notices_by_play.setdefault(notice.related_play_slug, []).append(notice)

    explicit_notice_by_play = {play_slug: notice_slug for play_slug, notice_slug in play_notice_map}
    explicit_prefaces_by_play = {play_slug: preface_slugs for play_slug, preface_slugs in play_preface_map}

    composed: list[PlayNavigation] = []
    for play in plays:
        base = by_play_slug.get(play.slug, PlayNavigation(play_slug=play.slug, play_title=play.title))
        front_items: list[PlayFrontItemNavigation] = []

        notice_candidates = sorted(notices_by_play.get(play.slug, []), key=lambda entry: entry.slug)
        selected_notice: NoticeEntry | None = None
        explicit_notice_slug = explicit_notice_by_play.get(play.slug)
        if explicit_notice_slug:
            selected_notice = notices_by_slug.get(explicit_notice_slug)
        if selected_notice is None and notice_candidates:
            selected_notice = notice_candidates[0]
        if selected_notice is not None:
            front_items.append(
                PlayFrontItemNavigation(
                    kind="piece_notice",
                    label="Notice de pièce",
                    href=f"notices/{selected_notice.slug}.html",
                )
            )

        explicit_prefaces = [
            prefaces_by_slug.get(slug) or notices_by_slug.get(slug)
            for slug in explicit_prefaces_by_play.get(play.slug, ())
        ]
        associated_prefaces = prefaces_by_play.get(play.slug, [])
        merged_prefaces: list[NoticeEntry] = []
        seen_prefaces: set[str] = set()
        for preface in [item for item in (*explicit_prefaces, *associated_prefaces) if item is not None]:
            if preface.slug in seen_prefaces:
                continue
            seen_prefaces.add(preface.slug)
            merged_prefaces.append(preface)
        preface_candidates = _order_prefaces_for_play(
            merged_prefaces,
            explicit_order=explicit_prefaces_by_play.get(play.slug, ()),
        )
        for index, preface in enumerate(preface_candidates, start=1):
            label = "Préface de l'auteur" if len(preface_candidates) == 1 else f"Préface {index}"
            front_items.append(
                PlayFrontItemNavigation(
                    kind="author_preface",
                    label=label,
                    href=f"notices/{preface.slug}.html",
                )
            )

        for front_item in base.front_items:
            if front_item.kind == "dramatis_personae":
                front_items.append(front_item)
        for front_item in base.front_items:
            if front_item.kind != "dramatis_personae":
                front_items.append(front_item)

        composed.append(replace(base, front_items=tuple(front_items)))

    return tuple(composed)


def _entry_nav_kind(entry: NoticeEntry) -> str:
    if entry.editorial_role == "author_preface":
        return "preface"
    if entry.notice_kind == "master_volume":
        return "notice_volume"
    return "notice"


def _entry_page_kind(entry: NoticeEntry, *, general_notice_slug: str | None) -> str:
    if entry.slug == (general_notice_slug or ""):
        return "notice_general"
    if entry.editorial_role == "author_preface":
        return "preface"
    return "notice_volume" if entry.notice_kind == "master_volume" else "notice"


def _build_navigation_tree(
    *,
    plays: list[PlayEntry],
    play_navigation: tuple[PlayNavigation, ...],
    notices: list[NoticeEntry],
    general_notice_slug: str | None,
) -> tuple[NavigationItem, ...]:
    navigation: list[NavigationItem] = [NavigationItem(label="Accueil", href="index.html", kind="index")]
    attached_notice_slugs: set[str] = set()

    if general_notice_slug:
        navigation.append(
            NavigationItem(
                label="Introduction générale",
                href=f"notices/{general_notice_slug}.html",
                kind="notice_general",
            )
        )

    play_nav_by_slug = {item.play_slug: item for item in play_navigation}
    play_nodes: list[NavigationItem] = []
    for play in plays:
        structure = play_nav_by_slug.get(play.slug, PlayNavigation(play_slug=play.slug, play_title=play.title))
        children: list[NavigationItem] = []

        for front_item in structure.front_items:
            if front_item.href.startswith("notices/") and front_item.href.endswith(".html"):
                slug = front_item.href.removeprefix("notices/").removesuffix(".html")
                if slug:
                    attached_notice_slugs.add(slug)
            children.append(
                NavigationItem(
                    label=front_item.label,
                    href=front_item.href,
                    kind=front_item.kind,
                )
            )

        for act in structure.acts:
            scene_nodes = tuple(
                NavigationItem(
                    label=scene.label,
                    href=f"plays/{play.slug}.html#{scene.anchor_id}",
                    kind="scene",
                )
                for scene in act.scenes
            )
            children.append(
                NavigationItem(
                    label=act.label,
                    href=f"plays/{play.slug}.html#{act.anchor_id}",
                    kind="act",
                    children=scene_nodes,
                )
            )

        play_nodes.append(
            NavigationItem(
                label=play.title,
                href="",
                kind="play_group",
                children=tuple(children),
            )
        )

    if play_nodes:
        navigation.append(NavigationItem(label="Pièces", href="", kind="plays_group", children=tuple(play_nodes)))

    uncategorized_notices = [
        notice
        for notice in notices
        if notice.related_play_slug is None
        and notice.slug != (general_notice_slug or "")
        and notice.slug not in attached_notice_slugs
        and notice.editorial_role != "author_preface"
    ]
    if uncategorized_notices:
        navigation.extend(
            NavigationItem(
                label=notice.title,
                href=f"notices/{notice.slug}.html",
                kind=_entry_nav_kind(notice),
            )
            for notice in sorted(uncategorized_notices, key=lambda item: item.slug)
        )

    return tuple(navigation)


def _should_keep_notice(entry: NoticeEntry, *, publish_notices: bool, publish_prefaces: bool) -> bool:
    if entry.editorial_role == "author_preface":
        return publish_prefaces
    return publish_notices


def build_site_manifest(config: SiteConfig) -> SiteManifest:
    warnings: list[str] = []

    plays: list[PlayEntry] = []
    for xml_path in _discover_xml_files(config.dramatic_xml_dir):
        try:
            plays.append(extract_play_entry(xml_path))
        except SiteBuilderExtractionError as exc:
            warnings.append(str(exc))
    plays = _order_plays(plays, play_order=config.play_order, warnings=warnings)

    play_dramatis_sources = _resolve_play_dramatis_sources(config=config, plays=plays, warnings=warnings)
    play_navigation = _collect_play_navigation(plays, warnings, play_dramatis_sources=play_dramatis_sources)

    notices: list[NoticeEntry] = []
    load_notice_like_docs = config.publish_notices or config.publish_prefaces
    if load_notice_like_docs:
        if config.notice_xml_dir is None:
            warnings.append("Notice/preface publication is enabled but notice_xml_dir is not configured.")
        else:
            xml_files = _discover_xml_files(config.notice_xml_dir)
            if not xml_files:
                warnings.append(f"No notice XML files found in '{config.notice_xml_dir}'.")
            for xml_path in xml_files:
                try:
                    notices.append(
                        extract_notice_entry(
                            xml_path,
                            resolve_xincludes=config.resolve_notice_xincludes,
                        )
                    )
                except SiteBuilderExtractionError as exc:
                    warnings.append(str(exc))

    notices = [
        notice
        for notice in notices
        if _should_keep_notice(
            notice,
            publish_notices=config.publish_notices,
            publish_prefaces=config.publish_prefaces,
        )
    ]

    notices = _associate_notices_with_plays(plays, notices)
    if config.publish_notices:
        notices = _apply_explicit_play_notice_map(
            notices,
            play_notice_map=config.play_notice_map,
            warnings=warnings,
        )
    if config.publish_prefaces:
        notices = _apply_explicit_play_preface_map(
            notices,
            play_preface_map=config.play_preface_map,
            warnings=warnings,
        )

    if config.publish_notices:
        notices, general_notice_slug = _apply_general_notice_selection(
            notices,
            general_notice_slug=config.general_notice_slug,
            warnings=warnings,
        )
    else:
        general_notice_slug = None

    play_slugs = {play.slug for play in plays}
    for play_slug, notice_slug in config.play_notice_map:
        if play_slug not in play_slugs:
            warnings.append(
                f"Configured play_notice_map entry '{play_slug} -> {notice_slug}' references unknown play slug."
            )
    for play_slug, preface_slugs in config.play_preface_map:
        if play_slug not in play_slugs:
            warnings.append(
                f"Configured play_preface_map entry '{play_slug} -> {', '.join(preface_slugs)}' references unknown play slug."
            )
    for play_slug, dramatis_slug in config.play_dramatis_map:
        if play_slug not in play_slugs:
            warnings.append(
                f"Configured play_dramatis_map entry '{play_slug} -> {dramatis_slug}' references unknown play slug."
            )

    plays, notices = _with_download_paths(config, plays, notices)
    play_navigation = _compose_play_navigation(
        plays=plays,
        play_navigation=play_navigation,
        notices=notices,
        play_notice_map=config.play_notice_map if config.publish_notices else (),
        play_preface_map=config.play_preface_map if config.publish_prefaces else (),
    )

    pages: list[SitePage] = [SitePage(kind="index", title=config.site_title, output_relpath="index.html")]
    for play in plays:
        pages.append(
            SitePage(
                kind="play",
                title=play.title,
                output_relpath=f"plays/{play.slug}.html",
                source_slug=play.slug,
            )
        )
    for notice in notices:
        pages.append(
            SitePage(
                kind=_entry_page_kind(notice, general_notice_slug=general_notice_slug),
                title=notice.title,
                output_relpath=f"notices/{notice.slug}.html",
                source_slug=notice.slug,
            )
        )

    navigation = _build_navigation_tree(
        plays=plays,
        play_navigation=play_navigation,
        notices=notices,
        general_notice_slug=general_notice_slug,
    )

    return SiteManifest(
        config=config,
        plays=tuple(plays),
        play_navigation=play_navigation,
        notices=tuple(notices),
        pages=tuple(pages),
        navigation=navigation,
        general_notice_slug=general_notice_slug,
        warnings=tuple(warnings),
    )
