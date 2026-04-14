from __future__ import annotations

import xml.etree.ElementTree as ET

from ets.annotations.markdown import append_annotation_content, convert_annotation_markdown

NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def _build_note_with_content(content: str) -> ET.Element:
    note = ET.Element("{http://www.tei-c.org/ns/1.0}note")
    append_annotation_content(note, content)
    return note


def test_italic_conversion() -> None:
    note = _build_note_with_content("Voir *Berenice*.")
    italic = note.find(".//tei:hi[@rend='italic']", NS)
    assert italic is not None
    assert italic.text == "Berenice"


def test_bold_conversion() -> None:
    note = _build_note_with_content("Texte **important**.")
    bold = note.find(".//tei:hi[@rend='bold']", NS)
    assert bold is not None
    assert bold.text == "important"


def test_smallcaps_conversion() -> None:
    note = _build_note_with_content("[RACINE]{.smallcaps}")
    sc = note.find(".//tei:hi[@rend='smallcaps']", NS)
    assert sc is not None
    assert sc.text == "RACINE"


def test_superscript_conversion() -> None:
    note = _build_note_with_content("x^2^")
    superscript = note.find(".//tei:hi[@rend='superscript']", NS)
    assert superscript is not None
    assert superscript.text == "2"


def test_subscript_conversion() -> None:
    note = _build_note_with_content("H~2~O")
    subscript = note.find(".//tei:hi[@rend='subscript']", NS)
    assert subscript is not None
    assert subscript.text == "2"


def test_hyperlink_conversion() -> None:
    note = _build_note_with_content("Voir [ce site](https://example.org).")
    ref = note.find(".//tei:ref", NS)
    assert ref is not None
    assert ref.text == "ce site"
    assert ref.get("target") == "https://example.org"


def test_paragraph_splitting() -> None:
    note = _build_note_with_content("Premier paragraphe.\n\nSecond paragraphe.")
    paragraphs = note.findall("./tei:p", NS)
    assert len(paragraphs) == 2
    assert (paragraphs[0].text or "").strip() == "Premier paragraphe."
    assert (paragraphs[1].text or "").strip() == "Second paragraphe."


def test_mixed_inline_markup_in_one_paragraph() -> None:
    note = _build_note_with_content(
        "Voir *Berenice*, passage **clef**, [source](https://example.org), H~2~O et x^2^."
    )
    assert note.find(".//tei:hi[@rend='italic']", NS) is not None
    assert note.find(".//tei:hi[@rend='bold']", NS) is not None
    assert note.find(".//tei:ref[@target='https://example.org']", NS) is not None
    assert note.find(".//tei:hi[@rend='subscript']", NS) is not None
    assert note.find(".//tei:hi[@rend='superscript']", NS) is not None


def test_malformed_syntax_is_preserved_as_literal_text() -> None:
    note = _build_note_with_content("Texte *non ferme et [lien](notaurl)")
    assert note.text == "Texte *non ferme et [lien](notaurl)"
    assert note.find(".//tei:hi", NS) is None
    assert note.find(".//tei:ref", NS) is None


def test_plain_text_single_paragraph_note_stays_unchanged() -> None:
    note = _build_note_with_content("Texte sans balisage.")
    assert note.text == "Texte sans balisage."
    assert note.find("./tei:p", NS) is None


def test_converter_reports_markup_presence() -> None:
    converted = convert_annotation_markdown("Texte **important**.")
    assert converted.has_inline_markup is True
    assert len(converted.paragraphs) == 1
