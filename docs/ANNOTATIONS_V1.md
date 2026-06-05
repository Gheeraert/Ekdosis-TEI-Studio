# Annotations éditoriales

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Objet

Le module d’annotations permet d’attacher des notes éditoriales à des lieux du texte sans polluer la transcription ETS.

## 2. Principe

Les annotations ne doivent pas être écrites directement dans `input.txt`.

La transcription reste le texte à collationner.
Les notes sont des données éditoriales associées.

## 3. Cible

Une annotation doit pouvoir être :

- créée depuis l’interface ;
- stockée localement ;
- associée à un passage stable ;
- injectée dans la TEI ;
- rendue en HTML ;
- plus tard exportée en LaTeX standard ou en notes selon la maquette.

## 4. Contenu

Le contenu d’une annotation peut utiliser une syntaxe légère documentée dans `ANNOTATION_MARKDOWN_V1.md`.

La TEI reste le format structuré final.

## 5. Règle de prudence

Ne pas confondre :

- notes éditoriales modernes ;
- variantes de l’apparat ;
- didascalies implicites ;
- commentaires de développement.

Chaque famille doit garder sa structure propre.
