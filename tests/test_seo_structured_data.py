from __future__ import annotations

import json

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
