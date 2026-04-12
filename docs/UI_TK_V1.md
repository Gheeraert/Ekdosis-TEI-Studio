# UI_TK_V1.md

## Objet

Cette phase du projet introduit une première interface graphique locale en **Tkinter** pour Ekdosis TEI Studio.

L’objectif n’est pas de recréer l’ancien monolithe `legacy`, mais de proposer une interface de travail simple, familière et robuste, branchée sur le **cœur refactoré** du projet.

Cette interface doit permettre une prise en main rapide par des **étudiants de master de lettres**, avec une ergonomie classique de type application de bureau.

## Principes directeurs

- Conserver un comportement **simple, explicite, rassurant**.
- Privilégier une interface **desktop locale** pour cette étape.
- Préserver un esprit **Windows-like** : menus, boutons, raccourcis, clic droit, boîtes de dialogue.
- Ne pas réintroduire de logique métier lourde dans l’interface.
- Faire de l’interface Tkinter une **coque légère** au-dessus des services applicatifs.
- Préparer dès maintenant une future migration vers une **webapp Flask**, en gardant le moteur indépendant de l’UI.

## Public visé

- Étudiantes et étudiants de master
- Utilisatrices et utilisateurs non techniciens
- Équipe éditoriale ayant besoin d’une interface lisible, stable et peu déroutante

## Périmètre de cette V1 Tkinter

La V1 doit proposer :

1. une **fenêtre principale** redimensionnable ;
2. une **zone de saisie** en partie haute ;
3. une **zone d’affichage des sorties** en partie basse ;
4. une **barre de contrôle intermédiaire** ;
5. des **menus classiques** ;
6. un branchement progressif vers les services existants.

## Hors périmètre pour cette phase

Ne pas implémenter dans cette phase :

- la future interface Flask ;
- une refonte graphique ambitieuse ;
- l’export LaTeX/Ekdosis dans l’interface ;
- des widgets complexes non indispensables ;
- une logique métier dupliquée dans les fichiers UI ;
- un système de persistance sophistiqué côté interface.

## Structure générale de la fenêtre

La fenêtre principale est organisée verticalement en trois zones :

### 1. Zone haute : saisie

Elle contient :

- un éditeur de texte principal ;
- une gouttière de numérotation des lignes ;
- une barre de défilement ;
- les opérations standard d’édition.

Fonctionnalités attendues :

- couper ;
- copier ;
- coller ;
- sélectionner tout ;
- annuler / rétablir ;
- clic droit contextuel ;
- recherche ;
- remplacement.

Le comportement doit rester fluide pour des fichiers de travail raisonnables.

### 2. Zone intermédiaire : contrôles

Elle contient :

- le **choix du témoin de référence** ;
- éventuellement le **numéro du premier vers** ;
- un bouton **Valider** ;
- un bouton **Générer le code** ;
- les boutons d’**export**.

Le bouton **Générer le code** doit déclencher automatiquement la validation avant génération.

### 3. Zone basse : sorties

Elle affiche les résultats **sans en-têtes complets** dans une interface en onglets.

Onglets minimum :

- `TEI`
- `HTML`

L’objectif ici est la **lecture rapide** des résultats, non une édition avancée.

## Menus attendus

### Fichier

- Nouveau
- Ouvrir
- Enregistrer
- Enregistrer sous
- Charger une configuration
- Créer une configuration
- Quitter

### Édition

- Annuler
- Rétablir
- Couper
- Copier
- Coller
- Sélectionner tout
- Rechercher
- Remplacer

### Outils

- Valider la saisie
- Générer le code XML-TEI
- Export TEI
- Export HTML

### Affichage

- Afficher / masquer certains panneaux si utile
- Recharger la prévisualisation si utile

### Aide

- À propos
- Rappel synthétique de la syntaxe de saisie

## Validation

La validation est une fonctionnalité centrale.

Règles :

- elle doit pouvoir être lancée **séparément** depuis le menu ou un bouton ;
- elle doit être lancée **automatiquement** avant la génération ;
- les messages doivent être compréhensibles ;
- les diagnostics doivent être reliés autant que possible à des numéros de ligne.

L’interface ne doit pas réimplémenter la validation : elle doit appeler les services du cœur.

