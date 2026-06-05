# Ekdosis-TEI Studio

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Présentation

Ekdosis-TEI Studio est un outil d’encodage, de validation, de visualisation et de publication pour des éditions critiques de théâtre classique français.

Il permet à une équipe éditoriale de travailler dans une transcription structurée légère, proche d’un pseudo-markdown, puis de produire une TEI régulière et réutilisable.

Le projet vise un double horizon :

- une édition numérique lisible et publiable sous forme de site statique ;
- une édition imprimée savante, notamment en LaTeX-Ekdosis pour l’apparat critique.

## 2. Principe central

La TEI générée par ETS est la représentation éditoriale canonique.

La chaîne cible est désormais :

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

La sortie LaTeX ne doit donc plus être considérée comme une seconde génération parallèle depuis la transcription brute.
Elle doit être dérivée de la TEI.

## 3. Publics visés

ETS s’adresse principalement :

- aux éditeurs et éditrices critiques ;
- aux équipes travaillant sur des textes dramatiques transmis par plusieurs témoins ;
- aux étudiants et étudiantes qui doivent transcrire sans écrire directement de XML ;
- aux presses universitaires et projets de publication souhaitant produire à la fois données, site et livre ;
- aux développeurs chargés de consolider une chaîne éditoriale testable.

L’outil doit rester utilisable par des non-informaticiens.
Il ne doit pas exiger de connaître TEI, LaTeX ou les humanités numériques.

## 4. Fonctionnalités actuelles importantes

Le projet contient déjà :

- un validateur du pseudo-markdown ETS ;
- un parseur de transcription dramatique ;
- une logique de collation des témoins ;
- une génération XML-TEI ;
- une prévisualisation HTML ;
- une interface Tkinter ;
- des modules d’annotations ;
- un module de références ;
- un module d’import de notices Word/Pandoc vers TEI ;
- un site builder statique ;
- des tests et fixtures pour les cas stables.

## 5. Syntaxe ETS de base

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

## 6. Strophes et métrique

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

## 7. Sorties

### TEI

La TEI est la sortie structurante.
Elle doit porter l’information éditoriale : témoins, variantes, locuteurs, vers, didascalies, strophes, métrique, métadonnées.

### HTML

Le HTML sert à la prévisualisation locale et au site statique.
Il doit être dérivé de la TEI.

### LaTeX-Ekdosis

Le LaTeX-Ekdosis est destiné au texte dramatique critique et à son apparat.
Le chantier actuel consiste à le rétablir depuis la TEI canonique.

### LaTeX standard

Les notices, introductions, bibliographies et péritextes doivent être exportés en LaTeX ordinaire.
Ils ne doivent pas être forcés dans Ekdosis.

### Mise en page PURH

La mise en page finale doit relever d’un template ou d’une classe PURH, partagé par les sorties Ekdosis et non-Ekdosis.

## 8. Organisation documentaire

Documents principaux :

- `AGENTS.md` : consignes Codex et règles d’architecture ;
- `docs/SPEC_V2.md` : spécification fonctionnelle actuelle ;
- `docs/LATEX_EXPORTS.md` : chantier LaTeX-Ekdosis, LaTeX standard, template PURH ;
- `docs/editer_racine_principes.md` : principes éditoriaux du projet Racine ;
- `docs/ETS_SITE_BUILDER.md` : publication statique ;
- `docs/notice_import/` : chaîne d’import des notices ;
- `docs/Documentation_ancienne.md` : mémoire historique.

## 9. Développement

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

## 10. Règle de prudence

Tout changement de syntaxe ETS doit être accompagné :

1. d’un test de validation ;
2. d’un test de génération TEI si la sortie change ;
3. d’une mise à jour documentaire ;
4. d’une vérification manuelle sur une fixture réaliste.
