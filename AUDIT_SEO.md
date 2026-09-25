# Audit SEO — corrections apportées

Ce rapport documente un audit externe (Codex) portant **exclusivement sur la couche SEO** ajoutée sur la branche `SEO` (sitemap, robots.txt, meta description, canonical, Open Graph/Twitter Card, JSON-LD, exposition du schéma ODD, intégration Tkinter et web), et les corrections qui en ont découlé.

Ce document ne couvre pas l'ensemble du projet Ekdosis-TEI Studio, seulement le périmètre SEO livré sur cette branche.

## Contexte

Après l'implémentation complète de la couche SEO (phases 1 à 8, voir l'historique Git de la branche `SEO`), un audit indépendant a été demandé à Codex avant toute fusion vers `main`. L'audit a porté sur :

- la sécurité (injection),
- l'exactitude des sorties générées (sitemap, robots.txt, canonical, Open Graph, JSON-LD),
- la cohérence avec la couche DTS existante,
- l'intégration aux deux interfaces de publication (Tkinter et web).

## Verdict de l'audit

> « La branche SEO constitue une bonne base, mais je déconseille sa fusion en production en l'état. Elle est fonctionnelle dans les scénarios nominaux et bien testée, mais comporte un risque XSS, deux défauts d'URL/robots importants, une intégration DTS discutable et une intégration incomplète avec l'interface web. »

Six problèmes ont été identifiés, tous vérifiés ligne par ligne contre le code réel avant correction (aucun faux positif détecté).

## Problèmes identifiés et corrections

### 1. [P1 — sécurité] Injection XSS possible dans le JSON-LD

**Constat.** Dans `src/ets/seo/structured_data.py`, la protection contre l'injection dans le `<script type="application/ld+json">` ne neutralisait que la séquence `</script` en minuscules. Or le parseur HTML ferme une balise `<script>` sur n'importe quelle casse (`</SCRIPT>`, `</ScRiPt>`, etc.), indépendamment de son attribut `type`. Un titre de pièce contenant une telle séquence pouvait fermer le bloc JSON-LD puis injecter un script exécutable.

**Correction.** Remplacement du remplacement sensible à la casse par un échappement systématique de `<`, `>` et `&` en séquences Unicode JSON (`<`, `>`, `&`), sur le modèle du filtre `json_script` de Django. Un test dédié rejoue l'injection à travers un vrai parseur HTML (`lxml`) et vérifie qu'un seul nœud `<script>` légitime existe dans le DOM résultant, plutôt que de se fier à une simple comparaison de sous-chaîne.

### 2. [P1 — exactitude/sécurité] Validation insuffisante de l'URL publique du site

**Constat.** `normalize_base_url` (`src/ets/seo/urls.py`) ne vérifiait que le schéma et le nom d'hôte. Étaient donc acceptées des URLs comme `https://example.org/site#fragment`, `https://example.org/site?preview=1` ou `https://user:secret@example.org/site`. Ce texte brut était ensuite concaténé dans toutes les URLs canoniques, Open Graph et du sitemap — un fragment cassait silencieusement la cible des URLs canoniques, des identifiants embarqués se retrouvaient publiés sur chaque page.

**Correction.** `normalize_base_url` rejette désormais explicitement une query string, un fragment et des identifiants utilisateur, et reconstruit l'URL depuis ses composants validés (`scheme`/`host`/`port`/`path`) plutôt que de conserver le texte brut d'origine. L'hôte est également normalisé en minuscules.

### 3. [P1 — fonctionnalité] `robots.txt` ne fonctionne pas pour un site publié sous un sous-répertoire

**Constat.** Deux défauts cumulés :
- Les règles `Disallow` générées (`src/ets/seo/robots.py`) ciblaient des chemins absolus depuis la racine du domaine (`/xml/`) sans tenir compte d'une `site_base_url` avec sous-chemin (ex. `https://example.org/corpus`), les rendant sans effet réel une fois le fichier publié sous `/corpus/`.
- Plus fondamentalement, un `robots.txt` publié à `https://example.org/corpus/robots.txt` n'est **jamais lu** par les robots, qui ne consultent que `/robots.txt` à la racine de l'hôte. Ce cas est particulièrement fréquent pour les hébergements institutionnels et GitHub Pages sous préfixe.

