from __future__ import annotations

from lxml import etree

from ets.markdown_editor.parser import parse_markdown
from ets.markdown_editor.tei_export import export_tei_document, export_tei_fragment


TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def test_export_tei_document_contains_expected_structure() -> None:
    source = (
        "# Notice de Bérénice\n\n"
        "Ce texte est *classique* et **important**, avec [u]souligné[/u], "
        "[sup]lle[/sup], H[sub]2[/sub]O, [caps]senatvs[/caps], [sc]romanvs[/sc], "
        "un [lien](https://example.org) et une note[^1].\n\n"
        "> Citation brève.\n\n"
        "1. Point un\n"
        "2. Point deux\n\n"
        ":::bibl\n"
        "- Référence A\n"
        "- Référence B\n"
        ":::\n\n"
        "[^1]: Note de bas de page."
    )
    parsed = parse_markdown(source)
    tei_xml = export_tei_document(parsed.document, title="Notice test")
    root = etree.fromstring(tei_xml.encode("utf-8"))

    assert root.xpath("name()") == "TEI"
    assert root.xpath("string(/tei:TEI/tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title)", namespaces=TEI_NS) == "Notice test"
    assert root.xpath("/tei:TEI/tei:text/tei:body/tei:div[@type='notice']", namespaces=TEI_NS)
    assert root.xpath("//tei:div[@type='section']/tei:head", namespaces=TEI_NS)
    assert root.xpath("//tei:p", namespaces=TEI_NS)
    assert root.xpath("//tei:quote", namespaces=TEI_NS)
    assert root.xpath("//tei:list/tei:item", namespaces=TEI_NS)
    assert root.xpath("//tei:hi[@rend='italic']", namespaces=TEI_NS)
    assert root.xpath("//tei:hi[@rend='bold']", namespaces=TEI_NS)
    assert root.xpath("//tei:hi[@rend='underline']", namespaces=TEI_NS)
    assert root.xpath("//tei:hi[@rend='superscript']", namespaces=TEI_NS)
    assert root.xpath("//tei:hi[@rend='subscript']", namespaces=TEI_NS)
    assert root.xpath("//tei:hi[@rend='caps']", namespaces=TEI_NS)
    assert root.xpath("//tei:hi[@rend='smallcaps']", namespaces=TEI_NS)
    assert root.xpath("//tei:ref[@target='https://example.org']", namespaces=TEI_NS)
    assert root.xpath("//tei:note[@place='foot']", namespaces=TEI_NS)
    assert root.xpath("//tei:listBibl/tei:bibl", namespaces=TEI_NS)


def test_export_tei_fragment_returns_notice_div_only() -> None:
    source = "## État du texte\n\nParagraphe simple."
    parsed = parse_markdown(source)
    fragment_xml = export_tei_fragment(parsed.document)
    root = etree.fromstring(fragment_xml.encode("utf-8"))

    assert root.xpath("name()") == "div"
    assert root.get("type") == "notice"
    assert root.xpath("./tei:div[@type='section']", namespaces=TEI_NS)
    assert root.xpath(".//tei:p", namespaces=TEI_NS)
