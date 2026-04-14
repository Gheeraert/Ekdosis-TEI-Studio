# AGENTS.md

## Project goal

This repository is a clean rewrite of **Ekdosis TEI Studio**.

The project converts a structured plain-text transcription format for **classical French drama with multiple witnesses** into **valid XML-TEI**, with a strong focus on:
- theatrical structure
- critical apparatus
- editorial annotations
- robustness on difficult edge cases
- testability
- future web integration

The project now also includes:
- a first **local Tkinter desktop UI**
- a first **editorial annotation layer**
- a limited **Markdown-inspired authoring syntax for annotation content**

The objective is **not** to repair the legacy monolithic application.  
The objective is to build a **new modular core**, with thin interface layers on top of it.

## Priority order of truth sources

When making decisions, use these sources in this order:

1. `fixtures/`  
   These are the most important source of truth.  
   They contain real inputs and expected XML outputs.

2. `docs/SPEC_V2.md`  
   This is the functional and architectural specification for the rewrite.

3. `docs/ANNOTATIONS_V1.md`  
   This defines the editorial annotation layer.

4. `docs/ANNOTATION_MARKDOWN_V1.md`  
   This defines the limited Markdown-inspired syntax allowed in annotation content and its conversion to TEI.

5. `docs/Documentation_ancienne.md` and other legacy docs  
   These explain the historical behavior and input conventions.

6. `legacy/`  
   Legacy code is reference material only. Reuse ideas if useful, but do not preserve its architecture.

## Immediate objective

Build and stabilize a modular, well-tested Python application that can:

1. read a plain text input file
2. parse structural markers such as:
   - `####...####` for act headers
   - `###...###` for scene headers
   - `##...##` for cast on stage
   - `#...#` for speaker changes
   - `**...**` for explicit stage directions
   - `***` for shared verse segmentation
3. collate parallel witness lines using a reference witness
4. generate minimal XML-TEI
5. expose core actions through a minimal local Tkinter UI
6. support a first editorial annotation layer
7. support a limited Markdown-inspired syntax in annotation content
8. pass the stable and regression fixture tests

## Non-goals for now

Do not build or restore:
- broad feature parity with legacy code
- a complex visual annotation editor
- free text selection anchoring in the source editor
- word-level or apparatus-internal note anchoring
- full Pandoc Markdown support
- LaTeX / ekdosis export of annotations
- HTML note rendering beyond the documented limited scope

These may come later, but the current phase remains focused on a stable core plus a thin desktop UI.

## Architectural rules

- No global mutable state
- No monolithic script
- Separate:
  - parsing
  - domain model
  - collation
  - TEI generation
  - annotation enrichment
  - validation
  - application services
  - UI
- Use typed Python
- Prefer dataclasses for domain objects
- Keep functions small and testable
- Avoid hidden side effects
- Keep UI code thin
- Keep annotation logic separate from collation/tokenization
- Keep Markdown parsing for annotations local to annotation content only

## Expected repository structure

- `src/ets/domain/` for domain model
- `src/ets/parser/` for parsing input text
- `src/ets/collation/` for tokenization and variant alignment
- `src/ets/tei/` for TEI generation
- `src/ets/annotations/` for editorial annotations and annotation enrichment
- `src/ets/application/` for service-layer APIs used by interfaces
- `src/ets/ui/` for interface code
- `src/ets/validation/` for structural and XML validation
- `tests/` for pytest test suite
- `fixtures/` for real inputs and expected outputs
- `legacy/` for archived historical code

## Testing rules

- Use `pytest`
- Prefer real fixtures over artificial examples
- Add regression tests for every bug fixed
- Keep unit tests and integration tests separate
- When UI tests are brittle, prefer testing UI-adjacent controller/state methods
- Any annotation feature must include tests for:
  - JSON validation
  - TEI enrichment
  - diagnostics
  - UI state stability where relevant

## TEI principles

Target output should be a clean TEI theatrical structure, progressively improved over time.

At minimum, support:
- TEI root and header
- witness list
- act and scene divisions
- speeches
- verse lines
- stage directions
- critical apparatus using lemma + readings
- editorial notes as a separate enrichment layer

The reference witness is the lemma witness.

## Editorial annotations policy

A first editorial annotation layer is in scope.

Rules:
- Do not add note syntax inside `input.txt`
- Do not modify tokenization rules to support annotations
- Do not mix annotation logic into witness collation
- Store annotations in a separate structured file, e.g. `annotations.json`
- Inject annotations after TEI generation, not during collation
- Prefer stable editorial anchors such as act / scene / line / stage index
- Do not use raw character offsets as the primary anchoring strategy in V1

## Annotation content markup policy

Annotation content may use a limited Markdown-inspired syntax.

This is an authoring convenience only.

Rules:
- TEI remains the canonical output model
- convert supported annotation markup to TEI during annotation enrichment
- do not introduce full Pandoc Markdown support
- do not broaden the supported syntax beyond the documented subset
- unsupported or malformed markup should remain literal text rather than generating broken TEI

See `docs/ANNOTATION_MARKDOWN_V1.md`.

## Legacy code policy

Legacy code is available only as a fallback source of logic.
Do not extend the old architecture.
Do not copy large chunks blindly.
Prefer reimplementation from specification and fixtures.

## How to work

When implementing:
1. inspect the fixture
2. infer the minimal structure needed
3. implement the smallest coherent slice
4. add or update tests
5. keep the code modular

When uncertain, prefer:
- fixture behavior
- explicit domain modeling
- simplicity
- deterministic output