**Correction.** Les règles `Disallow` sont désormais préfixées par le chemin de `site_base_url` (`/corpus/xml/` au lieu de `/xml/`). Le site builder ajoute en complément un avertissement explicite dans les résultats de build lorsque le site est publié sous un sous-répertoire, expliquant que ce fichier doit être installé manuellement à la racine du nom de domaine pour être pris en compte.

### 4. [P2 — DTS] Lien vers le schéma ODD potentiellement cassé et mal placé

**Constat.** Deux sous-problèmes :
- `export_dts_static()`, API publique du module DTS, ne copie pas elle-même le fichier ODD (seul le site builder le fait, via `_copy_tei_profile_resources`, avant d'appeler cette fonction). Un appel direct à `export_dts_static()` en dehors du site builder produisait donc un pointeur `conformsTo` vers un fichier potentiellement inexistant.
- Sur le plan sémantique, l'ODD décrit les documents TEI, pas le service DTS lui-même ; le porter au niveau du point d'entrée (`EntryPoint`) plutôt que par ressource (`Resource`) ne correspond pas aux conventions de métadonnées de la spécification DTS 1.0.

**Correction.** Le pointeur est retiré du `EntryPoint` (`api/dts/index.json`) et porté par `dublinCore.conformsTo` sur chaque `Resource` (vue individuelle, vue de collection racine, vue embarquée dans la navigation), cohérent avec `dublinCore.creator` déjà utilisé pour l'auteur. `export_dts_static()` n'émet plus ce pointeur par défaut : un nouveau paramètre explicite `include_odd_reference=True` doit être passé par l'appelant qui garantit que l'ODD est réellement publié à côté — le site builder l'active car cette garantie est vérifiée par son ordre d'appel interne.

### 5. [P2 — intégration] Couche SEO inaccessible depuis l'interface web

**Constat.** La phase d'intégration à l'interface utilisateur n'avait couvert que la boîte de dialogue Tkinter. Le formulaire web (`/publish/builder`) et ses quatre points de construction de configuration (génération du site, export JSON, export du paquet source, import du paquet source) ignoraient entièrement `site_base_url`. Ce n'était pas une régression, mais la fonctionnalité restait incompatible avec la voie de publication web du programme.

**Correction.** Ajout d'une case à cocher « Publier une couche SEO » et d'un champ URL publique dans `builder.html`, sur le même patron que la boîte de dialogue Tkinter (case = seule source de vérité ; décochée, une URL tapée est ignorée). Câblage dans les quatre routes Flask concernées, pré-remplissage du formulaire dans les trois chemins de rechargement de configuration côté JavaScript, et avertissement dynamique identique à celui de Tkinter quand la case est cochée sans URL renseignée.

### 6. [P2 — efficacité SEO] Commentaire trompeur sur la garantie offerte par `robots.txt`

**Constat.** Le commentaire accompagnant les règles `Disallow` par défaut affirmait qu'elles évitaient de « diluer les résultats de recherche ». C'est inexact : Google indique explicitement qu'une URL interdite au crawl peut malgré tout apparaître dans les résultats de recherche, sans extrait ni contenu — `robots.txt` n'est pas un mécanisme de non-indexation.

**Correction.** Corrigé en traitant le point 3 (même bloc de code) : le commentaire précise désormais que `Disallow` économise le budget de crawl sur du contenu quasi dupliqué, sans garantir l'absence d'indexation.

## Résultat

- Suite de tests complète : 1100 tests passent (1 skip préexistant sans rapport avec ce périmètre).
- `git diff --check` propre, aucun mojibake détecté.
- Chaque correction est accompagnée de tests dédiés, dont un test d'intégration avec un vrai parseur HTML pour la correction XSS et des tests bout-en-bout pour la cohérence des chemins relatifs DTS.

## Portée non couverte par cette passe

L'audit notait que l'exécution de `tests/web/` avait échoué dans son environnement faute de Flask installé — dans l'environnement utilisé pour ces corrections, Flask est disponible et l'intégralité de `tests/web/` passe ; aucune action n'était donc nécessaire de ce côté.
