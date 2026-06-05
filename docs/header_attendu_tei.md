# En-tête TEI et crédits de prévisualisation

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Deux niveaux à distinguer

ETS doit distinguer :

1. le vrai `teiHeader`, qui appartient à la TEI canonique ;
2. les blocs de crédits affichés dans les sorties HTML ou LaTeX.

Ne pas confondre les deux.

## 2. Métadonnées éditoriales importantes

La configuration peut contenir notamment :

- titre de l’œuvre ;
- acte ou scène courante ;
- auteur ;
- éditeur scientifique ;
- transcripteur ;
- témoins ;
- année ou description des témoins ;
- témoin de référence.

L’éditeur scientifique et le transcripteur sont facultatifs.
S’ils sont vides, les sorties ne doivent pas afficher de ligne vide.

## 3. Bloc de crédits attendu dans les rendus

Dans le bloc de crédits visible, ne plus afficher `type: dramatic_TEI`.

Afficher plutôt, si les champs existent :

```text
Éditeur scientifique : Prénom Nom
Transcripteur : Prénom Nom
```

Si l’un des champs est absent ou vide, ne rien afficher pour ce champ.

## 4. Témoins

Les identifiants de témoins doivent rester stables et cohérents entre :

- TEI ;
- HTML ;
- infobulles ;
- futurs exports LaTeX-Ekdosis.

Dans la TEI, les témoins sont typiquement référencés par `#A`, `#B`, etc.

Dans Ekdosis, ces témoins seront probablement rendus sous la forme `A`, `B`, etc., dans `wit={...}`.

## 5. Règle de prudence

Toute modification du header ou des crédits doit être testée sur :

- une configuration avec éditeur scientifique seul ;
- une configuration avec transcripteur seul ;
- une configuration avec les deux ;
- une configuration avec les deux champs vides.
