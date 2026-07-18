# Fixtures archivées

Ce dossier conserve des fixtures retirées du circuit actif : elles ne sont
référencées par aucun test et ne correspondent plus à la syntaxe ETS ou aux
conventions actuelles. Elles sont gardées comme mémoire du projet et comme
matériau de comparaison, conformément à la règle « le code hérité peut servir
de référence, jamais de modèle d'architecture » (AGENTS.md).

Aucun test ne doit dépendre de ce dossier. Pour les cas de référence actifs,
voir `fixtures/stable/` ; pour les cas limites connus, voir
`fixtures/known_issues/`.

## Contenu

### `andromaque_1_1/` — archivé le 18 juillet 2026

Révision antérieure du cas stable *Andromaque*, Acte I, Scène 1
(`fixtures/stable/input.txt` + `config.json` + `expected.xml`), dont le
`notes.md` est identique mot pour mot à celui de `fixtures/stable/`.

Motif d'archivage : la transcription utilise l'ancien marqueur de variante de
ligne entière à **six** dièses (`######…`), rejeté par le validateur actuel
(`E_HASH_MARKER_MALFORMED`) — la syntaxe en vigueur est `#####…`. Le fichier
`expected.xml` correspond à une sortie du moteur antérieure et ne reflète plus
la TEI générée aujourd'hui. La version corrigée et active de ce même cas vit à
la racine de `fixtures/stable/`.

### `britannicus_I.txt` — archivé le 18 juillet 2026

Copie orpheline de la transcription *Britannicus*, Acte I (5 témoins),
anciennement située à `tests/britannicus_I.txt` et référencée par aucun test.

Ne pas confondre avec `fixtures/stable/britannicus_I.txt` (version légèrement
différente, toujours active) : cette dernière est utilisée **délibérément comme
entrée invalide** par les tests de chemins d'erreur
(`test_input_validator.py`, `test_application_services.py`), qui la combinent
avec une configuration à nombre de témoins incompatible pour vérifier les
diagnostics `E_BLOCK_SIZE`.
