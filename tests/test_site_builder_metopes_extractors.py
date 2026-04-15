from __future__ import annotations

from pathlib import Path

from ets.site_builder.extractors import extract_notice_document


ROOT = Path(__file__).resolve().parents[1]
MINIMAL = ROOT / "fixtures" / "metopes" / "minimal"
REALISTIC = ROOT / "fixtures" / "metopes" / "realistic"


def _flatten_titles(sections: tuple) -> list[str]:
    titles: list[str] = []
    for section in sections:
        titles.append(section.title)
        titles.extend(_flatten_titles(section.children))
    return titles


def test_extract_metopes_standalone_document() -> None:
    document = extract_notice_document(MINIMAL / "Ch01_Introduction_test.xml")

    assert document.notice_kind == "standalone"
    assert document.title == "Introduction"
    assert document.text_type == "introduction"
    assert document.sections
    assert document.toc
    assert document.notes
    assert any("Note de bas de page" in note.text for note in document.notes)
    paragraph_html = "".join(document.sections[0].paragraphs)
    assert "<em>mise en forme italique</em>" in paragraph_html


def test_extract_metopes_master_volume_with_local_xincludes() -> None:
    document = extract_notice_document(MINIMAL / "Metopes_Test_Book.xml")

    assert document.notice_kind == "master_volume"
    assert document.sections
    assert document.toc
    assert len(document.included_documents) >= 3
    titles = _flatten_titles(document.sections)
    assert any("Introduction" in title for title in titles)


def test_extract_metopes_master_missing_xinclude_is_non_blocking() -> None:
    document = extract_notice_document(MINIMAL / "Metopes_Test_Book_Missing.xml")

    assert document.notice_kind == "master_volume"
    assert document.sections
    assert document.include_warnings
    assert any("Could not resolve xi:include" in warning for warning in document.include_warnings)


def test_extract_realistic_metopes_master_does_not_crash() -> None:
    document = extract_notice_document(REALISTIC / "Heraldique_et_Papaute_volII.xml")

    assert document.notice_kind == "master_volume"
    assert document.sections
    assert document.toc
