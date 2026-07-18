"""Contrôle d'une installation depuis une wheel réelle, hors du dépôt.

À exécuter avec l'interpréteur d'un environnement vierge dans lequel seule
la wheel construite a été installée, depuis un répertoire de travail
extérieur au dépôt (voir le job « wheel » de `.github/workflows/ci.yml`) :

    python tools/check_wheel_install.py

Le script vérifie que le paquet installé est auto-suffisant : ressources
embarquées, transformation TEI → HTML avec polices locales, application
Flask importable.
"""

from __future__ import annotations

import importlib.resources


MINIMAL_TEI = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Mini</title><author>Auteur</author></titleStmt>
      <publicationStmt><p>Test</p></publicationStmt>
      <sourceDesc>
        <listWit>
          <witness xml:id="A">A (1670) temoin A</witness>
          <witness xml:id="B">B (1671) temoin B</witness>
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
            <l n="1">Oui je viens <app><lem wit="#A">encore</lem><rdg wit="#B">encor</rdg></app> te chercher.</l>
          </sp>
        </div>
      </div>
    </body>
  </text>
</TEI>
"""

REQUIRED_RESOURCES = (
    "odd/ets-racine.odd",
    "schemas/ets-racine.rnc",
    "schemas/ets-racine.sch",
    "schemas/tei_all.rng",
    "xslt/tei-vers-html.xsl",
    "fonts/eb-garamond-latin.woff2",
    "fonts/eb-garamond-latin-ext.woff2",
    "fonts/im-fell-dw-pica-latin.woff2",
    "fonts/source-sans-pro-latin.woff2",
    "fonts/source-sans-pro-latin-ext.woff2",
    "fonts/LICENCES.md",
    "fonts/OFL.txt",
)


def main() -> None:
    import ets

    assert "site-packages" in ets.__file__, (
        f"ets doit provenir d'une installation wheel, pas de src/ : {ets.__file__}"
    )

    root = importlib.resources.files("ets.resources")
    missing = [
        path for path in REQUIRED_RESOURCES
        if not root.joinpath(*path.split("/")).is_file()
    ]
    assert not missing, f"Ressources manquantes dans le paquet installé : {missing}"

    from ets.html import render_html_preview_from_tei

    html = render_html_preview_from_tei(MINIMAL_TEI)
    assert "@font-face" in html, "aperçu HTML sans règle @font-face"
    assert "data:font/woff2;base64," in html, "aperçu HTML sans police en data-URI"
    assert "fonts.googleapis.com" not in html, "requête Google Fonts (googleapis)"
    assert "fonts.gstatic.com" not in html, "requête Google Fonts (gstatic)"
    assert "vers-container" in html, "structure HTML de l'aperçu inattendue"

    from ets.web import create_app

    app = create_app(testing=True)
    assert list(app.url_map.iter_rules()), "url_map Flask vide"

    print("Contrôle wheel : succès")
    print(f"- paquet : {ets.__file__}")
    print(f"- ressources vérifiées : {len(REQUIRED_RESOURCES)}")
    print(f"- aperçu HTML : {len(html)} caractères, polices embarquées")
    print(f"- routes Flask : {len(list(app.url_map.iter_rules()))}")


if __name__ == "__main__":
    main()
