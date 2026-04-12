# AGENTS.md

## Project goal

This repository is a clean rewrite of **Ekdosis TEI Studio**.

The project converts a structured plain-text transcription format for **classical French drama with multiple witnesses** into **valid XML-TEI**, with a strong focus on:
- theatrical structure
- critical apparatus
- robustness on difficult edge cases
- testability
- future web integration

The current objective is **not** to repair the legacy monolithic application.  
The objective is to build a **new modular core**.

## Critical collation engine
The critical collation engine must operate token by token across synchronized witness columns. Do not use line-level diffs as the main algorithm.

## Priority order of truth sources

When making decisions, use these sources in this order:

1. `fixtures/`  
   These are the most important source of truth.  
   They contain real inputs and expected XML outputs.

2. `docs/SPEC_V2.md`  
   This is the functional and architectural specification for the rewrite.

3. `docs/Documentation_ancienne.md` and other legacy docs  
   These explain the historical behavior and input conventions.

4. `legacy/`  
   Legacy code is reference material only. Reuse ideas if useful, but do not preserve its architecture.

## Immediate objective

Build a minimal, well-tested Python core that can:

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
5. pass the stable fixture tests
6. A minimal local desktop UI (Tkinter) is now in scope

## Non-goals for now
Do not build or restore:
- Flask UI
- LaTeX / ekdosis export
- broad feature parity with legacy code

These may come later, but the current phase is focused on the core TEI engine.

## Architectural rules

- No global mutable state
- No monolithic script
- Separate:
  - parsing
  - domain model
  - collation
  - TEI generation
  - validation
- Use typed Python
- Prefer dataclasses for domain objects
- Keep functions small and testable
- Avoid hidden side effects

## Expected repository structure

- `src/ets/domain/` for domain model
- `src/ets/parser/` for parsing input text
- `src/ets/collation/` for tokenization and variant alignment
- `src/ets/tei/` for TEI generation
- `src/ets/validation/` for structural and XML validation
- `tests/` for pytest test suite
- `fixtures/` for real inputs and expected outputs
- `legacy/` for archived historical code

## Testing rules

- Use `pytest`
- Prefer real fixtures over artificial examples
- Add regression tests for every bug fixed
- The first target is to pass the stable fixture exactly or with a documented XML normalization strategy
- Keep unit tests and integration tests separate

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

Important:
- The reference witness is the lemma witness.
- Do not restrict collation to verse lines.
- Any textual block produced from parallel witness lines must support `CollatedText`.

This includes:
  - act headers
  - scene headers
  - cast lists
  - speakers
  - explicit stage directions
  - verse lines

- Use regression fixtures in:
  - `fixtures/variant_head_and_cast/`
  - `fixtures/shared_verses/`
  - `fixtures/implied_stage_directions/`

- Do not implement special-case logic for heads or cast lists.
  The collation model must remain generic.

- Shared-verse support currently guaranteed:
  - three segments in the same scene
  - two segments across two successive scenes, only when the continuation in the next scene is explicitly marked by `***`

- A shared verse may cross at most one immediate scene boundary under this rule.
  Otherwise, the shared-verse state must be closed deterministically.

- Core principle:
  the system models "collatable text", not "variant verse".
  
- Implicit stage directions (`$$TYPE$$ ... $$fin$$`) are supported as simple spans within a single speech. They must be rendered as:

  `<stage xml:id="impliciteN" type="DI" ana="#TYPE"> ... </stage>`

  containing the collated and normally numbered `<l>` elements of the span.

- Current guaranteed scope for implicit stage directions:
  - simple non-nested spans
  - same speech
  - one or more consecutive verse lines

- Out of scope for now:
  - nested spans
  - interaction with shared verses
  - interaction with scene changes
  - witness-dependent presence or absence of span markers

- TYPE validation is intentionally left open at this stage.
  Do not hard-code a closed enum yet.


## UI Policy (Tkinter V1)

A first local desktop interface using Tkinter is now part of the project scope.

This UI must remain a thin layer above the application services.

Refer to `docs/UI_TK_V1.md` for detailed UI specifications.

### Rules

- No business logic in UI modules
- UI must only call application services
- No parsing, collation, or TEI generation inside UI code
- Keep UI components small, modular, and readable
- Avoid recreating a monolithic architecture like the legacy code

### Goal

Provide a simple, stable interface for:

- text input
- validation
- TEI generation
- HTML preview
- export

### Constraint

The core engine must remain fully usable without Tkinter.


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
