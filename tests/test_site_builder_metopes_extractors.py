from __future__ import annotations

from pathlib import Path

from ets.site_builder import extractors
from ets.site_builder.extractors import _is_safe_local_href, extract_notice_document


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


def test_is_safe_local_href_accepts_plain_relative_paths() -> None:
    assert _is_safe_local_href("Ch01_Introduction_test.xml")
    assert _is_safe_local_href("sub/Ch01_Introduction_test.xml")
    assert _is_safe_local_href("sub\\Ch01_Introduction_test.xml")


def test_is_safe_local_href_rejects_traversal_and_absolute_paths() -> None:
    assert not _is_safe_local_href("")
    assert not _is_safe_local_href("../secret.xml")
    assert not _is_safe_local_href("sub/../../secret.xml")
    assert not _is_safe_local_href("/etc/passwd")
    assert not _is_safe_local_href("\\Windows\\win.ini")
    assert not _is_safe_local_href("C:\\Windows\\win.ini")
    assert not _is_safe_local_href("C:/Windows/win.ini")
    assert not _is_safe_local_href("\\\\server\\share\\secret.xml")
    assert not _is_safe_local_href("http://example.com/x.xml")
    assert not _is_safe_local_href("file:///etc/passwd")


def _write_master_with_include(book_path: Path, href: str) -> None:
    book_path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<TEI
  xmlns="http://www.tei-c.org/ns/1.0"
  xmlns:xi="http://www.w3.org/2001/XInclude">
  <teiHeader>
    <fileDesc>
      <titleStmt><title type="main">Livre avec include suspect</title></titleStmt>
      <publicationStmt><p>Fixture de test</p></publicationStmt>
      <sourceDesc><p>Fixture de test</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text type="book" xml:id="book-traversal">
    <group type="book">
      <group type="suspect">
        <xi:include href="{href}" xpointer="text"/>
      </group>
    </group>
  </text>
</TEI>
""",
        encoding="utf-8",
    )


def _write_secret_notice(secret_path: Path) -> None:
    secret_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title type="main">SECRET CONTENT</title></titleStmt>
      <publicationStmt><p>secret</p></publicationStmt>
      <sourceDesc><p>secret</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text type="other">
    <body>
      <div><head>SECRET</head><p>Contenu confidentiel.</p></div>
    </body>
  </text>
</TEI>
""",
        encoding="utf-8",
    )


def test_extract_metopes_master_rejects_traversal_xinclude(tmp_path: Path) -> None:
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    secret = outside_dir / "secret.xml"
    _write_secret_notice(secret)

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    book = source_dir / "book.xml"
    _write_master_with_include(book, "../outside/secret.xml")

    document = extract_notice_document(book)

    assert document.notice_kind == "master_volume"
    flat_nodes = _flatten_nodes(document.sections)
    assert not any(node.node_kind == "included_document" for node in flat_nodes)
    assert not any("SECRET" in node.title for node in flat_nodes)

    joined_warnings = " | ".join(document.include_warnings)
    assert "../outside/secret.xml" in joined_warnings
    # No absolute server path should ever be echoed back to the caller.
    assert str(outside_dir.resolve()) not in joined_warnings
    assert str(secret.resolve()) not in joined_warnings


def test_extract_metopes_master_rejects_absolute_xinclude(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    book = source_dir / "book.xml"
    _write_master_with_include(book, "/etc/passwd")

    document = extract_notice_document(book)

    assert document.notice_kind == "master_volume"
    flat_nodes = _flatten_nodes(document.sections)
    assert not any(node.node_kind == "included_document" for node in flat_nodes)

    joined_warnings = " | ".join(document.include_warnings)
    assert "/etc/passwd" in joined_warnings
    assert str(source_dir.resolve()) not in joined_warnings


def test_extract_metopes_master_blocks_escape_even_if_href_check_bypassed(
    tmp_path: Path, monkeypatch
) -> None:
    """Defense in depth: even if the href pre-check were bypassed, the
    post-resolution Path.resolve().relative_to(...) guard must still
    refuse to read a file outside the source directory."""

    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    secret = outside_dir / "secret.xml"
    _write_secret_notice(secret)

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    book = source_dir / "book.xml"
    _write_master_with_include(book, "../outside/secret.xml")

    monkeypatch.setattr(extractors, "_is_safe_local_href", lambda href: True)

    document = extract_notice_document(book)

    assert document.notice_kind == "master_volume"
    flat_nodes = _flatten_nodes(document.sections)
    assert not any(node.node_kind == "included_document" for node in flat_nodes)
    assert not any("SECRET" in node.title for node in flat_nodes)

    joined_warnings = " | ".join(document.include_warnings)
    assert "outside the allowed directory" in joined_warnings
    assert "../outside/secret.xml" in joined_warnings
    assert str(outside_dir.resolve()) not in joined_warnings
    assert str(secret.resolve()) not in joined_warnings
