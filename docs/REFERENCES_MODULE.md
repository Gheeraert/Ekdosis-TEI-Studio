# Module Références (V1)

## Philosophie

Le module `ets.references` propose un flux éditorial simple pour les notices et commentaires:

- ajouter des références manuellement,
- importer des références (CSL JSON en priorité),
- insérer des citations dans le texte en cours,
- générer automatiquement une bibliographie à partir des références citées,
- choisir un style de publication simple.

L'interface reste non technique: l'utilisateur manipule des actions éditoriales, pas des formats internes.

## Actions UI visibles

Dans l'onglet **Références**:

- `Ajouter une référence`
- `Importer des références`
- `Insérer une citation`
- `Bibliographie`
- `Style de publication`

Les mêmes actions sont exposées dans le menu **Références**.

## Modèle de données

- `ReferenceRecord`: notice bibliographique normalisée (avec `raw_data` + `normalized_data`).
- `CitationOccurrence`: occurrence de citation liée à une référence.
- `BibliographyState`: bibliographie générée pour un style donné.

Cette séparation prépare les évolutions futures (Zotero API, styles plus riches, importeurs supplémentaires).

## Import pris en charge

- V1: **CSL JSON** (robuste, testé).
- BibTeX/RIS: points d'extension déjà prévus, non implémentés dans cette passe.

## Syntaxe interne d'insertion de citation (V1)

Insertion textuelle stable:

`{{CITE:reference_id|locator=p. 143|prefix=voir|suffix=n. 2|mode=note}}`

Cette forme est:

- lisible,
- facile à repérer,
- facilement parseable pour une future conversion TEI/citationnelle plus avancée.

Le parseur accepte les tokens existants et gère aussi les séparateurs `|` échappés (`\|`) dans les valeurs.

## Ciblage éditorial sécurisé (V1)

Dans cette passe de consolidation:

- l'insertion de citation cible uniquement l'éditeur Markdown;
- si aucun contexte Markdown pertinent n'est disponible, l'insertion est refusée avec message clair;
- la bibliographie est calculée à partir du contenu Markdown, pas de la transcription dramatique brute.

## Bibliographie automatique

La bibliographie n'est pas stockée comme un bloc figé:

- les citations sont extraites du texte courant,
- les références effectivement citées sont résolues,
- la liste est régénérée selon le style actif.

## Bloc `:::bibl` et tokens de citation

Comportement V1 consolidé:

- un token `{{CITE:...}}` dans `:::bibl` est rendu en texte lisible (pas en code brut);
- un diagnostic de transition est émis pour signaler que cet usage est déconseillé;
- la bibliographie de référence reste celle générée automatiquement depuis les citations du corps du texte.

## Styles de publication (V1)

Styles simples prédéfinis:

- `default_preview`
- `simple_note`
- `simple_author_date`

Le style est un `style_id` persistant côté service, facilement extensible.

## Limites explicites de V1

Non implémenté dans cette passe:

- synchronisation Zotero API,
- écriture vers Zotero,
- moteur CSL complet,
- dédoublonnage bibliographique avancé,
- logique citationnelle érudite exhaustive.
