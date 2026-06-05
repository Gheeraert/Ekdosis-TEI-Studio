# NOTICES_TEI_TARGET.md

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Objet

Ce fichier décrit la TEI cible pour les notices et péritextes.

## 2. Principe

La TEI des notices doit être régulière, sobre et facile à rendre en HTML comme en LaTeX standard.

## 3. Structure minimale

Exemple indicatif :

```xml
<TEI>
  <teiHeader>...</teiHeader>
  <text>
    <front>...</front>
    <body>
      <div type="notice">
        <head>Notice</head>
        <div type="section">
          <head>La création</head>
          <p>...</p>
        </div>
      </div>
    </body>
  </text>
</TEI>
```

## 4. Éléments recommandés

- `<div>` pour les sections ;
- `<head>` pour les titres ;
- `<p>` pour les paragraphes ;
- `<note>` pour les notes ;
- `<hi rend="italic">` pour les italiques ;
- `<list>` / `<item>` pour les listes ;
- `<quote>` ou `<cit>` selon les besoins ;
- `<bibl>` ou structure bibliographique simple.

## 5. Relation avec le texte dramatique

Ne pas introduire dans la TEI de notice les structures dramatiques :

- `<sp>` ;
- `<speaker>` ;
- `<l>` ;
- `<app>` ;
- `<lem>` ;
- `<rdg>`.

Ces éléments relèvent du texte critique dramatique.

## 6. Export LaTeX

La TEI de notice doit alimenter un convertisseur LaTeX standard :

```text
<head> → \section ou \subsection
<p> → paragraphe
<note> → \footnote{...}
<hi rend="italic"> → \emph{...}
```
