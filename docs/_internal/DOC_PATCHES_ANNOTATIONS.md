# Notes internes de documentation

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Statut

Ce fichier n’est pas une spécification fonctionnelle.
Il sert de mémoire interne pour les grands réalignements documentaires.

## 2. Réécriture du 5 juin 2026

Objectif : remettre la documentation Markdown en accord avec l’état actuel du projet.

Principes ajoutés ou clarifiés :

- TEI comme représentation canonique ;
- validateur comme gardien du seuil ;
- sortie LaTeX-Ekdosis à rétablir depuis la TEI ;
- sortie LaTeX standard pour les péritextes ;
- couche de mise en page PURH séparée ;
- site builder comme publication statique ;
- notices comme objets distincts du texte dramatique ;
- ancienne documentation reclassée comme mémoire historique.

## 3. Fichiers concernés

- `AGENTS.md`
- `README.md`
- `docs/SPEC_V2.md`
- `docs/LATEX_EXPORTS.md`
- `docs/editer_racine_principes.md`
- `docs/Documentation_ancienne.md`
- `docs/header_attendu_tei.md`
- `docs/HTML_OUTPUTS.md`
- `docs/UI_TK_V1.md`
- `docs/ETS_SITE_BUILDER.md`
- `docs/SITE_BUILDER_TARGET.md`
- `docs/notice_import/*`

## 4. Règle pour les futurs patchs

Toute mise à jour documentaire doit éviter d’empiler des doctrines contradictoires.

Si une ancienne règle est remplacée, l’indiquer clairement plutôt que la laisser coexister avec la nouvelle.
