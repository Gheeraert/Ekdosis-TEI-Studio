# Éditer Racine

## Principes généraux d’édition

Nous proposons **la première édition critique et semi-diplomatique complète de Racine**.

Elle tiendra compte :
- de toutes les variantes,
- de toutes les graphies (orthographe, ponctuation).

👉 Site de pré-production : http://www.edition-racine.org/

## Publication

Les douze pièces seront proposées :

- en version papier (PURH)
- sur une plateforme en libre accès (Université de Rouen)

Les textes seront accompagnés de :
- variantes complètes
- notices
- introductions
- commentaires
- notes
- bibliographies
- textes annexes

---

## Choix des textes

### Principe

L’édition en ligne proposera :
- toutes les variantes des éditions contrôlées par l’auteur :
  - éditions originales
  - éditions individuelles
  - éditions collectives
  - édition définitive (1697)

### Texte de référence

➡️ Édition originale

### Éditions retenues

- 1675-1676
- 1687
- 1697

### Éditions exclues

- contrefaçons
- erreurs d’impression non significatives

---

## Méthode d’encodage

Pipeline :

pseudo-markdown → TEI → LaTeX (Ekdosis)

---

## Règles essentielles

- respecter strictement le texte
- conserver les variantes
- même nombre de mots par ligne
- utiliser ~ pour bloquer les espaces

Exemple :

l’as~tu laissé  
l’as-tu laissé  

---

## Didascalies implicites

Encodage :

$$EVT$$  
texte  
$$fin$$  

---

## Version régularisée

- dissimilation u/v, i/j
- résolution des abréviations
- correction minimale

---

## Ressources

- https://tei-c.org/activities/sig/
- https://dramacode.github.io/moliere/
- https://cahier.hypotheses.org/guides/guide-correspondance

---

## Exemple

####ACTE I.####
###SCENE PREMIERE.###

##IOCASTE## ##OLYMPE##

#IOCASTE#

ILs sont sortis, Olympe~? Ah mortelles douleurs~!
