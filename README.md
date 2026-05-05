# Ekdosis TEI Studio — documentation V2

- **Dernière mise à jour proposée : 25 avril 2026**  
- **Projet :** Ekdosis TEI Studio  
- **Dépôt :** <https://github.com/Gheeraert/Ekdosis-TEI-Studio>
- **Site public :** <https://purh.univ-rouen.fr/logiciels/ekdosis-tei-studio/>
- **Vidéo de présentation :** <https://webtv.univ-rouen.fr/videos/2026-04-25-tei-studio_84924/>

---

## 1. Présentation

### Principes

**Ekdosis TEI Studio** est une plate-forme d’encodage, de validation, de prévisualisation et de publication statique pour des éditions critiques de textes dramatiques, en particulier le théâtre classique français transmis par plusieurs témoins.

Le projet vise à transformer une transcription structurée en texte brut — volontairement proche d’un balisage léger inspiré de Markdown — en **XML-TEI exploitable**, validable, testable et publiable sous forme de site statique sur le web, en quelques clics.

L’objectif n’est plus seulement de produire un fichier TEI isolé. La V2 s’oriente vers une chaîne éditoriale complète :

```text
transcription structurée
        ↓
analyse syntaxique
        ↓
modèle éditorial interne
        ↓
collation des témoins
        ↓
XML-TEI
        ↓
prévisualisation HTML
        ↓
publication statique
```

Cette version constitue une réécriture structurée du prototype historique : elle privilégie la séparation des responsabilités, les tests, les services réutilisables et une architecture capable d’évoluer vers plusieurs interfaces.

### Site public de téléchargement et tutoriel

- Page publique du projet et liens de téléchargements: https://purh.univ-rouen.fr/logiciels/ekdosis-tei-studio/
- Vidéo de présentation (24 minutes): https://webtv.univ-rouen.fr/videos/2026-04-25-tei-studio/ 

### Nota bene
- Ekdosis-TEI-Studio a été co-écrit avec Codex AI

---

## 2. Publics visés

Ekdosis TEI Studio s’adresse principalement :

- aux éditeurs et éditrices critiques de textes théâtraux ;
- aux chercheurs travaillant sur des corpus dramatiques anciens ;
- aux équipes éditoriales qui souhaitent produire une TEI régulière sans écrire tout le XML à la main ;
- aux projets d’édition numérique souhaitant publier des textes et paratextes dans un site statique ;
- aux développeurs et développeuses chargés d’industrialiser une chaîne d’édition savante.

Le projet assume une double exigence :

1. **rigueur philologique** : conservation des variantes, des graphies, de la ponctuation, des lacunes et des réécritures ;
2. **sobriété technique** : pas de base XML complexe obligatoire, pas de CMS imposé, pas de dépendance à un serveur lourd pour publier un site.
3. **simplicité** : **l'outil est destiné à des non-informaticiens**. Il ne nécessite aucune connaissance en humanités numériques. Il n'exige pas, en particulier, de connaître la TEI ni aucun protocole d'encodage complexe. Tout le travail passe par des interfaces graphiques standards, pilotables par menus et souris.


---

## 3. État général du projet

La V2 est une **réécriture modulaire**. Elle ne cherche pas à rafistoler le prototype monolithique, mais à reconstruire une base plus robuste.

### Fonctionnalités actuellement centrales

- parsing d’un format de transcription structuré ;
- génération d’un XML-TEI dramatique ;
- gestion de plusieurs témoins ;
- gestion d’un témoin de référence utilisé comme lemme ;
- encodage des variantes sous forme d’apparat critique TEI ;
- validation de structure et validation XML ;
- prévisualisation HTML ;
- interface Tkinter ;
- éditeur Markdown éditorial pour les textes d’accompagnement (fonctionnel mais en cours) ;
- module de publication statique : **ETS Site Builder** ;
- batterie de tests fondée sur des fixtures réalistes.

### Fonctionnalités en cours ou à stabiliser

- enrichissement progressif du rendu HTML du site ;
- publication complète de dossiers de pièces : notice, préface, personnages, actes, scènes ;
- documentation des normes éditoriales ;
- amélioration des cas limites ;
- consolidation des modules d’annotation et de notes éditoriales ;
- export FTP ;
- automatisation progressive de certains flux éditoriaux.

### Fonctionnalités non prioritaires ou indisponibles

