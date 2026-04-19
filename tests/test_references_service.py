from __future__ import annotations

import json
from pathlib import Path

from ets.references import (
    ReferencesService,
    build_citation_token,
    extract_citations,
    import_csl_json,
    parse_citation_token,
)


def test_import_csl_json_parses_common_fields() -> None:
    source = [
        {
            "id": "forestier1999",
            "type": "book",
            "title": "Berenice",
            "author": [{"family": "Forestier", "given": "Georges"}],
            "issued": {"date-parts": [[1999]]},
            "publisher": "Gallimard",
            "publisher-place": "Paris",
        },
        {
            "id": "article-demo",
            "type": "article-journal",
            "title": "Article test",
            "author": [{"literal": "A. Auteur"}],
            "issued": {"raw": "2007"},
            "container-title": "Revue test",
            "DOI": "10.1234/xyz",
        },
    ]
    runtime_dir = Path(__file__).resolve().parents[1] / "tests" / "_runtime"
    runtime_dir.mkdir(exist_ok=True)
    path = runtime_dir / "references_import_sample.json"
    path.write_text(json.dumps(source), encoding="utf-8")

    result = import_csl_json(path)
    assert not result.has_errors
    assert len(result.references) == 2
    first = result.references[0]
    assert first.id == "forestier1999"
    assert first.title == "Berenice"
    assert first.authors == ("Georges Forestier",)
    assert first.date == "1999"


def test_manual_reference_creation_and_search() -> None:
    service = ReferencesService()
    ref = service.add_manual_reference(
        title="L'inconscient dans l'oeuvre et la vie de Racine",
        authors=["Charles Mauron"],
        date="1957",
        publisher="Corti",
    )
    assert ref.origin == "manual"
    matches = service.search_references("mauron")
    assert len(matches) == 1
    assert matches[0].id == ref.id


def test_citation_token_roundtrip_extracts_occurrences() -> None:
    token = build_citation_token("forestier1999", locator="p. 143", prefix="voir", suffix="n. 2", mode="note")
    text = f"Texte {token} suite."
    occurrences = extract_citations(text, target_context="md")
    assert len(occurrences) == 1
    occ = occurrences[0]
    assert occ.reference_id == "forestier1999"
    assert occ.locator == "p. 143"
    assert occ.prefix == "voir"
    assert occ.suffix == "n. 2"


def test_citation_token_parsing_supports_escaped_pipe_and_spaces() -> None:
    token = build_citation_token("ref-a", locator="p. 2 | annexe", prefix="voir | cf.", suffix="fin")
    parsed = parse_citation_token(token)
    assert parsed is not None
    assert parsed.reference_id == "ref-a"
    assert parsed.locator == "p. 2 | annexe"
    assert parsed.prefix == "voir | cf."


def test_citation_token_invalid_forms_are_ignored() -> None:
    assert parse_citation_token("{{CITE:}}") is None
    assert parse_citation_token("{{CITE:locator=p.12}}") is None
    assert len(extract_citations("texte {{CITE:locator=p.12}}")) == 0


def test_bibliography_is_generated_from_cited_references_only() -> None:
    service = ReferencesService()
    cited = service.add_manual_reference(title="Berenice", authors=["Forestier"], date="1999")
    service.add_manual_reference(title="Unused", authors=["Nobody"], date="2000")

    token = service.build_citation_token(cited.id, locator="p. 12")
    state = service.bibliography_from_text(f"Intro {token}.")

    assert state.cited_reference_ids == (cited.id,)
    assert len(state.generated_entries) == 1
    rendered = service.bibliography_to_text(state)
    assert "Berenice" in rendered
    assert "Unused" not in rendered
