from __future__ import annotations

from .opengraph import open_graph_head_html
from .schema_reference import ODD_RELPATH, describedby_link_html
from .sitemap import build_sitemap_xml
from .structured_data import book_json_ld_html
from .urls import absolute_url, normalize_base_url

__all__ = [
    "absolute_url",
    "normalize_base_url",
    "open_graph_head_html",
    "book_json_ld_html",
    "ODD_RELPATH",
    "describedby_link_html",
    "build_sitemap_xml",
]
