# Sorties HTML V2

## Objectif

La V2 fournit deux sorties HTML distinctes à partir du même TEI :

1. **Preview HTML rapide**
2. **Export HTML publiable (base)**

Cette séparation permet de garder un rendu éditeur immédiat, tout en préparant une sortie plus stable pour la publication.

Les sorties HTML doivent désormais aussi pouvoir prendre en compte une première couche de **notes éditoriales**, lorsque le TEI en contient.

## Preview HTML rapide

- Fonction : `render_html_preview_from_tei(tei_xml: str) -> str`
- Module : `src/ets/html/transform.py`
- Mecanisme : transformation XSLT via fichier externe `tei-vers-html.xsl`
- But : affichage direct des elements editoriaux principaux (acte/scene, locuteurs, vers, variantes, didascalies)

La preview doit rester simple et robuste, sans habillage portail complexe.

Si le TEI contient des notes éditoriales, la preview doit afficher des appels de note lisibles ainsi qu’un rendu simple du contenu des notes.

## Export HTML publiable (base)

- Fonction : `render_html_export_from_tei(tei_xml: str, xml_href: str | None = None, options: HtmlExportOptions | None = None) -> str`
- Module : `src/ets/html/render.py`
- Mecanisme :
  - reutilise la preview XSLT comme couche de rendu du texte
  - ajoute un habillage HTML complet et un bloc de credits
  - permet d'ajouter un lien vers le XML source (`xml_href`)

Cette sortie est une base publiable et extensible. Elle n'est pas encore un clone du portail editorial final.
Elle ne cherche pas, a ce stade, a reproduire la structure complete de `fixtures/html_reference/britannicus_AI_S1_of4.html`.

Lorsque le TEI contient des notes éditoriales, l’export HTML doit les préserver.
Pour cette V1, un rendu simple et stable suffit : notes de fin, notes de bas de page simples, ou bloc de notes en fin de scène / fin de document.
Aucun dispositif interactif complexe n’est requis à ce stade.

## Enveloppe editoriale export (niveau actuel)

L'export ajoute maintenant une structure de page proche de la reference editoriale :

- `div#container`
- `aside#menu-lateral` (optionnel)
- `main`
- `div#header` (optionnel)
- bloc credits
- `section#contenu-editorial` (contenu transforme depuis la preview XSLT)
- `div#footer` (optionnel)

Le menu/header/footer restent volontairement simples a ce stade pour preparer une integration future.
L'export adapte aussi la mise en page :

- menu present : grille a deux colonnes
- menu absent : grille mono-colonne sans espace lateral vide

## Configuration simple de l'habillage

`HtmlExportOptions` permet de parametrer legerement l'enveloppe :

- `document_title`
- `css_href`
- `script_srcs`
- `include_menu`, `include_header`, `include_footer`
- `menu_placeholder`
- `header_html`, `footer_html`

## Qualite typographique (passe courte)

La passe actuelle corrige les libelles export en francais :

- `Scène`
- `Édition critique par`
- `Document généré le`
- `Télécharger le XML`

Cette amelioration reste volontairement sobre et n'ouvre pas de chantier editorial plus large.

## Notes éditoriales (V1)

Les notes éditoriales constituent une couche distincte de la transcription source.

En conséquence :

- elles ne sont pas saisies dans `input.txt`
- elles sont injectées dans le TEI après génération
- les sorties HTML doivent les rendre de façon lisible si elles sont présentes

Pour cette première version, un rendu simple est acceptable :

- appel de note discret dans le texte ;
- note affichée en bas de document ;
- ou note affichée en fin de scène.

L’objectif n’est pas encore de produire un appareil critique HTML richement interactif, mais d’assurer la continuité :
annotation -> TEI enrichi -> HTML lisible.

## Role de `tei-vers-html.xsl`

- `tei-vers-html.xsl` est la feuille de transformation principale pour le rendu TEI -> HTML.
- Elle est chargee depuis le fichier du depot (pas de XSLT embarquee en chaine Python).
- Les evolutions doivent privilegier de petits ajustements compatibles avec le TEI reel produit par le moteur.

## Statut de `fixtures/html_reference/britannicus_AI_S1_of4.html`

Le fichier `fixtures/html_reference/britannicus_AI_S1_of4.html` est une **reference de structure**.

- Ce n'est pas une golden fixture a reproduire au caractere pres.
- Les tests HTML verifient des proprietes structurelles et semantiques (presence d'elements/classes/contenu utile), pas une stricte egalite textuelle.
- L'export actuel s'en rapproche sur l'ossature, mais pas encore sur tous les details de portail (scripts, menu dynamique, theme complet).

## `teiHeader` vs `metadonnees`

- Le **header canonique** reste `teiHeader`.
- Le bloc optionnel `metadonnees` est un support de presentation HTML.
- Cette distinction doit rester explicite dans le code et la documentation.
