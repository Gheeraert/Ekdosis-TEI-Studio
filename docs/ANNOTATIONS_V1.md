# ANNOTATIONS_V1.md

## 1. Purpose

This document defines the first implementation scope for **editorial annotations** in Ekdosis TEI Studio v2.

These annotations are scholarly notes added by editors to the edited text.
They are not part of the witness transcription itself and must not interfere with parsing, tokenization, or collation.

The goal of this first version is to provide a simple, robust, testable annotation layer that can:

- store editorial notes separately from `input.txt`
- attach notes to stable dramatic locations
- inject notes into generated TEI
- render those notes in HTML outputs
- remain compatible with the current core-first architecture

## 2. Core principle

Editorial annotations must remain a **separate editorial layer**.

Therefore:

- do **not** add note syntax inside `input.txt`
- do **not** modify tokenization rules to support notes
- do **not** mix notes into witness collation
- do **not** attach notes to raw character offsets in the source text

Instead:

- keep `input.txt` for parallel witness transcription
- keep `config.json` for edition parameters
- add a separate `annotations.json` file for editorial notes

## 3. Scope of V1

### 3.1 In scope

This first version supports:

- note attached to a **single verse line**
- note attached to a **range of consecutive verse lines**
- note attached to a **full explicit stage direction**
- loading and saving annotation files
- simple creation / update / deletion workflows
- TEI enrichment after TEI generation
- basic HTML rendering of note calls and note contents

### 3.2 Out of scope

The following are explicitly out of scope for V1:

- note attached to a single word or phrase inside a verse
- note attached directly to `<app>`, `<lem>`, or `<rdg>`
- note authoring inside `input.txt`
- note anchoring by text selection offsets in the raw source editor
- collaborative multi-user editing
- annotation history / versioning
- LaTeX / ekdosis export of notes

## 4. Anchoring model

Annotations must rely on **stable editorial anchors**, not on fragile source offsets.

### 4.1 Anchor kinds

V1 supports three anchor kinds:

#### `line`

A note attached to one verse line.

Example:

```json
{
  "kind": "line",
  "act": "1",
  "scene": "1",
  "line": "42"
}
```

#### `line_range`

A note attached to a continuous range of verse lines.

Example:

```json
{
  "kind": "line_range",
  "act": "1",
  "scene": "1",
  "start_line": "42",
  "end_line": "44"
}
```

#### `stage`

A note attached to one explicit stage direction.

Example:

```json
{
  "kind": "stage",
  "act": "1",
  "scene": "1",
  "stage_index": 2
}
```

### 4.2 Stability rule

Anchors must target editorially meaningful locations such as:

- act number
- scene number
- line number
- stage direction order index

They must not depend on raw character position in the input text.

## 5. Storage format

Annotations must be stored in a separate JSON file, for example `annotations.json`.

Example:

```json
{
  "version": 1,
  "annotations": [
    {
      "id": "n1",
      "type": "explicative",
      "anchor": {
        "kind": "line",
        "act": "1",
        "scene": "1",
        "line": "42"
      },
      "content": "Allusion possible à la pompe triomphale romaine.",
      "resp": "TG",
      "status": "draft",
      "keywords": ["Rome", "lexique politique"]
    }
  ]
}
```

## 6. Data model

A dedicated annotation layer should be introduced, for example under:

```text
src/ets/annotations/
```

Suggested structure:

```text
src/ets/annotations/
  __init__.py
  models.py
  store.py
  service.py
  tei.py
```

Suggested domain objects:

- `AnnotationAnchor`
- `Annotation`
- `AnnotationCollection`

Suggested controlled values:

- annotation types:
  - `explicative`
  - `lexicale`
  - `intertextuelle`
  - `dramaturgique`
  - `textuelle`
  - `bibliographique`

- annotation status:
  - `draft`
  - `reviewed`
  - `validated`

## 7. Validation rules

Annotation validation should remain light but explicit.

At minimum, validate:

- `version == 1`
- unique annotation IDs
- allowed annotation type
- allowed annotation status
- valid anchor shape according to `kind`
- non-empty content

Examples of expected diagnostics:

- `E_ANN_INVALID_JSON`
- `E_ANN_DUPLICATE_ID`
- `E_ANN_INVALID_ANCHOR`
- `E_ANN_EMPTY_CONTENT`
- `E_ANN_TARGET_NOT_FOUND`

