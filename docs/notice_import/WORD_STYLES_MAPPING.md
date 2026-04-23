# WORD_STYLES_MAPPING.md

## 1. Objet

Ce document complète `NOTICES_CHAIN_SPEC.md`.

Il fixe la **table canonique des styles Word et des mises en forme autorisés** pour l’import des notices dans Ekdosis–TEI Studio (ETS), ainsi que leur **interprétation métier**, leur **statut de validation** et leur **cible TEI**.

Il s’applique uniquement à la chaîne d’import des **notices**, pas aux pièces de théâtre.

## 2. Principes généraux

Le module d’import distingue trois catégories :

1. **styles de paragraphe** : ils portent la structure du document ;
2. **mises en forme de caractère** : elles portent les effets inline ;
3. **objets Word** : notes, listes, tableaux.

Le validateur doit raisonner à partir de cette distinction.

## 3. Statuts de validation

Chaque style, mise en forme ou objet reçoit un statut :

- **Autorisé** : accepté sans réserve ;
- **Autorisé avec règle** : accepté, mais soumis à une condition métier ;
- **Toléré avec avertissement** : import possible, mais signalement recommandé ;
- **Interdit** : erreur bloquante.

## 4. Styles de paragraphe autorisés

### 4.1. Tableau canonique

| Catégorie | Nom Word FR | Nom Word EN | Statut | Rôle métier | Cible TEI | Observations |
|---|---|---|---|---|---|---|
| Paragraphe | Titre | Title | Autorisé | Titre principal du document | `<head type="main">...</head>` | Obligatoire une fois au moins |
| Paragraphe | Sous-titre | Subtitle | Autorisé avec règle | Sous-titre facultatif du document | `<head type="sub">...</head>` | Facultatif ; normalement placé après le titre principal |
| Paragraphe | Titre 1 | Heading 1 | Autorisé | Niveau 1 de section | ouverture de `<div type="section">` + `<head>` | Ne doit pas sauter directement à Titre 3 |
| Paragraphe | Titre 2 | Heading 2 | Autorisé | Niveau 2 de section | ouverture de `<div type="subsection">` + `<head>` | Dépend d’un niveau 1 déjà ouvert |
| Paragraphe | Titre 3 | Heading 3 | Autorisé | Niveau 3 de section | ouverture de `<div type="subsubsection">` + `<head>` | Dépend d’un niveau 2 déjà ouvert |
| Paragraphe | Titre 4 | Heading 4 | Autorisé | Niveau 4 de section | ouverture de `<div type="level4">` + `<head>` | Dépend d’un niveau 3 déjà ouvert |
| Paragraphe | Normal | Normal | Autorisé | Paragraphe courant | `<p>...</p>` | Style de base du corps de texte |
| Paragraphe | Sans espacement / Sans retrait / style natif sans retrait retenu par le projet | No Spacing / native no-indent style retained by the project | Autorisé avec règle | Paragraphe courant sans retrait | `<p rend="noindent">...</p>` | Le libellé exact doit être normalisé dans le code via table d’équivalence |
| Paragraphe | Citation | Quote | Autorisé | Citation en retrait | `<quote><p>...</p></quote>` | Pour les citations détachées seulement |
| Paragraphe | Légende | Caption | Autorisé | Légende d’image ou de tableau si prise en charge | `<p type="caption">...</p>` ou équivalent | À conserver simple en V1 |

### 4.2. Règles hiérarchiques sur les titres

Les styles `Titre 1` à `Titre 4` sont autorisés selon les règles suivantes :

- `Titre 1 -> Titre 2` : autorisé ;
- `Titre 2 -> Titre 3` : autorisé ;
- `Titre 3 -> Titre 4` : autorisé ;
- remontée d’un ou plusieurs niveaux : autorisée ;
- `Titre 1 -> Titre 3` sans `Titre 2` intermédiaire : interdit ;
- `Titre 2 -> Titre 4` sans `Titre 3` intermédiaire : interdit.

Tout saut de niveau interdit doit produire une **erreur bloquante**.

### 4.3. Règles sur le style sans retrait

Le projet exige la prise en charge d’un **style de rédaction sans retrait**, lui aussi natif de Word.

Comme les noms des styles varient selon la langue, la version de Word ou le gabarit, le code doit :

- accepter une **liste blanche de libellés équivalents** ;
- les ramener à une catégorie interne unique, par exemple `NOINDENT_PARAGRAPH` ;
- produire la TEI cible :

```xml
<p rend="noindent">...</p>
```

Le mélange irrégulier entre `Normal` et paragraphe sans retrait n’est pas bloquant, mais peut déclencher un **avertissement**.

