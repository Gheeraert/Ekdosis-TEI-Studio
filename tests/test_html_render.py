from __future__ import annotations

from pathlib import Path

import pytest
from lxml import html as lxml_html

from ets.annotations import (
    Annotation,
    AnnotationAnchor,
    AnnotationCollection,
    inject_annotations_into_tei,
    load_annotations,
)
from ets.core import run_pipeline
from ets.html import HtmlExportOptions, render_html_export_from_tei, render_html_preview_from_tei


def _stable_tei_xml() -> str:
    root = Path(__file__).resolve().parents[1]
    return run_pipeline(
        input_path=root / "fixtures" / "stable" / "input.txt",
        config_path=root / "fixtures" / "stable" / "config.json",
    )


def _annotated_fixture_tei_xml() -> str:
    root = Path(__file__).resolve().parents[1]
    fixture = root / "fixtures" / "annotations" / "berenice_1_1"
    tei_xml = run_pipeline(
        input_path=fixture / "input.txt",
        config_path=fixture / "config.json",
    )
    annotations = load_annotations(fixture / "annotations.json")
    return inject_annotations_into_tei(tei_xml, annotations)


def _annotated_markdown_tei_xml() -> str:
    root = Path(__file__).resolve().parents[1]
    fixture = root / "fixtures" / "annotations" / "berenice_1_1"
    tei_xml = run_pipeline(
        input_path=fixture / "input.txt",
        config_path=fixture / "config.json",
    )
    annotations = AnnotationCollection(
        version=1,
        annotations=[
            Annotation(
                id="n_md_html",
                type="explicative",
                anchor=AnnotationAnchor(kind="line", act="1", scene="1", line="1"),
                content=(
                    "Un *italique* et un **gras**, un [RACINE]{.smallcaps}, x^2^, H~2~O, "
                    "et un [lien](https://example.org).\n\nDeuxieme paragraphe."
                ),
                status="draft",
                keywords=[],
            )
        ],
    )
    return inject_annotations_into_tei(tei_xml, annotations)


def _annotated_long_note_tei_xml() -> str:
    root = Path(__file__).resolve().parents[1]
    fixture = root / "fixtures" / "annotations" / "berenice_1_1"
    tei_xml = run_pipeline(
        input_path=fixture / "input.txt",
        config_path=fixture / "config.json",
    )
    very_long_note = " ".join(["developpement"] * 40) + " [source](https://example.org)"
    annotations = AnnotationCollection(
        version=1,
        annotations=[
            Annotation(
                id="n_long_html",
                type="explicative",
                anchor=AnnotationAnchor(kind="line", act="1", scene="1", line="1"),
                content=very_long_note,
                status="draft",
                keywords=[],
            )
        ],
    )
    return inject_annotations_into_tei(tei_xml, annotations)


def test_html_preview_transforms_stable_tei_fixture() -> None:
    preview = render_html_preview_from_tei(_stable_tei_xml())
    doc = lxml_html.document_fromstring(preview)

    assert doc.xpath("//div[contains(@class, 'acte-titre') or contains(@class, 'acte-titre-sans-variation')]")
    assert doc.xpath("//div[contains(@class, 'scene-titre') or contains(@class, 'scene-titre-sans-variation')]")
    assert doc.xpath("//div[contains(@class, 'locuteur')]")
    assert doc.xpath("//div[contains(@class, 'vers-container')]")
    assert doc.xpath("//span[contains(@class, 'variation') and @data-tooltip]")
    assert not doc.xpath("//section[contains(@class, 'notes')]")
    assert not doc.xpath("//sup[contains(@class, 'note-call')]")


def test_html_export_generates_editorial_shell_and_credits() -> None:
    export = render_html_export_from_tei(_stable_tei_xml(), xml_href="../xml-tei/stable.xml")
    doc = lxml_html.document_fromstring(export)

    assert doc.xpath("string(/html/head/title)") == "Andromaque"
    assert doc.xpath("//div[@id='container' and contains(@class, 'with-menu')]")
    assert doc.xpath("//aside[@id='menu-lateral']")
    assert doc.xpath("//main")
    assert doc.xpath("//div[@id='header']")
    assert doc.xpath("//div[@id='footer']")
    assert doc.xpath("//section[@id='contenu-editorial']")

    credit_lines = [
        line.text_content().strip()
        for line in doc.xpath("//*[contains(@class, 'bloc-credit')]//*[contains(@class, 'credit-line')]")
    ]
    assert "Jean Racine - Andromaque, Acte 1, Scène 1" in credit_lines
    assert "Édition critique par Clémentine Gheeraert" in credit_lines
    assert any(line.startswith("Document généré le ") and "Ekdosis-TEI Studio" in line for line in credit_lines)
    assert any("Télécharger le XML" in line for line in credit_lines)
    assert doc.xpath("//a[@href='../xml-tei/stable.xml']")

    assert doc.xpath("//section[@id='contenu-editorial']//div[contains(@class, 'acte-titre') or contains(@class, 'acte-titre-sans-variation')]")
    assert doc.xpath("//section[@id='contenu-editorial']//div[contains(@class, 'scene-titre') or contains(@class, 'scene-titre-sans-variation')]")
    assert doc.xpath("//section[@id='contenu-editorial']//div[contains(@class, 'locuteur')]")
    assert doc.xpath("//section[@id='contenu-editorial']//div[contains(@class, 'vers-container')]")
    assert doc.xpath("//section[@id='contenu-editorial']//span[contains(@class, 'variation') and @data-tooltip]")


