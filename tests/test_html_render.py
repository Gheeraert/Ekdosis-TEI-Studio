from __future__ import annotations

from pathlib import Path

import pytest
from lxml import html as lxml_html

from ets.core import run_pipeline
from ets.html import HtmlExportOptions, render_html_export_from_tei, render_html_preview_from_tei


def _stable_tei_xml() -> str:
    root = Path(__file__).resolve().parents[1]
    return run_pipeline(
        input_path=root / "fixtures" / "stable" / "input.txt",
        config_path=root / "fixtures" / "stable" / "config.json",
    )


def test_html_preview_transforms_stable_tei_fixture() -> None:
    preview = render_html_preview_from_tei(_stable_tei_xml())
    doc = lxml_html.document_fromstring(preview)

    assert doc.xpath("//div[contains(@class, 'acte-titre') or contains(@class, 'acte-titre-sans-variation')]")
    assert doc.xpath("//div[contains(@class, 'scene-titre') or contains(@class, 'scene-titre-sans-variation')]")
    assert doc.xpath("//div[contains(@class, 'locuteur')]")
    assert doc.xpath("//div[contains(@class, 'vers-container')]")
    assert doc.xpath("//span[contains(@class, 'variation') and @data-tooltip]")


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
