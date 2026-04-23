# NOTICES_VALIDATION_RULES.md

## 1. Objet

Ce document complète :

- `NOTICES_CHAIN_SPEC.md`
- `WORD_STYLES_MAPPING.md`

Il définit les **règles de validation** applicables à l’import des **notices Word** dans Ekdosis–TEI Studio (ETS), ainsi que :

- les niveaux de sévérité ;
- les conditions d’acceptation ou de refus ;
- le format attendu des diagnostics ;
- les critères minimaux de test.

Il s’applique uniquement à la chaîne d’import des **notices**, pas aux pièces de théâtre.

---

## 2. Principe général

La validation intervient **dès le chargement du fichier `.docx`**.

Aucun document ne doit être considéré comme importé tant que cette validation n’a pas été exécutée.

Le validateur doit produire l’un des trois statuts suivants :

- `VALID`
- `VALID_WITH_WARNINGS`
- `INVALID`

### 2.1. Règle de décision

- `VALID` : aucune erreur bloquante, aucun avertissement.
- `VALID_WITH_WARNINGS` : aucune erreur bloquante, au moins un avertissement.
- `INVALID` : au moins une erreur bloquante.

### 2.2. Conséquences côté interface

- `VALID` : import autorisé, conversion TEI lancée, XML affiché.
- `VALID_WITH_WARNINGS` : import autorisé, conversion TEI lancée, XML affiché, avertissements visibles immédiatement.
- `INVALID` : import refusé, aucune conversion TEI finale considérée comme valide, rapport d’erreurs affiché immédiatement.

---

## 3. Niveaux de sévérité

Le validateur distingue deux niveaux de sévérité.

### 3.1. Erreur bloquante

Une erreur bloquante entraîne nécessairement :

- le statut `INVALID` ;
- le refus d’import ;
- l’absence d’affichage d’un XML final présenté comme conforme.

### 3.2. Avertissement

Un avertissement :

- n’empêche pas l’import ;
- doit être signalé à l’utilisateur ;
- doit être conservé dans le rapport de validation.

---

## 4. Ordre logique des contrôles

Le validateur doit, dans cet ordre logique, vérifier :

1. lisibilité technique du fichier ;
2. présence d’un document Word exploitable ;
3. extraction des styles et objets ;
4. conformité des styles de paragraphe ;
5. hiérarchie des titres ;
6. conformité des objets Word (notes, listes, tableaux) ;
7. conformité des mises en forme inline lorsque détectables ;
8. règles éditoriales simples ;
9. constitution du rapport final.

L’implémentation peut optimiser cet ordre, mais le rapport doit rester intelligible et stable.

---

## 5. Erreurs bloquantes

### 5.1. Fichier illisible ou corrompu

Doit produire une erreur bloquante :

- fichier non ouvrable ;
- `.docx` corrompu ;
- archive interne invalide ;
- document Word dont l’analyse échoue avant extraction fiable des styles.

### 5.2. Absence de titre principal

Doit produire une erreur bloquante :

- absence de paragraphe en style `Titre` / `Title`.

Le titre principal est obligatoire une fois au moins.

### 5.3. Style de paragraphe non autorisé

Doit produire une erreur bloquante :

- tout style de paragraphe hors liste blanche définie dans `WORD_STYLES_MAPPING.md`, sauf style explicitement toléré par configuration.

Exemples :

- `Intense Quote`
- `Heading 5`
- tout style personnalisé non documenté
- tout style décoratif ou ambigu

### 5.4. Saut hiérarchique interdit dans les titres

Doit produire une erreur bloquante :

- `Titre 1` suivi directement de `Titre 3` sans `Titre 2` intermédiaire ;
- `Titre 2` suivi directement de `Titre 4` sans `Titre 3` intermédiaire ;
- ouverture d’un `Titre 2`, `Titre 3` ou `Titre 4` sans qu’un niveau parent cohérent existe.

### 5.5. Objet Word interdit

Doit produire une erreur bloquante la présence de l’un des objets suivants, si détectables :

- zone de texte ;
- forme ;
- SmartArt ;
- commentaire Word ;
- suivi de modifications actif, si le projet confirme cette politique ;
- note de fin, si le projet la maintient hors profil V1.

### 5.6. Tableau non conforme à la définition V1

Doit produire une erreur bloquante :

- cellule fusionnée horizontalement ;
- cellule fusionnée verticalement ;
- tableau imbriqué ;
- image en cellule ;
- tableau utilisé pour simuler une mise en page complexe ;
- structure tabulaire impossible à convertir proprement en tableau simple.

### 5.7. Pseudo-structure manifestement non conforme

Doit produire une erreur bloquante, si le détecteur sait l’identifier de façon robuste :

- pseudo-liste fabriquée par tabulations ou tirets manuels à la place d’une vraie liste Word ;
- faux intertitre fabriqué par mise en forme directe alors qu’il ne correspond à aucun style autorisé ;
- faux tableau obtenu par alignement manuel.

