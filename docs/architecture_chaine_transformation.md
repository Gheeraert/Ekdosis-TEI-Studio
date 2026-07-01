# Chaîne de transformation Ekdosis-TEI Studio

> Présentation technique — chercheurs et développeurs  
> Fichier généré depuis le dépôt `C:\TEI_Studio_V3`

---

## Vue d'ensemble du pipeline

```
src/ets/core.py:46-77  run_pipeline_from_text()
│
├─ validate_input_text()          src/ets/validation/input_validator.py
├─ parse_play()                   src/ets/parser/text_parser.py
├─ validate_play_structure()      src/ets/validation/structural.py
├─ collate_play()                 src/ets/collation/engine.py
│    └─ classify_apparatus()      src/ets/collation/minor_variants.py
├─ generate_tei_xml()             src/ets/tei/generator.py
│
└─ [sorties]
   ├─ render_html_preview_from_tei()    src/ets/html/transform.py  → tei-vers-html.xsl
   ├─ tei_to_ekdosis()                  src/ets/latex/ekdosis_from_tei.py
   ├─ [PDF]                             src/ets/publication_pdf/
   └─ [DTS]                             src/ets/dts/
```

Point de départ pour toute démonstration : `core.py:46-77` — 32 lignes qui orchestrent la totalité de la chaîne.

```python
def run_pipeline_from_text(input_text, config, *, validate_input=True, ...) -> str:
    castlist_context = load_castlist_context(config, base_dir)
    if validate_input:
        report = validate_input_text(input_text, ...)
        if report.has_errors:
            raise InputValidationError(report.diagnostics)
    parsed   = parse_play(input_text, config)            # → Play
    validate_play_structure(parsed)
    collated = collate_play(parsed, sigla, ref_witness)  # → CollatedPlay
    return generate_tei_xml(collated, config, ...)       # → str TEI
```

---

## Passe 1 — Transcription pseudo-markdown

| | |
|---|---|
| **Rôle** | Ingestion du texte brut encodé par le philologue |
| **Fichiers principaux** | `src/ets/parser/text_parser.py` |
| **Classes / fonctions** | `_split_parallel_blocks()` lignes 20-39 ; regex lignes 7-17 ; `parse_play()` lignes 162-361 ; `_clean_verse_reading()` lignes 62-76 |
| **Tests** | `tests/test_parser_stable.py`, `tests/test_parser_stanzas.py` |

### Extrait de code (`text_parser.py:7-17`)

```python
_ACT_RE           = re.compile(r"^####(.+?)####$")
_SCENE_RE         = re.compile(r"^###(.+?)###$")
_SPEAKER_RE       = re.compile(r"^#(.+?)#$")
_STAGE_RE         = re.compile(r"^\*\*(?!\*)(.+?)(?<!\*)\*\*$")
_IMPLICIT_OPEN_RE = re.compile(r"^\$\$([A-Za-z][A-Za-z0-9_-]*)\$\$$")
_STANZA_OPEN_RE   = re.compile(r"^%%strophe(?:\s+(.+?))?%%$")
_METRICAL_PREFIX_RE = re.compile(r"^=(\d{2})=(.*)$")
```

### Exemple d'entrée (2 témoins)

```
####ACTE I####
####ACTE I####
###Scène première###
###Scène I###
#AGRIPPINE#
#AGRIPINE#
Mais qui vient ?
Mais qui vient?
```

Chaque bloc est séparé par une ligne vide. Un bloc de N lignes correspond à N témoins déclarés dans la configuration.

### Argument oral

La syntaxe pseudo-markdown est volontairement minimaliste — un philologue peut apprendre la notation en 10 minutes. Le parseur n'a pas de dépendances externes : 8 regex, une machine à états, ~350 lignes. C'est auditoriable.

---

## Passe 2 — Validation d'entrée

