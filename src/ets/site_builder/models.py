from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AssetConfig:
    logo_files: tuple[Path, ...] = ()
    asset_directories: tuple[Path, ...] = ()


@dataclass(frozen=True)
class HomePageSection:
    title: str
    paragraphs: tuple[str, ...] = ()


@dataclass(frozen=True)
class SiteConfig:
    site_title: str
    site_subtitle: str = ""
    dramatic_xml_dir: Path = Path(".")
    notice_xml_dir: Path | None = None
    dramatis_xml_dir: Path | None = None
    output_dir: Path = Path("out/site")
    assets: AssetConfig = field(default_factory=AssetConfig)
    show_xml_download: bool = False
    publish_notices: bool = True
    publish_prefaces: bool = True
    include_metadata: bool = True
    resolve_notice_xincludes: bool = True
    project_name: str = ""
    editor: str = ""
    credits: str = ""
    homepage_intro: str = ""
    homepage_sections: tuple[HomePageSection, ...] = ()
    general_notice_slug: str = ""
    home_page_notice_slug: str = ""
    play_notice_map: tuple[tuple[str, str], ...] = ()
    play_preface_map: tuple[tuple[str, tuple[str, ...]], ...] = ()
    play_dramatis_map: tuple[tuple[str, str], ...] = ()
    play_order: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlayEntry:
    source_path: Path
    slug: str
    title: str
    author: str | None
    document_type: str
    main_divisions: tuple[str, ...] = ()
    has_text_body: bool = False
    xml_download_relpath: str | None = None


@dataclass(frozen=True)
class PlaySceneNavigation:
    label: str
    anchor_id: str
    start_speech_index: int


@dataclass(frozen=True)
class PlayActNavigation:
    label: str
    anchor_id: str
    start_speech_index: int
    scenes: tuple[PlaySceneNavigation, ...] = ()


@dataclass(frozen=True)
class PlayFrontItemNavigation:
    kind: str
    label: str
    href: str
    anchor_id: str | None = None


@dataclass(frozen=True)
class PlayNavigation:
    play_slug: str
    play_title: str
    front_items: tuple[PlayFrontItemNavigation, ...] = ()
    dramatis_personae: tuple[str, ...] = ()
    acts: tuple[PlayActNavigation, ...] = ()


@dataclass(frozen=True)
class NoticeEntry:
    source_path: Path
    slug: str
    title: str
    subtitle: str | None
    author: str | None
    document_type: str
    authors: tuple[str, ...] = ()
    notice_kind: str = "standalone"
    has_text_body: bool = False
    related_play_slug: str | None = None
    editorial_role: str = "notice"
    xml_download_relpath: str | None = None
    document: "NoticeDocument | None" = None


@dataclass(frozen=True)
class NoticeNote:
    note_id: str
    label: str
    text: str


@dataclass(frozen=True)
class NoticeSection:
    section_id: str
    title: str
    kind: str
    level: int
    node_kind: str = "section"
    subtitle: str | None = None
    authors: tuple[str, ...] = ()
    text_type: str | None = None
    source_path: Path | None = None
    paragraphs: tuple[str, ...] = ()
    items: tuple[str, ...] = ()
    children: tuple["NoticeSection", ...] = ()


@dataclass(frozen=True)
class NoticeTocEntry:
    entry_id: str
    title: str
    level: int
    children: tuple["NoticeTocEntry", ...] = ()


@dataclass(frozen=True)
class NoticeDocument:
    source_path: Path
    slug: str
    title: str
    subtitle: str | None
    authors: tuple[str, ...]
    text_type: str
    notice_kind: str
    has_text_body: bool
    front_title_page: tuple[str, ...] = ()
    sections: tuple[NoticeSection, ...] = ()
    toc: tuple[NoticeTocEntry, ...] = ()
    notes: tuple[NoticeNote, ...] = ()
    include_warnings: tuple[str, ...] = ()
    included_documents: tuple[Path, ...] = ()
    related_play_slug: str | None = None
    editorial_role: str = "notice"


@dataclass(frozen=True)
class SitePage:
    kind: str
    title: str
    output_relpath: str
    source_slug: str | None = None


@dataclass(frozen=True)
class NavigationItem:
    label: str
    href: str
    kind: str
    children: tuple["NavigationItem", ...] = ()


@dataclass(frozen=True)
class SiteManifest:
    config: SiteConfig
    plays: tuple[PlayEntry, ...] = ()
    play_navigation: tuple[PlayNavigation, ...] = ()
    notices: tuple[NoticeEntry, ...] = ()
    pages: tuple[SitePage, ...] = ()
    navigation: tuple[NavigationItem, ...] = ()
    general_notice_slug: str | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class BuildResult:
    output_dir: Path
    play_count: int
    notice_count: int
    generated_pages: tuple[Path, ...] = ()
    copied_assets: tuple[Path, ...] = ()
    warnings: tuple[str, ...] = ()
