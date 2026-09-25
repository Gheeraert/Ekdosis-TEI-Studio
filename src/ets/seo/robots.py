from __future__ import annotations

from collections.abc import Iterable

# Raw download/export directories that duplicate content already indexable
# through the HTML pages (TEI XML, plain text, PDF, the DTS static export,
# the search index payload). Blocking them from generic crawling avoids
# diluting search results with near-duplicate or non-HTML content; it does
# not prevent direct access by DTS-aware tools or readers with a direct link.
DEFAULT_DISALLOWED_PATHS: tuple[str, ...] = (
    "/xml/",
    "/txt/",
    "/downloads/",
    "/api/dts/",
    "/search/index.json",
)


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
    """
    if not base_url:
        return ""

    lines = ["User-agent: *"]
    lines.extend(f"Disallow: {path}" for path in disallowed_paths)
    lines.append("")
    lines.append(f"Sitemap: {base_url}/sitemap.xml")
    return "\n".join(lines) + "\n"
