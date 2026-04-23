# NOTICES_CHAIN_SPEC.md

## 1. Objet

Spécification fonctionnelle et technique de la chaîne d’import des **notices rédigées en Word** pour Ekdosis–TEI Studio (ETS).

Cette chaîne est **distincte** de celle des pièces de théâtre. Elle concerne uniquement les **notices**, préfaces, introductions, page d'accueil bibliographies, commentaires liminaires et autres paratextes assimilés.

L’objectif est de proposer une mini-chaîne de type « Métopes légère » :

- sans macros Word ;
- sans XMLMind ;
- fondée sur des **styles natifs de Word** ;
- intégrée à ETS comme **module autonome et invisible pour l’utilisateur** ;
- avec **validation immédiate au chargement** ;
- conversion automatique vers une **TEI de notice maison** ;
- affichage du XML généré dans ETS.

## 2. Principe général

Chaîne visée :

`docx -> validation -> conversion pandoc -> normalisation TEI -> affichage XML`

L’utilisateur ne voit pas Pandoc, les filtres ni les étapes intermédiaires.

### Parcours utilisateur

1. L’utilisateur choisit un fichier `.docx` dans l’interface ETS.
2. ETS lance immédiatement une validation du document.
3. Si le document est conforme, ETS le convertit en XML-TEI.
4. ETS affiche le XML généré.
5. Si le document présente des erreurs bloquantes, ETS refuse l’import et affiche un rapport d’erreurs compréhensible.
6. Si le document présente seulement des avertissements, ETS autorise l’import mais affiche ces avertissements dès le chargement.

## 3. Contraintes de mise en œuvre

### 3.1. Module interne

Le module doit être **autonome** et **invisible** pour l’utilisateur.

Il ne doit pas introduire dans l’interface une notion supplémentaire du type :
- « lancer Pandoc » ;
- « appliquer un filtre » ;
- « convertir en TEI notice ».

Du point de vue de l’utilisateur, il s’agit simplement de :
- charger un docx ;
- être informé immédiatement si le fichier pose problème ;
- voir apparaître un XML conforme si tout va bien.

### 3.2. Dépendance technique

Le module s’appuie sur Pandoc avec lecture `docx+styles` et sur un filtre Lua ou une couche équivalente de normalisation.

### 3.3. Validation immédiate

La validation doit avoir lieu **dès le chargement du fichier**, avant toute conversion considérée comme valide.

Aucune importation silencieuse d’un document invalide n’est autorisée.

## 4. Périmètre fonctionnel de la V1

La V1 doit gérer :

- titre principal ;
- sous-titre éventuel ;
- **4 niveaux de titre** ;
- paragraphes courants ;
- **style de rédaction sans retrait** ;
- citations en retrait ;
- listes simples ;
- notes de bas de page ;
- italiques ;
- gras ;
- exposant ;
- indice ;
- **petites capitales** ;
- **tableaux simples** ;
- bibliographie simple.

### Hors périmètre V1

Sont exclus en V1 :

- tableaux complexes ;
- cellules fusionnées ;
- tableaux imbriqués ;
- images ancrées dans des tableaux ;
- zones de texte Word ;
- formes ;
- SmartArt ;
- commentaires Word ;
- suivi de modifications actif ;
- encodages sémantiques fins de type index, entités nommées, renvois complexes, apparatus critique, etc.

## 5. Styles Word autorisés

Le principe est le suivant :

- les **styles de paragraphe** portent la structure ;
- les **mises en forme de caractère** portent les effets inline.

### 5.1. Styles de paragraphe autorisés

Le module doit accepter les styles Word natifs suivants, en français et/ou en anglais selon la localisation de Word :

- `Titre` / `Title`
- `Sous-titre` / `Subtitle`
- `Titre 1` / `Heading 1`
- `Titre 2` / `Heading 2`
- `Titre 3` / `Heading 3`
- `Titre 4` / `Heading 4`
- `Normal`
- **style natif de paragraphe sans retrait** (mappé explicitement dans le code)
- `Citation` / `Quote`
- `Légende` / `Caption`

### 5.2. Remarque sur le style sans retrait

Le style de rédaction sans retrait fait partie des exigences de la V1.

Il doit être :
- un style **natif de Word** ;
- reconnu explicitement par le validateur ;
- converti en TEI par un rendu distinct du paragraphe ordinaire.

Le code doit pouvoir gérer les variantes de nommage liées à la langue ou au modèle Word, via une table d’équivalence.

### 5.3. Mise en forme de caractère autorisée

Les mises en forme inline autorisées sont :

- italique ;
- gras ;
- exposant ;
- indice ;
- **petites capitales**.

### 5.4. Petites capitales

Les petites capitales relèvent d’une **mise en forme de caractère**, non d’un style de paragraphe.

Le validateur doit les autoriser.

