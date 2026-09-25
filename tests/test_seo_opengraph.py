from __future__ import annotations

from ets.seo import open_graph_head_html


def test_open_graph_returns_empty_without_url() -> None:
    html_fragment = open_graph_head_html(
        title="Andromaque",
        description="Une tragédie de Jean Racine.",
        url=None,
        site_name="ETS Demo",
    )

    assert html_fragment == ""


def test_open_graph_includes_core_tags_when_url_is_set() -> None:
    html_fragment = open_graph_head_html(
        title="Andromaque",
        description="Une tragédie de Jean Racine.",
        url="https://edition.example.org/plays/andromaque.html",
        site_name="ETS Demo",
    )

    assert '<meta property="og:type" content="website">' in html_fragment
    assert '<meta property="og:title" content="Andromaque">' in html_fragment
    assert (
        '<meta property="og:url" content="https://edition.example.org/plays/andromaque.html">'
        in html_fragment
    )
    assert '<meta property="og:site_name" content="ETS Demo">' in html_fragment
    assert '<meta property="og:description" content="Une tragédie de Jean Racine.">' in html_fragment
    assert '<meta name="twitter:card" content="summary">' in html_fragment
    assert '<meta name="twitter:title" content="Andromaque">' in html_fragment


def test_open_graph_uses_large_image_card_when_image_is_set() -> None:
    html_fragment = open_graph_head_html(
        title="Andromaque",
        description="",
        url="https://edition.example.org/plays/andromaque.html",
        site_name="ETS Demo",
        image_url="https://edition.example.org/assets/logos/logo.png",
    )

    assert '<meta name="twitter:card" content="summary_large_image">' in html_fragment
    assert (
        '<meta property="og:image" content="https://edition.example.org/assets/logos/logo.png">'
        in html_fragment
    )
    assert (
        '<meta name="twitter:image" content="https://edition.example.org/assets/logos/logo.png">'
        in html_fragment
    )
    assert "og:description" not in html_fragment
    assert "twitter:description" not in html_fragment
