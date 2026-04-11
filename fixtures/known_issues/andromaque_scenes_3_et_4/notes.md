# Known issue — vers partagé avec changement de scène
## Andromaque, Acte I, scènes 3–4

## Statut
⚠️ Cas limite non correctement pris en charge par le moteur actuel

- Le moteur produit un XML partiellement exploitable
- Mais la gestion du vers partagé au moment du changement de scène n’est pas conceptuellement correcte
- Le résultat attendu ne peut pas être considéré comme solidement garanti par la logique actuelle
- Toute correction fiable suppose probablement une reprise plus profonde de la modélisation des vers et des divisions

---

## Description du cas

Ce cas couvre la transition entre deux scènes consécutives :

- scène III
- scène IV

Le problème porte sur un **vers partagé interrompu en fin de scène III**, puis poursuivi ou relayé au seuil de la scène IV.

Exemples concernés dans la saisie :

- scène III :
  - `Seigneur....***`
  - `***Vne autre fois ie t'ouuriray mon Ame,`
  - `Andromaque paroist.***`

- scène IV :
  - reprise immédiate du dialogue dans une nouvelle division scénique
  - ouverture de la scène IV avec une nouvelle structure de personnages et de locuteurs

---

## Nature du problème

Le moteur actuel sait gérer certains vers partagés **à l’intérieur d’une même scène**.

En revanche, ici, il doit articuler simultanément :

- un vers partagé (`***`)
- un changement de locuteur
- un changement de scène
- une rupture structurelle TEI (`<div type="scene">`)
- une renumérotation continue des vers

Or ces opérations ne relèvent pas du même niveau logique.

Le moteur actuel semble traiter :

- le vers partagé comme un phénomène local de ligne
- la scène comme une simple division de flux

Mais il ne dispose pas d’un véritable modèle permettant de dire :

> “ce segment appartient encore au même événement métrique, bien que la structure dramatique ait changé”

---

## Symptômes observés

### Dans la saisie

La fin de la scène III contient un vers partagé inachevé et un seuil dramatique :

- `Seigneur....***`
- `***Vne autre fois ie t'ouuriray mon Ame,`
- `Andromaque paroist.***`

### Dans la sortie TEI

Le moteur produit une numérotation fragmentée locale :

- `257.1`
- `257.2`
- `258.1`

puis la scène IV recommence avec :

- `258`
- `259`

Cela montre que :

- la continuité métrique et la continuité scénique ne sont pas vraiment distinguées
- la transition scène III / scène IV est absorbée de manière opportuniste
- le moteur ne dispose pas d’une stratégie explicite pour traiter un vers partagé traversant une frontière de scène

---

## Pourquoi c’est difficile à corriger dans la logique actuelle

Ce cas est difficile dans l’architecture présente parce que la génération semble reposer sur une boucle unique qui mélange :

- parsing de la saisie
- détection des locuteurs
- gestion des scènes
- gestion des vers partagés
- émission TEI
- numérotation

Dans cette logique, un changement de scène agit comme une rupture forte du flux.

Or ici, il faudrait au contraire pouvoir :

- reconnaître qu’une division scénique commence
- tout en maintenant une mémoire active du vers en cours
- puis décider explicitement si ce vers :
  - se poursuit,
  - se clôt,
  - ou doit être resegmenté

Cette capacité semble absente du moteur actuel.

---

## Conséquence éditoriale

Le cas ne peut pas être considéré comme correctement automatisé.

Même si la sortie TEI paraît localement acceptable, elle reste fragile et dépendante d’un comportement implicite.

Ce cas doit donc être traité comme :

- un **known issue**
- un **cas de non-régression futur**
- un **test prioritaire** si le moteur est repris en profondeur

---

## Ce que ce cas doit permettre à terme

Le moteur devrait être capable de distinguer clairement :

1. la continuité métrique
2. la continuité dialogique
3. la continuité structurelle (scènes, actes)

Et de décider explicitement, au passage d’une scène à l’autre :

- si le vers partagé doit être poursuivi
- comment le numéroter
- comment encoder la rupture dramatique sans casser l’unité métrique

---

## Rôle de ce fichier

Ce cas sert de :

- 🔴 known issue structurelle
- 🧪 fixture avancée
- 🧭 point d’appui pour une future refonte

Il ne doit pas être utilisé comme preuve que le moteur “gère” ce cas, mais comme preuve qu’il faut modéliser ce cas explicitement.

---

## Fichiers associés

### Scène III
- `input_scene3.txt`
- `expected_scene3.xml`

### Scène IV
- `input_scene4.txt`
- `expected_scene4.xml`

### Métadonnées
- `config_scene3.json`
- `config_scene4.json`

---

## Sources de référence

- saisie scène III
- TEI scène III
- saisie scène IV
- TEI scène IV

---

## Remarque méthodologique

Ce cas devra idéalement être rejoué plus tard sous forme de test automatisé :

- en traitant les deux scènes comme un ensemble lié
- ou en introduisant un test spécifique de transition inter-scénique