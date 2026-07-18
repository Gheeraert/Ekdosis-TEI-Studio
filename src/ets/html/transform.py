from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from lxml import etree

from .fonts import render_inline_font_style


def default_xslt_path() -> Path:
    return Path(__file__).resolve().parents[1] / "resources" / "xslt" / "tei-vers-html.xsl"


@lru_cache(maxsize=4)
def _load_xslt(xslt_path: str) -> etree.XSLT:
    path = Path(xslt_path)
    if not path.exists():
        raise FileNotFoundError(f"XSLT file not found: {path}")
    xslt_doc = etree.parse(str(path))
    return etree.XSLT(xslt_doc)


def render_html_preview_from_tei(
    tei_xml: str,
    xslt_path: str | Path | None = None,
    *,
    embed_fonts: bool = True,
) -> str:
    """Render a fast preview HTML from TEI XML using the packaged XSLT stylesheet.

    Par défaut, les polices sont incluses en data-URI pour produire un aperçu
    autoporteur, lisible hors ligne et sans requête externe. Le site statique
    passe ``embed_fonts=False`` et sert les WOFF2 depuis ses propres assets.
    """
    chosen_path = Path(xslt_path) if xslt_path is not None else default_xslt_path()
    transform = _load_xslt(str(chosen_path.resolve()))
    source_doc = etree.fromstring(tei_xml.encode("utf-8"))
    result = transform(source_doc)
    html = etree.tostring(result, encoding="unicode", method="html")
    if embed_fonts:
        head_start = html.find("<head>")
        if head_start >= 0:
            insert_at = head_start + len("<head>")
            html = html[:insert_at] + render_inline_font_style() + html[insert_at:]
    return html

