from __future__ import annotations

from datetime import date
import html as std_html

from lxml import etree, html as lxml_html

from .transform import render_html_preview_from_tei

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def _first_text(doc: etree._Element, xpath: str) -> str:
    result = doc.xpath(xpath, namespaces=TEI_NS)
    if result is None:
        return ""

    first: object
    if isinstance(result, list):
        if not result:
            return ""
        first = result[0]
    else:
        first = result

    if isinstance(first, etree._Element):
        return "".join(first.itertext()).strip()
    return str(first).strip()


def _extract_preview_assets(preview_doc: etree._Element) -> str:
    assets: list[str] = []
    for node in preview_doc.xpath("/html/head/style | /html/head/link"):
        assets.append(etree.tostring(node, encoding="unicode", method="html"))
    return "\n".join(assets)


def _extract_preview_body_content(preview_doc: etree._Element) -> str:
    body = preview_doc.xpath("/html/body")
    if not body:
        return ""
    html_fragments: list[str] = []
    for child in body[0]:
        class_name = child.get("class", "")
        if "bloc-credit" in class_name:
            continue
        html_fragments.append(etree.tostring(child, encoding="unicode", method="html"))
    return "\n".join(html_fragments)


def render_html_export_from_tei(tei_xml: str, xml_href: str | None = None) -> str:
    """Render a publication-ready HTML base from TEI XML."""
    preview_html = render_html_preview_from_tei(tei_xml)
    preview_doc = lxml_html.document_fromstring(preview_html)
    tei_doc = etree.fromstring(tei_xml.encode("utf-8"))

    title = _first_text(tei_doc, "string(/tei:TEI/tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title[1])") or "Edition TEI"
    author = _first_text(tei_doc, "string(/tei:TEI/tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:author[1])")
    editor = _first_text(tei_doc, "string(/tei:TEI/tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:editor[1])")
    act = _first_text(tei_doc, "string((/tei:TEI/tei:text/tei:body/tei:div[@type='act']/@n)[1])")

    credit_lines: list[str] = []
    if author or title:
        credit_lines.append(f"{author} - {title}" if author else title)
    if act:
        credit_lines.append(f"Acte {act}")
    if editor:
        credit_lines.append(f"Edition critique par {editor}")
    credit_lines.append(f"Document genere le {date.today().isoformat()} depuis Ekdosis-TEI Studio")

    assets = _extract_preview_assets(preview_doc)
    body_content = _extract_preview_body_content(preview_doc)
    xml_line = (
        f'<div class="credit-line"><a href="{std_html.escape(xml_href, quote=True)}">Telecharger le XML</a></div>'
        if xml_href
        else ""
    )
    credits_html = "\n".join(f'<div class="credit-line">{std_html.escape(line)}</div>' for line in credit_lines)

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{std_html.escape(title)}</title>
  {assets}
  <style>
    .ets-export-root {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 1rem;
    }}
    .ets-export-main {{
      max-width: 980px;
      margin: 0 auto;
    }}
    .ets-export-content {{
      margin-top: 1rem;
    }}
  </style>
</head>
<body class="ets-export-root">
  <main class="ets-export-main">
    <div class="bloc-credit">
      {credits_html}
      {xml_line}
    </div>
    <section class="ets-export-content">
      {body_content}
    </section>
  </main>
</body>
</html>
"""
