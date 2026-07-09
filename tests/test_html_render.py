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
from ets.core import run_pipeline, run_pipeline_from_text
from ets.domain import EditionConfig, Witness
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


def _mini_config() -> EditionConfig:
    return EditionConfig(
        title="Mini",
        author="Auteur",
        editor="Editeur",
        witnesses=[
            Witness(siglum="A", year="1670", description="temoin A"),
            Witness(siglum="B", year="1671", description="temoin B"),
            Witness(siglum="C", year="1672", description="temoin C"),
        ],
        reference_witness=0,
    )


def _mini_stanza_config() -> EditionConfig:
    return EditionConfig(
        title="Esther",
        author="Jean Racine",
        editor="Editeur",
        witnesses=[
            Witness(siglum="A", year="1689", description="temoin A"),
            Witness(siglum="B", year="1689", description="temoin B"),
            Witness(siglum="C", year="1689", description="temoin C"),
            Witness(siglum="D", year="1689", description="temoin D"),
        ],
        reference_witness=0,
    )


def _mini_stanza_text() -> str:
    return "\n".join(
        [
            *["####ACTE I####"] * 4,
            "",
            *["###SCENE I###"] * 4,
            "",
            *["#CHOEUR#"] * 4,
            "",
            *["%%strophe subtype=distique rhyme=aa%%"] * 4,
            "",
            "=12=Que vous semble, mes soeurs, de l’état où nous sommes~?",
            "=12=Que vous semble, mes soeurs, de l’estat où nous sommes~?",
            "=12=Que vous semble, mes soeurs, de l’estat où nous sommes~?",
            "=12=Que vous semble, mes soeurs, de l’état où nous sommes~?",
            "",
            *["=10=D’Esther, d’Aman qui tombe dans les pommes~?"] * 4,
            "",
            *["%%fin_strophe%%"] * 4,
        ]
    )


def _empty_reading_diagnostic_tei_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Diagnostic variantes vides</title>
        <author>Auteur</author>
      </titleStmt>
      <publicationStmt><p>Test</p></publicationStmt>
      <sourceDesc>
        <listWit>
          <witness xml:id="A">A (1670) temoin A</witness>
          <witness xml:id="B">B (1671) temoin B</witness>
          <witness xml:id="C">C (1672) temoin C</witness>
        </listWit>
      </sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <div type="act" n="1">
        <head>ACTE I</head>
        <div type="scene" n="1">
          <head>SCENE I</head>
          <sp>
            <speaker>ORESTE</speaker>
            <l n="1">Cas A<app type="minor" subtype="punctuation" ana="#punctuation_only"><lem wit="#A #B" type="omission"/><rdg wit="#C">,</rdg></app> suite.</l>
            <l n="2">Cas B <app><lem wit="#A" type="omission"/><rdg wit="#B">vraiment </rdg></app>suite.</l>
            <l n="3">Cas C <app><lem wit="#A">vraiment </lem><rdg wit="#B" type="omission"/></app>suite.</l>
            <l n="4">Cas D <app><lem wit="#A">cause</lem><rdg wit="#B">donne</rdg></app> suite.</l>
            <l n="5">Cas E<app type="minor" subtype="punctuation" ana="#punctuation_only"><lem wit="#C">,</lem><rdg wit="#A #B" type="omission"/></app> suite.</l>
            <l n="6">Cas F <app type="minor" subtype="mixed" ana="#case_only+punctuation_only"><lem wit="#A">Cause,</lem><rdg wit="#B">cause</rdg></app> suite.</l>
          </sp>
        </div>
      </div>
    </body>
  </text>
