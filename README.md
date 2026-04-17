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

## Future publication layer: ETS Site Builder

A planned autonomous module, **ETS Site Builder**, extends the project from TEI generation to full static scholarly publication.

Its purpose is to build a complete website automatically from XML editorial sources, with generated navigation, metadata display, assets management, and optional download links.

A key project assumption is that each play may be accompanied by a **separate TEI notice produced with Métopes**.

This means the publication workflow must support at least two XML inputs per play:
- the dramatic TEI produced by ETS,
- the scholarly notice TEI produced outside ETS with Métopes.

The long-term goal is not only to preview TEI locally, but to publish a complete static site in one step, without manually maintaining menus or page links.

The notice visualization layer may take direct inspiration from the **Impressions** project, which already follows a TEI Métopes -> static HTML book model with XSLT transformation, generated table of contents, previous/next navigation, and a lightweight GUI for editorial parameters.

## New publication requirements

The publication layer is now expected to progress beyond a merely functional prototype.

This means ETS Site Builder must increasingly account for:
- the elegance of the reading page,
- the hierarchy and clarity of navigation,
- the presence of a true editorial home page,
- independent general notices at site level,
- per-play notices distinct from the dramatic texts,
- collapsible navigation for acts and scenes,
- configuration persistence for repeated site regeneration,
- CSS and typographic choices that respect a literary scholarly audience.

The target audience includes researchers and readers accustomed to serious editorial environments and beautiful scholarly editions. Visual roughness, awkward layout, weak hierarchy, or degraded HTML rendering are therefore not secondary concerns: they are part of publication quality.

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
legacy/            archived historical code and publication references
```

A publication-oriented subpackage is expected under:

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
7. For publication work, validate both structure and real reading quality.

## Why fixtures matter

Fixtures are the strongest source of truth in this rewrite.

They provide:
- real encoded input
- expected output
- regression safety
- a concrete basis for design decisions

Whenever possible, new behavior should be added through:
- a fixture
- a test
- a minimal implementation step

## Additional documentation to read

- `AGENTS.md`
- `docs/SPEC_V2.md`
- `docs/ETS_SITE_BUILDER.md`
- `docs/SITE_BUILDER_TARGET.md`

## Current development principle

The repository must keep a clean separation between:
- core text parsing and TEI generation
- application/service orchestration
- user interface
- publication rendering
- autonomous editorial tools

In particular:
- UI must remain thin;
- the publication layer must reuse existing ETS XML -> HTML rendering engines wherever they exist;
- legacy sites may inspire structure and tone, but must not be copied architecturally.
