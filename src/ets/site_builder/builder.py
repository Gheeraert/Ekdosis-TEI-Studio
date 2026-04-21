from __future__ import annotations

from dataclasses import replace
import shutil
import time
from pathlib import Path

from .config import load_site_config
from .manifest import build_site_manifest
from .models import BuildResult, NoticeEntry, PlayEntry, SiteConfig
from .render import render_home_page, render_notice_page, render_play_page

_SUPPORTED_AUTO_LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".webp"}


def _write_page(output_root: Path, relpath: str, html_content: str) -> Path:
    target = (output_root / relpath).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html_content, encoding="utf-8")
    return target


def _prepare_output_dir(output_root: Path) -> None:
    resolved = output_root.resolve()
    dangerous_targets = {Path(resolved.anchor).resolve()}
    try:
        dangerous_targets.add(Path.home().resolve())
    except RuntimeError:
        pass

    if resolved in dangerous_targets:
        raise ValueError(f"Refusing to clean unsafe output directory: {resolved}")

    if resolved.exists():
        def _on_remove_error(func, path, excinfo):  # type: ignore[no-untyped-def]
            target = Path(path)
            try:
                target.chmod(0o666)
            except OSError:
                pass
            last_error: Exception | None = None
            for _ in range(5):
                try:
                    func(path)
                    return
                except OSError as error:
                    last_error = error
                    time.sleep(0.05)
            if last_error is not None:
                raise last_error

        shutil.rmtree(resolved, onexc=_on_remove_error)
    resolved.mkdir(parents=True, exist_ok=True)


def _copy_assets(config: SiteConfig, output_root: Path, warnings: list[str]) -> list[Path]:
    copied: list[Path] = []
    for logo in config.assets.logo_files:
        if not logo.exists():
            warnings.append(f"Logo not found: {logo}")
            continue
        target = output_root / "assets" / "logos" / logo.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(logo, target)
        copied.append(target.resolve())

    for directory in config.assets.asset_directories:
        if not directory.exists() or not directory.is_dir():
            warnings.append(f"Asset directory not found: {directory}")
            continue
        target = output_root / "assets" / directory.name
        shutil.copytree(directory, target, dirs_exist_ok=True)
        copied.append(target.resolve())
    return copied


def _auto_detect_logo_files(config: SiteConfig) -> tuple[Path, ...]:
    start = config.dramatic_xml_dir.resolve()

    candidates = []
    if start.is_dir():
        candidates.append(start)
    candidates.extend(start.parents)

    for base in candidates:
        logos_dir = base / "assets" / "logos"
        if not logos_dir.exists() or not logos_dir.is_dir():
            continue

        detected = [
            candidate.resolve()
            for candidate in logos_dir.iterdir()
            if candidate.is_file() and candidate.suffix.lower() in _SUPPORTED_AUTO_LOGO_EXTENSIONS
        ]
        detected.sort(key=lambda path: path.name.casefold())
        return tuple(detected)

    return ()


def _resolve_logo_files(config: SiteConfig) -> tuple[Path, ...]:
    detected = _auto_detect_logo_files(config)
    if detected:
        return detected
    return config.assets.logo_files


def _copy_xml_sources(
    *,
    output_root: Path,
    plays: tuple[PlayEntry, ...],
    notices: tuple[NoticeEntry, ...],
) -> None:
    for play in plays:
        if not play.xml_download_relpath:
            continue
        target = output_root / play.xml_download_relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(play.source_path, target)

    for notice in notices:
        if not notice.xml_download_relpath:
            continue
        target = output_root / notice.xml_download_relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(notice.source_path, target)


def build_static_site(config: SiteConfig) -> BuildResult:
    normalized_config = load_site_config(config)
    resolved_logos = _resolve_logo_files(normalized_config)
    if resolved_logos != normalized_config.assets.logo_files:
        normalized_config = replace(
            normalized_config,
            assets=replace(normalized_config.assets, logo_files=resolved_logos),
        )

    manifest = build_site_manifest(normalized_config)
    output_root = normalized_config.output_dir.resolve()
    _prepare_output_dir(output_root)

    warnings = list(manifest.warnings)
    generated_pages: list[Path] = []

    play_by_slug = {play.slug: play for play in manifest.plays}
    notice_by_slug = {notice.slug: notice for notice in manifest.notices}

    for page in manifest.pages:
        if page.kind == "index":
            html_content = render_home_page(manifest)
        elif page.kind == "play":
            play = play_by_slug.get(page.source_slug or "")
            if play is None:
                warnings.append(f"Missing play entry for slug '{page.source_slug}'.")
                continue
            html_content = render_play_page(manifest, play)
        elif page.kind in {"notice", "notice_volume", "notice_general", "preface"}:
            notice = notice_by_slug.get(page.source_slug or "")
            if notice is None:
                warnings.append(f"Missing notice entry for slug '{page.source_slug}'.")
                continue
            html_content = render_notice_page(manifest, notice)
        else:
            warnings.append(f"Unknown page kind '{page.kind}' for '{page.output_relpath}'.")
            continue
        generated_pages.append(_write_page(output_root, page.output_relpath, html_content))

    copied_assets = _copy_assets(normalized_config, output_root, warnings)
    _copy_xml_sources(output_root=output_root, plays=manifest.plays, notices=manifest.notices)

    return BuildResult(
        output_dir=output_root,
        play_count=len(manifest.plays),
        notice_count=len(manifest.notices),
        generated_pages=tuple(generated_pages),
        copied_assets=tuple(copied_assets),
        warnings=tuple(warnings),
    )
