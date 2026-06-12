# Ekdosis-TEI Studio

Dernière mise à jour documentaire : 12 juin 2026.

## 1. Présentation

Ekdosis-TEI Studio est un outil d’encodage, de validation, de visualisation et de publication pour des éditions critiques de théâtre classique français.

Il permet à une équipe éditoriale de travailler dans une transcription structurée légère, proche d’un pseudo-markdown, puis de produire une TEI régulière, réutilisable et exploitable pour plusieurs sorties.

Le projet vise désormais trois usages complémentaires :

- **un établi de saisie et de validation** pour produire la TEI d’une pièce ou d’un extrait ;
- **un générateur de site statique** pour publier un corpus d’œuvres et de paratextes ;
- **une chaîne imprimée savante**, notamment en LaTeX-Ekdosis pour le texte dramatique critique.

ETS doit rester utilisable par des littéraires, éditeurs et éditrices critiques, sans leur imposer l’écriture directe de XML, de LaTeX ou de code.

## 2. Principe central

La TEI générée par ETS est la représentation éditoriale canonique.

La chaîne cible est :

```text
transcription ETS
  → validation
  → parsing / modèle interne / collation
  → TEI canonique
  → prévisualisation HTML
  → site statique
  → LaTeX-Ekdosis pour le texte dramatique critique
  → LaTeX standard pour les péritextes
  → mise en page PURH
```

La sortie LaTeX ne doit donc pas être considérée comme une seconde génération parallèle depuis la transcription brute.
Elle doit être dérivée de la TEI.

Le développement récent va dans ce sens : les interfaces, qu’elles soient Tkinter ou Flask, doivent appeler des services applicatifs existants plutôt que dupliquer la logique métier.

## 3. Interfaces disponibles

### Interface Tkinter

L’interface historique reste l’outil complet de travail local.
Elle permet notamment :

- de charger une configuration ;
- de saisir ou charger une transcription ;
- de valider le pseudo-markdown ETS ;
- de générer TEI, HTML et LaTeX/Ekdosis ;
- d’utiliser les outils associés aux notices, au site statique et aux sorties éditoriales.

### Interface Flask

Une interface web légère a été ajoutée dans `src/ets/web/`.

Elle est pensée comme une couche d’accès au cœur ETS, sans base de données, sans privilèges utilisateurs et sans stockage serveur permanent.

Elle comporte actuellement quatre entrées principales :

```text
/                 établi de saisie
/publish/builder  constructeur de site
/publish/static   publication ZIP
/about            présentation rapide d’ETS
```

L’interface Flask doit rester une interface, non un second moteur.
Elle ne doit pas importer Tkinter ni porter de logique métier profonde.

## 4. Établi de saisie web

L’établi de saisie web permet de travailler sur une pièce, une scène ou un extrait.

Il accepte :

- une configuration ETS en JSON ;
- une transcription ETS ;
- une castlist / dramatis personae optionnelle ;
- ou un paquet ZIP ETS contenant ces éléments.

Il produit :

- une validation ;
- une TEI XML ;
- un aperçu HTML ;
- une sortie LaTeX/Ekdosis ;
- un paquet ZIP ETS réexportable.

Le paquet ZIP ETS de l’établi est destiné au travail sur une transcription dramatique.
Il ne doit pas être confondu avec le paquet ZIP de publication statique.

## 5. Publication statique web

La publication statique web correspond à un autre étage de la chaîne.

Elle sert à passer d’un ensemble de fichiers déjà préparés à un site statique complet.

Deux modes sont distingués.

### Constructeur de site

Le constructeur de site est le mode humain.

Il aide à construire une configuration de publication à partir de fichiers source :

- XML/TEI des pièces ;
- notices en DOCX stylé léger ou XML/TEI ;
- préfaces en DOCX stylé léger ou XML/TEI ;
- dramatis personae en XML/TEI ;
- page d’accueil et introduction générale en DOCX stylé léger ou XML/TEI ;
- logos ou assets éventuels.

L’objectif du constructeur est de produire une configuration de publication cohérente, sans demander à l’utilisateur d’écrire le JSON à la main.

