# SPEC_V2.md

## 1. Purpose

This document defines the functional and architectural specification for the clean rewrite of **Ekdosis TEI Studio**.

The application is intended to support scholarly editing of **classical drama with textual variants**, beginning from a structured plain-text encoding format and producing **valid XML-TEI**.

The rewrite must prioritize:
- clarity
- modularity
- testability
- robustness on edge cases
- compatibility with future interfaces, especially Flask
- clean support for a local desktop UI and editorial annotations

## 2. Functional objective

The system must convert an input text file containing parallel transcriptions of multiple witnesses into a TEI representation of a dramatic text with critical apparatus.

The user must be able to:
- define the number of witnesses
- define metadata for each witness
- choose a reference witness
- encode a dramatic text in a lightweight syntax
- process one scene, multiple scenes, or eventually an entire act
- generate TEI reliably
- enrich the generated TEI with editorial annotations

## 3. Input model

The input is a structured plain-text format, historically inspired by Markdown-like conventions.

### 3.1 Parallel blocks

A textual unit is usually encoded as a block of parallel lines, one line per witness.

For example, with three witnesses:

```text
Line in witness 1
Line in witness 2
Line in witness 3
```

A parser must interpret such blocks using the configured witness count.

### 3.2 Structural markers

The following markers must be recognized.

#### Act header
```text
####ACTE I####
```

#### Scene header
```text
###SCÈNE I###
```

#### Cast list
```text
##PHÈDRE## ##HIPPOLYTE##
```

#### Speaker
```text
#PHÈDRE#
```

#### Explicit stage direction
```text
**Elle sort.**
```

#### Shared verse segmentation
A shared verse may be split across speakers using `***`.

Example:
```text
Imaginations!***
***Éternelles clartés
```

#### Whole-line variant mode
A line beginning with `#####` must be treated as a whole-line variation unit.

#### Lacuna
```text
(lacune)
```

#### Implicit stage direction span
```text
$$EVT$$
...
$$fin$$
```

#### Italic markup
```text
son _temple_
```

#### Bound spacing
`~` indicates a non-breaking or editorially bound spacing unit.

#### Forced indentation
One or more initial `~` may be used to force visible indentation in a line.

## 4. Target domain model

The application must not directly transform raw strings into TEI.
It must first create a stable internal representation.

A recommended domain model includes the following concepts.

### 4.1 Configuration

```python
Witness
EditionConfig
```

Witness must include:
- identifier or siglum
- year
- description

EditionConfig must include:
- work metadata
- witness list
- reference witness index
- optional initial line numbering data

### 4.2 Dramatic structure

```python
Play
Act
Scene
Speech
StageDirection
ImplicitStageSpan
Verse
SharedVerse
VerseSegment
```

### 4.3 Critical structure

```python
CollatedText
LiteralText
VariantText
ApparatusEntry
Reading
```

## 5. Parsing requirements

### 5.1 General strategy

Parsing must happen in stages:

1. raw line reading
2. grouping into parallel blocks according to witness count
3. classification of blocks
4. construction of a structured intermediate representation
5. transformation into domain objects

### 5.2 Parser responsibilities

The parser must:
- respect configured witness count
- detect malformed blocks
- distinguish structural blocks from verse blocks
- preserve ordering
- identify transitions between speeches
- identify transitions between acts and scenes
- support multi-scene inputs
- support eventual act-level inputs

### 5.3 Parser non-responsibilities

The parser must not:
- generate XML directly
- store hidden global state
- perform UI tasks
- make formatting decisions unrelated to structure

## 6. Collation requirements

### 6.1 General principle

Collation must happen only on already-identified textual units.

The reference witness is the lemma witness.

### 6.2 Minimal first implementation

A first implementation may provide:
- tokenization based on editorial word units
- comparison of witness token sequences
- production of apparatus entries only where variation exists
- literal text output where witnesses are identical

### 6.3 Required design

The collation subsystem should be separable into:
- tokenization
- alignment
- apparatus construction

Recommended functions:

```python
tokenize_editorial_text(text: str) -> list[str]
align_variants_by_token(token_matrix: list[list[str]], ref_index: int) -> list[AlignmentUnit]
build_apparatus_from_alignment(...) -> CollatedText
collate_parallel_verse(...) -> CollatedText
```

