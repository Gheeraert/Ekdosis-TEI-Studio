# Fixtures Métopes minimales

Ce dossier contient un petit corpus synthétique, pensé pour des tests rapides et déterministes.

## Objectifs

- tester la détection d'un volume maître
- tester la résolution d'une structure volume / chapitres
- tester l'extraction des titres et sous-titres
- tester plusieurs niveaux de divisions internes
- tester le rendu minimal d'italiques, de notes et d'une bibliographie

## Cas couverts

- `Metopes_Test_Book.xml` : volume maître avec `xi:include`
- `Ch01_Introduction_test.xml` : texte de type `introduction`
- `Ch02_Sections_et_titres.xml` : texte de type `chapter` avec `section1`, `section2`, `section3`
- `Ch99_Bibliographie_test.xml` : texte de type `bibliography`
