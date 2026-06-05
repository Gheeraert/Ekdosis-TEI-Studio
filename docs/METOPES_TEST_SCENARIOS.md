# Scénarios de test Métopes / notices

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Objet

Ce fichier rassemble des scénarios de test pour l’import et le rendu des notices ou péritextes issus d’une chaîne Word/Pandoc/Métopes-compatible.

## 2. Tests minimaux

Vérifier :

- chargement d’un document simple ;
- extraction du titre ;
- extraction des auteurs si présents ;
- sections et sous-sections ;
- paragraphes ;
- italiques ;
- notes ;
- listes ;
- citations simples ;
- bibliographie simple si disponible.

## 3. Tests d’intégration site

Vérifier qu’une notice peut être :

- attachée à une pièce ;
- affichée avant le texte dramatique ;
- intégrée dans la navigation ;
- publiée dans un site statique ;
- séparée du dramatis personae.

## 4. Tests futurs LaTeX

Vérifier qu’une notice TEI peut être exportée en LaTeX standard :

- `\section` ;
- `\subsection` ;
- paragraphes ;
- notes ;
- italiques ;
- citations ;
- bibliographie.

Ne pas utiliser Ekdosis pour ces tests.
