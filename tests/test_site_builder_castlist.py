from __future__ import annotations

from pathlib import Path

from lxml import html as lxml_html

from ets.site_builder.builder import build_static_site
from ets.site_builder.config import site_config_from_dict


def _write_play_xml(path: Path, *, front: str = "", body_line: str | None = None) -> None:
    line = body_line or '<l><app><lem wit="#A">Je parle.</lem><rdg wit="#B">Je dis.</rdg></app></l>'
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
        <listWit>
          <witness xml:id="A">A (1670) Barbin, BNF cote RES YF 3208</witness>
          <witness xml:id="B">B (1676) Collective</witness>
          <witness xml:id="C">C (1687) Collective</witness>
          <witness xml:id="D">D (1697) Definitive</witness>
          <witness xml:id="E">E (1670-Reg.) Premiere edition regularisee</witness>
        </listWit>
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
            {line}
          </sp>
        </div>
      </div>
    </body>
  </text>
</TEI>
""",
        encoding="utf-8",
    )


def _build_site(tmp_path: Path, *, front: str = "", body_line: str | None = None) -> str:
    dramatic_dir = tmp_path / "dramatic"
    output_dir = tmp_path / "site"
    dramatic_dir.mkdir()
    _write_play_xml(dramatic_dir / "phedre.xml", front=front, body_line=body_line)

    config = site_config_from_dict(
        {
            "site_title": "ETS Demo",
            "dramatic_xml_dir": str(dramatic_dir),
            "output_dir": str(output_dir),
        }
    )
    build_static_site(config)
    return (output_dir / "plays" / "phedre.html").read_text(encoding="utf-8")


def _visible_text_without_hidden(node) -> str:
    fragments: list[str] = []
    if node.get("hidden") is not None:
        return ""
    if node.text:
        fragments.append(node.text)
    for child in node:
        fragments.append(_visible_text_without_hidden(child))
        if child.tail:
            fragments.append(child.tail)
    return "".join(fragments)


def test_site_builder_without_dramatis_personae_keeps_old_behavior(tmp_path: Path) -> None:
    play_html = _build_site(tmp_path)
    doc = lxml_html.document_fromstring(play_html)

    assert not doc.xpath("//section[@id='dramatis-personae']")
    assert not doc.xpath("//main/nav//a[contains(@href, '#dramatis-personae')]")
    assert "Dramatis personae" not in play_html


def test_site_builder_published_play_embeds_relative_apparatus_script(tmp_path: Path) -> None:
    body_line = """
            <l><app type="minor" subtype="mixed" ana="#case_only+punctuation_only">
              <lem wit="#A #B #E">QUOY? </lem>
              <rdg wit="#D">Quoy! </rdg>
            </app> suite.</l>
    """

    play_html = _build_site(tmp_path, body_line=body_line)
    doc = lxml_html.document_fromstring(play_html)
    variant = doc.xpath("//section[contains(@class, 'dramatic-content')]//span[contains(@class, 'variation')]")[0]
    readings = variant.xpath("./span[contains(@class, 'app-reading')]")

    assert readings[0].get("data-wits") == "A B E"
    assert readings[1].get("data-wits") == "D"
    assert readings[1].get("hidden") is not None
    tooltip = variant.get("data-tooltip") or ""
    assert "D (1697): Quoy!" in tooltip
    assert "Definitive" not in tooltip
    assert "readingSignature" in play_html
    assert "buildRelativeTooltip" in play_html
    assert "variation-no-alternatives" in play_html
    assert "node.setAttribute('data-tooltip', tooltip)" in play_html
    assert "compactWitnessLabel" in play_html
    assert "data-witness-full-label" in play_html
    assert "A - A" not in play_html
    assert "B - B" not in play_html
    assert "C - C" not in play_html
    assert "D - D" not in play_html
    assert "E - E" not in play_html
    assert "min-width: min(18rem, calc(100vw - 4rem))" in play_html
    assert "max-width: min(42rem, calc(100vw - 4rem))" in play_html
    assert "box-sizing: border-box" in play_html


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
    cast_variant = doc.xpath("//section[@id='dramatis-personae']//ul[contains(@class, 'cast-list')]/li//span[contains(@class, 'variation') and contains(@data-tooltip, \"Thesee, Roi d'Athenes\")]")[0]
    assert _visible_text_without_hidden(cast_variant) == "Thesee, roi d'Athenes"
    assert cast_variant.xpath("./span[contains(@class, 'app-reading-default') and @data-kind='lem' and @data-wits='A']")
    assert cast_variant.xpath("./span[@hidden and @data-kind='rdg' and @data-wits='B' and normalize-space(.)=\"Thesee, Roi d'Athenes\"]")
    assert doc.xpath("//section[@id='dramatis-personae']//li[normalize-space(.)='Aricie']")
    setting_variant = doc.xpath("//section[@id='dramatis-personae']/p[contains(@class, 'setting')]//span[contains(@class, 'variation') and contains(@data-tooltip, 'La Scene est a Trezene.')]")[0]
    assert _visible_text_without_hidden(setting_variant) == "La scene est a Trezene."
    assert setting_variant.xpath("./span[contains(@class, 'app-reading-default') and @data-kind='lem' and @data-wits='A']")
    assert setting_variant.xpath("./span[@hidden and @data-kind='rdg' and @data-wits='B' and normalize-space(.)='La Scene est a Trezene.']")

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
          <castItem xml:id="casse">
            <note type="semi-diplomatic">
              <app type="minor" subtype="case" ana="#case_only">
                <lem wit="#A">Fils</lem>
                <rdg wit="#B">fils</rdg>
              </app>
            </note>
          </castItem>
          <castItem xml:id="espacement">
            <note type="semi-diplomatic">
              <app type="minor" subtype="spacing" ana="#spacing_or_hyphen_only">
                <lem wit="#A">bien-tost</lem>
                <rdg wit="#B">bientost</rdg>
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
    assert _visible_text_without_hidden(addition) == ""
    addition_readings = addition.xpath("./span[contains(@class, 'app-reading')]")
    assert len(addition_readings) == 2
    assert addition_readings[0].get("data-kind") == "lem"
    assert addition_readings[0].get("data-wits") == "A"
    assert addition_readings[0].get("data-omission") == "true"
    assert "app-reading-active" in (addition_readings[0].get("class") or "")
    assert addition_readings[1].get("data-kind") == "rdg"
    assert addition_readings[1].get("data-wits") == "B"
    assert addition_readings[1].get("hidden") is not None
    assert addition_readings[1].text_content() == "vraiment "
    assert "\\25E6" not in play_html
    assert "min-height: 1em" in play_html

    dramatis_text = doc.xpath("//section[@id='dramatis-personae']")[0].text_content()
    dramatis_visible_text = _visible_text_without_hidden(doc.xpath("//section[@id='dramatis-personae']")[0])
    assert "vraiment" not in dramatis_visible_text
    assert "\u25e6" not in dramatis_text

    omission = doc.xpath("(//section[@id='dramatis-personae']//span[contains(@class, 'variation')])[2]")[0]
    assert "variation-empty" not in (omission.get("class") or "")
    assert _visible_text_without_hidden(omission) == "Visible"
    omission_readings = omission.xpath("./span[contains(@class, 'app-reading')]")
    assert omission_readings[0].get("data-wits") == "A"
    assert omission_readings[1].get("data-wits") == "B"
    assert omission_readings[1].get("data-omission") == "true"
    assert omission_readings[1].get("hidden") is not None
    assert "omission" in (omission.get("data-tooltip") or "")

    punctuation = doc.xpath("(//section[@id='dramatis-personae']//span[contains(@class, 'variation')])[3]")[0]
    assert "variation-empty" in (punctuation.get("class") or "")
    assert "variation-punctuation-only" in (punctuation.get("class") or "")
    assert _visible_text_without_hidden(punctuation) == ""
    punctuation_readings = punctuation.xpath("./span[contains(@class, 'app-reading')]")
    assert punctuation_readings[0].get("data-wits") == "A"
    assert punctuation_readings[0].get("data-omission") == "true"
    assert punctuation_readings[1].get("data-wits") == "B"
    assert punctuation_readings[1].get("hidden") is not None
    assert "," in (punctuation.get("data-tooltip") or "")

    mixed = doc.xpath("(//section[@id='dramatis-personae']//span[contains(@class, 'variation')])[4]")[0]
    assert "variation-punctuation-only" not in (mixed.get("class") or "")
    assert "variation-mixed" in (mixed.get("class") or "")
    assert _visible_text_without_hidden(mixed) == "Cause,"

    case_variant = doc.xpath("(//section[@id='dramatis-personae']//span[contains(@class, 'variation')])[5]")[0]
    assert "variation-case-only" in (case_variant.get("class") or "")

    spacing_variant = doc.xpath("(//section[@id='dramatis-personae']//span[contains(@class, 'variation')])[6]")[0]
    assert "variation-spacing-or-hyphen-only" in (spacing_variant.get("class") or "")

    assert "apparatus-controls" in play_html
    assert "data-minor-master" in play_html
    assert "data-minor-child" in play_html
    assert "apparatus-minor-children" in play_html
    assert "margin-left: 1.35rem" in play_html
    assert "indeterminate" in play_html
    assert "syncMinorMasterState" in play_html
    assert "--site-header-offset" in play_html
    assert "z-index: 1700" in play_html
    assert "max-height:" in play_html
    assert "overflow: auto" in play_html
    assert ".app-reading[hidden]" in play_html
    assert "variation-no-alternatives" in play_html
    assert "data-wits" in play_html
    assert "app-reading-active" in play_html
    assert "Variantes de ponctuation" in play_html
    assert "hide-punctuation-variants" in play_html
    assert "hide-case-variants" in play_html
    assert "hide-spacing-variants" in play_html
    assert "hide-minor-variants" in play_html


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
