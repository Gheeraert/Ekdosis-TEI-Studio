# Export DTS statique

## Objectif

Ekdosis-TEI Studio ne doit pas devenir un serveur DTS dynamique.

L’objectif est de générer, au moment de la publication du site statique, une couche DTS statique à partir des fichiers TEI déjà produits par ETS.

Cette couche doit permettre à des outils extérieurs de :

- découvrir la collection ;
- parcourir les œuvres ;
- naviguer dans la structure acte / scène / vers ;
- récupérer le document TEI complet et des fragments TEI par acte, scène ou vers.

Le site HTML reste destiné aux lecteurs humains.
La TEI reste le format savant canonique.
DTS est une façade d’interopérabilité, générée automatiquement.

## Principes architecturaux

- Aucun serveur dynamique.
- Aucune base de données.
- Aucune dépendance lourde.
- Aucun moteur de recherche dans cette passe.
- Aucun changement dans les interfaces Tkinter ou Flask.
- Aucun changement dans le protocole de transcription.
- Le DTS statique est une sortie de publication supplémentaire.
- L’export DTS statique est optionnel et désactivé par défaut.
- Le builder permet de l’activer avec l’option « Exporter une couche DTS statique expérimentale ».
- Lorsqu’il est activé, il produit `api/dts/` et `api-dts.html`.
- L’échec de génération DTS pour une pièce ne doit pas faire échouer toute la construction du site : produire un warning.
- Les liens JSON doivent fonctionner lorsque le site est publié dans un sous-répertoire : utiliser des chemins relatifs par défaut et ne pas coder d’URL absolue de déploiement.
- Le slug d’une pièce doit venir du manifest ou de l’objet déjà construit par le site builder. Un slug ne peut être recalculé dans le module DTS que comme fallback explicite.
- Les sorties JSON doivent être déterministes : indentation stable, `ensure_ascii=False`, ordre stable des collections et ordre documentaire stable des nœuds de navigation.

## Niveau visé

Viser une première conformité expérimentale de type DTS Level 0.

La première passe doit seulement produire :

- un point d’entrée DTS ;
- une collection racine ;
- une ressource par pièce ;
- une navigation minimale ;
- un document TEI complet par pièce.

Une extension expérimentale produit également un fragment TEI bien formé pour chaque acte, scène et vers indexé. Un fragment de vers conserve un conteneur `<sp>` réduit au `<speaker>` éventuel et au seul `<l>` demandé.

Ne pas implémenter dans cette première passe :

- recherche plein texte ;
- serveur HTTP dynamique ;
- query parameters complexes ;
- pagination ;
- négociation avancée de mediaType.

## Arborescence cible

Dans le site généré :

```text
site/
  api-dts.html
  api/
    dts/
      index.json
      collection/
        index.json
        <slug>.json
      navigation/
        <slug>/
          index.json
          <ref>.json
      document/
        <slug>/
          full.xml
          <ref>.xml
```

## Correspondance ETS / DTS

Une pièce ETS devient une Resource DTS.

La structure TEI dramatique est interprétée ainsi :

```text
TEI
  text
    body
      div type="act" n="1"
        div type="scene" n="1"
          sp
            l n="1" xml:id="A1S1L1"
```

devient :

```text
Resource : pièce
Navigation niveau 1 : actes
Navigation niveau 2 : scènes
Navigation niveau 3 : vers
```

Les `@xml:id` existants doivent être utilisés lorsqu’ils existent.

Si un acte ou une scène n’a pas de `@xml:id`, construire un identifiant logique à partir de `@n` :

- acte 1 : `A1` ;
- scène 1 de l’acte 1 : `A1S1`.

Dans cette première passe, ne pas modifier les fichiers TEI sources pour ajouter ces identifiants manquants. Cette consolidation pourra faire l’objet d’une passe ultérieure dans le générateur TEI.

## Package à créer

Créer :

```text
src/ets/dts/
  __init__.py
  models.py
  tei_index.py
  jsonld.py
  document_fragments.py
  demo_page.py
  static_export.py
```

## Rôle des fichiers

`models.py` :

- définir des dataclasses simples pour représenter :
  - `DTSResource` ;
  - `DTSNavNode` ;
  - `DTSTeiIndex`.

`tei_index.py` :

- parser une TEI avec lxml ;
- extraire titre, auteur, slug, actes, scènes, vers ;
- ne pas modifier la TEI source ;
- produire un index interne exploitable par `jsonld.py`.

