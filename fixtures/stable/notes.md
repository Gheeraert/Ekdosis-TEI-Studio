# Fixture – Cas standard fonctionnel
## Andromaque, Acte I, Scène 1

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

## Entrées

### 1. Texte source (multi-témoins)
Voir fichier :
→ :contentReference[oaicite:0]{index=0}

Caractéristiques :

- 6 témoins alignés ligne à ligne
- structure explicite :
  - `####ACTE####`
  - `###SCENE###`
  - `##PERSONNAGES##`
  - `#LOCUTEUR#`
- variantes régulières (orthographe, ponctuation)
- vers partagés simples (***), correctement gérés
- pas de cas pathologique

---

### 2. Métadonnées

Voir fichier :
→ :contentReference[oaicite:1]{index=1}

Points importants :

- 6 témoins définis (A–F)
- numérotation du vers initial
- personnages explicitement fournis
- informations éditoriales complètes

---

## Sortie attendue

### XML TEI produit

Voir fichier :
→ :contentReference[oaicite:2]{index=2}

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
- variantes possibles sur les titres d’acte gérées via `<app>`

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

Toute modification du moteur doit :

✔ conserver un output strictement identique (ou équivalent structurellement)  
✔ ne pas introduire de régression  

---

## Points de vigilance déjà validés

- alignement des variantes stable
- gestion des locuteurs correcte
- continuité des vers OK
- intégration TEI propre
- compatibilité XSLT validée

---

## À utiliser pour

- tests de non-régression
- comparaison avec cas difficiles
- validation après modification de :
  - `comparer_etats`
  - `aligner_variantes_par_mot`

---

## Fichiers associés

- `input.txt` Transcription entrée dans l'interface utilisateur
- `expected.xml` sortie XML-TEI
- `config.json` Fichier de métadonnées associées à la scène (configuration de la scène)

## Remarque

Ce fixture représente un cas **idéal**.  
Tout écart observé sur ce cas après modification doit être considéré comme une régression.