Cette règle doit rester prudente : si la détection n’est pas fiable, mieux vaut un avertissement qu’un faux positif bloquant.

---

## 6. Avertissements

### 6.1. Alternance peu cohérente entre paragraphe standard et paragraphe sans retrait

Doit produire un avertissement :

- alternance fréquente entre `Normal` et le style sans retrait sans logique visible.

Le projet peut choisir ultérieurement de raffiner cette heuristique.

### 6.2. Paragraphes vides parasites

Doit produire un avertissement :

- paragraphe vide isolé ;
- série de paragraphes vides ;
- paragraphes vides autour d’un titre ou dans une section bibliographique.

### 6.3. Usage excessif de la mise en forme directe

Peut produire un avertissement :

- usage très abondant du gras ;
- usage très abondant de l’italique ;
- séquences de petites capitales anormalement longues hors logique éditoriale.

Ces avertissements sont utiles mais non bloquants.

### 6.4. Usage d’un style toléré mais non recommandé

Doit produire un avertissement :

- emploi de `Body Text` / `Corps de texte` si ce style est toléré par le projet ;
- emploi de `List Paragraph` sans structure de liste suffisamment nette.

### 6.5. Absence de rubrique bibliographique

Peut produire un avertissement :

- aucune rubrique intitulée `Bibliographie` détectée.

Cet avertissement ne doit jamais bloquer l’import.

### 6.6. Incohérences éditoriales simples

Peuvent produire un avertissement :

- succession inhabituelle de titres vides ;
- sous-titre sans titre principal immédiatement voisin ;
- citation très longue non stylée comme `Citation` ;
- présence d’un style de légende sans objet voisin identifiable.

---

## 7. Règles de contrôle détaillées

## 7.1. Contrôle du titre principal

Le document doit contenir exactement :

- au moins un titre principal ;
- idéalement un seul.

### Politique recommandée

- zéro `Titre` : erreur bloquante ;
- un `Titre` : conforme ;
- plusieurs `Titre` : avertissement ou erreur selon politique finale.

Pour la V1, je recommande :

- plusieurs titres principaux = **avertissement** si l’un d’eux peut raisonnablement être considéré comme principal ;
- erreur bloquante seulement si la structure devient indécidable.

## 7.2. Contrôle de la hiérarchie des titres

Le validateur doit reconstruire une pile de niveaux :

- `Titre 1`
- `Titre 2`
- `Titre 3`
- `Titre 4`

Sont autorisés :

- ouverture d’un niveau immédiatement inférieur ;
- maintien au même niveau ;
- remontée d’un ou plusieurs niveaux.

Sont interdits :

- saut descendant de plus d’un niveau ;
- niveau enfant sans parent logique.

## 7.3. Contrôle des styles de paragraphe

Chaque paragraphe doit être classé dans une catégorie interne stable, par exemple :

- `DOC_TITLE`
- `DOC_SUBTITLE`
- `HEADING_1`
- `HEADING_2`
- `HEADING_3`
- `HEADING_4`
- `PARA`
- `PARA_NOINDENT`
- `BLOCK_QUOTE`
- `CAPTION`

Tout paragraphe non classable dans cette table doit être signalé comme erreur bloquante, sauf règle explicite de tolérance.

## 7.4. Contrôle du style sans retrait

Le style sans retrait :

- doit appartenir à une liste blanche ;
- doit être ramené à une catégorie interne unique ;
- ne doit pas être confondu avec un style simplement “sans espacement” si le projet ne le souhaite pas.

Le validateur doit permettre une configuration explicite des libellés acceptés.

## 7.5. Contrôle des citations

Un paragraphe en style `Citation` / `Quote` est valide.

Une très longue citation en style `Normal` peut donner lieu à un avertissement heuristique, mais pas à une erreur bloquante, sauf si le projet décide d’une règle plus prescriptive.

## 7.6. Contrôle des notes

Seules les notes de bas de page Word natives sont autorisées.

Doivent produire :

- note de bas de page native : conforme ;
- note de fin : erreur bloquante si hors profil ;
- appel de note simulé manuellement dans le texte : avertissement au mieux, si détectable.

## 7.7. Contrôle des listes

Sont conformes :

- vraies listes Word à puces ;
- vraies listes Word numérotées.

Sont non conformes :

- liste simulée par tirets saisis à la main ;
- liste simulée par tabulations.

Si la détection automatique n’est pas fiable, préférer l’avertissement.

## 7.8. Contrôle des tableaux

Le validateur doit identifier chaque tableau et vérifier :

- nombre de lignes et de colonnes ;
- absence de fusion ;
- absence de tableau imbriqué ;
- absence d’image ;
- convertibilité simple.

Tout tableau non convertible proprement en V1 doit être bloquant.

## 7.9. Contrôle des petites capitales

Les petites capitales sont autorisées comme mise en forme inline.

Le validateur ne doit jamais les traiter comme un signal structurel.

Leur présence n’est jamais bloquante en soi.

## 7.10. Contrôle des métadonnées parasites

