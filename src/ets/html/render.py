from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
import html as std_html

from lxml import etree, html as lxml_html

from .transform import render_html_preview_from_tei

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}


@dataclass(frozen=True)
class HtmlExportOptions:
    document_title: str | None = None
    css_href: str | None = None
    script_srcs: tuple[str, ...] = field(default_factory=tuple)
    include_menu: bool = True
    include_header: bool = True
    include_footer: bool = True
    menu_placeholder: str = "Chargement du menu..."
    header_html: str = ""
    footer_html: str = ""


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

def _build_credit_block(
    *,
    author: str,
    title: str,
    act: str,
    scene: str,
    editor: str,
    xml_href: str | None,
) -> str:
    context: list[str] = []
    if act:
        context.append(f"Acte {std_html.escape(act)}")
    if scene:
        context.append(f"Scène {std_html.escape(scene)}")
    context_suffix = f", {', '.join(context)}" if context else ""
    title_html = f'<span class="italic">{std_html.escape(title)}</span>' if title else ""
    first_line_text = ""
    if author and title_html:
        first_line_text = f"{std_html.escape(author)} - {title_html}{context_suffix}"
    elif title_html:
        first_line_text = f"{title_html}{context_suffix}"
    elif author:
        first_line_text = f"{std_html.escape(author)}{context_suffix}"

    credit_lines: list[str] = []
    if first_line_text:
        credit_lines.append(f'<div class="credit-line">{first_line_text}</div>')
    if editor:
        credit_lines.append(f'<div class="credit-line">Édition critique par {std_html.escape(editor)}</div>')
    credit_lines.append(
        f'<div class="credit-line">Document généré le {date.today().isoformat()} depuis Ekdosis-TEI Studio</div>'
    )
    if xml_href:
        escaped_href = std_html.escape(xml_href, quote=True)
        credit_lines.append(
            f'<div class="credit-line"><a href="{escaped_href}" download>Télécharger le XML</a></div>'
        )
    return "\n".join(credit_lines)


def _build_export_shell(
    *,
    title: str,
    assets: str,
    body_content: str,
    credit_html: str,
    options: HtmlExportOptions,
) -> str:
    menu_html = (
        f'<aside id="menu-lateral">{std_html.escape(options.menu_placeholder)}</aside>' if options.include_menu else ""
    )
    header_html = f'<div id="header">{options.header_html}</div>' if options.include_header else ""
    footer_html = f'<div id="footer">{options.footer_html}</div>' if options.include_footer else ""
    css_link = f'<link rel="stylesheet" href="{std_html.escape(options.css_href, quote=True)}">' if options.css_href else ""
    scripts = "\n".join(
        f'<script src="{std_html.escape(src, quote=True)}"></script>' for src in options.script_srcs
    )

    container_classes = "with-menu" if options.include_menu else "without-menu"

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{std_html.escape(title)}</title>
  {css_link}
  {assets}
  <style>
    body {{
      margin: 0;
      padding: 0;
    }}
    #container {{
      display: grid;
      grid-template-columns: 240px 1fr;
      min-height: 100vh;
    }}
    #container.without-menu {{
      grid-template-columns: 1fr;
    }}
    #menu-lateral {{
      border-right: 1px solid #ddd;
      padding: 1rem;
      font-family: sans-serif;
      color: #444;
    }}
    main {{
      width: 100%;
      max-width: 980px;
      margin: 0 auto;
      padding: 1rem;
    }}
    #header, #footer {{
      min-height: 1.5rem;
    }}
    .bloc-credit {{
      margin: 1rem auto 1.5rem;
      max-width: 760px;
      border: 1px solid #d6d2ca;
      border-radius: 6px;
      padding: 0.75rem 1rem;
      background: #fffdf8;
      line-height: 1.35;
    }}
    .credit-line + .credit-line {{
      margin-top: 0.25rem;
    }}
    .ets-export-content {{
      margin-top: 1rem;
    }}
  </style>
</head>
<body>
  <div id="container" class="{container_classes}">
    {menu_html}
    <main>
      {header_html}
      <section class="bloc-credit" aria-label="Crédits de l'édition">
        {credit_html}
      </section>
      <section id="contenu-editorial" class="ets-export-content">
        {body_content}
      </section>
      {footer_html}
    </main>
  </div>
  {scripts}
</body>
</html>
"""


def render_html_export_from_tei(
    tei_xml: str,
    xml_href: str | None = None,
    options: HtmlExportOptions | None = None,
) -> str:
    """Render a publication-ready HTML base from TEI XML."""
    selected = options or HtmlExportOptions()
    preview_html = render_html_preview_from_tei(tei_xml)
    preview_doc = lxml_html.document_fromstring(preview_html)
    tei_doc = etree.fromstring(tei_xml.encode("utf-8"))

    title = _first_text(tei_doc, "string(/tei:TEI/tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title[1])") or "Edition TEI"
    author = _first_text(tei_doc, "string(/tei:TEI/tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:author[1])")
    editor = _first_text(tei_doc, "string(/tei:TEI/tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:editor[1])")
    act = _first_text(tei_doc, "string((/tei:TEI/tei:text/tei:body/tei:div[@type='act']/@n)[1])")
    scene = _first_text(tei_doc, "string((/tei:TEI/tei:text/tei:body/tei:div[@type='act']/tei:div[@type='scene']/@n)[1])")

    assets = _extract_preview_assets(preview_doc)
    body_content = _extract_preview_body_content(preview_doc)
    credits_html = _build_credit_block(
        author=author,
        title=title,
        act=act,
        scene=scene,
        editor=editor,
        xml_href=xml_href,
    )
    page_title = selected.document_title or title
    return _build_export_shell(
        title=page_title,
        assets=assets,
        body_content=body_content,
        credit_html=credits_html,
        options=selected,
    )
