# Internal patch notes — annotations V1

This document was used to update project documentation.
It is not part of the functional specification.

# DOC_PATCHES_ANNOTATIONS.md

Ce dossier contient deux choses :

1. un **nouveau fichier** à ajouter au projet : `docs/ANNOTATIONS_V1.md`
2. des **versions mises à jour complètes** des fichiers de documentation existants

## Nouveau fichier

- `updated_project_docs/docs/ANNOTATIONS_V1.md`

## Fichiers existants mis à jour

- `updated_project_docs/README.md`
- `updated_project_docs/AGENTS.md`
- `updated_project_docs/docs/SPEC_V2.md`
- `updated_project_docs/docs/UI_TK_V1.md`
- `updated_project_docs/docs/HTML_OUTPUTS.md`

## Nature des changements

### README.md
- ajout du périmètre « editorial annotations »
- mise à jour de la structure du dépôt
- ajout d’une section dédiée aux annotations
- mise à jour de la roadmap

### AGENTS.md
- annotations éditoriales ajoutées au scope
- non-goals précisés
- nouvelle section `Editorial annotations policy`
- objectif UI enrichi

### docs/SPEC_V2.md
- milestone initial légèrement resserré
- milestones ultérieurs complétés
- nouvelle section `Editorial annotations (V1)`

### docs/UI_TK_V1.md
- annotations ajoutées au périmètre Tkinter
- onglet `Annotations`
- menus enrichis
- services attendus enrichis
- contrainte UX explicite pour éviter la sélection libre dans le texte source en V1
- critère de réussite mis à jour

### docs/HTML_OUTPUTS.md
- prise en compte des notes éditoriales dans la preview
- prise en compte des notes éditoriales dans l’export
- nouvelle section `Notes éditoriales (V1)`

## Conseil de dépôt

Ordre recommandé :

1. ajouter `docs/ANNOTATIONS_V1.md`
2. comparer puis remplacer les fichiers existants si le contenu vous convient
3. seulement ensuite lancer Codex sur l’implémentation
