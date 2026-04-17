from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .extractors import SiteBuilderExtractionError, extract_notice_entry, extract_play_entry
from .models import NavigationItem, NoticeEntry, PlayEntry, SiteConfig, SiteManifest, SitePage


def _discover_xml_files(directory: Path) -> list[Path]:
    if not directory.exists() or not directory.is_dir():
        return []
    return sorted((path for path in directory.rglob("*.xml") if path.is_file()), key=lambda item: item.as_posix())


def _with_download_paths(config: SiteConfig, plays: list[PlayEntry], notices: list[NoticeEntry]) -> tuple[list[PlayEntry], list[NoticeEntry]]:
    if not config.show_xml_download:
        return plays, notices

    mapped_plays = [
        replace(play, xml_download_relpath=f"xml/dramatic/{play.slug}.xml")
        for play in plays
    ]
    mapped_notices = [
        replace(notice, xml_download_relpath=f"xml/notices/{notice.slug}.xml")
        for notice in notices
    ]
    return mapped_plays, mapped_notices


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
        if notice.related_play_slug:
            mapped.append(notice)
            continue
        if notice.slug in play_slugs:
            mapped.append(replace(notice, related_play_slug=notice.slug))
            continue
        mapped.append(notice)
    return mapped


def _apply_explicit_play_notice_map(
    notices: list[NoticeEntry],
    *,
    play_notice_map: tuple[tuple[str, str], ...],
    warnings: list[str],
) -> list[NoticeEntry]:
    if not play_notice_map:
        return notices

    notice_by_slug = {notice.slug: notice for notice in notices}
    mapped: list[NoticeEntry] = []
    for notice in notices:
        mapped.append(notice)

    for play_slug, notice_slug in play_notice_map:
        target = notice_by_slug.get(notice_slug)
        if target is None:
            warnings.append(
                f"Configured play_notice_map entry '{play_slug} -> {notice_slug}' ignored: notice slug not found."
            )
            continue
        replaced = replace(target, related_play_slug=play_slug)
        mapped = [replaced if item.slug == notice_slug else item for item in mapped]
        notice_by_slug[notice_slug] = replaced
    return mapped


def _apply_general_notice_selection(
    notices: list[NoticeEntry],
    *,
    general_notice_slug: str,
    warnings: list[str],
) -> tuple[list[NoticeEntry], str | None]:
    if not general_notice_slug:
        return notices, None

    notice_by_slug = {notice.slug: notice for notice in notices}
    target = notice_by_slug.get(general_notice_slug)
    if target is None:
        warnings.append(
            f"Configured general_notice_slug '{general_notice_slug}' not found among detected notices."
        )
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


def _normalize_division_label(raw_label: str) -> str:
    cleaned = " ".join(raw_label.split())
    if not cleaned:
        return ""
    parts = cleaned.split(" ", 1)
    kind = parts[0].lower()
    suffix = parts[1] if len(parts) > 1 else ""
    if kind.startswith("act"):
        prefix = "Acte"
    elif kind.startswith("scene"):
        prefix = "Scene"
    else:
        prefix = parts[0].capitalize()
    return f"{prefix} {suffix}".strip()


def _play_division_tree(play: PlayEntry) -> tuple[tuple[str, tuple[str, ...]], ...]:
    acts: list[tuple[str, tuple[str, ...]]] = []
    current_act_label: str | None = None
    current_scenes: list[str] = []

    def flush_current() -> None:
        nonlocal current_act_label, current_scenes
        if current_act_label is None:
            return
        acts.append((current_act_label, tuple(current_scenes)))
        current_act_label = None
        current_scenes = []

    for division in play.main_divisions:
        label = _normalize_division_label(division)
        lowered = division.strip().lower()
        if lowered.startswith("act"):
            flush_current()
            current_act_label = label or "Acte"
            current_scenes = []
            continue
        if lowered.startswith("scene"):
            if current_act_label is None:
                current_act_label = "Scenes"
                current_scenes = []
            current_scenes.append(label or "Scene")

    flush_current()
    return tuple(acts)