La sortie **LaTeX / ekdosis** appartient à l’histoire du projet et reste un horizon possible, mais elle n’est pas l’axe prioritaire de la V2. Elle doit être considérée comme **indisponible ou instable** tant qu’elle n’a pas été reconstruite comme module propre, testé et séparé du cœur TEI.

---

## 4. Principes d’architecture

La V2 repose sur un principe simple : **ne jamais enfermer la logique métier dans l’interface**.

L’interface graphique doit collecter les informations, appeler des services, puis afficher les résultats. Elle ne doit pas contenir elle-même la logique de parsing, de collation, de génération TEI ou de publication.

### Couches principales

```text
src/ets/
  domain/          modèles éditoriaux internes
  parser/          analyse de la transcription structurée
  collation/       alignement et comparaison des témoins
  tei/             génération XML-TEI
  validation/      contrôles structurels et XML
  application/     services appelables par l’interface
  ui/              interface Tkinter
  markdown_editor/ éditeur Markdown éditorial
  site_builder/    génération de site statique
  tools/           outils autonomes
tests/             batterie pytest
fixtures/          cas réels et sorties attendues
docs/              documentation du projet
legacy/            ancien code et références historiques
```

### Règles de conduite

- plus de script monolithique ;
- pas d’état global mutable ;
- pas de logique métier dans Tkinter ;
- pas de menus reconstruits à plusieurs endroits ;
- pas de publication dépendant de l’ordre accidentel des fichiers ;
- tests de non-régression pour chaque bug significatif ;
- préférence donnée aux fixtures réelles plutôt qu’aux exemples artificiels.

---

## 5. Format de transcription dramatique

Le format de saisie est volontairement léger. Il doit permettre à des éditeurs non spécialistes de la TEI de produire un texte structuré.

### Marqueurs principaux

| Marqueur | Fonction |
|---|---|
| `####...####` | titre d’acte |
| `###...###` | titre de scène |
| `##...##` | personnages présents dans la scène |
| `#...#` | locuteur |
| `**...**` | didascalie explicite |
| `***` | segmentation d’un vers partagé |
| `#####` | variante calculée sur la ligne entière |
| `$$TYPE$$ ... $$fin$$` | didascalie implicite ou segment interprété |
| `_..._` | italique |
| `~` | espace liée ou neutralisée pour l’alignement |

### Exemple minimal

```text
####ACTE I.####
####ACTE I.####
####ACTE PREMIER.####

###SCÈNE I.###
###SCÈNE PREMIÈRE.###
###SCÈNE I.###

##ANTIOCHUS, ARSACE.##
##ANTIOCHUS, ARSACE.##
##ANTIOCHUS, ARSACE.##

#ANTIOCHUS#
#ANTIOCHUS#
#ANTIOCHUS#

**Antiochus entre.**
**Antiochus entre.**
**Antiochus entre.**

Arrestons un moment. La pompe de ces lieux,
Arrestons un moment. La pompe de ces lieux,
Arrêtons un moment. La pompe de ces lieux,
```

Chaque bloc doit contenir autant de lignes qu’il y a de témoins attendus. La cohérence du nombre de témoins est une condition fondamentale pour que la collation soit possible.

---

## 6. Témoins, lemme et variantes

La transcription repose sur un alignement parallèle des témoins.

Le témoin de référence est utilisé comme **lemme**. Les autres témoins produisent, lorsque c’est nécessaire, des lectures variantes.

La structure TEI attendue suit le modèle général :

```xml
<app>
  <lem wit="#A">Arrestons</lem>
  <rdg wit="#C">Arrêtons</rdg>
</app>
```

Quand plusieurs témoins partagent la même forme, leurs identifiants peuvent être regroupés :

```xml
<app>
  <lem wit="#A #B">Arrestons</lem>
  <rdg wit="#C">Arrêtons</rdg>
</app>
```

### Variantes mot à mot

Le moteur peut comparer des lignes alignées mot à mot, à condition que le nombre de tokens reste compatible entre témoins.

L’espace liée par `~` permet d’éviter de découper certains groupes :

```text
Ie~feray~plus~encore
```

Ce groupe peut être traité comme une unité, afin d’éviter une divergence artificielle dans le nombre de mots.

### Variantes de ligne entière

Le préfixe `#####` force une variante globale de ligne :

```text
##### Accordez quelque tréve à ma douleur amere,
##### Accordez cette grace aux larmes d’une Mere.
```

Ce mode est destiné aux réécritures importantes, aux hémistiches remaniés, aux déplacements ou aux passages dont l’alignement mot à mot serait trompeur.

### Lacunes

Une lacune peut être signalée explicitement :