## 5. Styles de paragraphe tolérés ou interdits

### 5.1. Tolérés avec avertissement

| Nom Word FR | Nom Word EN | Statut | Traitement |
|---|---|---|---|
| Corps de texte | Body Text | Toléré avec avertissement | Peut être remappé vers `<p>` si le projet choisit de le tolérer ; à éviter dans le profil recommandé |
| Liste à puces / Liste numérotée appliquées comme style de paragraphe explicite | List Paragraph | Toléré avec avertissement | Préférer les listes Word natives ; si la structure de liste est correctement détectée, convertir normalement |

### 5.2. Interdits

| Nom Word FR | Nom Word EN | Statut | Motif |
|---|---|---|---|
| Citation intense | Intense Quote | Interdit | Style hors profil |
| Titre 5 et au-delà | Heading 5+ | Interdit | Hors périmètre V1 |
| styles personnalisés non documentés | custom styles | Interdit | Le profil V1 repose sur une liste blanche stricte |
| tout style décoratif non prévu | decorative/custom styles | Interdit | Ambiguïté structurelle |

Tout style de paragraphe hors liste blanche doit produire une **erreur bloquante**.

## 6. Mises en forme de caractère autorisées

### 6.1. Tableau canonique

| Catégorie | Mise en forme Word | Statut | Rôle métier | Cible TEI | Observations |
|---|---|---|---|---|---|
| Caractère | Italique | Autorisé | Emphase, titre d’œuvre, usage éditorial courant | `<hi rend="italic">...</hi>` | Autorisé librement |
| Caractère | Gras | Autorisé | Emphase forte, repérage ponctuel | `<hi rend="bold">...</hi>` | Un usage excessif peut donner lieu à avertissement |
| Caractère | Exposant | Autorisé | Appels, abréviations, formes savantes | `<hi rend="sup">...</hi>` | Autorisé |
| Caractère | Indice | Autorisé | Formes savantes, notation | `<hi rend="sub">...</hi>` | Autorisé |
| Caractère | Petites capitales | Autorisé | Mise en forme savante inline | `<hi rend="smallcaps">...</hi>` | Exigence explicite de la V1 |

### 6.2. Règle importante sur les petites capitales

Les petites capitales sont une **mise en forme de caractère**.

Elles ne doivent jamais être interprétées comme :

- un style de paragraphe ;
- un niveau de titre ;
- un signal structurel.

Le convertisseur doit les conserver comme balisage inline :

```xml
<hi rend="smallcaps">...</hi>
```

### 6.3. Tolérances et avertissements

| Mise en forme | Statut | Traitement |
|---|---|---|
| soulignement | Toléré avec avertissement ou interdit selon politique finale | déconseillé pour la V1 ; si toléré, à signaler |
| changement direct de police/couleur | Toléré avec avertissement | non sémantique ; à signaler si détectable |
| capitales tapées au clavier pour imiter des petites capitales | Interdit en pratique éditoriale, non toujours détectable automatiquement | la documentation utilisateur doit l’interdire explicitement |

## 7. Objets Word autorisés

### 7.1. Notes de bas de page

| Objet | Statut | Cible TEI | Observations |
|---|---|---|---|
| note de bas de page Word native | Autorisé | `<note place="foot">...</note>` | Seul format de note autorisé en V1 |
| note de fin Word | Interdit ou hors profil V1 | n/a | À refuser si la politique du projet l’exclut |

### 7.2. Listes

| Objet | Statut | Cible TEI | Observations |
|---|---|---|---|
| liste à puces Word native | Autorisé | `<list><item>...</item></list>` | Autorisée |
| liste numérotée Word native | Autorisé | `<list><item>...</item></list>` | Le type numéroté peut être conservé si besoin ultérieur |
| pseudo-liste fabriquée par tabulations ou tirets manuels | Interdit | n/a | Erreur de structuration |

### 7.3. Tableaux

| Objet | Statut | Cible TEI | Observations |
|---|---|---|---|
| tableau Word simple | Autorisé | `<table>...</table>` | Autorisé en V1 |
| tableau avec cellules fusionnées | Interdit | n/a | Hors profil V1 |
| tableau imbriqué | Interdit | n/a | Hors profil V1 |
| tableau avec image en cellule | Interdit | n/a | Hors profil V1 |
| tableau utilisé pour simuler une mise en page complexe | Interdit | n/a | Hors profil V1 |

Un **tableau simple** est défini comme un tableau :

- sans fusion de cellules ;
- sans tableau imbriqué ;
- sans image ;
- sans structure typographique complexe ;
- à contenu textuel simple.

## 8. Sections bibliographiques

La V1 ne requiert pas de style Word spécifique de bibliographie.

