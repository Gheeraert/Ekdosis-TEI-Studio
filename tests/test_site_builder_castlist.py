from __future__ import annotations

from pathlib import Path

from lxml import html as lxml_html

from ets.site_builder.builder import build_static_site
from ets.site_builder.config import site_config_from_dict


def _write_play_xml(path: Path, *, front: str = "") -> None:
    path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="phedre">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Phedre</title>
        <author>Jean Racine</author>
      </titleStmt>
      <publicationStmt>
        <p>Test</p>
      </publicationStmt>
      <sourceDesc>
        <p>Test</p>
      </sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    {front}
    <body>
      <div type="act" n="1">
        <head>ACTE 1</head>
        <div type="scene" n="1">
          <head>SCENE 1</head>
          <sp>
            <speaker>THESEE</speaker>
            <l><app><lem wit="#A">Je parle.</lem><rdg wit="#B">Je dis.</rdg></app></l>
          </sp>
        </div>
      </div>
    </body>
  </text>
</TEI>
""",
        encoding="utf-8",
    )


def _build_site(tmp_path: Path, *, front: str = "") -> str:
    dramatic_dir = tmp_path / "dramatic"
    output_dir = tmp_path / "site"
    dramatic_dir.mkdir()
    _write_play_xml(dramatic_dir / "phedre.xml", front=front)

    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(dramatic_dir),
            "output_dir": str(output_dir),
        }
    )
    build_static_site(config)
    return (output_dir / "plays" / "phedre.html").read_text(encoding="utf-8")


def test_site_builder_without_dramatis_personae_keeps_old_behavior(tmp_path: Path) -> None:
    play_html = _build_site(tmp_path)
    doc = lxml_html.document_fromstring(play_html)

    assert not doc.xpath("//section[@id='dramatis-personae']")
    assert not doc.xpath("//main/nav//a[contains(@href, '#dramatis-personae')]")
    assert "Dramatis personae" not in play_html


def test_site_builder_renders_embedded_dramatis_personae_before_first_act(tmp_path: Path) -> None:
    front = """
    <front>
      <div type="dramatis-personae">
        <head><app><lem wit="#A">Acteurs</lem><rdg wit="#B">Acteurs</rdg></app></head>
        <castList>
          <castItem xml:id="thesee">
            <role>Thesee</role>
            <roleDesc>roi d'Athenes</roleDesc>
            <note type="semi-diplomatic">
              <app>
                <lem wit="#A">Thesee, roi d'Athenes</lem>
                <rdg wit="#B">Thesee, Roi d'Athenes</rdg>
              </app>
            </note>
          </castItem>
          <castItem xml:id="aricie">
            <role>Aricie</role>
            <roleDesc/>
            <note type="semi-diplomatic">Aricie</note>
          </castItem>
        </castList>
        <stage type="setting">
          <app>
            <lem wit="#A">La scene est a Trezene.</lem>
            <rdg wit="#B">La Scene est a Trezene.</rdg>
          </app>
        </stage>
      </div>
    </front>
    """

    play_html = _build_site(tmp_path, front=front)
    doc = lxml_html.document_fromstring(play_html)

    dramatis_sections = doc.xpath("//section[contains(@class, 'dramatis-personae')]")
    assert len(dramatis_sections) == 1
    assert doc.xpath("//section[@id='dramatis-personae' and contains(@class, 'dramatis-personae-block')]")
    assert not doc.xpath("//section[contains(@class, 'dramatic-content')]//section[contains(@class, 'dramatis-personae')]")
    assert doc.xpath("//section[@id='dramatis-personae']/h2[normalize-space(.)='Acteurs']")
    assert doc.xpath("//section[@id='dramatis-personae']//ul[contains(@class, 'cast-list')]/li//span[contains(@class, 'variation') and normalize-space(.)=\"Thesee, roi d'Athenes\"]")
    assert doc.xpath("//section[@id='dramatis-personae']//ul[contains(@class, 'cast-list')]/li//span[contains(@class, 'variation') and contains(@data-tooltip, \"Thesee, Roi d'Athenes\")]")
    assert doc.xpath("//section[@id='dramatis-personae']//li[normalize-space(.)='Aricie']")
    assert doc.xpath("//section[@id='dramatis-personae']/p[contains(@class, 'setting')]//span[contains(@class, 'variation') and normalize-space(.)='La scene est a Trezene.']")
    assert doc.xpath("//section[@id='dramatis-personae']/p[contains(@class, 'setting')]//span[contains(@class, 'variation') and contains(@data-tooltip, 'La Scene est a Trezene.')]")

    nav_links = doc.xpath("//main/nav//a[contains(@href, '#dramatis-personae')]")
    assert len(nav_links) == 1
    assert nav_links[0].text_content().strip() == "Dramatis personae"
    assert play_html.index('#dramatis-personae') < play_html.index("#ets-nav-phedre-act-1")
    assert play_html.index('id="dramatis-personae"') < play_html.index('id="ets-nav-phedre-act-1"')
    assert "roleDesc" not in play_html
    assert doc.xpath("//section[contains(@class, 'dramatic-content')]//*[normalize-space(.)='ACTE 1']")
    assert doc.xpath("//section[contains(@class, 'dramatic-content')]//*[normalize-space(.)='SCENE 1']")
    assert doc.xpath("//section[contains(@class, 'dramatic-content')]//*[normalize-space(.)='THESEE']")
    assert doc.xpath("//section[contains(@class, 'dramatic-content')]//span[contains(@class, 'variation') and contains(@data-tooltip, 'Je dis.')]")
    assert "Je parle." in play_html


def test_structured_dramatis_python_renderer_keeps_empty_lemma_empty(tmp_path: Path) -> None:
    front = """
    <front>
      <div type="dramatis-personae">
        <head>Acteurs</head>
        <castList>
          <castItem xml:id="ajout">
            <note type="semi-diplomatic">
              <app>
                <lem wit="#A" type="omission"/>
                <rdg wit="#B">vraiment </rdg>
              </app>
            </note>
          </castItem>
          <castItem xml:id="omission">
            <note type="semi-diplomatic">
              <app>
                <lem wit="#A">Visible</lem>
                <rdg wit="#B" type="omission"/>
              </app>
            </note>
          </castItem>
          <castItem xml:id="ponctuation">
            <note type="semi-diplomatic">
              <app type="minor" subtype="punctuation" ana="#punctuation_only">
                <lem wit="#A" type="omission"/>
                <rdg wit="#B">,</rdg>
              </app>
            </note>
          </castItem>
          <castItem xml:id="mixte">
            <note type="semi-diplomatic">
              <app type="minor" subtype="mixed" ana="#case_only+punctuation_only">
                <lem wit="#A">Cause,</lem>
                <rdg wit="#B">cause</rdg>
              </app>
            </note>
          </castItem>
        </castList>
      </div>
    </front>
    """

    play_html = _build_site(tmp_path, front=front)
    doc = lxml_html.document_fromstring(play_html)

    addition = doc.xpath("(//section[@id='dramatis-personae']//span[contains(@class, 'variation')])[1]")[0]
    assert "variation-empty" in (addition.get("class") or "")
    assert addition.get("tabindex") == "0"
    assert "vraiment" in (addition.get("data-tooltip") or "")
    assert addition.text_content() == ""
    assert "\\25E6" not in play_html
    assert "min-height: 1em" in play_html

    dramatis_text = doc.xpath("//section[@id='dramatis-personae']")[0].text_content()
    assert "vraiment" not in dramatis_text
    assert "\u25e6" not in dramatis_text

    omission = doc.xpath("(//section[@id='dramatis-personae']//span[contains(@class, 'variation')])[2]")[0]
    assert "variation-empty" not in (omission.get("class") or "")
    assert omission.text_content() == "Visible"
    assert "omission" in (omission.get("data-tooltip") or "")

    punctuation = doc.xpath("(//section[@id='dramatis-personae']//span[contains(@class, 'variation')])[3]")[0]
    assert "variation-empty" in (punctuation.get("class") or "")
    assert "variation-punctuation-only" in (punctuation.get("class") or "")
    assert punctuation.text_content() == ""
    assert "," in (punctuation.get("data-tooltip") or "")

    mixed = doc.xpath("(//section[@id='dramatis-personae']//span[contains(@class, 'variation')])[4]")[0]
    assert "variation-punctuation-only" not in (mixed.get("class") or "")
    assert mixed.text_content() == "Cause,"

    assert "Masquer les variantes de ponctuation" in play_html
    assert "hide-punctuation-variants" in play_html


def test_site_builder_uses_default_title_and_role_fallback_without_head(tmp_path: Path) -> None:
    front = """
    <front>
      <div type="dramatis-personae">
        <castList>
          <castItem xml:id="helene">
            <role>Helene</role>
          </castItem>
        </castList>
      </div>
    </front>
    """

    play_html = _build_site(tmp_path, front=front)
    doc = lxml_html.document_fromstring(play_html)

    assert doc.xpath("//section[@id='dramatis-personae']/h2[normalize-space(.)='Dramatis personae']")
    assert doc.xpath("//section[@id='dramatis-personae']//li[normalize-space(.)='Helene']")
    assert not doc.xpath("//section[@id='dramatis-personae']/p[contains(@class, 'setting')]")