## 8. TEI integration

### 8.1 Integration strategy

Annotations must be injected **after** the normal TEI generation step.

Pipeline:

1. generate TEI from the current core pipeline
2. parse the generated TEI
3. resolve annotation anchors against TEI elements
4. insert `<note>` elements
5. serialize the enriched TEI

### 8.2 Important rule

Do not refactor the whole TEI generator just to support annotations in V1.

A post-generation enrichment step is preferred.

### 8.3 Stable TEI identifiers

Annotatable TEI elements should receive stable `xml:id` values whenever possible.

Recommended conventions:

- verse line: `A{act}S{scene}L{line}`
- explicit stage direction: `A{act}S{scene}ST{index}`

Examples:

```xml
<l xml:id="A1S1L42" n="42">Arrestons un moment. La pompe de ces lieux,</l>
```

```xml
<stage xml:id="A1S1ST2">Antiochus entre</stage>
```

### 8.4 Note examples

Single-line note:

```xml
<note xml:id="n1" type="explicative" target="#A1S1L42">
  Allusion possible à la pompe triomphale romaine.
</note>
```

Range note:

```xml
<note xml:id="n2" type="dramaturgique" target="#A1S1L42 #A1S1L43 #A1S1L44">
  Cette séquence concentre une montée pathétique très rapide.
</note>
```

Stage note:

```xml
<note xml:id="n3" type="dramaturgique" target="#A1S1ST2">
  Entrée fortement motivée sur le plan scénique.
</note>
```

## 9. HTML rendering

### 9.1 Preview HTML

If TEI contains editorial notes, the HTML preview should render:

- a visible note call
- readable note content

For V1, a simple rendering is sufficient:

- notes at end of scene
- or notes at end of document
- or simple footnote-like blocks

No complex interactive apparatus is required.

### 9.2 Export HTML

Publication-oriented HTML export must preserve editorial notes.

A simple and stable rendering is preferred over a sophisticated one.

## 10. UI integration (Tkinter)

### 10.1 General rule

The Tkinter UI must remain thin and must use application services.

### 10.2 V1 UX recommendation

The first UI version should provide:

- an `Annotations` tab or panel
- a list of current annotations
- add / edit / delete actions
- load / save annotation file actions

### 10.3 Important UX constraint

Do not build V1 around free mouse selection inside the raw source editor.

For this phase, anchors should be entered explicitly through a dialog using:

- act
- scene
- line / range / stage index

This is less ambitious but much more robust.

## 11. Application services

The UI should be able to call services such as:

- `load_annotations(path)`
- `save_annotations(collection, path)`
- `create_annotation(collection, annotation)`
- `update_annotation(collection, annotation)`
- `delete_annotation(collection, annotation_id)`
- `inject_annotations_into_tei(tei_xml, annotations)`

Exact names may vary, but the architectural separation must remain clear.

## 12. Testing policy

Add dedicated tests for annotations, for example:

```text
tests/
  test_annotations_store.py
  test_annotations_validation.py
  test_annotations_tei_injection.py
  test_annotations_html_render.py
```

### 12.1 Required test cases

- valid JSON load
- invalid JSON rejection
- duplicate ID rejection
- invalid anchor rejection
- TEI injection on existing line target
- TEI injection on line range
- TEI injection on stage direction
- diagnostic when TEI target is not found
- HTML rendering includes note call and note content

## 13. Fixtures

Add at least one small dedicated fixture, for example:

```text
fixtures/annotations/berenice_1_1/
  input.txt
  config.json
  annotations.json
  expected_annotated.xml
```

This fixture should remain minimal and stable.

## 14. Acceptance criteria

V1 is considered complete when:

- annotations can be loaded from JSON
- annotations can be saved back to JSON
- the UI can add / edit / delete annotations
- generated TEI can be enriched with `<note>` elements
- HTML outputs show notes in a readable form
- the collation engine remains independent from note logic

## 15. Forbidden shortcuts

For this feature, do not:

- add inline note syntax to `input.txt`
- alter tokenization rules for note support
- mix note logic into the collation engine
- use raw source character offsets as anchors
- rebuild the whole TEI generator around annotations
- over-engineer V1 with complex UI interactions
