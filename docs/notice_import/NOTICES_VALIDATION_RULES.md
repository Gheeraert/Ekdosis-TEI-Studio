# NOTICES_VALIDATION_RULES.md

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Objet

La validation des notices garantit que les documents importés peuvent produire une TEI régulière et publiable.

## 2. Types de diagnostics

Recommandation :

| Niveau | Sens |
|---|---|
| erreur bloquante | empêche l’import |
| avertissement | import possible mais résultat à vérifier |
| information | remarque non problématique |

## 3. Erreurs bloquantes possibles

- document illisible ;
- structure vide ;
- titre absent si requis ;
- style inconnu dans une zone structurante ;
- note mal formée ;
- niveau de titre incohérent ;
- bibliographie impossible à parser si elle est obligatoire.

## 4. Avertissements possibles

- style autorisé mais rare ;
- saut de niveau de titre ;
- élément ignoré ;
- image ou tableau non pris en charge ;
- bibliographie simplifiée.

## 5. Règle de clarté

Un diagnostic doit indiquer :

- le problème ;
- l’emplacement si possible ;
- le style concerné ;
- la correction attendue.

## 6. Tests

Chaque règle bloquante doit avoir un test.
Chaque style accepté doit avoir au moins une fixture positive.