```text
##### (lacune)
```

ou, selon le contexte, dans les didascalies :

```text
**(lacune)**
```

Le traitement exact dépend du type de bloc concerné.

---

## 7. Didascalies explicites et implicites

### Didascalies explicites

Les didascalies explicites sont saisies entre doubles astérisques :

```text
**Antiochus entre.**
```

Elles sont encodées en TEI comme des éléments de type `stage`.

### Didascalies implicites

Les didascalies implicites ou interprétatives sont encodées à l’aide de délimiteurs typés :

```text
$$EVT$$
Va chez elle. Dy-luy qu’importun à regret,
Va chez elle. Dy-luy qu’importun à regret,
$$fin$$
```

Les types utilisés doivent être documentés dans les normes du projet. Les catégories déjà employées ou envisagées comprennent notamment :

| Code | Sens |
|---|---|
| `SPC` | parole |
| `ASP` | aspect |
| `TMP` | temps |
| `EVT` | événement |
| `SET` | décor |
| `PROX` | proxémie |
| `ATT` | attitude |
| `VOI` | voix |

Ces balises doivent rester au service d’une lecture dramaturgique contrôlée. Elles ne doivent pas devenir une annotation libre et incohérente.

---

## 8. Vers partagés

Les vers partagés entre deux locuteurs sont signalés avec `***`.

Exemple :

```text
Souvent ce cabinet***
Souvent ce cabinet***
Souvent ce cabinet***

#ARSACE#
#ARSACE#
#ARSACE#

***Superbe et solitaire,
***Superbe et solitaire,
***Superbe et solitaire,
```

Le moteur doit produire une structure TEI cohérente sans perdre l’information de partage du vers ni casser la hiérarchie des prises de parole.

---

## 9. Validation

La validation comporte plusieurs niveaux.

### Validation structurelle

Elle vérifie notamment :

- la cohérence du nombre de témoins par bloc ;
- la présence attendue des actes, scènes, locuteurs ;
- les changements de structure ;
- les erreurs de syntaxe évidentes ;
- les cas où un bloc ne peut pas être interprété.

### Validation XML

Le XML généré doit être bien formé. Lorsqu’un schéma est disponible, il doit pouvoir être validé avec Relax NG.

### Validation éditoriale

Certains contrôles ne sont pas seulement techniques. Ils relèvent de la cohérence éditoriale :

- un personnage mal identifié ;
- une scène déplacée ;
- un bloc de personnages absent ;
- une lacune non signalée ;
- une variante globale oubliée ;
- un alignement mot à mot forcé alors qu’il est trompeur.

La validation doit donc produire des erreurs bloquantes lorsque la génération est impossible, mais aussi des avertissements non bloquants quand l’édition peut continuer.

---

## 10. Interface Tkinter

L’interface Tkinter est une couche de travail locale. Elle doit rester mince et appeler les services du cœur.

Elle peut proposer :

- ouverture et sauvegarde de fichiers ;
- saisie ou édition d’une transcription ;
- génération TEI ;
- validation ;
- prévisualisation HTML ;
- export des résultats ;
- accès aux outils spécialisés ;
- menus adaptés au mode courant ;
- dialogue de publication du site ;
- diagnostics lisibles.

### Modes de travail

L’interface distingue progressivement deux familles d’usages :

1. **mode transcription dramatique** : production de TEI à partir du format structuré ;
2. **mode Markdown éditorial** : rédaction de notices, introductions, pages d’accueil ou préfaces.

Les menus non pertinents doivent pouvoir être désactivés selon le mode actif, afin de limiter les erreurs de manipulation.

---

## 11. Éditeur Markdown éditorial

Le module `ets.markdown_editor` sert à produire des contenus éditoriaux d’accompagnement :

- texte d’accueil ;
- introduction générale ;
- notice de pièce ;
- préface ;
- page statique.

Il n’a pas vocation à devenir un traitement de texte complet. Il fournit un dialecte Markdown contrôlé, convertible en aperçu et en TEI.

### Éléments pris en charge

- titres ;
- paragraphes ;
- citations ;
- listes ;
- italiques ;
- gras ;
- liens ;
- notes de bas de page ;
- exposants ;
- indices ;
- petites capitales ;
- blocs bibliographiques simples.

### Extensions maison

Exemples de balises légères :

```text
[caps]TEXTE EN CAPITALES[/caps]
[sc]petites capitales[/sc]
[sup]e[/sup]
[sub]n[/sub]
[u]texte souligné[/u]
```

