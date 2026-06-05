# SITE_BUILDER_TARGET.md — cible éditoriale du site statique

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Cible

Le site statique doit devenir un environnement de publication savante pour les éditions ETS.

Il ne doit pas être seulement un export technique du texte dramatique.

## 2. Principes

1. La TEI est la source.
2. La navigation est construite à partir d’un modèle explicite.
3. Une pièce est un dossier éditorial.
4. Le dramatis personae appartient à la couche dramatique.
5. Les notices et préfaces restent des objets distincts.
6. Le rendu doit être sobre mais élégant.
7. Chaque avancée doit être testable.

## 3. Structure cible d’une pièce

```text
Pièce
  Notice
  Préfaces / péritextes
  Dramatis personae
  Texte
    Acte I
      Scène I
      Scène II
    Acte II
      ...
```

## 4. Navigation attendue

La navigation doit pouvoir produire :

- un menu global ;
- un menu par pièce ;
- des ancres stables ;
- des liens vers notices et péritextes ;
- des liens vers actes et scènes ;
- un retour au début de la pièce.

## 5. Rendu dramatique

Le rendu dramatique doit afficher :

- actes ;
- scènes ;
- personnages présents ;
- locuteurs ;
- vers ;
- numéros ;
- variantes ;
- didascalies ;
- strophes si présentes.

## 6. Rendu des notices

Le rendu des notices doit couvrir progressivement :

- titres ;
- sections ;
- paragraphes ;
- italiques ;
- notes ;
- listes ;
- citations ;
- bibliographie simple.

## 7. Hors cible immédiate

Ne pas viser tout de suite :

- un CMS ;
- une base de données ;
- une recherche plein texte complexe ;
- une maquette définitive ;
- une équivalence complète avec Métopes ;
- une mise en page imprimée PURH.

## 8. Relation avec le livre

Le site et le livre doivent partager les données TEI.

Le site produit du HTML.
Le livre produira du LaTeX.

Les divergences doivent relever du rendu, non du contenu éditorial.