</TEI>
"""


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


def test_html_preview_renders_dramatis_personae_front_structurally() -> None:
    tei_xml = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Britannicus</title>
        <author>Jean Racine</author>
      </titleStmt>
      <publicationStmt><p>Test</p></publicationStmt>
      <sourceDesc>
        <listWit>
          <witness xml:id="A">A (1670) témoin A</witness>
          <witness xml:id="B">B (1671) témoin B</witness>
          <witness xml:id="C">C (1672) témoin C</witness>
          <witness xml:id="D">D (1673) témoin D</witness>
          <witness xml:id="E">E (1674) témoin E</witness>
        </listWit>
      </sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <front>
      <div type="dramatis-personae">
        <head>Acteurs</head>
        <castList>
          <castItem xml:id="britannicus">
            <role>Britannicus</role>
            <roleDesc>prince de Rome</roleDesc>
            <note type="semi-diplomatic">
              <app>
                <lem wit="#A #C #D #E">Britannicus, prince de Rome</lem>
                <rdg wit="#B">Britannicus, Prince de Rome</rdg>
              </app>
            </note>
          </castItem>
          <castItem xml:id="neron">
            <role>Néron</role>
            <roleDesc>empereur de Rome</roleDesc>
          </castItem>
        </castList>
        <stage type="setting">
          <app>
            <lem wit="#A">La scène est à Rome.</lem>
            <rdg wit="#B">La Scene est à Rome.</rdg>
          </app>
        </stage>
      </div>
    </front>
    <body>
      <div type="act" n="1">
        <head>ACTE I</head>
        <div type="scene" n="1">
          <head>SCENE I</head>
          <sp>
            <speaker>BRITANNICUS</speaker>
            <l n="1">Je parle.</l>
          </sp>
        </div>
      </div>
    </body>
  </text>
</TEI>
"""
    preview = render_html_preview_from_tei(tei_xml)
    doc = lxml_html.document_fromstring(preview)

    section = doc.xpath("//section[contains(@class, 'dramatis-personae')]")[0]
    assert section.xpath(".//div[contains(@class, 'dramatis-head') and normalize-space(.)='Acteurs']")
    assert section.xpath(".//ul[contains(@class, 'cast-list')]")
    assert section.xpath(".//li[contains(@class, 'cast-item')]//span[contains(@class, 'variation') and contains(., 'Britannicus, prince de Rome')]")
    assert section.xpath(".//li[contains(@class, 'cast-item')]//span[contains(@class, 'variation') and contains(@data-tooltip, 'Britannicus, Prince de Rome')]")
    assert section.xpath(".//li[contains(@class, 'cast-item')]//span[contains(@class, 'cast-role') and normalize-space(.)='Néron']")
    assert section.xpath(".//li[contains(@class, 'cast-item')]//span[contains(@class, 'cast-desc') and normalize-space(.)='empereur de Rome']")
    assert section.xpath(".//p[contains(@class, 'didascalie') and contains(@class, 'setting')]//span[contains(@class, 'variation') and contains(., 'La scène est à Rome.')]")
    assert doc.xpath("//div[contains(@class, 'acte-titre') or contains(@class, 'acte-titre-sans-variation')]")
    assert doc.xpath("//div[contains(@class, 'vers-container')]")


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
    assert "Édition scientifique par Clémentine Gheeraert" in credit_lines
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

    assert doc.xpath("//sup[contains(@class, 'note-call') and @id='noteref-1-berenice-A1S1L1']/a[@href='#note-1' and text()='1']")
    assert doc.xpath("//sup[contains(@class, 'note-call') and @id='noteref-2-berenice-A1S1L2']/a[@href='#note-2' and text()='2']")
    assert doc.xpath("//sup[contains(@class, 'note-call') and @id='noteref-2-berenice-A1S1L3']/a[@href='#note-2' and text()='2']")
    assert doc.xpath("//sup[contains(@class, 'note-call') and @id='noteref-3-berenice-A1S1ST1']/a[@href='#note-3' and text()='3']")

    assert doc.xpath("//li[@id='note-1']//a[contains(@class, 'note-backlink') and @href='#noteref-1-berenice-A1S1L1']")
    assert doc.xpath("//li[@id='note-2']//a[contains(@class, 'note-backlink') and @href='#noteref-2-berenice-A1S1L2']")
    assert doc.xpath("//li[@id='note-3']//a[contains(@class, 'note-backlink') and @href='#noteref-3-berenice-A1S1ST1']")


def test_html_note_call_has_native_preview_attributes() -> None:
    preview = render_html_preview_from_tei(_annotated_fixture_tei_xml())
    doc = lxml_html.document_fromstring(preview)

    link = doc.xpath("//sup[@id='noteref-1-berenice-A1S1L1']/a")[0]
    assert link.get("title") == "Ouverture solennelle de la scene."
    assert link.get("aria-label") == "Note 1: Ouverture solennelle de la scene."


def test_html_note_call_preview_is_plain_text_not_raw_xml() -> None:
    preview = render_html_preview_from_tei(_annotated_markdown_tei_xml())
    doc = lxml_html.document_fromstring(preview)

    title = doc.xpath("//sup[@id='noteref-1-berenice-A1S1L1']/a/@title")[0]
    assert "<" not in title
    assert ">" not in title
    assert "*" not in title


def test_html_note_call_preview_truncates_long_notes() -> None:
    preview = render_html_preview_from_tei(_annotated_long_note_tei_xml())
    doc = lxml_html.document_fromstring(preview)

    title = doc.xpath("//sup[@id='noteref-1-berenice-A1S1L1']/a/@title")[0]
    assert title.endswith("…")
    assert len(title) == 201