### Bloc bibliographique

```text
:::bibl
- Jean Racine, *Bérénice*, Paris, 1671.
- Georges Forestier, *Jean Racine*, Paris, Gallimard, 2006.
:::
```

La bibliographie peut rester simple dans une première version. Le modèle doit toutefois rester ouvert à une évolution future vers BibTeX, Zotero ou CSL.

---

## 12. Annotations et notes éditoriales

Le projet peut intégrer un module d’annotations éditoriales permettant d’ajouter des notes à un texte TEI produit par ETS.

L’objectif est de permettre :

- l’ajout de notes explicatives ;
- leur rattachement à un vers ou à un point du texte ;
- leur conversion en TEI ;
- leur rendu HTML avec appels de notes ;
- leur réutilisation lors de l’export ou de la publication.

Le principe architectural reste le même : les annotations doivent enrichir le modèle ou le XML via un service dédié, non être bricolées directement dans le rendu HTML ou dans l’interface.

---

## 13. ETS Site Builder

**ETS Site Builder** est le module de publication statique du projet.

Il doit produire un site HTML complet à partir de sources XML et de fichiers de configuration, sans nécessiter de CMS ni de base de données.

### Sources éditoriales

Le site peut combiner plusieurs familles de documents :

- TEI dramatique produit par ETS ;
- notices produites avec Métopes ou un sous-ensemble TEI compatible ;
- préfaces d’auteur ;
- introduction générale ;
- texte d’accueil ;
- pages institutionnelles ;
- fichiers d’actifs : logos, images, CSS, bannières.

### Modèle éditorial d’une pièce

Une pièce ne doit pas être traitée comme un simple texte découpé en actes et scènes. Elle devient un **dossier éditorial**.

Ordre canonique attendu :

1. notice de la pièce, si elle existe ;
2. préface(s) de l’auteur, si elles existent ;
3. personnages, si la section existe ;
4. acte I ;
5. scènes de l’acte I ;
6. acte II ;
7. scènes de l’acte II ;
8. etc.

Cet ordre est éditorial, non alphabétique. Il ne doit pas dépendre de l’ordre des fichiers sur le disque.

### Navigation

La navigation doit être construite à partir d’une seule structure explicite.

Le menu ne doit pas être recréé indépendamment par plusieurs modules. Il doit venir d’un modèle intermédiaire unique, construit en amont, puis consommé par le rendu.

Cette règle évite les divergences comme :

- ordre du menu différent de l’ordre de chargement ;
- duplication de liens internes ;
- sections visibles dans un panneau mais absentes dans un autre ;
- ancres mal placées ;
- menu qui se décale ou perd son contexte pendant le défilement.

### Configuration

La configuration de publication doit pouvoir contenir notamment :

```json
{
  "site_title": "Édition critique de Racine",
  "site_subtitle": "Projet d’édition numérique",
  "dramatic_xml_dir": "chemin/vers/xml_dramatiques",
  "notice_xml_dir": "chemin/vers/notices",
  "output_dir": "chemin/vers/site_genere",
  "show_xml_download": true,
  "publish_notices": true,
  "publish_prefaces": true,
  "play_order": ["thebaide", "alexandre", "andromaque"],
  "play_notice_map": {
    "thebaide": "notice-thebaide"
  },
  "play_preface_map": {
    "berenice": ["preface-berenice"]
  }
}
```

Les références manquantes doivent produire des avertissements explicites, non des échecs obscurs.

---

## 14. Rendu HTML et qualité éditoriale

La qualité du rendu n’est pas un simple supplément esthétique. Pour une édition littéraire, elle fait partie de l’exigence scientifique.

Le site généré doit viser :

- lisibilité ;
- hiérarchie claire ;
- sobriété ;
- élégance ;
- confort de lecture ;
- menus stables ;
- typographie crédible ;
- cohérence entre thème clair et thème sombre ;
- bonne intégration des variantes et notes.

Le rendu dramatique doit réutiliser le moteur ETS XML → HTML réel lorsque celui-ci existe. Il ne faut pas remplacer un rendu savant par une approximation locale plus simple mais moins fidèle.

---

## 15. Fixtures et tests

Les fixtures sont la principale source de vérité du projet.

Elles doivent contenir :

- des entrées réelles ;
- des cas difficiles ;
- les sorties attendues ;
- les régressions connues ;
- des exemples représentatifs du travail éditorial.

### Règles de test

