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

It now also includes:
- a first local **Tkinter desktop UI**
- a first **editorial annotation layer**
- a limited **Markdown-inspired authoring syntax for annotation content**

## Main objective

The project aims to support scholarly editing workflows for classical drama, especially when several textual witnesses must be collated and encoded in TEI.

The application should be able to:
- parse a structured plain-text encoding format
- identify dramatic structure
- manage a configurable number of witnesses
- identify a reference witness used as lemma
- align and collate variant readings
- generate valid XML-TEI
- enrich the generated TEI with editorial annotations
- remain robust in the presence of difficult editorial cases

## Scope of the current development phase

The current focus is the first local desktop UI, plus a first editorial annotation layer.

This UI must stay thin and rely on the existing core services.

It should:
- provide a minimal Tkinter desktop interface for text input, validation, TEI generation, HTML preview, and export
- surface validator diagnostics clearly and help users correct them
- support a first workflow for editorial annotations
- store annotations in a separate structured file
- enrich generated TEI with editorial notes
- support a limited Markdown-inspired syntax in annotation content
- convert supported annotation markup to TEI during annotation enrichment
- display notes in downstream HTML outputs once TEI rendering support is in place
- preserve the current core-first architecture
- pass the stable fixture tests

It should not yet aim at:
- full legacy feature parity
- broad Flask UI work
- word-level annotation anchoring inside variant apparatus
- note authoring directly inside `input.txt`
- full Pandoc Markdown support
- LaTeX / ekdosis output for annotations

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
src/ets/              core package
src/ets/annotations/  editorial annotation layer
src/ets/ui/           local interface code
tests/                test suite
fixtures/             real inputs and expected outputs
docs/                 project documentation
legacy/               archived historical code
```

## Editorial annotations

The project now prepares a first editorial annotation layer.

Annotations are treated as a separate scholarly layer:
- they are not written inside `input.txt`
- they are stored in a separate structured file
- they are injected after TEI generation
- they are rendered downstream from the enriched TEI

See `docs/ANNOTATIONS_V1.md`.

## Annotation content markup

Annotation content may use a limited Markdown-inspired authoring syntax.

This syntax is only an input convenience.
It must be converted to TEI during annotation enrichment.

See `docs/ANNOTATION_MARKDOWN_V1.md`.

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
- first Tkinter desktop UI
- TEI and HTML outputs exposed in the interface
- stable export workflow

### Milestone 5
- editorial annotations V1
- stable TEI identifiers for annotable elements
- limited Markdown-to-TEI conversion for annotation content
- note rendering in HTML outputs

### Milestone 6
- Flask-based UI on top of the stable core

## Legacy material

The old codebase may be kept under `legacy/` for consultation.
It is not the foundation of the new architecture.

## Development

Use Python with type hints and pytest.

A simple CLI target may still be useful, for example:

```bash
python -m ets.cli --input fixtures/stable/input.txt --config fixtures/stable/config.json --output out.xml
```

## License

To be defined according to the intended publication model of the repository.
