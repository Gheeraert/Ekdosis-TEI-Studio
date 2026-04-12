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

## 2. Functional objective

The system must convert an input text file containing parallel transcriptions of multiple witnesses into a TEI representation of a dramatic text with critical apparatus.

The user must be able to:
- define the number of witnesses
- define metadata for each witness
- choose a reference witness
- encode a dramatic text in a lightweight syntax
- process one scene, multiple scenes, or eventually an entire act
- generate TEI reliably


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
- Any textual element derived from parallel witness lines must be treated as potentially variant-bearing.
- The collation model must not be limited to verse lines. Act headers, scene headers, cast lists, speakers, stage directions, and verse lines must all be able to contain a `CollatedText` structure rendered as literal text or inline TEI apparatus (`app`, `lem`, `rdg`).
- The core abstraction is therefore not “variant verse” but “collatable text”.

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

In ordinary parallel witness blocks, token counts must be strictly identical across witnesses. Validation must fail otherwise.

Whole-line variants must be triggered only by the explicit `#####` marker and must not rely on heuristic rewriting of marker syntax.

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

### 6.4 Variant-bearing dramatic headings

Act headers, scene headers, and scene cast lists are textual units that may carry variants.

They must not be reduced to plain strings during parsing.

The following elements must support the same token-based collation model as verse lines:

- act headers: `####...####`
- scene headers: `###...###`
- scene cast lists: `##...##`

If variants are present, the TEI output must render an inline apparatus with `<app>`, `<lem>`, and `<rdg>`.

The fixture `fixtures/variant_head_and_cast/` documents this requirement.

### 6.5 Future needs

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
    validation/
    render/
    cli.py
tests/
fixtures/
docs/
legacy/
```

## 12. Interface policy

The first development phase must not depend on any GUI.

### 12.1 Forbidden in phase 1
- Tkinter rewrite
- Flask app
- HTML visual editor

### 12.2 Allowed in phase 1
- CLI entry point
- file-based workflow
- fixture-driven testing

### 12.3 Phase 2+
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
4. collate witness lines against a reference witness
5. generate minimal TEI
6. pass the stable fixture test suite

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
- difficult shared verse chains
- advanced alignment strategies
- better identifiers and TEI enrichment

### Milestone 5
- Flask interface
- TEI preview
- editing workflow support
