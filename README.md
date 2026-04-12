# Ekdosis TEI Studio v2

A structured rewrite of **Ekdosis TEI Studio**, focused on producing robust **XML-TEI** for edited texts of classical French drama with multiple witnesses.

## Project status

This repository is a **clean rewrite** of the previous application.

The legacy application successfully explored a practical encoding workflow, but it became difficult to evolve because:
- UI code and business logic were tightly coupled
- global variables accumulated state unpredictably
- edge cases multiplied
- difficult cases such as shared verses, multi-scene inputs, and long structured files became hard to maintain

This new version starts from a different principle:

**plain text input -> structured parsing -> domain model -> collation -> TEI output**

## Main objective

The project aims to support scholarly editing workflows for classical drama, especially when several textual witnesses must be collated and encoded in TEI.

The core engine should be able to:
- parse a structured plain-text encoding format
- identify dramatic structure
- manage a configurable number of witnesses
- identify a reference witness used as lemma
- align and collate variant readings
- generate valid XML-TEI
- remain robust in the presence of difficult editorial cases

## Scope of the first development phase

The first milestone is intentionally limited.

It should:
- read plain-text fixture inputs
- parse acts, scenes, cast lists, speaker changes, explicit stage directions, and ordinary verse blocks
- collate witness lines with a reference witness
- produce minimal XML-TEI
- pass the stable fixture tests

It should not yet aim at:
- full legacy feature parity
- graphical UI
- Flask UI
- HTML preview
- LaTeX / ekdosis output

## Input format

The historical project uses a lightweight text syntax inspired by Markdown.

Examples of structural markers:

- `####...####` -> act header
- `###...###` -> scene header
- `##...##` -> cast list
- `#...#` -> speaker
- `**...**` -> explicit stage direction
- `***` -> shared verse segmentation
- `#####` -> whole-line variant mode
- `$$TYPE$$ ... $$fin$$` -> implicit stage direction span
- `_..._` -> italic text
- `~` -> non-breaking or editorially bound spacing

The exact target behavior is documented in `docs/SPEC_V2.md` and in the fixtures.

## Repository structure

```text
src/ets/           core package
tests/             test suite
fixtures/          real inputs and expected outputs
docs/              project documentation
legacy/            archived historical code
```

## Recommended development workflow

1. Start from a real fixture.
2. Build the smallest domain model needed to represent it.
3. Implement parsing for that slice only.
4. Add collation logic only where needed.
5. Generate TEI.
6. Lock behavior with pytest.

## Current guaranteed shared-verse cases

The current core guarantees the following shared-verse cases:

- three-segment shared verse within a single scene
- two-segment shared verse across two successive scenes when the continuation in the next scene is explicitly marked by `***`

These cases are covered by regression fixtures in `fixtures/shared_verses/`.

## Why fixtures matter

Fixtures are the strongest source of truth in this rewrite.

They provide:
- real encoded input
- expected output
- regression safety
- a concrete basis for design decisions

The stable fixture should be the first development target.

## Fixtures

The directory `fixtures/variant_head_and_cast/` contains real-world regression cases
for textual variation in:

- act headers
- scene headers
- cast lists

These fixtures ensure that the collation engine correctly handles variation
in all structural textual elements, not only verse lines.

`fixtures/shared_verses/` contains regression cases for prioritized shared-verse patterns.

`fixtures/implied_stage_directions/` contains regression cases for implicit stage directions (`$$TYPE$$ ... $$fin$$`).

## Current guaranteed implicit stage direction cases

The current core supports simple implicit stage direction spans:

- `$$TYPE$$` opens a span
- `$$fin$$` closes it
- the span remains inside the current speech
- the span contains one or more normally collated and numbered verse lines
- TEI output uses `<stage xml:id="impliciteN" type="DI" ana="#TYPE">`

These cases are covered by regression fixtures in `fixtures/implied_stage_directions/`.

## Design principles

- explicit domain model
- no global mutable state
- deterministic transformations
- modular code
- tests before feature expansion
- TEI-first rather than UI-first

## Roadmap

### Milestone 1
- minimal parser
- minimal domain model
- basic collation
- minimal TEI output
- stable fixture passes

### Milestone 2
- shared verses
- lacunae
- whole-line variants
- italic markup

### Milestone 3
- multiple scenes in a single input file
- stronger structural validation
- richer TEI witness metadata

### Milestone 4
- difficult multi-segment verse cases
- advanced edge-case handling
- better TEI identifiers and `@who`

### Milestone 5
- Flask-based UI on top of the stable core

## Legacy material

The old codebase may be kept under `legacy/` for consultation.
It is not the foundation of the new architecture.

## Development

Use Python with type hints and pytest.

A simple first CLI target is expected, for example:

```bash
python -m ets.cli --input fixtures/stable/input.txt --config fixtures/stable/config.json --output out.xml
```

## License

To be defined according to the intended publication model of the repository.