def test_html_note_call_preview_keeps_short_notes_untruncated() -> None:
    preview = render_html_preview_from_tei(_annotated_fixture_tei_xml())
    doc = lxml_html.document_fromstring(preview)

    title = doc.xpath("//sup[@id='noteref-1-berenice-A1S1L1']/a/@title")[0]
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


def test_html_preview_renders_underscore_italic_without_literal_underscores() -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "#ORESTE#",
            "#ORESTE#",
            "#ORESTE#",
            "",
            "Oui je viens en son _temple_ adorer l’Eternel",
            "Oui je viens en son _temple_ adorer l’Eternel",
            "Oui je viens en son _temple_ adorer l’Eternel",
        ]
    )
    tei_xml = run_pipeline_from_text(text, _mini_config())
    assert "_temple_" not in tei_xml

    preview = render_html_preview_from_tei(tei_xml)
    doc = lxml_html.document_fromstring(preview)
    assert doc.xpath("//span[contains(@class, 'italic') and text()='temple'] | //em[text()='temple']")
    assert "_temple_" not in doc.text_content()


def test_html_preview_renders_stanza_and_meter_classes() -> None:
    tei_xml = run_pipeline_from_text(_mini_stanza_text(), _mini_stanza_config())
    preview = render_html_preview_from_tei(tei_xml)
    doc = lxml_html.document_fromstring(preview)

    assert doc.xpath("//div[@class='lg stanza' and @data-subtype='distique' and @data-rhyme='aa']")
    assert doc.xpath("//div[contains(@class, 'vers-container') and contains(@class, 'met-12')]")
    assert doc.xpath("//div[contains(@class, 'vers-container') and contains(@class, 'met-10')]")
    variants = doc.xpath("//span[contains(@class, 'variation') and @data-tooltip]")
    assert variants
    assert "estat" in variants[0].get("data-tooltip")


def test_html_preview_marks_empty_active_reading_variant_anchors_without_text_pollution() -> None:
    preview = render_html_preview_from_tei(_empty_reading_diagnostic_tei_xml())
    doc = lxml_html.document_fromstring(preview)

    lines = doc.xpath("//div[contains(@class, 'vers-container')]")
    assert len(lines) == 6

    punctuation_addition = lines[0].xpath(".//span[contains(@class, 'variation')]")[0]
    word_addition = lines[1].xpath(".//span[contains(@class, 'variation')]")[0]
    word_omission = lines[2].xpath(".//span[contains(@class, 'variation')]")[0]
    ordinary_variant = lines[3].xpath(".//span[contains(@class, 'variation')]")[0]
    visible_punctuation = lines[4].xpath(".//span[contains(@class, 'variation')]")[0]
    mixed_variant = lines[5].xpath(".//span[contains(@class, 'variation')]")[0]

    assert punctuation_addition.text_content() == ""
    assert "variation-empty" in (punctuation_addition.get("class") or "")
    assert "variation-punctuation-only" in (punctuation_addition.get("class") or "")
    assert punctuation_addition.get("tabindex") == "0"
    assert "Apparat critique" in (punctuation_addition.get("aria-label") or "")
    assert "," in (punctuation_addition.get("data-tooltip") or "")

    assert word_addition.text_content() == ""
    assert "variation-empty" in (word_addition.get("class") or "")
    assert word_addition.get("tabindex") == "0"
    assert "Apparat critique" in (word_addition.get("aria-label") or "")
    assert "vraiment" in (word_addition.get("data-tooltip") or "")

    assert word_omission.text_content() == "vraiment "
    assert "variation-empty" not in (word_omission.get("class") or "")
    assert word_omission.get("tabindex") is None
    assert "B (1671):" in (word_omission.get("data-tooltip") or "")

    assert ordinary_variant.text_content() == "cause"
    assert "variation-empty" not in (ordinary_variant.get("class") or "")
    assert ordinary_variant.get("tabindex") is None
    assert "donne" in (ordinary_variant.get("data-tooltip") or "")

    assert visible_punctuation.text_content() == ","
    assert "variation-punctuation-only" in (visible_punctuation.get("class") or "")
    assert "Cas E, suite." in lines[4].text_content()

    assert mixed_variant.text_content() == "Cause,"
    assert "variation-punctuation-only" not in (mixed_variant.get("class") or "")

    assert "Masquer les variantes de ponctuation" in preview
    assert "hide-punctuation-variants" in preview
    assert "\\25E6" not in preview
    assert "\u25e6" not in preview
    assert "\u25e6" not in doc.text_content()
    assert "min-height: 1em" in preview
    assert "Cas A suite." in lines[0].text_content()
    assert "Cas B suite." in lines[1].text_content()