- tout bug corrigé devrait donner lieu à un test ;
- les cas limites doivent être conservés ;
- les tests doivent rester lisibles ;
- les tests de publication doivent vérifier la structure HTML produite ;
- les tests ne doivent pas seulement vérifier que “ça ne plante pas”.

Commandes usuelles :

```powershell
python -m pytest
```

Pour cibler un fichier :

```powershell
python -m pytest tests/test_nom_du_fichier.py
```

Pour un test précis :

```powershell
python -m pytest tests/test_nom_du_fichier.py::test_nom_du_test
```

---

## 16. Développement assisté et branches

Le projet peut être développé avec l’aide de Codex ou d’autres assistants, mais les passes doivent rester contrôlées.

Bonnes pratiques :

- travailler sur une branche dédiée ;
- demander des patches ciblés ;
- éviter les refontes silencieuses ;
- relire les fichiers modifiés ;
- vérifier que la logique métier ne migre pas dans l’interface ;
- exécuter les tests ciblés ;
- committer fréquemment ;
- préserver une branche stable.

### Mise à jour de `main` depuis `dev`

Lorsque `dev` contient l’état validé et que `main` doit être remplacée par cet état :

```powershell
git checkout main
git fetch origin
git reset --hard origin/dev
git push --force-with-lease origin main
```

`--force-with-lease` est préférable à `--force`, car il refuse de pousser si le dépôt distant a changé entre-temps.

---

## 17. Ce qui ne doit pas revenir

La V2 a précisément pour but d’éviter les problèmes du prototype historique.

À éviter :

- ajouter une correction rapide directement dans Tkinter ;
- dupliquer une logique dans deux fichiers ;
- trier des pièces ou des menus par hasard ;
- créer des conventions implicites non documentées ;
- mélanger notices, préfaces et texte dramatique dans un seul objet flou ;
- modifier un rendu HTML en contournant le modèle TEI ;
- accepter une sortie visuellement dégradée au motif qu’elle est techniquement valide.

---

## 18. Feuille de route synthétique

### Court terme

- stabiliser la génération TEI ;
- consolider les tests ;
- documenter les normes de transcription ;
- stabiliser le dialogue de publication ;
- fiabiliser l’ordre des pièces et des menus ;
- améliorer les avertissements non bloquants.

### Moyen terme

- consolider ETS Site Builder ;
- publier les notices, préfaces et textes dramatiques dans un même site ;
- améliorer le rendu HTML ;
- intégrer proprement notes et annotations ;
- stabiliser les configurations JSON ;
- Transformer le standalone en webapp par exemple via Flask

### Long terme

- enrichir la TEI dramaturgique ;
- mieux typer les didascalies ;
- produire plusieurs visualisations à partir d’un même XML ;
- permettre éventuellement un affichage par témoin ;
- envisager, si nécessaire, une reconstruction propre de la sortie LaTeX / ekdosis ;
- maintenir une chaîne d’édition sobre, statique et pérenne.
- Ambition ultérieure: transformer TEI Studio en une chaîne de production de données éditoriales fondée sur un modèle cohérent et complet du texte théâtral

---

## 19. Glossaire rapide

| Terme | Sens |
|---|---|
| témoin | version textuelle collationnée |
| lemme | lecture de référence dans l’apparat critique |
| lecture variante | forme différente portée par un autre témoin |
| apparat critique | ensemble des variantes encodées en TEI |
| fixture | fichier de test représentant un cas réel ou attendu |
| notice | paratexte critique moderne sur une pièce |
| préface | paratexte auctorial ou historique rattaché à l’œuvre |
| dramatis personae | liste des personnages |
| site statique | site HTML généré sans base de données ni CMS |
| service layer | couche applicative appelée par l’interface |

---

## 20. Principe directeur

Ekdosis TEI Studio doit rester un outil d’édition savante, non un simple convertisseur.

Sa vocation est de produire des **données éditoriales structurées** : un texte dramatique, ses témoins, ses variantes, ses paratextes, ses notes, sa navigation, ses métadonnées et ses formes de publication.

La TEI n’est donc pas seulement un format de sortie. Elle devient le point d’articulation entre la philologie, l’édition numérique, la publication statique et la transmission durable d’un corpus.

---

## Installation from source

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Important external tools and resources

- Pandoc is required for the editorial notice import workflow. It must be installed on the system PATH, or provided alongside the executable in bundled distributions.
- Non-Python runtime resources (for example XSLT stylesheets, Relax NG schemas, templates, CSS/assets, logos) are not pip dependencies. They must be included in the application distribution package.
