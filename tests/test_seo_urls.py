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


def test_normalize_base_url_rejects_query_string() -> None:
    with pytest.raises(ValueError, match="query string"):
        normalize_base_url("https://example.org/edition?preview=1")


def test_normalize_base_url_rejects_fragment() -> None:
    with pytest.raises(ValueError, match="fragment"):
        normalize_base_url("https://example.org/edition#section")


def test_normalize_base_url_rejects_user_credentials() -> None:
    with pytest.raises(ValueError, match="credentials"):
        normalize_base_url("https://user:secret@example.org/edition")


def test_normalize_base_url_rejects_missing_host() -> None:
    with pytest.raises(ValueError, match="host"):
        normalize_base_url("https:///edition")


def test_normalize_base_url_lowercases_host_and_keeps_port() -> None:
    assert normalize_base_url("https://Example.ORG:8080/edition/") == (
        "https://example.org:8080/edition"
    )


def test_normalize_base_url_rebuilds_from_components_not_raw_text() -> None:
    # A malicious-looking suffix that urlsplit would still parse as query or
    # fragment must never survive into the normalized, reconstructed URL.
    with pytest.raises(ValueError):
        normalize_base_url("https://example.org/edition?x=<script>alert(1)</script>")


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
