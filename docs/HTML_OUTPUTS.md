# Sorties HTML

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Objet

Les sorties HTML servent à deux usages :

1. prévisualisation locale dans l’interface ;
2. publication statique via ETS Site Builder.

Dans les deux cas, le HTML doit être dérivé de la TEI canonique.

## 2. Prévisualisation rapide

La prévisualisation doit afficher de façon lisible :

- le titre ;
- les crédits disponibles ;
- les actes ;
- les scènes ;
- les personnages présents si disponibles ;
- les locuteurs ;
- les vers ;
- les didascalies ;
- les variantes ;
- les lacunes ;
- les italiques ;
- les strophes si présentes.

## 3. Variantes

Les variantes doivent pouvoir être consultées au survol ou via un dispositif équivalent.

Les infobulles doivent afficher les témoins et, si disponible, leurs années ou descriptions.

Si une année disparaît du tooltip, vérifier d’abord :

- la configuration des témoins ;
- le `teiHeader` ;
- le mapping abréviation → description ;
- la validité du XML.

## 4. Crédits

Ne pas afficher `type: dramatic_TEI` comme crédit public.

Afficher si disponibles :

```text
Éditeur scientifique : ...
Transcripteur : ...
```

Les champs vides sont ignorés.

## 5. Didascalies implicites

Les didascalies implicites peuvent être rendues discrètement mais doivent rester repérables.

Elles ne doivent pas perturber l’alignement du texte dramatique.

## 6. Site statique

Le site statique doit articuler :

- notices ;
- préfaces ;
- dramatis personae ;
- texte dramatique ;
- navigation actes/scènes.

Le rendu dramatique HTML du site ne doit pas réimplémenter une logique différente de la prévisualisation sans raison forte.

## 7. Tests recommandés

Tester au minimum :

- un vers simple ;
- une variante locale ;
- une variante de ligne entière ;
- une lacune ;
- un changement de locuteur ;
- un vers partagé ;
- une didascalie ;
- un tooltip avec année ;
- un bloc de crédits avec éditeur/transcripteur.