| | |
|---|---|
| **Rôle** | Détecter les incohérences avant de passer au parseur (fail-fast) |
| **Fichiers principaux** | `src/ets/validation/input_validator.py`, `src/ets/validation/structural.py`, `src/ets/validation/tei_validator.py` |
| **Classes / fonctions** | `ValidationDiagnostic` lignes 17-32 ; `ValidationReport` lignes 34-40 ; `InputValidationError` lignes 43-48 |
| **Tests** | `tests/test_input_validator.py`, `tests/test_parallel_text_strict_validation.py` |

### Extrait de code (`input_validator.py:17-40`)

```python
@dataclass(frozen=True)
class ValidationDiagnostic:
    level: DiagnosticLevel
    code: str
    message: str
    line_number: int | None = None
    block_index: int | None = None
    act: str | None = None
    scene: str | None = None
    speaker: str | None = None
    token_counts: list[int] | None = None   # différence de tokens par témoin

@dataclass(frozen=True)
class ValidationReport:
    diagnostics: list[ValidationDiagnostic]

    @property
    def has_errors(self) -> bool:
        return any(item.level == DiagnosticLevel.ERROR for item in self.diagnostics)
```

### Ce qui est vérifié

- Équilibre des blocs parallèles (N lignes = N témoins)
- Cohérence des marqueurs (`####`, `###`, `#`, `**`, `$$`, `%%`)
- Sigles des témoins reconnus dans la configuration
- Résolution des personnages contre le castlist
- Syntaxe et comptage de lignes des strophes

### Argument oral

La validation est séparée du parseur — le parseur peut supposer que l'entrée est bien formée. Le diagnostic est précis : numéro de bloc, acte, scène, locuteur, comptage de tokens par témoin. Une validation réussie est une précondition explicite, pas une supposition silencieuse.

---

## Passe 3 — Parseur → arbre dramatique

| | |
|---|---|
| **Rôle** | Construire un arbre typé `Play > Act > Scene > Speech > VerseLine` |
| **Fichiers principaux** | `src/ets/domain/model.py` (lignes 33-108), `src/ets/parser/text_parser.py` (lignes 162-361) |
| **Classes / fonctions** | `VerseLine`, `StageDirection`, `ImplicitStageSpan`, `Stanza`, `Speech`, `Scene`, `Act`, `Play` |
| **Tests** | `tests/test_parser_stable.py`, `tests/test_stage_direction.py` |

### Extrait de code (`domain/model.py:33-108`)

```python
@dataclass
class VerseLine:
    number: str
    readings: list[str]       # une lecture par témoin, alignées positionellement
    block_index: int
    whole_line_variant: bool = False
    met: str | None = None

SpeechElement = VerseLine | StageDirection | ImplicitStageSpan | Stanza

@dataclass
class Speech:
    speaker_readings: list[str]
    elements: list[SpeechElement]

    @property
    def verses(self) -> list[VerseLine]:   # aplatit strophes et spans implicites
        verses: list[VerseLine] = []
        for element in self.elements:
            if isinstance(element, VerseLine):
                verses.append(element)
            elif isinstance(element, (ImplicitStageSpan, Stanza)):
                verses.extend(element.lines)
        return verses

@dataclass
class Play:
    acts: list[Act] = field(default_factory=list)
```

### Argument oral

Le modèle de domaine est entièrement immutable sauf les conteneurs racines. Chaque `VerseLine.readings` est une liste positionnelle alignée sur les témoins — c'est la convention que tout le reste du pipeline respecte. Un `Speech` expose ses vers à plat via `.verses` quel que soit l'imbrication interne (strophes, spans implicites).

---

## Passe 4 — Collation → arbre des variantes

| | |
|---|---|
| **Rôle** | Aligner les lectures témoin par témoin au niveau du token et classer chaque variante |
| **Fichiers principaux** | `src/ets/collation/engine.py`, `src/ets/collation/tokenizer.py`, `src/ets/domain/model.py` (lignes 129-227) |
| **Classes / fonctions** | `align_variants_by_token()` lignes 63-92 ; `build_apparatus_from_alignment()` lignes 95-116 ; `collate_play()` ligne 194 ; `ApparatusTokenSegment`, `CollatedText`, `CollatedPlay` |
| **Tests** | `tests/test_collation_tokenizer.py`, `tests/test_collation_columns.py` |