`jsonld.py` :

- produire les dictionnaires JSON-LD correspondant :
  - EntryPoint ;
  - Collection racine ;
  - Resource par pièce ;
  - Navigation.

`static_export.py` :

- écrire les fichiers dans `output_dir/api/dts/` ;
- créer les dossiers nécessaires ;
- écrire du JSON indenté et stable ;
- copier ou sérialiser le TEI complet dans `document/<slug>/full.xml` ;
- garantir que les chemins restent dans `output_dir`.

`document_fragments.py` :

- parser la TEI source sans la modifier ;
- produire une enveloppe TEI minimale pour chaque acte, scène et vers ;
- conserver le contexte minimal `<sp>` et `<speaker>` pour un vers ;
- encoder les références utilisées comme noms de fichiers de la même façon que les fichiers Navigation ;
- écrire les fragments dans `document/<slug>/<ref>.xml`.

`demo_page.py` :

- produire la page statique `api-dts.html` à la racine du site ;
- présenter les points d’entrée DTS et les ressources de chaque pièce ;
- proposer des liens relatifs vers le TEI complet et les premiers fragments acte, scène et vers disponibles ;
- rester autonome, sans JavaScript, appel réseau ou nouvelle dépendance CSS.

## Vérification locale

Un petit outil autonome permet de contrôler un site statique déjà généré :

```bash
python tools/dts_probe.py chemin/vers/site
python tools/dts_probe.py chemin/vers/site --json
```

Le probe lit `api/dts/`, vérifie les fichiers attendus, suit les liens relatifs vers les fragments TEI et contrôle que ces fragments sont des XML bien formés. Il sert à préparer une démonstration DTS ou une discussion technique sur l’export statique, sans créer de serveur ni moteur de recherche.

## Index et page de recherche statiques

L’option `enable_search_index=True` génère :

```text
search/index.json
search.html
```

`search/index.json` contient les vers indexables des pièces, avec le texte normalisé, le locuteur, la référence logique et un lien vers l’ancre HTML du vers dans le site publié.

`search.html` est une page de recherche statique côté navigateur. Elle charge `search/index.json`, filtre localement les résultats et ne nécessite ni serveur, ni dépendance externe. Si `enable_dts=True` est également activé, les résultats exposent aussi les liens vers les fragments TEI DTS et vers la navigation DTS.

## Intégration

Intégrer l’export dans le site builder, après la copie des sources XML.

Ne pas modifier l’interface utilisateur.

La construction génère également `api-dts.html`, page de démonstration destinée à ouvrir facilement les fichiers DTS depuis un navigateur. Cette page rappelle la distinction entre lecture HTML, TEI canonique et interopérabilité DTS.

Ajouter une fonction interne du type :

```python
_export_dts_static(output_root, manifest, warnings)
```

ou équivalent selon l’architecture existante.

En cas d’erreur sur une pièce :

- ajouter un warning lisible de la forme `DTS export skipped for <slug>: <reason>` ;
- continuer la génération du site.

Une erreur DTS isolée ne doit jamais masquer ni remplacer une erreur générale du site builder.

## Tests attendus

Créer :

```text
tests/test_dts_static_export.py
```

Vérifier :

- que `api/dts/index.json` est créé ;
- que `api-dts.html` est créée et contient des liens relatifs vers les sorties DTS ;
- que `api/dts/collection/index.json` est créé ;
- qu’une pièce est exposée comme Resource ;
- que `api/dts/navigation/<slug>/index.json` existe ;
- que la navigation contient au moins les actes et scènes ;
- que `api/dts/document/<slug>/full.xml` existe ;
- que les fragments acte, scène et vers sont des XML bien formés ;
- qu’un fragment de vers ne contient pas les autres vers de la scène ;
- que les liens `document` des unités de navigation pointent vers les fragments ;
- que l’export DTS ne casse pas la génération globale du site ;
- qu’une erreur DTS isolée produit un warning et non un échec global.

## Contraintes

- Pas de FastAPI.
- Pas de BaseX.
- Pas de SaxonC.
- Pas de serveur.
- Pas de moteur de recherche.
- Pas de modification Tkinter.
- Pas de modification Flask.
- Pas de refonte du générateur TEI dans cette première passe.

Important : DTS doit être traité ici comme un format d’export statique, non comme une fonctionnalité serveur. L’architecture doit rester compatible avec l’objectif d’ETS : générer des sites savants publiables par simple dépôt de fichiers.
