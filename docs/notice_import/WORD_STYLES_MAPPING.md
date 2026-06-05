# WORD_STYLES_MAPPING.md

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Objet

Ce fichier décrit les styles Word acceptés pour l’import des notices et péritextes.

La liste exacte peut évoluer, mais toute évolution doit être testée.

## 2. Principe

Les éditeurs travaillent avec des styles Word simples.
ETS valide ces styles puis les convertit vers une TEI de notice.

## 3. Familles de styles recommandées

| Famille | Exemple de style | TEI cible |
|---|---|---|
| titre notice | `Titre` | `<head>` principal |
| titre niveau 1 | `Titre 1` | `<div><head>` |
| titre niveau 2 | `Titre 2` | `<div><head>` imbriqué |
| paragraphe | `Normal` | `<p>` |
| citation | `Citation` | `<quote>` ou `<cit>` |
| note | note Word | `<note>` |
| bibliographie | `Bibliographie` | `<listBibl>` ou `<bibl>` |

## 4. Styles interdits

Les styles décoratifs ou non structurants doivent être refusés ou ignorés avec avertissement selon le cas.

Ne pas déduire une structure éditoriale de la seule apparence visuelle.

## 5. LaTeX

Ces styles devront aussi permettre un export LaTeX standard :

- titres → `\section`, `\subsection`, etc. ;
- paragraphes → paragraphes LaTeX ;
- notes → `\footnote{...}` ;
- italiques → `\emph{...}` ;
- bibliographie → environnement ou macro PURH à définir.
