# CODEX_TASKLIST_NOTICE_IMPORT.md

## 1. Objet

Ce document fournit à Codex une feuille de route d’implémentation pour le module d’import des **notices Word** dans Ekdosis–TEI Studio (ETS).

Il complète :

- `NOTICES_CHAIN_SPEC.md`
- `WORD_STYLES_MAPPING.md`
- `NOTICES_VALIDATION_RULES.md`
- `NOTICES_TEI_TARGET.md`

Il ne traite **que** des notices, pas des pièces de théâtre.

---

## 2. Résultat attendu

Mettre en place un module **interne et invisible pour l’utilisateur** qui permette de :

1. charger un fichier `.docx` depuis l’interface ETS ;
2. valider immédiatement sa conformité au profil Word défini ;
3. produire un rapport de validation lisible ;
4. refuser l’import si le document est invalide ;
5. convertir le document valide en XML-TEI selon la cible fixée ;
6. transmettre le XML généré à la couche existante d’affichage / édition.

---

## 3. Contraintes à respecter absolument

### 3.1. Visibilité utilisateur

L’utilisateur ne doit pas voir :

- Pandoc ;
- les filtres ;
- les étapes intermédiaires ;
- une logique séparée nommée « conversion notice ».

Pour l’utilisateur, le flux doit rester :

- choisir un `.docx` ;
- recevoir immédiatement un diagnostic ;
- voir apparaître un XML si tout est conforme.

### 3.2. Contrat de validation

Aucun document invalide ne doit être importé silencieusement.

Le diagnostic doit être produit **dès le chargement**.

### 3.3. Stabilité

L’implémentation doit être :

- modulaire ;
- testable ;
- déterministe ;
- sans logique métier enfouie dans l’interface.

---

## 4. Architecture recommandée

Créer un sous-package dédié, par exemple :

```text
src/ets/notice_import/
```

avec au minimum :

```text
src/ets/notice_import/__init__.py
src/ets/notice_import/models.py
src/ets/notice_import/style_registry.py
src/ets/notice_import/pandoc_bridge.py
src/ets/notice_import/validator.py
src/ets/notice_import/tei_builder.py
src/ets/notice_import/reporting.py
src/ets/notice_import/service.py
```

### Rôle des modules

`models.py`
- dataclasses ou structures de données pour les diagnostics, règles, résultats de validation, fragments intermédiaires, etc.

`style_registry.py`
- table canonique des styles Word acceptés ;
- équivalences FR/EN ;
- catégorie interne de chaque style.

`pandoc_bridge.py`
- encapsulation de l’appel à Pandoc ;
- lecture du `docx` ;
- récupération d’un format intermédiaire exploitable.

`validator.py`
- application des règles décrites dans `NOTICES_VALIDATION_RULES.md`.

`tei_builder.py`
- conversion vers la TEI cible décrite dans `NOTICES_TEI_TARGET.md`.

`reporting.py`
- formatage du rapport de validation pour l’interface.

`service.py`
- point d’entrée orchestral utilisé par l’UI :
  - charger ;
  - valider ;
  - convertir ;
  - renvoyer résultat + diagnostics.

---

## 5. Ordre de travail recommandé

## Étape 1 — Définir les modèles internes

Créer les structures internes minimales.

### À produire

- `ValidationSeverity` (`ERROR`, `WARNING`)
- `ValidationStatus` (`VALID`, `VALID_WITH_WARNINGS`, `INVALID`)
- `ValidationMessage`
- `ValidationReport`
- `NoticeImportResult`
- catégories internes de styles, par exemple :
  - `TITLE_MAIN`
  - `TITLE_SUB`
  - `HEADING_1`
  - `HEADING_2`
  - `HEADING_3`
  - `HEADING_4`
  - `PARAGRAPH`
  - `PARAGRAPH_NOINDENT`
  - `QUOTE_PARAGRAPH`
  - `CAPTION`

### Critères d’acceptation

