from __future__ import annotations

import html
from collections.abc import Iterable

from .document_fragments import encoded_reference
from .models import DTSNavNode, DTSTeiIndex


def _link(href: str, label: str) -> str:
    return (
        f'<a href="{html.escape(href, quote=True)}">'
        f"{html.escape(label)}"
        "</a>"
    )


def _first_nodes(index: DTSTeiIndex) -> tuple[DTSNavNode | None, DTSNavNode | None, DTSNavNode | None]:
    first_act = index.navigation[0] if index.navigation else None
    first_scene = first_act.children[0] if first_act and first_act.children else None
    first_line = first_scene.children[0] if first_scene and first_scene.children else None
    return first_act, first_scene, first_line


def _fragment_link(slug: str, node: DTSNavNode, label: str) -> str:
    href = f"api/dts/document/{slug}/{encoded_reference(node.identifier)}.xml"
    return f"<li>{_link(href, label)} <code>{html.escape(node.identifier)}</code></li>"


def _resource_section(index: DTSTeiIndex) -> str:
    resource = index.resource
    slug = resource.slug
    first_act, first_scene, first_line = _first_nodes(index)
    links = [
        f"<li>{_link(f'api/dts/collection/{slug}.json', 'Resource DTS')}</li>",
        f"<li>{_link(f'api/dts/navigation/{slug}/index.json', 'Navigation DTS')}</li>",
        f"<li>{_link(f'api/dts/document/{slug}/full.xml', 'TEI complet')}</li>",
    ]
    if first_act is not None:
        links.append(_fragment_link(slug, first_act, "Premier acte"))
    if first_scene is not None:
        links.append(_fragment_link(slug, first_scene, "Première scène"))
    if first_line is not None:
        links.append(_fragment_link(slug, first_line, "Premier vers"))

    author = (
        f'<p class="metadata">{html.escape(resource.author)}</p>'
        if resource.author
        else ""
    )
    return (
        '<section class="resource">'
        f"<h2>{html.escape(resource.title)}</h2>"
        f"{author}"
        f"<ul>{''.join(links)}</ul>"
        "</section>"
    )


def render_dts_demo_page(indexes: Iterable[DTSTeiIndex], *, site_title: str) -> str:
    ordered_indexes = sorted(indexes, key=lambda item: item.resource.slug)
    resource_sections = "".join(_resource_section(index) for index in ordered_indexes)
    if not resource_sections:
        resource_sections = "<p>Aucune pièce DTS n’a pu être exportée.</p>"

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>API DTS statique — {html.escape(site_title)}</title>
  <style>
    body {{ max-width: 900px; margin: 0 auto; padding: 2rem 1.25rem; color: #24201b; background: #f7f3ea; font: 18px/1.55 Georgia, serif; }}
    h1, h2 {{ line-height: 1.2; }}
    a {{ color: #6c3328; }}
    code {{ font-size: 0.9em; }}
    .intro, .resource, .questions {{ margin: 1.5rem 0; padding: 1rem 1.25rem; background: #fffdf8; border: 1px solid #d8cdbd; }}
    .metadata {{ color: #62594e; }}
  </style>
</head>
<body>
  <main>
    <h1>API DTS statique</h1>
    <section class="intro">
      <p>Cette page permet d’explorer les fichiers DTS produits avec le site statique.</p>
      <p><strong>HTML</strong> sert à la lecture humaine. <strong>TEI</strong> reste le format savant canonique. <strong>DTS</strong> forme une couche d’interopérabilité statique pour la découverte, la navigation et la récupération de fragments.</p>
      <ul>
        <li>{_link("api/dts/index.json", "Point d’entrée DTS")}</li>
        <li>{_link("api/dts/collection/index.json", "Collection DTS")}</li>
      </ul>
    </section>
    {resource_sections}
    <section class="questions">
      <h2>Questions ouvertes</h2>
      <ul>
        <li>Conformité exacte de l’enveloppe TEI contenant <code>dts:fragment</code>.</li>
        <li>Pertinence du fragment de vers sous forme de <code>sp</code> réduit avec <code>speaker</code> et un seul <code>l</code>.</li>
        <li>Limites d’une API DTS entièrement matérialisée en fichiers statiques.</li>
      </ul>
    </section>
  </main>
</body>
</html>
"""