### Publication ZIP

La publication ZIP est le mode expert.

Elle attend un ZIP source déjà configuré, contenant exactement un fichier JSON de publication et les fichiers d’entrée auxquels ce JSON renvoie.

Le principe est :

```text
publication_source.zip
  → décompression temporaire
  → lecture de publication_config.json
  → conversion éventuelle DOCX → TEI
  → génération du site statique
  → site_statique.zip
```

Aucun fichier n’est stocké durablement sur le serveur.

Le JSON de publication doit utiliser des chemins relatifs internes au ZIP.
Les chemins absolus et les chemins sortant du ZIP, par exemple `../`, doivent être refusés.

Exemple de structure :

```text
publication_source.zip
├── publication_config.json
├── dramatic/
│   ├── britannicus.xml
│   └── phedre.xml
├── notices/
│   ├── britannicus.docx
│   └── phedre.xml
├── prefaces/
│   └── britannicus.docx
├── dramatis/
│   └── britannicus.xml
└── assets/
    └── logos/
        └── logo.png
```

Dans cette première version web :

- la génération PDF n’est pas activée ;
- la publication FTP n’est pas activée ;
- le mode back / privilège n’est pas présent ;
- `output_dir` est ignoré en mode web et remplacé par un dossier temporaire contrôlé.

## 6. Import DOCX vers TEI

ETS prend en charge des DOCX stylés légèrement pour les paratextes.

La chaîne est :

```text
DOCX stylé léger
  → Pandoc
  → AST Pandoc JSON
  → parsing interne
  → validation des styles
  → construction TEI
  → TEI temporaire
  → site builder
```

Cette chaîne concerne les sources éditoriales suivantes :

- page d’accueil ;
- introduction générale ;
- notices de pièces ;
- préfaces de pièces.

Les pièces dramatiques proprement dites restent des fichiers XML/TEI.
Les dramatis personae restent également XML/TEI dans la chaîne de publication statique.

Pandoc est un prérequis de la chaîne DOCX.
Son absence n’est pas un mode normal d’utilisation.

## 7. Fonctionnalités actuelles importantes

Le projet contient notamment :

- un validateur du pseudo-markdown ETS ;
- un parseur de transcription dramatique ;
- une logique de collation des témoins ;
- une génération XML-TEI ;
- une prévisualisation HTML ;
- une génération LaTeX/Ekdosis ;
- une interface Tkinter ;
- une interface Flask légère ;
- un import/export de paquets ZIP ETS ;
- un constructeur de site web ;
- une publication statique ZIP vers ZIP ;
- des modules d’annotations ;
- un module de références ;
- un module d’import de notices Word/Pandoc vers TEI ;
- un site builder statique ;
- des tests et fixtures pour les cas stables.

## 8. Syntaxe ETS de base

Le protocole de transcription utilise notamment :

```text
####ACTE I####              titre d’acte
###SCENE I###               titre de scène
##PHEDRE## ##OENONE##       personnages présents
#PHEDRE#                    locuteur
**Elle s’assied.**           didascalie explicite
***                         segmentation de vers partagé
#####                       variante de ligne entière
##### (lacune)              lacune dans un témoin
_texte_                     italique
~                           espace insécable ou alinéa manuel
$$EVT$$ ... $$fin$$         didascalie implicite
%%strophe ...%%             ouverture de strophe lyrique
%%fin_strophe%%             fermeture de strophe lyrique
=12=                        indication métrique en contexte strophique
```

Le caractère `#` est réservé au balisage ETS.
Un `#` parasite dans le texte transcrit est une erreur bloquante.

## 9. Strophes et métrique

Dans le cours ordinaire d’une tragédie, l’alexandrin n’est pas marqué par `=12=`.

Dans les strophes lyriques, tous les vers portent un préfixe métrique explicite, y compris les alexandrins :

```text
%%strophe subtype=distique rhyme=aa%%
=12=Premier vers lyrique
=10=Second vers lyrique
%%fin_strophe%%
```

Pour une variante de ligne entière dans une strophe, la syntaxe correcte est :

