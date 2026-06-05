# SPEC_V2.md — spécification fonctionnelle actuelle

Dernière mise à jour documentaire : 5 juin 2026.

Ce fichier conserve son nom historique `SPEC_V2.md` pour ne pas casser les références existantes, mais il décrit l’état cible actuel du projet.

## 1. Objet

Ekdosis-TEI Studio transforme une transcription ETS en TEI canonique, puis dérive différents rendus et exports de cette TEI.

Le système doit rester modulaire, testable et utilisable par des éditeurs non techniciens.

## 2. Principe cardinal

La TEI est la source canonique des sorties éditoriales.

```text
ETS transcription
  → validation
  → parsing
  → modèle interne
  → collation
  → TEI canonique
  → HTML / site / LaTeX
```

Aucune sortie de publication ne doit reconstituer sa propre logique éditoriale à partir du texte brut si la TEI contient déjà l’information nécessaire.

## 3. Couches du système

Les responsabilités doivent rester séparées :

| Couche | Rôle |
|---|---|
| validation | refuser le pseudo-markdown ETS invalide |
| parser | transformer les lignes en structures dramatiques |
| domain | représenter les objets éditoriaux internes |
| collation | comparer les témoins et produire les variantes |
| TEI | générer la représentation canonique |
| HTML | prévisualiser ou publier depuis la TEI |
| site builder | construire un site statique complet |
| notice import | convertir des notices Word/Pandoc vers TEI |
| annotations | gérer les notes éditoriales |
| références | gérer citations et bibliographie |
| LaTeX | produire les sorties imprimées depuis la TEI |
| UI Tk | orchestrer les services sans logique métier lourde |

## 4. Syntaxe ETS supportée

Le validateur et le parseur doivent traiter au minimum :

```text
####...####                  actes
###...###                    scènes
##...##                      personnages présents
#...#                        locuteurs
**...**                      didascalies explicites
***                          segments de vers partagés
#####...                     variantes de ligne entière
##### (lacune)               lacunes
_..._                        italiques
~                            espace insécable ou retrait manuel
$$TYPE$$ ... $$fin$$         didascalies implicites
%%strophe ...%%              strophes lyriques
%%fin_strophe%%              fin de strophe
=02= à =12=                  indication métrique en strophe
```

## 5. Validation d’entrée

Le validateur est bloquant.

Il ne corrige pas silencieusement la transcription.
Il empêche une entrée malade de parvenir à la génération TEI.

Règles importantes :

- `#` est réservé au balisage ETS ;
- tout `#` isolé ou mal équilibré est invalide ;
- les formes `NOM#`, `######foo`, `##### foo#bar` sont invalides ;
- `#####=12=...` est valide en contexte métrique ;
- `=12=#####...` est invalide ;
- `#####=12=(lacune)` est valide ;
- un marqueur de strophe doit être fermé ;
- les bornes de didascalie implicite doivent être équilibrées.

Les diagnostics doivent être clairs, localisables et exploitables dans l’interface.

## 6. TEI dramatique cible

La TEI doit représenter :

- le titre et les métadonnées ;
- les témoins ;
- l’éditeur scientifique et le transcripteur si renseignés ;
- les actes et scènes ;
- les personnages présents ;
- les locuteurs ;
- les vers ;
- les vers partagés ;
- les didascalies explicites ;
- les didascalies implicites ;
- les variantes ;
- les lacunes ;
- les italiques ;
- les espaces insécables ;
- les strophes et mètres.

Les variantes doivent être représentées par :

```xml
<app>
  <lem wit="#A">...</lem>
  <rdg wit="#B #C">...</rdg>
</app>
```

Les vers partagés doivent tendre vers une représentation TEI naturelle : fragments de `<l>` avec même numéro de vers et attribut `@part` quand c’est nécessaire.

## 7. Strophes lyriques

Hors strophe, l’alexandrin ordinaire n’est pas marqué `=12=`.

Dans une strophe lyrique :

- ouverture par `%%strophe ...%%` ;
- fermeture par `%%fin_strophe%%` ;
- tous les vers portent un mètre explicite ;
- `subtype` devient `@subtype` ;
- `rhyme` devient `@rhyme` ;
- la TEI cible utilise `<lg type="stanza">` et `<l met="...">`.

Exemple cible :

```xml
<lg type="stanza" subtype="distique" rhyme="aa">
  <l met="12">...</l>
  <l met="10">...</l>
</lg>
```

## 8. HTML

La prévisualisation HTML et le site statique doivent consommer la TEI.

Le rendu HTML doit préserver :

- structure acte/scène ;
- locuteurs ;
- numéros de vers ;
- didascalies ;
- variantes au survol ou autre dispositif lisible ;
- dates ou descriptions de témoins si disponibles ;
- notices et péritextes quand ils existent.

## 9. Site builder

Le site builder assemble des dossiers éditoriaux par pièce :

1. notice savante ;
2. préfaces ou péritextes ;
3. dramatis personae ;
4. texte dramatique ;
5. actes et scènes.

Il doit produire un site statique déterministe, sans dépendance à un serveur lourd.

## 10. Notices et péritextes

Les notices issues de Word/Pandoc forment une TEI de prose savante.

Elles sont distinctes du texte dramatique.
Elles peuvent être publiées en HTML et exportées en LaTeX standard.

## 11. LaTeX

Il existe deux sorties LaTeX :

1. TEI dramatique → LaTeX-Ekdosis ;
2. TEI de prose savante → LaTeX standard.

Ces sorties sont ensuite réunies dans une couche PURH.

Voir `docs/LATEX_EXPORTS.md`.

## 12. Interface Tk

L’interface Tkinter doit rester une couche d’orchestration :

- ouvrir/enregistrer ;
- gérer la configuration ;
- lancer validation, TEI, HTML, site, exports ;
- afficher diagnostics et sorties ;
- proposer des boîtes de dialogue simples.

Elle ne doit pas contenir de logique éditoriale profonde.

## 13. Tests

Les tests doivent couvrir :

- validation d’entrée ;
- parsing ;
- collation ;
- génération TEI ;
- strophes ;
- vers partagés ;
- didascalies implicites ;
- HTML ;
- site builder ;
- notices ;
- UI ;
- futurs exports LaTeX.

Tout nouveau chantier doit commencer par des fixtures minimales, puis être vérifié sur des fixtures réalistes.
