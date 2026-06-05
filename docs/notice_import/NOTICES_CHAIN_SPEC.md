# NOTICES_CHAIN_SPEC.md

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Objet

La chaîne d’import des notices transforme une prose savante structurée en TEI exploitable par ETS.

Elle vise les notices, introductions, préfaces éditoriales, annexes et bibliographies simples.

## 2. Principe

La notice est un objet éditorial autonome.

Elle n’est pas :

- le texte dramatique ;
- le dramatis personae ;
- l’apparat critique ;
- une annotation locale.

## 3. Chaîne cible

```text
DOCX stylé
  → Pandoc ou parseur compatible
  → validation des styles
  → modèle notice
  → TEI notice
  → HTML site
  → LaTeX standard
```

## 4. Styles

Les styles acceptés sont définis dans `WORD_STYLES_MAPPING.md`.

Tout style inconnu doit produire un diagnostic.
Selon sa gravité, il peut être bloquant ou non.

## 5. TEI cible

La TEI de notice doit rester simple :

- titres ;
- paragraphes ;
- divisions ;
- notes ;
- italiques ;
- listes ;
- citations ;
- bibliographie simple.

## 6. Publication

La notice doit pouvoir être attachée à une pièce et apparaître avant le texte dramatique dans la navigation.

## 7. LaTeX

La notice doit être exportable en LaTeX standard, pas en Ekdosis.
