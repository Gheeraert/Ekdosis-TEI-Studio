from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from lxml import etree


def default_xslt_path() -> Path:
    return Path(__file__).resolve().parents[3] / "tei-vers-html.xsl"


@lru_cache(maxsize=4)
def _load_xslt(xslt_path: str) -> etree.XSLT:
    path = Path(xslt_path)
    if not path.exists():
        raise FileNotFoundError(f"XSLT file not found: {path}")
    xslt_doc = etree.parse(str(path))
    return etree.XSLT(xslt_doc)


def render_html_preview_from_tei(tei_xml: str, xslt_path: str | Path | None = None) -> str:
    """Render a fast preview HTML from TEI XML using the repository XSLT file."""
    chosen_path = Path(xslt_path) if xslt_path is not None else default_xslt_path()
    transform = _load_xslt(str(chosen_path.resolve()))
    source_doc = etree.fromstring(tei_xml.encode("utf-8"))
    result = transform(source_doc)
    return etree.tostring(result, encoding="unicode", method="html")

