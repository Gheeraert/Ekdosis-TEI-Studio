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


def _flatten_nodes(sections: tuple) -> list:
    nodes: list = []
    for section in sections:
        nodes.append(section)
        nodes.extend(_flatten_nodes(section.children))
    return nodes


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
    assert document.sections[0].section_id.startswith("doc-")


def test_extract_metopes_master_volume_with_local_xincludes() -> None:
    document = extract_notice_document(MINIMAL / "Metopes_Test_Book.xml")

    assert document.notice_kind == "master_volume"
    assert document.sections
    assert document.toc
    assert len(document.included_documents) >= 3
    titles = _flatten_titles(document.sections)
    assert any("Introduction" in title for title in titles)
    flat_nodes = _flatten_nodes(document.sections)
    included = [node for node in flat_nodes if node.node_kind == "included_document"]
    assert included
    assert any(node.source_path and node.source_path.name == "Ch01_Introduction_test.xml" for node in included)
    assert any(node.children for node in included)


def test_extract_metopes_master_keeps_group_and_document_distinction() -> None:
    document = extract_notice_document(MINIMAL / "Metopes_Test_Book.xml")

    top_groups = [section for section in document.sections if section.node_kind == "group"]
    assert top_groups
    first_group = top_groups[0]
    assert first_group.node_kind == "group"
    assert any(child.node_kind == "included_document" for child in first_group.children)


def test_extract_metopes_master_missing_xinclude_is_non_blocking() -> None:
    document = extract_notice_document(MINIMAL / "Metopes_Test_Book_Missing.xml")

    assert document.notice_kind == "master_volume"
    assert document.sections
    assert document.include_warnings
    assert any("Could not resolve xi:include" in warning for warning in document.include_warnings)
    flat_nodes = _flatten_nodes(document.sections)
    assert any(node.kind == "missing_include" for node in flat_nodes)


def test_extract_realistic_metopes_master_does_not_crash() -> None:
    document = extract_notice_document(REALISTIC / "Heraldique_et_Papaute_volII.xml")

    assert document.notice_kind == "master_volume"
    assert document.sections
    assert document.toc
