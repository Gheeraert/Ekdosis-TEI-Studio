from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AssetConfig:
    logo_files: tuple[Path, ...] = ()
    asset_directories: tuple[Path, ...] = ()


@dataclass(frozen=True)
class SiteConfig:
    site_title: str
    site_subtitle: str = ""
    dramatic_xml_dir: Path = Path(".")
    notice_xml_dir: Path | None = None
    output_dir: Path = Path("out/site")
    assets: AssetConfig = field(default_factory=AssetConfig)
    show_xml_download: bool = False
    publish_notices: bool = True
    include_metadata: bool = True
    project_name: str = ""
    editor: str = ""
    credits: str = ""


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
class NoticeEntry:
    source_path: Path
    slug: str
    title: str
    author: str | None
    document_type: str
    has_text_body: bool = False
    related_play_slug: str | None = None
    xml_download_relpath: str | None = None


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


@dataclass(frozen=True)
class SiteManifest:
    config: SiteConfig
    plays: tuple[PlayEntry, ...] = ()
    notices: tuple[NoticeEntry, ...] = ()
    pages: tuple[SitePage, ...] = ()
    navigation: tuple[NavigationItem, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class BuildResult:
    output_dir: Path
    play_count: int
    notice_count: int
    generated_pages: tuple[Path, ...] = ()
    copied_assets: tuple[Path, ...] = ()
    warnings: tuple[str, ...] = ()
