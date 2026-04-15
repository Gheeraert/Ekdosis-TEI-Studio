# Scénarios de test conseillés pour ETS Site Builder

## Niveau 1 — fixtures minimales

### Détection du volume maître
- charger `Metopes_Test_Book.xml`
- vérifier que le document est reconnu comme un volume de type `book`
- vérifier que la navigation principale n'est pas vide

### Extraction des chapitres
- détecter l'introduction
- détecter le chapitre à sections hiérarchisées
- détecter la bibliographie

### Extraction des titres
- titre principal du volume
- sous-titre du volume
- titre d'introduction
- titre du chapitre
- titres imbriqués `section1 / section2 / section3`

### Rendu HTML minimal
- génération d'une page d'accueil
- génération d'une page de chapitre
- génération d'une page d'introduction
- présence visible des titres
- présence visible d'au moins une note
- présence visible d'un passage en italique

## Niveau 2 — fixtures réalistes

### Volume maître réel
- charger `Heraldique_et_Papaute_volII.xml`
- vérifier la détection de `group type="book"`
- vérifier la prise en compte des `xi:include`
- vérifier la détection des grands ensembles (`introduction`, `section1`, `bibliography`, etc.)

### Introduction réelle
- charger `Ch01_Introduction.xml`
- vérifier l'extraction du titre principal
- vérifier l'extraction de l'auteur
- vérifier la présence de notes de bas de page
- vérifier la présence d'italiques

### Robustesse
- vérifier qu'un build sans résolution complète de tous les `xi:include` échoue proprement ou dégrade proprement, selon la stratégie retenue
- vérifier que le rendu ne casse pas en présence de métadonnées incomplètes
