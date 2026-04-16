from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SiteBuildRequest:
    source: dict[str, object] | str | Path


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