## Architecture technique attendue

L’interface Tkinter ne doit contenir que :

- la gestion des widgets ;
- la récupération des entrées utilisateur ;
- l’appel aux services ;
- l’affichage des résultats ;
- la gestion des messages, états et boîtes de dialogue.

La logique métier doit rester dans le cœur de l’application.

## Règle d’architecture impérative

**Aucun code métier complexe dans `ui/tk/`.**

En particulier, les modules Tkinter ne doivent pas :

- parser directement les blocs de saisie ;
- exécuter la collation eux-mêmes ;
- produire eux-mêmes le XML-TEI ;
- générer eux-mêmes le HTML.

Ils doivent appeler des fonctions de service dédiées.

## Services attendus côté application

L’UI doit pouvoir appeler une API Python simple, stable et testable, par exemple :

- `validate_input(text, config)`
- `generate_tei(text, config)`
- `generate_html_preview(text, config)`
- `export_tei(text, config, output_path)`
- `export_html(text, config, output_path)`

Les noms exacts peuvent évoluer, mais le principe doit être conservé :
**UI mince, services centraux.**

## Arborescence cible pour l’interface

Organisation visée :

```text
src/ets/
  ui/
    tk/
      main_window.py
      editor.py
      output_notebook.py
      control_bar.py
      menus.py
      dialogs/
        search_dialog.py
        config_dialog.py
        validation_dialog.py

Cette arborescence peut évoluer légèrement, mais doit rester lisible.

## Stratégie de développement

Le développement doit se faire par étapes courtes.

### Étape 1

Créer une coquille d’interface navigable avec :

- fenêtre principale ;
- menu ;
- éditeur en haut ;
- onglets TEI / HTML en bas ;
- barre de contrôle intermédiaire.

### Étape 2

Brancher les actions simples :

- ouvrir / enregistrer ;
- copier / coller ;
- recherche simple ;
- changement de témoin de référence.

### Étape 3

Brancher la validation réelle.

### Étape 4

Brancher la génération TEI et la prévisualisation HTML.

### Étape 5

Brancher les exports.

## Orientation UX

L’interface doit être :

- sobre ;
- lisible ;
- stable ;
- peu intimidante ;
- familière pour un usage universitaire non technique.

Éviter :

- les effets visuels inutiles ;
- les dispositions surchargées ;
- les icônes obscures sans libellé ;
- les fenêtres multiples non nécessaires.

## Rapport au legacy

Le dossier `legacy` peut servir de source d’inspiration ergonomique et fonctionnelle, mais ne doit pas être recopié en bloc.

On peut y reprendre :

- les grands principes d’organisation de la fenêtre ;
- certains raccourcis ;
- certaines formulations ;
- la logique d’usage générale.

On ne doit pas y reprendre :

- le couplage fort entre interface et logique métier ;
- les variables globales envahissantes ;
- les fonctions monolithiques longues et peu testables.

## Préparation de Flask

Même si cette phase porte sur Tkinter, tout choix d’architecture doit faciliter une future interface web Flask.

En conséquence :

- le moteur doit rester indépendant de l’interface ;
- les services doivent être réutilisables sans Tkinter ;
- les formats d’entrée et de sortie doivent rester clairs ;
- l’UI ne doit pas devenir le centre du programme.

## Consignes pour les contributions Codex

Toute contribution touchant à l’UI Tkinter doit respecter les règles suivantes :

- ne pas déplacer de logique métier dans les modules UI ;
- limiter la taille et la responsabilité de chaque fichier ;
- privilégier des composants lisibles ;
- conserver une interface simple ;
- ne pas réintroduire un monolithe comparable au `legacy` ;
- documenter brièvement les nouveaux composants ;
- produire une interface immédiatement testable localement.

## Critère de réussite de cette phase

Cette phase sera considérée comme réussie lorsque l’on disposera d’une interface Tkinter permettant :

- de saisir ou coller un texte ;
- de charger ou créer une configuration ;
- de choisir le témoin de référence ;
- de lancer la validation ;
- de générer et afficher le TEI ;
- de générer et afficher un HTML de prévisualisation ;
- d’exporter les résultats ;
- le tout dans une interface claire, stable et compréhensible.