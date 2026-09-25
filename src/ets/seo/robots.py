from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import urlsplit

# Raw download/export directories that duplicate content already indexable
# through the HTML pages (TEI XML, plain text, PDF, the DTS static export,
# the search index payload). Disallowing them saves crawl budget on
# near-duplicate, non-HTML content; it does NOT guarantee they stay out of
# search results (a disallowed URL can still be indexed without a snippet),
# and it never blocks direct access by a DTS-aware tool or a reader with a
# direct link.
DEFAULT_DISALLOWED_PATHS: tuple[str, ...] = (
    "/xml/",
    "/txt/",
    "/downloads/",
    "/api/dts/",
    "/search/index.json",
)


def robots_txt_url_path(base_url: str) -> str:
    """Return the path prefix (if any) under which the site is published.

    ``base_url`` is expected to already be normalized (see
    ``ets.seo.urls.normalize_base_url``). An empty string means the site is
    published at the domain root.
    """
    return urlsplit(base_url).path


def build_robots_txt(
    base_url: str | None,
    *,
    disallowed_paths: Iterable[str] = DEFAULT_DISALLOWED_PATHS,
) -> str:
    """Build a robots.txt document.

    Returns an empty string when ``base_url`` is not configured: without a
    known public URL there is no meaningful ``Sitemap:`` directive to emit,
    and callers should skip writing robots.txt entirely in that case
    (mirrors the sitemap.xml degradation).

    ``Disallow`` rules are prefixed with ``base_url``'s own path component,
    so they still match reality when the site is published under a
    subdirectory. This does not make the file effective on its own in that
    case: robots.txt is only ever read by crawlers at the web server's
    domain root, never inside a published subdirectory. Callers publishing
    under a subdirectory must warn the operator to install this file at
    their domain root manually (see ``robots_txt_url_path``).
    """
    if not base_url:
        return ""

    url_path = robots_txt_url_path(base_url).rstrip("/")
    lines = ["User-agent: *"]
    lines.extend(f"Disallow: {url_path}{path}" for path in disallowed_paths)
    lines.append("")
    lines.append(f"Sitemap: {base_url}/sitemap.xml")
    return "\n".join(lines) + "\n"
