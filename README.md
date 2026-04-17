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

The long-term target is broader than TEI generation alone. The project is meant to support:
- a stable modular TEI engine,
- local and/or web interfaces built on top of that engine,
- a static publication layer called **ETS Site Builder**.

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
- advanced LaTeX / ekdosis output
- large-scale publication polish before the core is stable

Presentation work is allowed only if it remains a separate layer over the core.

## Convenience utilities

ETS also includes small autonomous workflow utilities exposed in the Tkinter **Tools** menu.

- A plain-text transcription merge tool can concatenate multiple `.txt`/`.md` transcription files in explicit user-defined order.
- This utility is independent from TEI parsing, TEI generation, and `site_builder`.

## Future publication layer: ETS Site Builder

A planned autonomous module, **ETS Site Builder**, will extend the project from TEI generation to full static scholarly publication.

Its purpose is to build a complete website automatically from XML editorial sources, with generated navigation, metadata display, assets management, and optional download links.

A key project assumption is that each play may be accompanied by a **separate TEI notice produced with Métopes**.

This means the publication workflow must support at least two XML inputs per play:
- the dramatic TEI produced by ETS,
- the scholarly notice TEI produced outside ETS with Métopes.

The long-term goal is not only to preview TEI locally, but to publish a complete static site in one step, without manually maintaining menus or page links.

The notice visualization layer may take direct inspiration from the **Impressions** project, which already follows a TEI Métopes → static HTML book model with XSLT transformation, generated table of contents, previous/next navigation, and a lightweight GUI for editorial parameters.



## Current documented Métopes subset for ETS Site Builder

For the next development steps, the notice layer should target a deliberately limited Métopes subset.

Two source situations are considered especially important:

1. a **master Métopes volume** with `text type="book"`, nested `group` elements, and optional `xi:include` references;
2. a **standalone notice or chapter file** with a `text` node, optional `front`, `titlePage`, `body`, paragraphs, inline highlighting, and notes.

The first implementation stages should focus on:
- optional `xi:include` resolution,
- extraction of hierarchical `group` structures,
- extraction of `head` and `title`,
- support for `front/titlePage`,
- support for `body/p`,
- support for inline `hi`,
- support for notes,
- minimal deterministic HTML rendering.

This is enough for a first serious publication slice and for realistic automated tests. Full generic Métopes coverage is not required at this stage.

The repository is also expected to maintain two complementary Métopes fixture families:
- `fixtures/metopes/minimal/` for small synthetic tests;
- `fixtures/metopes/realistic/` for integration tests on real or lightly adapted Métopes files.

In early ETS Site Builder milestones, the relation between a dramatic TEI play and a Métopes notice should remain explicit and simple:
- direct configuration,
- shared slug,
- or stable filename convention.

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

A later publication-oriented subpackage is expected under:

```text
src/ets/site_builder/
```

## Recommended development workflow

1. Start from a real fixture.
2. Build the smallest domain model needed to represent it.
3. Implement parsing for that slice only.
4. Add collation logic only where needed.
5. Generate TEI.
6. Lock behavior with pytest.

## Why fixtures matter

Fixtures are the strongest source of truth in this rewrite.

They provide:
- real encoded input
- expected output
- regression safety
- a concrete basis for design decisions

The stable fixture should be the first development target.

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

### Milestone 6
- ETS Site Builder
- automatic navigation generation
- static site build from TEI inputs
- optional XML downloads
- integration of one Métopes notice per play

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