- typage clair ;
- sérialisation simple si besoin ;
- aucune dépendance UI.

---

## Étape 2 — Établir le registre des styles Word

Implémenter la table canonique décrite dans `WORD_STYLES_MAPPING.md`.

### À produire

Une table centralisée qui associe :

- nom Word observé ;
- éventuel alias ;
- catégorie interne ;
- statut ;
- remarque métier.

### Exigences

Le registre doit reconnaître au minimum :

- `Titre` / `Title`
- `Sous-titre` / `Subtitle`
- `Titre 1` / `Heading 1`
- `Titre 2` / `Heading 2`
- `Titre 3` / `Heading 3`
- `Titre 4` / `Heading 4`
- `Normal`
- style natif sans retrait retenu
- `Citation` / `Quote`
- `Légende` / `Caption`

### Critères d’acceptation

- une fonction de normalisation type `normalize_style_name()` ;
- une fonction de résolution type `resolve_style_category()` ;
- comportement documenté pour style inconnu.

---

## Étape 3 — Mettre en place le pont Pandoc

Implémenter un adaptateur unique pour Pandoc.

### Objectif

Lire un `.docx` stylé et obtenir un format intermédiaire exploitable par le validateur et le convertisseur.

### Recommandation

Commencer avec une sortie intermédiaire simple à inspecter (`json` Pandoc ou équivalent stable), plutôt que de coupler d’emblée toute l’implémentation à un writer TEI.

### À produire

- fonction ou classe : `load_docx_via_pandoc(path)`
- gestion propre des erreurs système :
  - Pandoc absent ;
  - erreur de lecture ;
  - docx corrompu.

### Critères d’acceptation

- erreurs encapsulées proprement ;
- aucune fuite technique brute vers l’UI ;
- test automatisé sur un fichier minimal valide.

---

## Étape 4 — Implémenter la validation

Appliquer systématiquement les règles de `NOTICES_VALIDATION_RULES.md`.

### Règles à implémenter en priorité

#### Erreurs bloquantes
- absence de titre principal ;
- style de paragraphe non autorisé ;
- saut de niveau interdit dans la hiérarchie des titres ;
- tableau non conforme à la définition V1 ;
- objet Word interdit si détectable ;
- structure manifestement non importable.

#### Avertissements
- paragraphes vides parasites ;
- alternance incohérente entre paragraphe standard et sans retrait ;
- usage excessif de mise en forme directe ;
- absence de rubrique bibliographique ;
- styles tolérés non recommandés si activés.

### À produire

- `validate_notice_document(intermediate_doc) -> ValidationReport`

### Critères d’acceptation

- rapport stable et testable ;
- messages munis d’un code de règle ;
- sévérité explicite ;
- localisation du problème quand possible.

---

## Étape 5 — Produire le rapport pour l’interface

Transformer le rapport brut en un objet ou format d’affichage UI.

### Objectif

Permettre à ETS d’afficher immédiatement :

- statut global ;
- nombre d’erreurs ;
- nombre d’avertissements ;
- détail lisible.

### Exemple de rendu attendu

- `Import refusé` — 2 erreurs, 1 avertissement
- `Import conforme avec avertissements` — 0 erreur, 3 avertissements
- `Import conforme` — aucun problème détecté

### Critères d’acceptation

- formulation claire ;
- pas de jargon Pandoc ;
- pas de stack trace ;
- détails suffisamment précis pour corriger le `.docx`.

---

## Étape 6 — Construire la TEI cible

Implémenter la conversion XML selon `NOTICES_TEI_TARGET.md`.

### Éléments à produire obligatoirement

- `<TEI xmlns="http://www.tei-c.org/ns/1.0">`
- `<teiHeader>` minimal
- `<text>`
- `<body>`
- `<div type="notice" xml:id="...">`
- `<head type="main">`
- éventuellement `<head type="sub">`
- `div` imbriqués pour les niveaux 1 à 4
- `<p>`
- `<p rend="noindent">`
- `<quote><p>...</p></quote>`
- `<list>` / `<item>`
- `<note place="foot">`
- `<table>` simple
- `<hi rend="italic|bold|smallcaps|sup|sub">`
- `<listBibl>` / `<bibl>` quand la rubrique bibliographique est détectée