def _build_navigation_tree(
    *,
    plays: list[PlayEntry],
    notices: list[NoticeEntry],
    general_notice_slug: str | None,
) -> tuple[NavigationItem, ...]:
    navigation: list[NavigationItem] = [NavigationItem(label="Accueil", href="index.html", kind="index")]

    notice_by_play_slug: dict[str, NoticeEntry] = {}
    for notice in notices:
        if notice.related_play_slug and notice.related_play_slug not in notice_by_play_slug:
            notice_by_play_slug[notice.related_play_slug] = notice

    if general_notice_slug:
        navigation.append(
            NavigationItem(
                label="Notice generale",
                href=f"notices/{general_notice_slug}.html",
                kind="notice_general",
            )
        )

    play_nodes: list[NavigationItem] = []
    for play in plays:
        children: list[NavigationItem] = [
            NavigationItem(
                label="Lecture",
                href=f"plays/{play.slug}.html",
                kind="play_page",
            )
        ]

        related_notice = notice_by_play_slug.get(play.slug)
        if related_notice is not None:
            children.append(
                NavigationItem(
                    label="Notice de piece",
                    href=f"notices/{related_notice.slug}.html",
                    kind="notice",
                )
            )

        for act_label, scenes in _play_division_tree(play):
            scene_nodes = tuple(
                NavigationItem(
                    label=scene_label,
                    href=f"plays/{play.slug}.html",
                    kind="scene",
                )
                for scene_label in scenes
            )
            children.append(
                NavigationItem(
                    label=act_label,
                    href=f"plays/{play.slug}.html",
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
        navigation.append(
            NavigationItem(
                label="Pieces",
                href="",
                kind="plays_group",
                children=tuple(play_nodes),
            )
        )

    uncategorized_notices = [
        notice
        for notice in notices
        if notice.related_play_slug is None and notice.slug != (general_notice_slug or "")
    ]
    if uncategorized_notices:
        navigation.append(
            NavigationItem(
                label="Notices",
                href="",
                kind="notices_group",
                children=tuple(
                    NavigationItem(
                        label=notice.title,
                        href=f"notices/{notice.slug}.html",
                        kind="notice_volume" if notice.notice_kind == "master_volume" else "notice",
                    )
                    for notice in uncategorized_notices
                ),
            )
        )

    return tuple(navigation)


def build_site_manifest(config: SiteConfig) -> SiteManifest:
    warnings: list[str] = []

    plays: list[PlayEntry] = []
    for xml_path in _discover_xml_files(config.dramatic_xml_dir):
        try:
            plays.append(extract_play_entry(xml_path))
        except SiteBuilderExtractionError as exc:
            warnings.append(str(exc))
    plays = _order_plays(plays, play_order=config.play_order, warnings=warnings)

    notices: list[NoticeEntry] = []
    if config.publish_notices:
        if config.notice_xml_dir is None:
            warnings.append("Notice publication is enabled but notice_xml_dir is not configured.")
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

    notices = _associate_notices_with_plays(plays, notices)
    notices = _apply_explicit_play_notice_map(
        notices,
        play_notice_map=config.play_notice_map,
        warnings=warnings,
    )
    notices, general_notice_slug = _apply_general_notice_selection(
        notices,
        general_notice_slug=config.general_notice_slug,
        warnings=warnings,
    )
    if config.play_notice_map:
        play_slugs = {play.slug for play in plays}
        for play_slug, notice_slug in config.play_notice_map:
            if play_slug not in play_slugs:
                warnings.append(
                    f"Configured play_notice_map entry '{play_slug} -> {notice_slug}' references unknown play slug."
                )
    plays, notices = _with_download_paths(config, plays, notices)

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
    if config.publish_notices:
        for notice in notices:
            if notice.slug == general_notice_slug:
                notice_page_kind = "notice_general"
            else:
                notice_page_kind = "notice_volume" if notice.notice_kind == "master_volume" else "notice"
            pages.append(
                SitePage(
                    kind=notice_page_kind,
                    title=notice.title,
                    output_relpath=f"notices/{notice.slug}.html",
                    source_slug=notice.slug,
                )
            )

    navigation = _build_navigation_tree(
        plays=plays,
        notices=notices if config.publish_notices else [],
        general_notice_slug=general_notice_slug if config.publish_notices else None,
    )

    return SiteManifest(
        config=config,
        plays=tuple(plays),
        notices=tuple(notices),
        pages=tuple(pages),
        navigation=navigation,
        general_notice_slug=general_notice_slug if config.publish_notices else None,
        warnings=tuple(warnings),
    )
