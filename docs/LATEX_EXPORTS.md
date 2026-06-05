# LATEX_EXPORTS.md — sorties LaTeX, Ekdosis et mise en page PURH

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Objet

Ce document fixe l’architecture cible pour le rétablissement des sorties LaTeX.

Le projet distingue désormais :

1. le texte dramatique critique, exporté en LaTeX-Ekdosis ;
2. les péritextes et paratextes, exportés en LaTeX standard ;
3. la mise en page finale PURH, portée par une couche commune.

## 2. Principe central

La sortie LaTeX doit être dérivée de la TEI canonique.

Ne pas restaurer l’ancienne architecture directe :

```text
ETS transcription → LaTeX
```

La cible est :

```text
ETS transcription → TEI canonique → LaTeX
```

## 3. Deux familles de LaTeX

### 3.1 Texte dramatique critique

Le texte dramatique critique utilise Ekdosis pour :

- les témoins ;
- les lemmes ;
- les variantes ;
- les lacunes ;
- l’apparat critique ;
- les vers numérotés ;
- les structures dramatiques.

La TEI source contient notamment :

```xml
<app>
  <lem wit="#A">...</lem>
  <rdg wit="#B #C">...</rdg>
</app>
```

La sortie cible peut utiliser des formes du type :

```latex
\app{
  \lem[wit={A}]{...}
  \rdg[wit={B,C}]{...}
}
```

La syntaxe exacte doit être confirmée à partir des sorties V1 fonctionnelles.

### 3.2 Péritextes et paratextes

Les notices, introductions, préfaces éditoriales modernes, bibliographies et annexes en prose ne doivent pas être forcées dans Ekdosis.

Elles doivent produire du LaTeX standard :

```latex
\section{Notice}
\subsection{La création}
Texte de la notice...\footnote{Note.}
```

## 4. Couche PURH

La mise en page PURH ne doit pas être codée directement dans les convertisseurs.

Elle doit être isolée dans une couche commune :

```text
latex/
  purh.cls              option idéale à terme
  purh-ekdosis.sty      macros pour le texte critique
  purh-peritexts.sty    macros pour la prose savante
  templates/
    main.tex
    preamble.tex
```

Le générateur produit du contenu.
Le template PURH produit le livre.

## 5. Assemblage cible

Un export complet pourrait produire :

```text
export_latex/
  main.tex
  metadata.tex
  purh_preamble.tex
  peritexts/
    notice.tex
    introduction.tex
    bibliographie.tex
  edition/
    texte_critique_ekdosis.tex
```

`main.tex` assemble les parties :

```latex
\documentclass{purh}
\input{purh_preamble}
\input{metadata}

\begin{document}
\maketitle
\input{peritexts/notice}
\input{peritexts/introduction}
\mainmatter
\input{edition/texte_critique_ekdosis}
\backmatter
\input{peritexts/bibliographie}
\end{document}
```

## 6. Convertisseur TEI → Ekdosis

Créer une couche dédiée, par exemple :

```text
src/ets/latex/
  ekdosis_from_tei.py
  standard_from_tei.py
  escaping.py
  templates.py
```

Le convertisseur Ekdosis doit consommer de la TEI.
Il doit gérer le contenu XML mixte : `node.text`, enfants XML, `child.tail`.

Cas à traiter en première passe :

- `<text>` / `<body>` ;
- actes ;
- scènes ;
- `<sp>` ;
- `<speaker>` ;
- `<l>` ;
- `<stage>` ;
- `<app>` ;
- `<lem>` ;
- `<rdg>` ;
- lacunes ;
- italiques `<hi rend="italic">` ;
- espaces insécables ;
- vers partagés ;
- strophes si déjà stabilisées dans la TEI.

Hors périmètre de la première passe :

- maquette PURH définitive ;
- dramatis personae complexe ;
- notices complètes ;
- bibliographies complexes ;
- raffinements typographiques avancés.

## 7. Convertisseur TEI → LaTeX standard

Le convertisseur standard doit viser la prose savante :

- titres ;
- paragraphes ;
- notes ;
- citations ;
- listes ;
- italiques ;
- petites capitales si nécessaire ;
- références bibliographiques simples ;
- sections et sous-sections.

Il peut être développé après le noyau Ekdosis.

## 8. Fixtures de référence

Les sorties V1 fonctionnelles sont essentielles.

Créer des fixtures :

```text
tests/fixtures/latex/ekdosis/simple_line/input.xml
tests/fixtures/latex/ekdosis/simple_line/expected.tex

tests/fixtures/latex/ekdosis/local_variant/input.xml
tests/fixtures/latex/ekdosis/local_variant/expected.tex

tests/fixtures/latex/ekdosis/shared_verse/input.xml
tests/fixtures/latex/ekdosis/shared_verse/expected.tex
```

Ajouter ensuite un acte ou une scène complète issue de la V1.

## 9. Ce que l’on peut reprendre de la V1

Reprendre :

- la syntaxe des macros Ekdosis ;
- le préambule minimal qui compilait ;
- les règles d’échappement LaTeX ;
- les exemples de sortie validés ;
- les conventions de numérotation des vers.

Ne pas reprendre :

- l’architecture monolithique ;
- la génération directe depuis la transcription ;
- les dépendances implicites à l’interface ;
- les corrections tardives qui masqueraient des entrées invalides.

## 10. Ordre recommandé du chantier

1. Inventorier les sorties V1 correctes.
2. Choisir 3 fixtures minimales TEI → `.tex`.
3. Écrire `escaping.py`.
4. Écrire le rendu inline TEI récursif.
5. Écrire le rendu des `<app>/<lem>/<rdg>`.
6. Écrire le rendu des `<sp>`, `<speaker>`, `<l>`, `<stage>`.
7. Produire une scène `.tex` compilable.
8. Ajouter le squelette PURH minimal.
9. Ajouter les péritextes en LaTeX standard.
10. Assembler un volume complet.