Peuvent donner lieu à avertissement ou erreur selon niveau de gravité :

- document vide ou quasi vide ;
- succession de contenus techniques sans texte réel ;
- présence de nombreux champs Word non résolus, si détectables.

---

## 8. Rapport de validation

Le rapport remis à l’interface doit être structuré, stable et exploitable.

### 8.1. Champs minimaux attendus

Le rapport doit contenir au minimum :

- `status`
- `blocking_error_count`
- `warning_count`
- `messages`

### 8.2. Structure recommandée d’un message

Chaque message devrait contenir :

- `severity` : `error` ou `warning`
- `code` : identifiant stable de règle
- `message` : texte lisible
- `location` : localisation humaine ou technique
- `style_name` : si pertinent
- `paragraph_index` ou équivalent : si disponible
- `suggestion` : correction conseillée si possible

### 8.3. Exemples de codes stables

- `DOCX_UNREADABLE`
- `MISSING_TITLE`
- `UNKNOWN_PARAGRAPH_STYLE`
- `HEADING_LEVEL_SKIP`
- `FORBIDDEN_WORD_OBJECT`
- `TABLE_COMPLEX`
- `EMPTY_PARAGRAPH_SERIES`
- `MIXED_NORMAL_NOINDENT`
- `MISSING_BIBLIO_SECTION`

### 8.4. Exemple de message

```json
{
  "severity": "error",
  "code": "UNKNOWN_PARAGRAPH_STYLE",
  "message": "Style de paragraphe non autorisé : Intense Quote",
  "location": "paragraphe 18",
  "style_name": "Intense Quote",
  "paragraph_index": 18,
  "suggestion": "Remplacer ce style par Citation ou Normal selon le cas."
}
```

---

## 9. Critères d’acceptation fonctionnels

Le module sera considéré comme conforme si les comportements suivants sont vérifiés.

### 9.1. Cas conformes

1. un document minimal avec `Titre` + paragraphes `Normal` est importé sans erreur ;
2. un document avec `Titre 1` à `Titre 4` correctement emboîtés est importé ;
3. un document avec petites capitales inline est importé ;
4. un document avec style sans retrait est importé ;
5. un document avec tableau simple est importé ;
6. un document avec notes de bas de page Word natives est importé.

### 9.2. Cas avec avertissements

1. un document avec paragraphes vides parasites importe avec avertissement ;
2. un document mêlant `Normal` et style sans retrait de façon irrégulière importe avec avertissement ;
3. un document sans bibliographie importe avec avertissement si cette règle est activée.

### 9.3. Cas bloquants

1. un document sans `Titre` est refusé ;
2. un document contenant un style non autorisé est refusé ;
3. un document avec saut `Titre 1 -> Titre 3` est refusé ;
4. un document avec tableau à cellules fusionnées est refusé ;
5. un document corrompu est refusé.

---

## 10. Fixtures minimales à prévoir

Le paquet de tests fourni à Codex doit comprendre au minimum :

- `notice_ok_minimal.docx`
- `notice_ok_full.docx`
- `notice_ok_smallcaps.docx`
- `notice_ok_noindent.docx`
- `notice_ok_simple_table.docx`
- `notice_ok_footnotes.docx`
- `notice_warn_empty_paragraphs.docx`
- `notice_warn_mixed_noindent.docx`
- `notice_warn_missing_biblio.docx`
- `notice_bad_missing_title.docx`
- `notice_bad_unknown_style.docx`
- `notice_bad_heading_jump.docx`
- `notice_bad_table_merged_cells.docx`
- `notice_bad_unreadable.docx`

Pour chaque fixture, prévoir autant que possible :

- le rapport de validation attendu ;
- le statut attendu ;
- la TEI attendue pour les cas valides.

---

## 11. Recommandations d’implémentation

### 11.1. Séparer validation et conversion

Même si Pandoc sert au pipeline, il faut distinguer :

- une phase de **validation métier** ;
- une phase de **conversion TEI**.

La conversion ne doit jamais masquer une non-conformité métier.

### 11.2. Préférer des codes de règle stables

Les messages visibles peuvent évoluer, mais les codes internes doivent rester stables pour :

- les tests ;
- le débogage ;
- les futures traductions d’interface.

### 11.3. Éviter les heuristiques agressives en V1

Lorsque la détection n’est pas sûre :

- préférer l’avertissement ;
- éviter les faux positifs bloquants ;
- garder les règles bloquantes pour les cas objectivement identifiables.

---

## 12. Résumé prescriptif

Le validateur de notices doit :

- s’exécuter immédiatement au chargement d’un `.docx` ;
- refuser tout document comportant au moins une erreur bloquante ;
- signaler tout avertissement sans empêcher l’import ;
- produire un rapport stable, structuré et testable ;
- distinguer clairement styles autorisés, styles tolérés, styles interdits et objets interdits ;
- garantir que seule une notice conforme au profil Word défini entre dans la chaîne TEI comme document valide.
