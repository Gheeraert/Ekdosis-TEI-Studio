# ETS Site Builder

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Objet

ETS Site Builder est le module de publication statique du projet.

Il assemble des sources TEI éditoriales et produit un site HTML consultable sans serveur lourd.

## 2. Principe

Le site builder ne remplace pas le moteur TEI.
Il consomme des sources TEI déjà produites ou importées.

Sources possibles :

- TEI dramatique produite par ETS ;
- notices TEI issues de Word/Pandoc ;
- préfaces ou péritextes ;
- pages éditoriales autonomes ;
- ressources statiques.

## 3. Dossier éditorial d’une pièce

Une pièce publiée n’est pas seulement une suite d’actes et de scènes.
Elle forme un dossier éditorial.

Ordre canonique recommandé :

1. notice savante ;
2. préface(s) ou péritexte(s) ;
3. dramatis personae ;
4. texte dramatique ;
5. actes et scènes.

## 4. Navigation

La navigation doit être déterministe et fondée sur une structure intermédiaire explicite.

Elle ne doit pas dépendre de l’ordre de découverte des fichiers.

Elle doit pouvoir distinguer :

- éléments de front matter ;
- texte dramatique ;
- actes ;
- scènes ;
- pages globales.

## 5. Notices

Une notice est un objet éditorial distinct du texte dramatique.

Elle ne doit pas être confondue avec :

- le dramatis personae ;
- les préfaces d’auteur ;
- le texte de la pièce ;
- les annotations d’apparat.

## 6. Qualité visuelle

Le site doit être lisible et agréable pour un public de chercheurs en littérature.

La sobriété technique ne signifie pas pauvreté visuelle.

Attendus :

- hiérarchie claire ;
- typographie correcte ;
- navigation stable ;
- pages légères ;
- absence de dépendance à un CMS ;
- possibilité d’hébergement institutionnel simple.

## 7. Relation avec LaTeX

Le site builder est une sortie numérique.

Il ne doit pas porter la mise en page PURH imprimée.

Toutefois, il partage la même source TEI que les futurs exports LaTeX.
C’est cette source commune qui garantit la cohérence entre site et livre.