Le convertisseur doit les transformer en TEI :

```xml
<hi rend="smallcaps">...</hi>
```

## 6. Objets Word autorisés

### 6.1. Notes

Seules les **notes de bas de page Word natives** sont autorisées.

Leur conversion cible est :

```xml
<note place="foot">...</note>
```

### 6.2. Listes

Les listes Word natives simples sont autorisées.

Conversion cible :

```xml
<list>
  <item>...</item>
</list>
```

### 6.3. Tableaux

Les **tableaux simples** sont autorisés.

#### Définition d’un tableau simple en V1

Un tableau est considéré comme simple s’il respecte toutes les conditions suivantes :

- aucune cellule fusionnée horizontalement ;
- aucune cellule fusionnée verticalement ;
- pas de tableau imbriqué ;
- pas d’image dans une cellule ;
- pas de mise en page complexe simulée par le tableau ;
- contenu textuel simple dans les cellules.

Conversion cible :

```xml
<table>
  ...
</table>
```

Si un tableau dépasse ces contraintes, il doit être signalé comme **erreur bloquante**.

## 7. Règles éditoriales à faire respecter

Le validateur doit considérer comme correct uniquement un document respectant les principes suivants :

- les intertitres sont de vrais styles Word ;
- les citations détachées sont en style `Citation` ;
- les notes sont de vraies notes de bas de page Word ;
- les tableaux sont de vrais tableaux Word ;
- les petites capitales utilisent la fonction dédiée de Word ;
- il n’y a pas de faux retraits manuels ;
- il n’y a pas de faux titres fabriqués en gras ;
- il n’y a pas de tabulations décoratives ;
- il n’y a pas de double retour uniquement typographique pour simuler des espacements.

## 8. Politique de validation

Le validateur doit produire deux types de diagnostic :

- **erreurs bloquantes** ;
- **avertissements**.

### 8.1. Erreurs bloquantes

Un document doit être **refusé** si l’un des cas suivants est rencontré :

- absence de titre principal ;
- style de paragraphe non autorisé ;
- saut de niveau hiérarchique invalide (`Titre 1` directement suivi de `Titre 3`, etc.) ;
- tableau complexe ;
- objet Word non pris en charge ;
- document corrompu ou illisible ;
- structure manifestement incohérente.

### 8.2. Avertissements

Un document peut être importé avec avertissements dans les cas suivants :

- paragraphes vides parasites ;
- usage suspectement abondant du gras ou de l’italique ;
- rubrique bibliographique absente ;
- alternance peu cohérente entre paragraphe normal et paragraphe sans retrait ;
- éléments tolérés mais atypiques.

## 9. Règles hiérarchiques sur les titres

Le module doit reconstruire la structure de la notice à partir des styles :

- `Titre` = titre principal du document ;
- `Sous-titre` = sous-titre facultatif ;
- `Titre 1` = niveau de section ;
- `Titre 2` = niveau de sous-section ;
- `Titre 3` = niveau de sous-sous-section ;
- `Titre 4` = niveau 4.

### 9.1. Règles de validité

Sont autorisés :
- `Titre 1` puis `Titre 2` ;
- `Titre 2` puis `Titre 3` ;
- `Titre 3` puis `Titre 4` ;
- remontées d’un ou plusieurs niveaux.

Sont interdits :
- `Titre 1` puis `Titre 3` sans `Titre 2` intermédiaire ;
- `Titre 2` puis `Titre 4` sans `Titre 3` ;
- plusieurs titres principaux dans le même document si cela ne correspond pas au modèle choisi.

## 10. Mapping TEI cible

### 10.1. Structure

- `Titre` -> `<head type="main">`
- `Sous-titre` -> `<head type="sub">`
- `Titre 1` -> `<div type="section">`
- `Titre 2` -> `<div type="subsection">`
- `Titre 3` -> `<div type="subsubsection">`
- `Titre 4` -> `<div type="level4">`
- `Normal` -> `<p>`
- style sans retrait -> `<p rend="noindent">`
- `Citation` -> `<quote><p>...</p></quote>`
- `Légende` -> `<p type="caption">...</p>` ou équivalent décidé dans la couche TEI

### 10.2. Inline

- italique -> `<hi rend="italic">`
- gras -> `<hi rend="bold">`
- exposant -> `<hi rend="sup">`
- indice -> `<hi rend="sub">`
- petites capitales -> `<hi rend="smallcaps">`

### 10.3. Appareils

- note Word -> `<note place="foot">`
- liste -> `<list>` / `<item>`
- tableau simple -> `<table>`

## 11. Bibliographie

Il n’est pas nécessaire d’introduire un style Word spécifique de bibliographie dans la V1.

Règle :
- une section intitulée `Bibliographie` est repérée à partir de son titre ;
- les paragraphes qui suivent, jusqu’au prochain titre de même niveau ou de niveau supérieur, sont interprétés comme entrées bibliographiques ;
- ils sont transformés en :