### Extrait de code (`engine.py:63-116`)

```python
def align_variants_by_token(token_matrix, witness_sigla, ref_index):
    for i in range(max_len):           # colonne par colonne
        lemma = CollatedReading(text=token_matrix[ref_index][i], ...)
        readings = [CollatedReading(...) for token in order if token != lemma_token]
        is_literal = len(non_empty_order) == 1
        aligned.append((lemma, readings, is_literal))

def build_apparatus_from_alignment(alignment):
    for lemma, readings, is_literal in alignment:
        if is_literal:
            segments.append(LiteralTokenSegment(text=lemma.text + suffix))
        else:
            classification = classify_apparatus(lemma.text, [r.text for r in readings])
            segments.append(ApparatusTokenSegment(
                lemma=..., readings=...,
                candidate_class=classification.candidate_class,
                visibility_policy=classification.visibility_policy,
                rule_code=classification.rule_code,
            ))
    return CollatedText(segments=segments)
```

### Modèle de données résultant (`domain/model.py:141-160`)

```python
@dataclass(frozen=True)
class ApparatusTokenSegment:
    lemma: CollatedReading
    readings: list[CollatedReading]
    candidate_class: str = "substantive"
    visibility_policy: str = "visible"
    rule_code: str = "substantive_default"

@dataclass(frozen=True)
class CollatedText:
    segments: list[CollatedTokenSegment]   # LiteralTokenSegment | ApparatusTokenSegment
```

### Argument oral

L'alignement est positionnel — pas de CollateX, pas de graphe de variantes. C'est un choix délibéré : pour le théâtre classique en alexandrins, les textes sont déjà syllabiquement contraints et le nombre de tokens par vers est stable. On gagne en déterminisme et en vitesse. La validation du `token_matrix` en amont garantit que le désalignement reste une erreur explicite, pas un résultat silencieusement faux.

---

## Passe 5 — Génération TEI XML

| | |
|---|---|
| **Rôle** | Sérialiser `CollatedPlay` en TEI P5 conforme avec appareil critique token-level |
| **Fichiers principaux** | `src/ets/tei/generator.py`, `src/ets/validation/tei_validator.py` |
| **Classes / fonctions** | `_append_reading()` lignes 35-56 ; `_append_collated_text()` ligne 104 ; `generate_tei_xml()` |
| **Tests** | `tests/test_tei_xml_ids.py`, `tests/test_tei_stanzas.py`, `tests/test_tei_validator.py` |

### Extrait de code (`tei/generator.py:35-56`)

```python
def _append_reading(parent: ET.Element, tag: str, reading: CollatedReading) -> None:
    element = ET.SubElement(parent, _tei(tag), {"wit": _wit_attr(reading.witness_sigla)})
    # _wit_attr(["A","C"]) → "#A #C"
    _append_inline_italics(element, None, reading.text)
    # le soulignement _texte_ devient <hi rend="italic">texte</hi>
```

### Exemple de sortie

```xml
<l n="123">
  Mais qui
  <app>
    <lem wit="#A #C">vient ?</lem>
    <rdg wit="#B" type="minor" subtype="punctuation">vient?</rdg>
  </app>
</l>
```

### Argument oral

Le générateur n'utilise que `xml.etree.ElementTree` de la bibliothèque standard — zéro dépendance externe. Le TEI produit est validé par RelaxNG (`tei_validator.py:62-108`). Le TEI est le format canonique : toutes les autres sorties (HTML, LaTeX, DTS) en dérivent ; on ne revient jamais en arrière vers `CollatedPlay`.

---

## Passe 6 — Transformation HTML via XSLT / preview / site builder

| | |
|---|---|
| **Rôle** | Prévisualisation dans l'éditeur + génération du site statique |
| **Fichiers principaux** | `src/ets/html/transform.py`, `tei-vers-html.xsl` (racine du dépôt), `src/ets/site_builder/builder.py` |
| **Classes / fonctions** | `render_html_preview_from_tei()` lignes 22-28 ; `_load_xslt()` lignes 13-19 |
| **Tests** | `tests/test_html_render.py`, `tests/test_site_builder_realistic_integration.py` |