### 6.4 Future needs

The design must leave room for:
- whole-line variant mode
- lacuna handling
- partial rewritings
- shared verse segments
- difficult multi-segment partitioning

## 7. Shared verse requirements

Shared verses are a core requirement, not a marginal edge case.

A verse may be:
- complete and attached to one speaker
- split across two or more speakers
- split into 2, 3, 4, or more segments

The internal model must therefore represent a shared verse as a structured object, not as a formatting accident.

A `SharedVerse` should contain:
- a common metrical identity
- an ordered list of `VerseSegment`
- one speaker association per segment
- content per segment

This is essential for future robustness.

## 8. TEI generation requirements

### 8.1 First milestone TEI

The first milestone may target a minimal but valid TEI output.

It should generate at least:
- `TEI`
- `teiHeader`
- witness metadata
- dramatic body
- divisions for acts and scenes
- speeches
- verse lines
- stage directions
- critical apparatus

### 8.2 Expected dramatic structure

The TEI generator should progressively support:
- `div type="act"`
- `div type="scene"`
- `sp`
- `speaker`
- `l`
- `stage`
- `app`
- `lem`
- `rdg`

### 8.3 Future enrichment

Later versions may add:
- stable XML identifiers
- `@who`
- richer `teiHeader`
- explicit witness declarations
- analytic annotation for implicit stage directions
- editorial annotation enrichment

## 9. Validation requirements

Validation must exist at two levels.

### 9.1 Structural validation

Check:
- witness count consistency
- malformed parallel blocks
- unclosed implicit stage spans
- impossible structural transitions
- missing speaker where required

### 9.2 XML validation

Check:
- XML well-formedness
- optional schema compatibility
- deterministic serialization

## 10. Testing policy

Tests are mandatory and central.

### 10.1 Test categories

#### Unit tests
For:
- marker recognition
- block grouping
- tokenization
- alignment
- numbering logic

#### Integration tests
For:
- complete fixture input to TEI output

#### Regression tests
For every bug fixed in difficult cases

### 10.2 Fixture policy

Fixtures are the main behavioral specification.
The stable fixture is the first target.
Known-issue fixtures must be converted progressively into passing regression tests.

### 10.3 Comparison strategy

When comparing generated XML to expected XML:
- exact comparison is acceptable where stable
- otherwise normalize whitespace and serialization consistently
- document the chosen strategy

## 11. Repository architecture

Recommended structure:

```text
src/
  ets/
    domain/
    parser/
    collation/
    tei/
    annotations/
    application/
    ui/
    validation/
    render/
    cli.py
tests/
fixtures/
docs/
legacy/
```

## 12. Interface policy

The core must remain usable independently from any GUI.

### 12.1 Current interface scope
The project may include:
- a local Tkinter desktop UI
- file-based workflow
- fixture-driven testing
- later, a Flask presentation layer

### 12.2 Constraints
Interfaces must remain thin:
- no business logic in the UI
- no direct XML generation in UI code
- no duplication of parser/collation/annotation validation logic

### 12.3 Future interfaces
Once the core is stable, Flask may be added as a separate presentation layer.

## 13. Legacy code policy

The previous codebase may be consulted for logic and conventions, but:
- it is not the source of architectural authority
- it must not dictate the new shape of the application
- it should remain isolated under `legacy/`

## 14. Initial milestone definition

The first milestone is complete when the application can:

1. load the stable fixture input
2. read its witness configuration
3. parse acts, scenes, cast, speakers, and ordinary verse blocks
4. validate malformed blocks and token-count inconsistencies
5. collate witness lines against a reference witness
6. generate minimal TEI
7. expose these actions through a simple Tkinter interface
8. display TEI and HTML preview outputs
9. keep the core usable independently from the UI
10. pass the stable fixture test suite

## 15. Subsequent milestone suggestions

### Milestone 2
- explicit stage directions
- shared verses
- lacunae
- whole-line variants
- italics

### Milestone 3
- multiple scenes in one file
- stronger structural validation
- richer witness metadata

### Milestone 4
- stable Tkinter UI workflow
- better diagnostics display
- export stability

