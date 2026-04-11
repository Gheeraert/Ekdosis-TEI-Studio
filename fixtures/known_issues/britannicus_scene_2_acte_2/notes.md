# Cas difficile — vers morcelé et gestion multi-états

## Statut
⚠️ Cas non correctement pris en charge par le moteur actuel

- Le XML TEI fourni (`expected.xml`) correspond au **résultat attendu**
- Ce résultat n’est **pas généré automatiquement**
- Une **correction manuelle est actuellement nécessaire** (VS Code)

---

## Description du cas

Ce cas est issu d’un passage de *Britannicus* (Acte IV, scène II) avec :

- plusieurs témoins (A, B, C, D, E)
- structure dialoguée (AGRIPPINE / NÉRON)
- didascalies explicites (`**...**`)
- italiques internes (`_..._`)
- variantes nombreuses
- passages marqués `~~~~~~` (segments particuliers)

Le point critique est la présence de **vers morcelés en plusieurs segments**, parfois :

- implicites (non signalés par `***`)
- répartis sur plusieurs lignes
- pouvant interagir avec variantes et locuteurs

---

## Problème principal

Le moteur actuel (`comparer_etats`) ne parvient pas à :

- reconstruire correctement les vers continus à partir de segments multiples
- maintenir une numérotation cohérente des vers
- gérer correctement l’imbrication :
  - vers morcelé
  - variantes
  - changement de locuteur
  - didascalies

En conséquence :

- la sortie TEI est incorrecte ou incohérente
- une intervention manuelle est nécessaire pour obtenir un XML exploitable

---

## Nature du problème (hypothèses techniques)

Ce cas met en évidence plusieurs fragilités structurelles :

1. **Absence de modèle explicite du vers**
   - le vers est traité comme une ligne, non comme une unité logique reconstruite

2. **Dépendance à des marqueurs explicites (`***`)**
   - ici, le morcellement n’est pas toujours marqué ou pas de façon fiable

3. **Couplage fort dans `comparer_etats`**
   - gestion simultanée :
     - parsing
     - variantes
     - locuteurs
     - génération TEI
   - rend difficile la gestion de cas imbriqués

4. **Alignement des variantes non robuste sur segments discontinus**
   - `aligner_variantes_par_mot` suppose des unités relativement stables

---

## Conséquences

- impossibilité actuelle de traiter automatiquement certains passages complexes
- nécessité de corrections manuelles (coût en temps élevé)
- risque d’incohérence éditoriale

---

## Objectif à terme

Permettre au moteur de :

- reconstruire des vers à partir de segments multiples
- gérer les vers morcelés **même sans marquage explicite**
- maintenir :
  - la cohérence TEI
  - la numérotation
  - les variantes
  - les locuteurs

---

## Piste de traitement (à ne pas implémenter sans tests)

Ce cas devra être traité après mise en place de fixtures et tests, en particulier :

- introduire une **représentation intermédiaire du vers**
- découpler :
  - segmentation
  - alignement des variantes
  - génération TEI
- renforcer la détection des continuités de vers (heuristique ou marquage enrichi)

---

## Rôle de ce fichier

Ce cas sert de :

- 🔴 **cas limite critique**
- 🧪 **fixture de test avancée**
- 🧭 **guide pour évolution du moteur**

Il ne doit **pas être modifié** tant que le comportement cible n’est pas stabilisé.

---

## Fichiers associés

- `input.txt` : saisie brute multi-témoins
- `expected.xml` : sortie TEI corrigée manuellement (référence cible)
- `config.json` : métadonnées de la scène en JSON
---