### Extrait de code (`html/transform.py:13-28`)

```python
@lru_cache(maxsize=4)           # la feuille XSLT est compilée une fois pour toutes
def _load_xslt(xslt_path: str) -> etree.XSLT:
    xslt_doc = etree.parse(str(path))
    return etree.XSLT(xslt_doc)

def render_html_preview_from_tei(tei_xml: str, xslt_path=None) -> str:
    transform = _load_xslt(str(chosen_path.resolve()))
    source_doc = etree.fromstring(tei_xml.encode("utf-8"))
    result = transform(source_doc)
    return etree.tostring(result, encoding="unicode", method="html")
```

### Argument oral

La prévisualisation dans l'éditeur et le site statique utilisent exactement la même feuille XSLT (`tei-vers-html.xsl`). Ce que vous voyez dans l'éditeur est ce qui sera publié — pas deux codebases de rendu à maintenir en synchronisation. Le cache `lru_cache` évite de reparser la feuille XSLT à chaque frappe.

---

## Passe 7 — Transformation LaTeX-Ekdosis

| | |
|---|---|
| **Rôle** | Produire un `.tex` prêt pour `pdflatex` + package `ekdosis` |
| **Fichiers principaux** | `src/ets/latex/ekdosis_from_tei.py`, `src/ets/latex/escaping.py`, `src/ets/latex/templates.py` |
| **Classes / fonctions** | `tei_to_ekdosis()` lignes 36-64 ; `render_ekdosis_witness_declarations_from_root()` lignes 72-80 ; `_RenderContext` lignes 20-33 |
| **Tests** | `tests/test_ekdosis_from_tei.py`, `tests/test_standard_latex_from_tei.py`, `tests/test_castlist_latex_from_tei.py` |

### Extrait de code (`ekdosis_from_tei.py:36-64`)

```python
def tei_to_ekdosis(xml_input, *, standalone=False, apparatus_policy="full") -> str:
    root = _parse_xml_input(xml_input)     # accepte str XML ou Path
    context = _RenderContext(apparatus_policy=apparatus_policy)
    body = root.find(".//tei:text/tei:body", namespaces=NS)
    fragment = "\n".join(
        line for child in body
        for line in _render_block(child, context=context)
    )
    if standalone:
        return wrap_standalone(fragment,
            witness_declarations=render_ekdosis_witness_declarations_from_root(root))
    return fragment
```

### Exemple de sortie

```latex
\DeclareWitness{A}{A}{Première édition, 1670}
\DeclareWitness{B}{B}{Seconde édition, 1676}

\verseline[123]{\app{\lem[wit=A]{Mais qui vient~?}}{\rdg[wit=B]{Mais qui vient~}}}
```

### Argument oral

La transformation part du TEI — pas directement du `CollatedPlay`. C'est intentionnel : le TEI est le format canonique ; LaTeX est une vue. Si le package `ekdosis` évolue, on ne touche qu'à ce module. Le paramètre `apparatus_policy` permet de produire une édition sans apparat (texte seul) ou avec apparat complet.

---

## Passe 8 — Classification et masquage des variantes mineures

| | |
|---|---|
| **Rôle** | Distinguer variantes substantielles et graphiques/orthographiques ; décider de leur visibilité dans le PDF |
| **Fichiers principaux** | `src/ets/collation/minor_variants.py` |
| **Classes / fonctions** | `VariantClassification` lignes 35-56 ; `classify_pair()` lignes 261-328 ; `classify_apparatus()` lignes 358-368 ; `apply_historic_graphic_rules()` lignes 123-249 ; `aggregate_pair_classifications()` lignes 331-355 |
| **Tests** | `tests/test_minor_variants.py`, `tests/test_variant_heads_and_cast.py` |

### Extrait de code — décision de visibilité (`minor_variants.py:35-56`)

