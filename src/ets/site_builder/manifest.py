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


def build_site_manifest(config: SiteConfig) -> SiteManifest:
    warnings: list[str] = []

    plays: list[PlayEntry] = []
    for xml_path in _discover_xml_files(config.dramatic_xml_dir):
        try:
            plays.append(extract_play_entry(xml_path))
        except SiteBuilderExtractionError as exc:
            warnings.append(str(exc))

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
                    notices.append(extract_notice_entry(xml_path))
                except SiteBuilderExtractionError as exc:
                    warnings.append(str(exc))

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
            pages.append(
                SitePage(
                    kind="notice",
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
            NavigationItem(label=f"Notice - {notice.title}", href=f"notices/{notice.slug}.html", kind="notice")
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
