# Documentation ancienne — mémoire historique

Ce fichier conserve la mémoire des conventions et comportements de la première version d’Ekdosis-TEI Studio.
Il ne doit pas être utilisé comme spécification prioritaire si les tests, `AGENTS.md` ou `docs/SPEC_V2.md` disent autre chose.

## 1. Statut

La V1 était fonctionnelle et a notamment produit des sorties LaTeX-Ekdosis utiles.
Cependant, son architecture était plus monolithique.

Dans la version actuelle, on peut reprendre de la V1 :

- les exemples fonctionnels ;
- les conventions Ekdosis ;
- les macros qui compilaient ;
- les règles d’échappement LaTeX ;
- les sorties attendues comme fixtures.

On ne doit pas reprendre :

- la génération directe depuis la transcription brute ;
- la confusion entre UI et logique métier ;
- les dépendances implicites ;
- les correctifs tardifs qui masquent une entrée invalide.

## 2. Ancienne syntaxe de base

| Ancien marqueur | Fonction |
|---|---|
| `####n####` | début d’acte |
| `###n###` | début de scène |
| `##NOM##` | personnages présents |
| `#NOM#` | locuteur |
| `**...**` | didascalie |
| `***` | vers partagé |
| `#####` | variante de ligne entière |
| `_..._` | italique |
| `~` | espace insécable |

## 3. Ce qui reste valable

L’esprit général reste valable : permettre une saisie simple, puis produire une édition critique encodée.

La logique d’apparat reste valable :

```text
transcription parallèle des témoins
  → comparaison
  → lemme / lectures
  → apparat critique
```

## 4. Ce qui a changé

La TEI est désormais la source canonique.

Les sorties HTML, site et LaTeX doivent être dérivées de la TEI.

Le validateur d’entrée a été durci : les marqueurs ETS malformés sont des erreurs bloquantes.

Les strophes lyriques et vers métrés ont désormais des conventions spécifiques.

## 5. Utilisation recommandée

Pour un chantier Codex, ce fichier peut servir uniquement à répondre à des questions du type :

- “À quoi ressemblait l’ancienne sortie Ekdosis ?”
- “Quelle macro était utilisée pour tel cas ?”
- “Quelle syntaxe compilait dans la V1 ?”

Il ne doit pas servir à reconstruire l’ancienne architecture.