La règle métier est la suivante :

- un titre de section intitulé `Bibliographie` ouvre une section bibliographique ;
- les paragraphes qui suivent sont lus comme entrées bibliographiques jusqu’au prochain titre de même niveau ou de niveau supérieur ;
- ces paragraphes sont transformés en :

```xml
<listBibl>
  <bibl>...</bibl>
  <bibl>...</bibl>
</listBibl>
```

Les styles autorisés dans une section bibliographique sont donc, par défaut :

- `Normal` ;
- style sans retrait ;
- éventuellement `Citation` si le projet décide de le tolérer dans ce contexte.

## 9. Diagnostic attendu du validateur

### 9.1. Erreurs bloquantes

Doivent entraîner un refus d’import :

- absence de `Titre` ;
- style de paragraphe non autorisé ;
- saut hiérarchique de titre interdit ;
- présence d’un objet Word interdit ;
- présence d’un tableau non simple ;
- document illisible ou corrompu.

### 9.2. Avertissements

Peuvent laisser passer l’import :

- alternance peu cohérente entre `Normal` et style sans retrait ;
- usage abondant du gras ou de l’italique ;
- paragraphes vides parasites ;
- usage de styles tolérés mais non recommandés ;
- absence de rubrique bibliographique.

## 10. Catégories internes recommandées pour le code

Le validateur peut ramener les noms Word vers des catégories internes stables :

| Catégorie interne | Styles Word sources possibles |
|---|---|
| `DOC_TITLE` | `Titre`, `Title` |
| `DOC_SUBTITLE` | `Sous-titre`, `Subtitle` |
| `HEADING_1` | `Titre 1`, `Heading 1` |
| `HEADING_2` | `Titre 2`, `Heading 2` |
| `HEADING_3` | `Titre 3`, `Heading 3` |
| `HEADING_4` | `Titre 4`, `Heading 4` |
| `PARA` | `Normal`, éventuellement `Body Text` si toléré |
| `PARA_NOINDENT` | liste blanche du style natif sans retrait retenu |
| `BLOCK_QUOTE` | `Citation`, `Quote` |
| `CAPTION` | `Légende`, `Caption` |

Pour les mises en forme inline :

| Catégorie interne | Mise en forme Word |
|---|---|
| `ITALIC` | italique |
| `BOLD` | gras |
| `SUPERSCRIPT` | exposant |
| `SUBSCRIPT` | indice |
| `SMALLCAPS` | petites capitales |

## 11. Exemples de mapping

### 11.1. Titre et paragraphe

Source Word :
- `Titre` : *Bérénice*
- `Normal` : premier paragraphe de notice

Cible TEI :

```xml
<head type="main">Bérénice</head>
<p>Premier paragraphe de notice...</p>
```

### 11.2. Paragraphe sans retrait

Source Word :
- style sans retrait natif du projet

Cible TEI :

```xml
<p rend="noindent">Paragraphe sans retrait...</p>
```

### 11.3. Petites capitales inline

Source Word :
- mot ou groupe de mots en petites capitales

Cible TEI :

```xml
<p>Texte avec <hi rend="smallcaps">petites capitales</hi>.</p>
```

### 11.4. Citation

Source Word :
- paragraphe en style `Citation`

Cible TEI :

```xml
<quote>
  <p>Texte cité...</p>
</quote>
```

### 11.5. Bibliographie

Source Word :
- `Titre 1` : Bibliographie
- paragraphes suivants en `Normal`

Cible TEI :

```xml
<div type="section">
  <head>Bibliographie</head>
  <listBibl>
    <bibl>Forestier, ...</bibl>
    <bibl>Guibert, ...</bibl>
  </listBibl>
</div>
```

## 12. Règles documentaires à communiquer aux utilisateurs

Le guide utilisateur devra rappeler explicitement :

- utiliser les styles Word natifs prévus ;
- ne pas inventer de styles supplémentaires ;
- utiliser le style sans retrait prévu par le projet, non des retraits manuels ;
- utiliser la vraie fonction Word de petites capitales ;
- utiliser de vraies notes Word ;
- utiliser de vrais tableaux Word simples ;
- ne pas fabriquer de listes à la main ;
- ne pas fabriquer d’intertitres en gras.

## 13. Phrase contractuelle pour Codex

Toute occurrence d’un style de paragraphe hors liste blanche doit être traitée comme une erreur bloquante. Toute mise en forme inline autorisée doit être conservée dans la TEI cible. Le style sans retrait doit être reconnu comme catégorie distincte du paragraphe normal. Les petites capitales doivent être traitées comme mise en forme de caractère et converties en `<hi rend="smallcaps">`.