def test_html_export_accepts_simple_layout_options() -> None:
    export = render_html_export_from_tei(
        _stable_tei_xml(),
        xml_href="../xml-tei/stable.xml",
        options=HtmlExportOptions(
            document_title="Edition export test",
            css_href="../../../css/portail.css",
            script_srcs=("../../../js/site.js",),
            include_menu=False,
            include_header=False,
            include_footer=True,
            footer_html="Pied de page test",
        ),
    )
    doc = lxml_html.document_fromstring(export)
    assert doc.xpath("string(/html/head/title)") == "Edition export test"
    assert doc.xpath("//link[@rel='stylesheet' and @href='../../../css/portail.css']")
    assert doc.xpath("//script[@src='../../../js/site.js']")
    assert doc.xpath("//div[@id='container' and contains(@class, 'without-menu')]")
    assert not doc.xpath("//aside[@id='menu-lateral']")
    assert not doc.xpath("//div[@id='header']")
    assert doc.xpath("//div[@id='footer']")
    assert "Pied de page test" in doc.text_content()


def test_html_preview_uses_external_xslt_file_path() -> None:
    with pytest.raises(FileNotFoundError):
        render_html_preview_from_tei(_stable_tei_xml(), xslt_path="missing_stylesheet.xsl")


def test_html_preview_renders_note_calls_notes_block_numbering_and_backlinks() -> None:
    preview = render_html_preview_from_tei(_annotated_fixture_tei_xml())
    doc = lxml_html.document_fromstring(preview)

    note_numbers = [item.text_content().strip() for item in doc.xpath("//section[contains(@class, 'notes')]//li")]
    assert note_numbers == [
        "Ouverture solennelle de la scene.↩",
        "Le rythme s'accelere sur la fin de la replique.↩",
        "Entree scenique structurante.↩",
    ]

    assert doc.xpath("//sup[contains(@class, 'note-call') and @id='noteref-1-A1S1L1']/a[@href='#note-1' and text()='1']")
    assert doc.xpath("//sup[contains(@class, 'note-call') and @id='noteref-2-A1S1L2']/a[@href='#note-2' and text()='2']")
    assert doc.xpath("//sup[contains(@class, 'note-call') and @id='noteref-2-A1S1L3']/a[@href='#note-2' and text()='2']")
    assert doc.xpath("//sup[contains(@class, 'note-call') and @id='noteref-3-A1S1ST1']/a[@href='#note-3' and text()='3']")

    assert doc.xpath("//li[@id='note-1']//a[contains(@class, 'note-backlink') and @href='#noteref-1-A1S1L1']")
    assert doc.xpath("//li[@id='note-2']//a[contains(@class, 'note-backlink') and @href='#noteref-2-A1S1L2']")
    assert doc.xpath("//li[@id='note-3']//a[contains(@class, 'note-backlink') and @href='#noteref-3-A1S1ST1']")


def test_html_note_call_has_native_preview_attributes() -> None:
    preview = render_html_preview_from_tei(_annotated_fixture_tei_xml())
    doc = lxml_html.document_fromstring(preview)

    link = doc.xpath("//sup[@id='noteref-1-A1S1L1']/a")[0]
    assert link.get("title") == "Ouverture solennelle de la scene."
    assert link.get("aria-label") == "Note 1: Ouverture solennelle de la scene."


def test_html_note_call_preview_is_plain_text_not_raw_xml() -> None:
    preview = render_html_preview_from_tei(_annotated_markdown_tei_xml())
    doc = lxml_html.document_fromstring(preview)

    title = doc.xpath("//sup[@id='noteref-1-A1S1L1']/a/@title")[0]
    assert "<" not in title
    assert ">" not in title
    assert "*" not in title


def test_html_note_call_preview_truncates_long_notes() -> None:
    preview = render_html_preview_from_tei(_annotated_long_note_tei_xml())
    doc = lxml_html.document_fromstring(preview)

    title = doc.xpath("//sup[@id='noteref-1-A1S1L1']/a/@title")[0]
    assert title.endswith("…")
    assert len(title) == 201


def test_html_note_call_preview_keeps_short_notes_untruncated() -> None:
    preview = render_html_preview_from_tei(_annotated_fixture_tei_xml())
    doc = lxml_html.document_fromstring(preview)

    title = doc.xpath("//sup[@id='noteref-1-A1S1L1']/a/@title")[0]
    assert not title.endswith("…")


def test_html_preview_renders_structured_tei_inside_note_body() -> None:
    preview = render_html_preview_from_tei(_annotated_markdown_tei_xml())
    doc = lxml_html.document_fromstring(preview)

    assert doc.xpath("//section[contains(@class, 'notes')]//li[@id='note-1']/p[1]")
    assert doc.xpath("//section[contains(@class, 'notes')]//li[@id='note-1']/p[2]")
    assert doc.xpath("//section[contains(@class, 'notes')]//li[@id='note-1']//span[contains(@class, 'italic') and text()='italique']")
    assert doc.xpath("//section[contains(@class, 'notes')]//li[@id='note-1']//span[contains(@class, 'bold') and text()='gras']")
    assert doc.xpath("//section[contains(@class, 'notes')]//li[@id='note-1']//span[contains(@class, 'smallcaps') and text()='RACINE']")
    assert doc.xpath("//section[contains(@class, 'notes')]//li[@id='note-1']//span[contains(@class, 'superscript') and text()='2']")
    assert doc.xpath("//section[contains(@class, 'notes')]//li[@id='note-1']//span[contains(@class, 'subscript') and text()='2']")
    assert doc.xpath("//section[contains(@class, 'notes')]//li[@id='note-1']//a[@href='https://example.org' and text()='lien']")
