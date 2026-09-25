from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit, urlunsplit

_ALLOWED_SCHEMES = ("http", "https")


def normalize_base_url(value: Any) -> str | None:
    """Normalize an optional public site URL used for SEO outputs.

    Returns ``None`` when no base URL is configured, so callers can degrade
    gracefully (no sitemap, no canonical/OpenGraph tags) instead of emitting
    invalid absolute URLs. Never used by the DTS static export, which must
    keep its own paths relative regardless of this setting.

    Rejects anything that is not a plain "scheme://host[:port][/path]" value:
    a query string or fragment would end up concatenated into every
    canonical/OpenGraph/sitemap URL and silently point at the wrong page (or
    leak a tracking parameter into every published page); embedded user
    credentials would be published the same way. The URL is rebuilt from its
    validated components rather than kept as raw text, so nothing beyond
    scheme/host/port/path can slip through.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None

    parsed = urlsplit(text)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(
            "Invalid site configuration: 'site_base_url' must use http or https."
        )
    if not parsed.hostname:
        raise ValueError(
            "Invalid site configuration: 'site_base_url' must include a host name."
        )
    if parsed.username or parsed.password:
        raise ValueError(
            "Invalid site configuration: 'site_base_url' must not include user credentials."
        )
    if parsed.query:
        raise ValueError(
            "Invalid site configuration: 'site_base_url' must not include a query string."
        )
    if parsed.fragment:
        raise ValueError(
            "Invalid site configuration: 'site_base_url' must not include a fragment."
        )

    netloc = parsed.hostname
    if parsed.port is not None:
        netloc = f"{netloc}:{parsed.port}"
    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme, netloc, path, "", ""))


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
