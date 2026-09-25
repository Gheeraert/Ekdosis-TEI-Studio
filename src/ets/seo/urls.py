from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

_ALLOWED_SCHEMES = ("http", "https")


def normalize_base_url(value: Any) -> str | None:
    """Normalize an optional public site URL used for SEO outputs.

    Returns ``None`` when no base URL is configured, so callers can degrade
    gracefully (no sitemap, no canonical/OpenGraph tags) instead of emitting
    invalid absolute URLs. Never used by the DTS static export, which must
    keep its own paths relative regardless of this setting.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None

    parsed = urlsplit(text)
    if parsed.scheme not in _ALLOWED_SCHEMES or not parsed.netloc:
        raise ValueError(
            "Invalid site configuration: 'site_base_url' must be an absolute http(s) URL."
        )
    return text.rstrip("/")


def absolute_url(base_url: str | None, relpath: str) -> str | None:
    """Join a normalized base URL with a site-relative path.

    Returns ``None`` when ``base_url`` is not configured. ``relpath`` must be
    a relative, non-empty path (as produced by the site builder), never an
    absolute URL or a path escaping the site root.
    """
    if base_url is None:
        return None
    clean_relpath = relpath.strip().lstrip("/")
    if not clean_relpath:
        raise ValueError("Invalid relpath: expected a non-empty relative path.")
    return f"{base_url}/{clean_relpath}"
