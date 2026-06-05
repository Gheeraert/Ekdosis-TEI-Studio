# Markdown Editor Module

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Objet

Le module Markdown Editor sert aux textes de prose éditoriale ou aux fragments structurés hors transcription dramatique stricte.

Il ne remplace pas le parseur ETS du texte dramatique.

## 2. Périmètre

Il peut couvrir :

- édition de prose ;
- prévisualisation ;
- diagnostics ;
- export TEI fragmentaire ;
- export TEI complet selon le contexte.

## 3. Relation avec les notices

Pour les notices plus structurées, la chaîne Word/Pandoc et le module `editorial_notice_import` peuvent être préférables.

Le Markdown Editor doit rester un outil léger, non un second système complet d’édition.

## 4. Règle d’architecture

Le module doit produire de la TEI ou un modèle structuré.
Les rendus HTML et LaTeX doivent être dérivés de cette structure.

## 5. Limites

Ne pas lui faire traiter :

- les témoins dramatiques parallèles ;
- les variantes ;
- les vers partagés ;
- la syntaxe ETS complète ;
- l’apparat critique Ekdosis.