```python
@dataclass(frozen=True)
class VariantClassification:
    candidate_class: str      # "substantive", "minor_punctuation", "minor_graphic_safe", ...
    visibility_policy: str    # "hide_safe" | "inspect" | "visible"
    rule_code: str            # "case_only", "historic_graphic_key_identity", ...
    reason: str

    @property
    def is_minor(self) -> bool:
        return self.visibility_policy in {"hide_safe", "inspect"}
```

### Extrait de code — cascade de règles (`minor_variants.py:261-328`)

```python
def classify_pair(left, right) -> VariantClassification:
    if left_norm == right_norm:
        return VariantClassification("identical",          "hide_safe", "literal_identity", ...)
    if left_norm.lower() == right_norm.lower():
        return VariantClassification("minor_case",         "hide_safe", "case_only", ...)
    if remove_spaces_and_hyphens(left) == remove_spaces_and_hyphens(right):
        return VariantClassification("minor_spacing",      "hide_safe", "spacing_or_hyphen_only", ...)
    # ... ponctuation, accent ...
    left_graphic, _ = apply_historic_graphic_rules(left_norm)
    right_graphic, _ = apply_historic_graphic_rules(right_norm)
    if left_graphic == right_graphic:
        return VariantClassification("minor_graphic_safe", "hide_safe", rule_code, ...)
    # Damerau-Levenshtein pour métathèse probable
    if graphic_dam_d == 1 and graphic_lev_d == 2 and graphic_sim >= 0.90:
        return VariantClassification("minor_metathesis_probable", "inspect", "damerau_metathesis", ...)
    return VariantClassification("substantive",            "visible",   "substantive_default", ...)
```

### Normalisation historique (`apply_historic_graphic_rules`, lignes 123-249)

Règles pour le français d'Ancien Régime :

| Règle | Exemple |
|---|---|
| Ligatures, long-s | `œ`→`oe`, `ſ`→`s` |
| Lettres confondues | `j`→`i`, `v`→`u`, `y`→`i` |
| Formes figées | `vostre`→`votre`, `estre`→`etre`, `tousiours`→`toujours` |
| Finales | `-z`/`-x`→`-s`, `t` étymologique avant `s` |
| Consonnes doubles | `tt`→`t`, `ss`→`s` |

### Politiques de visibilité dans le PDF

| `visibility_policy` | Comportement par défaut |
|---|---|
| `hide_safe` | Omis du PDF (opt-in pour le voir) |
| `inspect` | Affiché avec marqueur de confiance basse |
| `visible` | Toujours affiché |

### Argument oral

Ce module est le seul endroit du pipeline qui contient de la logique linguistique. Il est délibérément conservateur : quand on hésite entre `hide_safe` et `inspect`, on choisit `inspect`. Un éditeur peut toujours re-classer manuellement dans le TEI, mais on ne peut pas récupérer une variante qu'on a silencieusement cachée. La liste de normalisations (`vostre`, `estre`, etc.) a été construite et validée sur le corpus *Britannicus*.

---

## Passe 9 — Implémentation DTS

| | |
|---|---|
| **Rôle** | Exposer l'édition via l'API Distributed Text Services (endpoints statiques, navigation, passages, recherche) |
| **Fichiers principaux** | `src/ets/dts/models.py`, `src/ets/dts/tei_index.py`, `src/ets/dts/static_export.py`, `src/ets/dts/jsonld.py`, `src/ets/dts/document_fragments.py`, `src/ets/web/publication_routes.py` |
| **Classes / fonctions** | `DTSNavNode` lignes 7-14 ; `DTSTeiIndex` lignes 25-28 ; `_export_resource()` lignes 34-52 |
| **Tests** | `tests/test_dts_probe.py`, `tests/test_dts_static_export.py` |

### Extrait de code — modèle de navigation (`dts/models.py:7-28`)

```python
@dataclass(frozen=True)
class DTSNavNode:
    identifier: str              # "act1", "act1.scene2"
    cite_type: str               # "act" | "scene" | "line"
    level: int
    parent: str | None
    label: str
    children: tuple["DTSNavNode", ...] = ()

@dataclass(frozen=True)
class DTSTeiIndex:
    resource: DTSResource
    navigation: tuple[DTSNavNode, ...] = ()
```