```text
#####=12=Un vers entièrement variant
#####=12=(lacune)
```

La forme inverse `=12=#####...` doit être rejetée.

## 10. Sorties

### TEI

La TEI est la sortie structurante.
Elle doit porter l’information éditoriale : témoins, variantes, locuteurs, vers, didascalies, strophes, métrique, métadonnées.

### HTML

Le HTML sert à la prévisualisation locale et au site statique.
Il doit être dérivé de la TEI.

### Site statique

Le site statique est produit par le site builder.
Il agrège les pièces TEI, les paratextes, les notices, les préfaces, les dramatis personae et les assets.

### LaTeX-Ekdosis

Le LaTeX-Ekdosis est destiné au texte dramatique critique et à son apparat.
Le chantier actuel consiste à le maintenir depuis la TEI canonique.

### LaTeX standard

Les notices, introductions, bibliographies et péritextes doivent être exportés en LaTeX ordinaire.
Ils ne doivent pas être forcés dans Ekdosis.

### Mise en page PURH

La mise en page finale doit relever d’un template ou d’une classe PURH, partagé par les sorties Ekdosis et non-Ekdosis.

## 11. Organisation documentaire

Documents principaux :

- `AGENTS.md` : consignes Codex et règles d’architecture ;
- `docs/SPEC_V2.md` : spécification fonctionnelle actuelle ;
- `docs/LATEX_EXPORTS.md` : chantier LaTeX-Ekdosis, LaTeX standard, template PURH ;
- `docs/editer_racine_principes.md` : principes éditoriaux du projet Racine ;
- `docs/ETS_SITE_BUILDER.md` : publication statique ;
- `docs/notice_import/` : chaîne d’import des notices ;
- `docs/Documentation_ancienne.md` : mémoire historique.

Modules importants :

- `src/ets/application/` : services applicatifs appelables par les interfaces ;
- `src/ets/web/` : interface Flask ;
- `src/ets/site_builder/` : génération du site statique ;
- `src/ets/application/editorial_notice_import/` : import DOCX/Pandoc vers TEI ;
- `src/ets/latex/` : génération LaTeX/Ekdosis ;
- `src/ets/ui/tk/` : interface Tkinter.

## 12. Développement

Installation minimale :

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Lancement des tests :

```bash
python -m pytest
```

Sous Windows, si `python` n’est pas disponible :

```powershell
py -m pytest
```

Tests web ciblés :

```bash
python -m pytest tests/web -q
```

Lancement local de l’interface Flask, selon l’environnement :

```powershell
$env:PYTHONPATH="src"
python -m flask --app "ets.web.app:create_app()" run --debug
```

ou, si le dépôt fournit un script de lancement :

```powershell
python run_web.py
```

## 13. Règles d’architecture

- Le cœur métier ne doit pas dépendre de Tkinter.
- Le cœur métier ne doit pas dépendre de Flask.
- Tkinter et Flask doivent appeler les mêmes services applicatifs.
- Les sorties doivent rester dérivées de la TEI canonique autant que possible.
- La logique de génération ne doit pas être dupliquée dans les interfaces.
- La couche Flask doit rester stateless : pas de base de données, pas de stockage durable.
- Les uploads ZIP doivent être traités dans des répertoires temporaires et validés contre les traversées de chemins.
- Les chemins absolus fournis par l’utilisateur ne doivent pas être utilisés en mode web.
- La génération PDF et la publication FTP sont exclues de la première interface Flask.

## 14. Règle de prudence

Tout changement de syntaxe ETS doit être accompagné :

1. d’un test de validation ;
2. d’un test de génération TEI si la sortie change ;
3. d’une mise à jour documentaire ;
4. d’une vérification manuelle sur une fixture réaliste.

Tout changement dans l’interface web doit être accompagné au minimum :

1. d’un test de route ;
2. d’une vérification que Tkinter n’est pas importé ;
3. d’une vérification des chemins temporaires si des fichiers sont uploadés ;
4. d’un test manuel dans le navigateur si l’ergonomie est concernée.
