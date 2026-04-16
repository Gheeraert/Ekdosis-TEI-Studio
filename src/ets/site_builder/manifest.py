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
            notice_page_kind = "notice_volume" if notice.notice_kind == "master_volume" else "notice"
            pages.append(
                SitePage(
                    kind=notice_page_kind,
                    title=notice.title,
                    output_relpath=f"notices/{notice.slug}.html",
                    source_slug=notice.slug,
                )
            )

    navigation: list[NavigationItem] = [NavigationItem(label="Accueil", href="index.html", kind="index")]
    navigation.extend(
        NavigationItem(label=play.title, href=f"plays/{play.slug}.html", kind="play")
        for play in plays
    )
    if config.publish_notices:
        navigation.extend(
            NavigationItem(
                label=f"Notice - {notice.title}",
                href=f"notices/{notice.slug}.html",
                kind="notice_volume" if notice.notice_kind == "master_volume" else "notice",
            )
            for notice in notices
        )

    return SiteManifest(
        config=config,
        plays=tuple(plays),
        notices=tuple(notices),
        pages=tuple(pages),
        navigation=tuple(navigation),
        warnings=tuple(warnings),
    )
