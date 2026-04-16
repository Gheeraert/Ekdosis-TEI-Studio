from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SiteBuildRequest:
    source: dict[str, object] | str | Path


@dataclass(frozen=True)
class SiteIdentityInput:
    site_title: str
    site_subtitle: str = ""
    project_name: str = ""
    editor: str = ""
    credits: str = ""
    homepage_intro: str = ""


@dataclass(frozen=True)
class SiteAssetsInput:
    logo_files: tuple[Path, ...] = ()
    asset_directories: tuple[Path, ...] = ()


@dataclass(frozen=True)
class DramaticDocumentInput:
    source_path: Path


@dataclass(frozen=True)
class DramaticPlayInput:
    play_slug: str
    documents: tuple[DramaticDocumentInput, ...]
    related_notice_slug: str | None = None


@dataclass(frozen=True)
class NoticeInput:
    source_path: Path


@dataclass(frozen=True)
class SitePublicationRequest:
    identity: SiteIdentityInput
    output_dir: Path
    plays: tuple[DramaticPlayInput, ...]
    play_order: tuple[str, ...] = ()
    notices: tuple[NoticeInput, ...] = ()
    assets: SiteAssetsInput = field(default_factory=SiteAssetsInput)
    show_xml_download: bool = False
    publish_notices: bool = True
    include_metadata: bool = True
    resolve_notice_xincludes: bool = True
    play_notice_map: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class SiteBuildServiceResult:
    ok: bool
    output_dir: Path | None = None
    generated_pages: tuple[Path, ...] = ()
    copied_assets: tuple[Path, ...] = ()
    warnings: tuple[str, ...] = ()
    play_count: int = 0
    notice_count: int = 0
    message: str | None = None
    error_code: str | None = None
    error_detail: str | None = None
    generated_page_relpaths: tuple[str, ...] = field(default_factory=tuple)