### Extrait de code — export statique (`static_export.py:34-52`)

```python
def _export_resource(output_root: Path, index: DTSTeiIndex) -> tuple[str, ...]:
    dts_root = Path("api") / "dts"
    _write_json(output_root, dts_root / "collection" / f"{slug}.json",  resource(index))
    _write_json(output_root, dts_root / "navigation" / slug / "index.json", navigation(index))
    for node in _flatten(index):
        _write_json(output_root,
            dts_root / "navigation" / slug / f"{encoded_reference(node.identifier)}.json",
            navigation(index, ref=node.identifier))
    # export des fragments XML par passage
    shutil.copy2(index.resource.source_path, document_target)
    export_document_fragments(output_root, index, safe_target=_safe_target)
```

### Structure des endpoints générés

```
api/dts/collection/{slug}.json          ← métadonnées de la ressource (JSON-LD)
api/dts/navigation/{slug}/index.json    ← arbre complet
api/dts/navigation/{slug}/{ref}.json    ← nœud individuel
api/dts/document/{slug}/full.xml        ← TEI complet
api/dts/document/{slug}/{ref}.xml       ← fragment de passage
```

### Argument oral

L'implémentation DTS est entièrement statique — pas de serveur, pas de base de données. Elle s'héberge sur GitHub Pages ou n'importe quel CDN. Le même `DTSTeiIndex` sert à la fois la navigation dans le site web et les endpoints JSON-LD DTS, ce qui garantit la cohérence entre les deux interfaces.

---

## Synthèse des tests par passe

| Passe | Fichiers de test |
|---|---|
| Pseudo-markdown | `tests/test_parser_stable.py`, `tests/test_parser_stanzas.py` |
| Validation d'entrée | `tests/test_input_validator.py`, `tests/test_parallel_text_strict_validation.py` |
| Arbre dramatique | `tests/test_parser_stable.py`, `tests/test_stage_direction.py` |
| Collation | `tests/test_collation_tokenizer.py`, `tests/test_collation_columns.py` |
| Variantes mineures | `tests/test_minor_variants.py`, `tests/test_variant_heads_and_cast.py` |
| TEI XML | `tests/test_tei_xml_ids.py`, `tests/test_tei_stanzas.py`, `tests/test_tei_validator.py` |
| HTML / XSLT | `tests/test_html_render.py`, `tests/test_site_builder_realistic_integration.py` |
| LaTeX-Ekdosis | `tests/test_ekdosis_from_tei.py`, `tests/test_standard_latex_from_tei.py` |
| DTS | `tests/test_dts_probe.py`, `tests/test_dts_static_export.py` |
| Pipeline bout-en-bout | `tests/test_pipeline_stable.py`, `tests/test_multiscene_integration.py` |

---

## Index des fichiers clés

| Rôle | Chemin |
|---|---|
| Orchestration du pipeline | `src/ets/core.py` |
| Modèle de domaine complet | `src/ets/domain/model.py` |
| Parseur pseudo-markdown | `src/ets/parser/text_parser.py` |
| Validation d'entrée | `src/ets/validation/input_validator.py` |
| Moteur de collation | `src/ets/collation/engine.py` |
| Classification des variantes mineures | `src/ets/collation/minor_variants.py` |
| Génération TEI XML | `src/ets/tei/generator.py` |
| Validation TEI RelaxNG | `src/ets/validation/tei_validator.py` |
| Transformation HTML (XSLT) | `src/ets/html/transform.py` + `tei-vers-html.xsl` |
| Transformation LaTeX-Ekdosis | `src/ets/latex/ekdosis_from_tei.py` |
| Modèles DTS | `src/ets/dts/models.py` |
| Export statique DTS | `src/ets/dts/static_export.py` |
| Services applicatifs | `src/ets/application/services.py` |
| Site builder | `src/ets/site_builder/builder.py` |
| PDF publication | `src/ets/publication_pdf/service.py` |
