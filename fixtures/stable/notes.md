# Fixture – Cas standard fonctionnel
## Andromaque, Acte I, Scène 1

Dernière mise à jour : 18 juillet 2026.

## Objectif

Ce fixture documente un cas **entièrement fonctionnel**, servant de référence stable pour :

- validation du pipeline complet
- non-régression
- comparaison avec cas limites

Le moteur doit produire un XML TEI correct **sans intervention manuelle**, et ce XML doit être :

- bien formé
- cohérent structurellement
- directement transformable en HTML via XSLT

---

## Fichiers du cas stable

- `input.txt` — transcription source multi-témoins (entrée utilisateur)
- `config.json` — métadonnées de la scène (témoins, personnages, numérotation)
- `expected.xml` — sortie XML-TEI de référence

Tests associés : `tests/test_pipeline_stable.py`, `tests/test_parser_stable.py`,
`tests/test_application_services.py`.

### 1. Texte source (`input.txt`)

Caractéristiques :

- 6 témoins alignés ligne à ligne
- structure explicite :
  - `####ACTE####`
  - `###SCENE###`
  - `##PERSONNAGES##`
  - `#LOCUTEUR#`
- variantes régulières (orthographe, ponctuation)
- variantes de ligne entière (`#####…`)
- vers partagés simples (***), correctement gérés
- pas de cas pathologique

### 2. Métadonnées (`config.json`)

Points importants :

- 6 témoins définis (A–F)
- numérotation du vers initial
- personnages explicitement fournis
- informations éditoriales complètes

### 3. Sortie attendue (`expected.xml`)

XML-TEI de référence produit par le moteur pour cette entrée.

---

## Autre fichier du dossier : `britannicus_I.txt`

Transcription de *Britannicus*, Acte I, alignée sur **5 témoins**.

Ce fichier ne fait pas partie du cas stable Andromaque. Il est utilisé
**délibérément comme entrée invalide** par les tests de chemins d'erreur :
combiné à une configuration dont le nombre de témoins ne correspond pas
(`fixtures/known_issues/britannicus_scene_2_acte_2/config.json`, 6 témoins),
il doit déclencher des diagnostics `E_BLOCK_SIZE` avec contexte (acte, scène,
numéro de bloc).

Tests associés : `tests/test_input_validator.py`,
`tests/test_application_services.py`.

Ne pas « corriger » ce fichier pour le faire passer avec cette configuration :
l'écart est voulu.

---

## Propriétés attendues (critères de validation)

### Structure TEI

- `<TEI>` racine valide
- `<teiHeader>` complet
- `<text><body>` correctement formé
- division hiérarchique :
  - `<div type="act">`
  - `<div type="scene">`

### Structure dramatique

- `<sp>` correctement ouverts/fermés
- `<speaker>` correct
- alternance des locuteurs respectée

### Vers

- `<l n="...">` correctement numérotés
- continuité stricte des numéros
- gestion correcte des vers partagés :
  - ex : 37.1 / 37.2

### Variantes

- utilisation correcte de :
  - `<app>`
  - `<lem>`
  - `<rdg>`
- alignement mot à mot cohérent
- pas de fragmentation excessive

### Typographie

- apostrophes normalisées
- espaces insécables cohérents
- ponctuation respectée

### Scènes et actes

- titres correctement encodés :
  - `<head>`
- variantes possibles sur les titres d'acte gérées via `<app>`

### HTML (post-XSLT)

Le XML produit doit pouvoir être transformé :

- sans erreur
- sans correction manuelle
- rendu lisible et structuré

---

## Rôle de ce fixture

Ce cas sert de :

- **baseline de confiance**
- référence pour comparaison
- garde-fou lors des refactorings

Toute modification du moteur (validation, parsing, collation, génération TEI)
doit :

✔ conserver un output strictement identique (ou équivalent structurellement)
✔ ne pas introduire de régression

## Remarques

Ce fixture représente un cas **idéal**.
Tout écart observé sur ce cas après modification doit être considéré comme une régression.

Une révision antérieure de ce même cas, utilisant l'ancien marqueur `######`
(syntaxe désormais rejetée par le validateur), est conservée dans
`fixtures/archive/andromaque_1_1/`.
