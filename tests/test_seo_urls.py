from __future__ import annotations

import pytest

from ets.seo import absolute_url, normalize_base_url


def test_normalize_base_url_returns_none_when_absent() -> None:
    assert normalize_base_url(None) is None
    assert normalize_base_url("") is None
    assert normalize_base_url("   ") is None


def test_normalize_base_url_strips_trailing_slash() -> None:
    assert normalize_base_url("https://example.org/edition/") == "https://example.org/edition"
    assert normalize_base_url("https://example.org") == "https://example.org"


def test_normalize_base_url_rejects_non_http_values() -> None:
    with pytest.raises(ValueError, match="site_base_url"):
        normalize_base_url("example.org")

    with pytest.raises(ValueError, match="site_base_url"):
        normalize_base_url("ftp://example.org")


def test_absolute_url_returns_none_without_base_url() -> None:
    assert absolute_url(None, "pieces/andromaque.html") is None


def test_absolute_url_joins_base_and_relpath() -> None:
    base_url = normalize_base_url("https://example.org/edition/")
    assert absolute_url(base_url, "pieces/andromaque.html") == (
        "https://example.org/edition/pieces/andromaque.html"
    )
    assert absolute_url(base_url, "/pieces/andromaque.html") == (
        "https://example.org/edition/pieces/andromaque.html"
    )


def test_absolute_url_rejects_empty_relpath() -> None:
    base_url = normalize_base_url("https://example.org")
    with pytest.raises(ValueError, match="relpath"):
        absolute_url(base_url, "")
