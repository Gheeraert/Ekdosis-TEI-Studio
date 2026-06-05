from __future__ import annotations

from pathlib import Path

from ets.application.site_publication_config import SitePublicationDialogConfig

from .templates import render_publication_pdf_master


def build_publication_pdf_master(
    prepared_config: SitePublicationDialogConfig,
    build_dir: str | Path,
) -> Path:
    """Write a provisional LaTeX master for a prepared publication config."""
    target_dir = Path(build_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    master_path = target_dir / "master.tex"
    master_path.write_text(render_publication_pdf_master(prepared_config), encoding="utf-8")
    return master_path.resolve()
