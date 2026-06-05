# Interface Tkinter

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Objet

L’interface Tkinter est la principale interface locale d’Ekdosis-TEI Studio.

Elle doit rester une coque claire au-dessus des services applicatifs, sans absorber la logique métier.

## 2. Public

L’interface s’adresse à des utilisateurs non techniciens : étudiants, éditeurs, chercheurs, transcripteurs.

Elle doit rester :

- lisible ;
- rassurante ;
- explicite ;
- robuste ;
- proche des usages desktop classiques.

## 3. Fonctions attendues

L’interface peut proposer :

- ouverture et sauvegarde de transcriptions ;
- autosauvegarde ;
- gestion de configuration ;
- validation d’entrée ;
- génération TEI ;
- prévisualisation HTML ;
- génération de site ;
- import de notices ;
- fusion ou outils éditoriaux ;
- annotations ;
- références ;
- futurs exports LaTeX.

## 4. Règle d’architecture

La logique profonde doit rester dans `src/ets/application`, `src/ets/tei`, `src/ets/html`, `src/ets/site_builder`, etc.

L’interface appelle des services.
Elle ne doit pas :

- parser elle-même la syntaxe ETS ;
- corriger directement la TEI ;
- fabriquer un export LaTeX de son côté ;
- dupliquer le validateur.

## 5. Diagnostics

Les erreurs doivent être compréhensibles par un littéraire.

Un message doit dire :

- où est le problème ;
- quel marqueur est malformé ;
- ce qu’il faut corriger ;
- si l’erreur bloque la génération.

## 6. Boutons et menus

Si une action existe dans un menu et devient fréquente, elle peut être doublée par un bouton.

Exemple : un bouton “Générer site” peut appeler strictement le même service que le menu correspondant.

Ne pas créer deux chemins logiques différents pour la même action.

## 7. Tests UI

Les tests Tk doivent nettoyer les callbacks `after` et détruire les fenêtres après usage.

Les tests ne doivent pas laisser de boîte modale ouverte.

Pour les garde-fous UI, préférer des fonctions testables et des services séparés.
