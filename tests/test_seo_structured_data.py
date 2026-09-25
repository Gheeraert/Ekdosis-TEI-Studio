from __future__ import annotations

import json

from lxml import html as lxml_html

from ets.seo import book_json_ld_html


def test_book_json_ld_returns_empty_without_url() -> None:
    assert book_json_ld_html(title="Andromaque", author="Jean Racine", url=None) == ""


def test_book_json_ld_contains_expected_fields() -> None:
    html_fragment = book_json_ld_html(
        title="Andromaque",
        author="Jean Racine",
        url="https://edition.example.org/plays/andromaque.html",
        description="Une tragédie de Jean Racine.",
        site_name="ETS Demo",
    )

    assert html_fragment.startswith('<script type="application/ld+json">')
    assert html_fragment.endswith("</script>")

    payload = html_fragment[len('<script type="application/ld+json">') : -len("</script>")]
    data = json.loads(payload)

    assert data["@context"] == "https://schema.org"
    assert data["@type"] == "Book"
    assert data["name"] == "Andromaque"
    assert data["url"] == "https://edition.example.org/plays/andromaque.html"
    assert data["inLanguage"] == "fr"
    assert data["author"] == {"@type": "Person", "name": "Jean Racine"}
    assert data["description"] == "Une tragédie de Jean Racine."
    assert data["publisher"] == {"@type": "Organization", "name": "ETS Demo"}


def test_book_json_ld_omits_author_when_absent() -> None:
    html_fragment = book_json_ld_html(
        title="Pièce anonyme",
        author=None,
        url="https://edition.example.org/plays/piece.html",
    )

    payload = html_fragment[len('<script type="application/ld+json">') : -len("</script>")]
    data = json.loads(payload)

    assert "author" not in data
    assert "description" not in data
    assert "publisher" not in data


def test_book_json_ld_survives_mixed_case_script_close_injection() -> None:
    # HTML closes a <script> element on ANY case variant of "</script",
    # regardless of its type attribute. A lowercase-only defense would miss
    # this. Parsed through a real HTML parser (not a substring check) to
    # verify the injected markup never becomes a separate, live DOM node.
    malicious_title = (
        'Andromaque</SCRIPT><script>window.__xss__=1</script>'
        '<script type="application/ld+json">'
    )
    html_fragment = book_json_ld_html(
        title=malicious_title,
        author=None,
        url="https://edition.example.org/plays/andromaque.html",
    )

    page = f"<html><head>{html_fragment}</head><body></body></html>"
    doc = lxml_html.fromstring(page)
    scripts = doc.xpath("//script")

    assert len(scripts) == 1
    assert scripts[0].get("type") == "application/ld+json"
    data = json.loads(scripts[0].text)
    assert data["name"] == malicious_title


def test_book_json_ld_escapes_angle_brackets_and_ampersand() -> None:
    html_fragment = book_json_ld_html(
        title="Tom & Jerry <injected>",
        author=None,
        url="https://edition.example.org/plays/piece.html",
    )

    assert "<injected>" not in html_fragment
    assert "Tom & Jerry" not in html_fragment  # raw & must be escaped too

    payload = html_fragment[len('<script type="application/ld+json">') : -len("</script>")]
    data = json.loads(payload)
    assert data["name"] == "Tom & Jerry <injected>"