### Règles impératives

- sortie déterministe ;
- pas d’éléments TEI improvisés ;
- pas d’encodages avancés hors spec ;
- exactement un `div type="notice"` racine dans le corps.

---

## Étape 7 — Orchestration du service d’import

Créer un service unique utilisé par l’interface.

### Signature indicative

```python
result = import_notice_docx(path)
```

avec un résultat contenant au minimum :

- statut global ;
- rapport de validation ;
- XML TEI si import autorisé ;
- erreur système éventuelle si la chaîne échoue avant validation métier.

### Contrat impératif

- si `INVALID` : pas de XML importé comme résultat valide ;
- si `VALID` ou `VALID_WITH_WARNINGS` : XML TEI disponible.

---

## Étape 8 — Intégration à l’interface ETS

Raccorder le service à l’interface existante.

### Objectif

Quand l’utilisateur charge un `.docx` de notice :

1. ETS appelle le service ;
2. ETS affiche immédiatement le rapport ;
3. ETS n’affiche le XML que si l’import est accepté.

### Exigences

- aucune logique métier de validation dans la couche UI ;
- l’UI ne fait qu’orchestrer l’appel et afficher le résultat.

---

## 6. Tests à implémenter

Créer un sous-ensemble de tests dédié, par exemple :

```text
tests/notice_import/
```

avec au minimum :

```text
tests/notice_import/test_style_registry.py
tests/notice_import/test_validator.py
tests/notice_import/test_tei_builder.py
tests/notice_import/test_service.py
tests/notice_import/test_integration_notice_import.py
```

### Fixtures minimales attendues

Créer un dossier par exemple :

```text
tests/fixtures/notice_import/
```

avec au minimum :

- `notice_ok_minimal.docx`
- `notice_ok_full.docx`
- `notice_ok_smallcaps.docx`
- `notice_ok_noindent.docx`
- `notice_ok_biblio.docx`
- `notice_bad_unknown_style.docx`
- `notice_bad_heading_jump.docx`
- `notice_bad_table_merged_cells.docx`
- `notice_warn_empty_paragraphs.docx`

Et, si possible, pour chacun :

- XML attendu ;
- rapport de validation attendu.

---

## 7. Priorités de développement

Ordre de priorité recommandé :

1. style registry ;
2. modèles internes ;
3. pont Pandoc ;
4. validation ;
5. reporting ;
6. génération TEI ;
7. service d’orchestration ;
8. intégration UI.

La priorité absolue est la **validation immédiate et fiable**.

---

## 8. Critères d’acceptation globaux

Le ticket peut être considéré comme terminé si :

1. un `.docx` conforme est importé et converti en TEI stable ;
2. un `.docx` invalide est refusé avec diagnostic lisible ;
3. les petites capitales sont conservées comme `<hi rend="smallcaps">` ;
4. le style sans retrait produit `<p rend="noindent">` ;
5. les titres 1 à 4 produisent la hiérarchie TEI attendue ;
6. les tableaux simples passent ;
7. les tableaux hors profil V1 sont refusés ;
8. les tests automatisés couvrent les cas nominaux et les principaux cas d’échec.

---

## 9. Anti-objectifs

L’implémentation ne doit pas :

- refondre l’architecture générale d’ETS ;
- injecter la logique métier dans la couche UI ;
- improviser une TEI plus riche que la cible fixée ;
- élargir silencieusement le profil Word supporté ;
- chercher à traiter les pièces via cette chaîne.

---

## 10. Consigne finale à Codex

Implémenter un module d’import de notices **sobre, robuste, modulaire et test-driven**, conforme aux spécifications documentées, avec validation immédiate au chargement, refus des imports invalides, et production d’une TEI stable pour les documents conformes.
