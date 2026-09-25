from __future__ import annotations

from collections.abc import Iterable
from xml.sax.saxutils import escape

from .urls import absolute_url

_SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"


def build_sitemap_xml(base_url: str, relpaths: Iterable[str]) -> str:
    """Build a sitemap.xml document listing the given site-relative pages.

    ``base_url`` must already be a normalized, absolute http(s) URL (see
    ``ets.seo.urls.normalize_base_url``); callers should skip generating a
    sitemap entirely when no base URL is configured, rather than passing a
    placeholder here.
    """
    url_entries = []
    for relpath in relpaths:
        loc = absolute_url(base_url, relpath)
        url_entries.append(f"  <url>\n    <loc>{escape(loc)}</loc>\n  </url>")

    body = "\n".join(url_entries)
    body_block = f"{body}\n" if body else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="{_SITEMAP_NAMESPACE}">\n'
        f"{body_block}"
        "</urlset>\n"
    )