### Milestone 5
- editorial annotations V1
- stable TEI identifiers for annotable elements
- HTML rendering of notes

### Milestone 6
- annotation-content Markdown subset to TEI conversion
- annotation rendering improvements
- richer editorial note workflows

### Milestone 7
- Flask interface
- TEI preview
- editing workflow support

## 16. Editorial annotations (V1)

### 16.1 General principle

Editorial annotations are in scope, but they must remain a **separate editorial layer**.

Therefore:

- do not add note syntax inside `input.txt`
- do not alter tokenization or collation rules for note support
- do not anchor notes to raw source offsets
- do not mix note authoring with witness transcription

A separate annotation file, e.g. `annotations.json`, must be used.

See `docs/ANNOTATIONS_V1.md`.

### 16.2 Initial supported targets

V1 supports:
- note on a single verse line
- note on a range of verse lines
- note on an explicit stage direction

V1 does not yet support:
- note on a word or phrase inside a verse
- note directly targeting `<app>`, `<lem>`, or `<rdg>`
- note syntax embedded in `input.txt`

### 16.3 Storage model

Annotations should be stored in a dedicated structured file separate from:
- `input.txt`
- `config.json`

A JSON-based format is acceptable for V1 and should remain readable and stable.

### 16.4 Anchoring model

Annotations must use editorially meaningful anchors, such as:
- act number
- scene number
- line number
- stage direction index

The preferred anchor kinds for V1 are:
- `line`
- `line_range`
- `stage`

### 16.5 TEI integration

Annotation support must be implemented as a **post-generation TEI enrichment step**.

Expected sequence:
1. generate TEI through the normal pipeline
2. parse the TEI
3. resolve annotation anchors
4. inject `<note>` elements
5. serialize enriched TEI

Do not refactor the whole TEI generator around note support in this phase.

### 16.6 Stable identifiers

Annotatable TEI elements should receive stable `xml:id` values when possible.

Recommended conventions:
- line: `A{act}S{scene}L{line}`
- explicit stage direction: `A{act}S{scene}ST{index}`

### 16.7 UI integration

The Tkinter UI may expose annotation workflows, but must remain thin.

Allowed in V1:
- annotation list display
- add / edit / delete actions
- load / save annotation file actions

Not required in V1:
- free text selection anchoring inside the raw source editor
- advanced WYSIWYG note editing

### 16.8 HTML rendering

If generated TEI contains editorial notes, HTML outputs should render:
- visible note calls
- readable note contents

For V1, a simple rendering model is acceptable:
- end-of-scene notes
- end-of-document notes
- simple footnote-like blocks

### 16.9 Testing and fixtures

Annotation support must include dedicated tests and at least one dedicated fixture.

Typical tests include:
- annotation JSON validation
- duplicate ID rejection
- anchor resolution
- TEI note injection
- HTML note rendering
- diagnostics when a target is missing

## 17. Annotation content markup (V1)

### 17.1 General principle

Annotation content may include a limited Markdown-inspired syntax.

This syntax is an **authoring convenience**, not the canonical model.
TEI remains the canonical output model.

See `docs/ANNOTATION_MARKDOWN_V1.md`.

### 17.2 Supported subset

The first version should support only a small editorially useful subset, including:
- italic
- bold
- small caps
- superscript
- subscript
- hyperlinks
- paragraph breaks on blank lines

### 17.3 Conversion rule

Supported annotation markup must be converted to TEI during annotation enrichment, inside `<note>` content.

The expected pipeline is:
1. annotation content is written in the UI
2. it is stored as text in `annotations.json`
3. TEI is generated normally
4. annotation enrichment resolves anchors
5. supported inline markup is converted into TEI nodes inside `<note>`
6. enriched TEI is serialized
7. HTML rendering consumes the resulting TEI structure

### 17.4 Out of scope

The following are out of scope for V1:
- full Pandoc Markdown support
- lists, tables, images, raw HTML
- arbitrary classes/attributes
- nested complex Markdown structures
- markdown parsing outside annotation content

### 17.5 Validation policy

Markdown conversion should be conservative:
- valid supported syntax -> convert to TEI
- malformed syntax -> preserve as literal text
- never generate malformed TEI from partial markdown parsing
