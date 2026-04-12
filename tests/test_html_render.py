from __future__ import annotations

from pathlib import Path

import pytest
from lxml import html as lxml_html

from ets.core import run_pipeline
from ets.html import render_html_export_from_tei, render_html_preview_from_tei


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


def test_html_export_generates_complete_document_with_credits() -> None:
    export = render_html_export_from_tei(_stable_tei_xml(), xml_href="../xml-tei/stable.xml")
    doc = lxml_html.document_fromstring(export)

    title = doc.xpath("string(/html/head/title)")
    assert title == "Andromaque"
    assert doc.xpath("//main[contains(@class, 'ets-export-main')]")
    credit_lines = [
        line.text_content().strip()
        for line in doc.xpath("//div[contains(@class, 'bloc-credit')]//div[contains(@class, 'credit-line')]")
    ]
    assert "Jean Racine - Andromaque" in credit_lines
    assert "Acte 1" in credit_lines
    assert "Edition critique par Clémentine Gheeraert" in credit_lines
    assert any(line.startswith("Document genere le ") and "Ekdosis-TEI Studio" in line for line in credit_lines)
    assert doc.xpath("//a[@href='../xml-tei/stable.xml']")
    assert doc.xpath("//section[contains(@class, 'ets-export-content')]")
    assert doc.xpath("//div[contains(@class, 'locuteur')]")
    assert doc.xpath("//span[contains(@class, 'variation') and @data-tooltip]")


def test_html_preview_uses_external_xslt_file_path() -> None:
    with pytest.raises(FileNotFoundError):
        render_html_preview_from_tei(_stable_tei_xml(), xslt_path="missing_stylesheet.xsl")
