# Éditer Racine — principes éditoriaux et chaîne ETS

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Projet éditorial

Le projet Racine vise une édition critique et semi-diplomatique complète du théâtre de Racine.

Elle doit tenir compte :

- des variantes textuelles ;
- des variantes de ponctuation ;
- des graphies ;
- des noms de personnages ;
- des locuteurs ;
- des didascalies explicites et implicites ;
- des strophes et mètres quand ils apparaissent ;
- des péritextes et notices.

## 2. Supports de publication

Les douze pièces doivent pouvoir être publiées :

- sous forme numérique, dans un site statique en libre accès ;
- sous forme imprimée, dans une mise en page PURH ;
- avec une chaîne suffisamment structurée pour produire des données éditoriales réutilisables.

## 3. Principe de chaîne

La transcription ETS n’est pas la publication finale.
Elle est une interface de saisie savante, simplifiée pour les éditeurs.

La chaîne cible est :

```text
transcription ETS
  → validation
  → TEI canonique
  → HTML / site
  → LaTeX-Ekdosis / LaTeX standard
  → mise en page PURH
```

La TEI est le pivot.

## 4. Syntaxe de transcription

Principaux marqueurs :

| Marqueur | Fonction |
|---|---|
| `####...####` | acte |
| `###...###` | scène |
| `##...##` | personnage présent dans la scène |
| `#...#` | locuteur |
| `**...**` | didascalie explicite |
| `***` | vers partagé |
| `#####...` | variante de ligne entière |
| `##### (lacune)` | lacune |
| `_..._` | italique |
| `~` | espace insécable ou retrait manuel |
| `$$TYPE$$ ... $$fin$$` | didascalie implicite |
| `%%strophe ...%%` | strophe lyrique |
| `=02=` à `=12=` | mètre dans une strophe |

## 5. Réserve du caractère dièse

Le caractère `#` appartient au balisage ETS.
Il ne doit jamais apparaître comme caractère parasite dans le texte.

Toute forme mal équilibrée doit être rejetée avant génération TEI.

## 6. Didascalies implicites

Les didascalies implicites peuvent être encodées par :

```text
$$EVT$$
Va chez elle. Dy-luy qu’importun à regret,
$$fin$$
```

Types disponibles :

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

## 7. Strophes lyriques

Les strophes lyriques sont distinctes du flux dramatique ordinaire.

Dans le flux tragique ordinaire, l’alexandrin n’est pas marqué `=12=`.

Dans les strophes, tous les vers sont métrés :

```text
%%strophe subtype=distique rhyme=aa%%
=12=Premier vers
=10=Second vers
%%fin_strophe%%
```

Pour les variantes de ligne entière métrées :

```text
#####=12=Vers variant
#####=12=(lacune)
```

## 8. Sortie TEI

La TEI doit préserver la richesse philologique plutôt que normaliser le texte.

Elle doit notamment représenter :

- les témoins ;
- les variantes ;
- les graphies ;
- les lacunes ;
- les italiques ;
- les espaces insécables ;
- les strophes ;
- les métadonnées ;
- les rôles éditoriaux : éditeur scientifique, transcripteur si renseigné.

## 9. Sorties imprimées

Le texte dramatique critique relève de LaTeX-Ekdosis.

Les notices, introductions, bibliographies et péritextes relèvent du LaTeX standard.

La mise en page finale doit être portée par une couche PURH commune.

## 10. Finalité scientifique

ETS ne produit pas seulement un texte.
Il produit un modèle éditorial du texte : une donnée philologique structurée, vérifiable, publiable et réexploitable.

C’est ce point qui relie le projet à la problématique de l’édition comme production de données.