```xml
<div type="section">
  <head>Bibliographie</head>
  <listBibl>
    <bibl>...</bibl>
    <bibl>...</bibl>
  </listBibl>
</div>
```

## 12. Rapport utilisateur

Au chargement d’un docx, ETS doit afficher un diagnostic clair.

### 12.1. États possibles

- **Import conforme**
- **Import conforme avec avertissements**
- **Import refusé**

### 12.2. Contenu minimal du rapport

Le rapport doit comporter :

- un statut global ;
- le nombre d’erreurs et d’avertissements ;
- la liste détaillée des problèmes ;
- une indication localisable quand c’est possible.

### 12.3. Exemple de sortie attendue

- Erreur : style non autorisé `Intense Quote`
- Erreur : saut hiérarchique invalide `Titre 2 -> Titre 4`
- Avertissement : 3 paragraphes vides consécutifs dans la section `Bibliographie`
- Avertissement : usage du style sans retrait mélangé de façon irrégulière

## 13. Refus d’import

En cas d’erreur bloquante :

- le XML final ne doit pas être présenté comme valide ;
- le document ne doit pas être injecté silencieusement dans la chaîne ;
- ETS doit demander implicitement correction par l’utilisateur via le rapport d’erreurs.

## 14. Architecture logicielle recommandée

Organisation suggérée :

- `src/ets/notice_import/validator.py`
- `src/ets/notice_import/pandoc_bridge.py`
- `src/ets/notice_import/tei_mapper.py`
- `src/ets/notice_import/report.py`
- `src/ets/notice_import/__init__.py`

### 14.1. `validator.py`

Responsabilités :
- détecter les styles utilisés ;
- vérifier leur conformité ;
- contrôler la hiérarchie des titres ;
- détecter les objets interdits ;
- classifier les problèmes en erreurs / avertissements.

### 14.2. `pandoc_bridge.py`

Responsabilités :
- appeler Pandoc ;
- utiliser `docx+styles` ;
- récupérer la représentation intermédiaire utile ;
- remonter les erreurs techniques d’exécution.

### 14.3. `tei_mapper.py`

Responsabilités :
- appliquer les règles métier ;
- produire la TEI cible ;
- gérer la bibliographie ;
- gérer le style sans retrait ;
- gérer les petites capitales.

### 14.4. `report.py`

Responsabilités :
- produire un diagnostic lisible pour l’interface ;
- sérialiser les erreurs et avertissements ;
- fournir un résumé compact et un détail exploitable.

## 15. Commande Pandoc de référence

Commande de travail indicative :

```bash
pandoc notice.docx \
  -f docx+styles \
  --lua-filter=word_notice_to_tei.lua \
  -t tei \
  -s \
  -o notice.xml
```

Cette commande est indicative. L’implémentation finale peut passer par un flux AST ou une autre orchestration interne, du moment que le comportement spécifié est respecté.

## 16. Jeux de tests attendus

Codex devra disposer d’un corpus de fixtures minimales.

### 16.1. Fixtures docx

- `notice_ok_minimal.docx`
- `notice_ok_full.docx`
- `notice_ok_smallcaps.docx`
- `notice_ok_noindent.docx`
- `notice_ok_biblio.docx`
- `notice_ok_table_simple.docx`
- `notice_bad_unknown_style.docx`
- `notice_bad_heading_jump.docx`
- `notice_bad_table_merged_cells.docx`
- `notice_bad_missing_title.docx`
- `notice_warn_empty_paragraphs.docx`
- `notice_warn_irregular_noindent.docx`

### 16.2. Attendus associés

Pour chaque fixture, fournir :

- le rapport de validation attendu ;
- si import autorisé : le XML TEI attendu ;
- si import refusé : la liste des erreurs attendues.

## 17. Critères d’acceptation

Le travail sera considéré comme acceptable si :

1. un docx conforme est importé et converti automatiquement ;
2. les styles autorisés sont reconnus correctement ;
3. les petites capitales sont conservées comme `hi rend="smallcaps"` ;
4. le style sans retrait est conservé comme paragraphe distinct ;
5. les tableaux simples passent ;
6. les tableaux complexes sont refusés ;
7. les erreurs sont signalées dès le chargement ;
8. l’utilisateur n’a aucune manipulation technique supplémentaire à effectuer ;
9. le module reste autonome et non intrusif dans l’interface.

## 18. Phrase contractuelle à retenir pour Codex

Le module d’import de notices est invisible pour l’utilisateur. Au chargement d’un docx, le programme doit valider immédiatement le document, signaler toute erreur ou tout avertissement, refuser la conversion en cas d’erreur bloquante, et ne produire du XML-TEI qu’à partir d’un document conforme au profil Word défini dans cette spécification.
