# CODEX_TASKLIST_NOTICE_IMPORT.md

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Objet

Ce fichier sert de liste de tâches pour le module d’import de notices.

Le module doit convertir des documents de prose savante vers une TEI régulière, sans perturber la chaîne dramatique ETS.

## 2. Documents de référence

- `NOTICES_CHAIN_SPEC.md`
- `WORD_STYLES_MAPPING.md`
- `NOTICES_VALIDATION_RULES.md`
- `NOTICES_TEI_TARGET.md`

## 3. Tâches prioritaires

1. Vérifier les styles Word acceptés.
2. Produire des diagnostics clairs en cas de style inconnu.
3. Convertir vers une TEI de notice simple.
4. Publier la notice dans le site builder.
5. Préparer l’export LaTeX standard des péritextes.

## 4. Non-objectifs

Ne pas :

- mélanger notice et texte dramatique ;
- convertir une notice en Ekdosis ;
- dépendre d’un chemin absolu local ;
- masquer les erreurs de styles ;
- réimplémenter toute la chaîne Métopes.

## 5. Tests nécessaires

Prévoir des fixtures pour :

- notice minimale ;
- notice avec sections ;
- notice avec notes ;
- notice avec listes ;
- notice avec bibliographie ;
- document contenant un style interdit.
