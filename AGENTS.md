# AGENTS.md — instructions for Codex

Last documentation refresh: 2026-06-05.

## 1. Project identity

Ekdosis-TEI Studio is an editorial tool for critical editions of French classical drama, especially seventeenth-century theatre transmitted by multiple witnesses.

The application lets non-technical editors transcribe texts in a simplified ETS pseudo-markdown format, validate that input, generate canonical XML-TEI, preview the edition in HTML, and prepare publication outputs.

The project is no longer a small proof of concept. It now has several cooperating layers:

1. input validation;
2. parsing and domain modeling;
3. witness collation;
4. canonical TEI generation;
5. HTML preview and site publication;
6. annotation and reference utilities;
7. Word/Pandoc notice import;
8. future LaTeX exports for print publication.

## 2. Highest architectural principle

The generated TEI is the canonical editorial representation.

All publication outputs must be derived from the canonical TEI whenever possible.

Expected pipeline:

```text
ETS transcription
  → validation
  → parsing / domain model / collation
  → canonical TEI
  → HTML preview / static site
  → LaTeX-Ekdosis for critical dramatic text
  → standard LaTeX for peritexts
  → PURH print template
```

Do not restore a legacy direct `ETS transcription → LaTeX` pipeline.
Do not duplicate editorial logic between TEI generation and LaTeX generation.

## 3. Sources of truth, in priority order

Use these sources in this order:

1. tests and fixtures;
2. `docs/SPEC_V2.md`;
3. this file;
4. focused module docs in `docs/`;
5. legacy documentation and `legacy/`, as reference material only.

If tests and docs disagree, prefer tests and propose a documentation correction.
If legacy code and current architecture disagree, prefer current architecture.

## 4. Current active priorities

### 4.1 Input validation

The validator is the gatekeeper. Invalid ETS pseudo-markdown must be rejected before TEI, HTML, or LaTeX generation.

Key rule: `#` is reserved for ETS markers and must not appear as ordinary transcribed text outside a valid marker.

Valid marker families include:

```text
#SPEAKER#
##CAST##
###SCENE###
####ACT####
##### whole-line variant
##### (lacune)
#####=12= metered whole-line variant in stanza contexts
```

Malformed hash markers must remain blocking errors, especially cases like `NOM#`, `######foo`, `##### foo#bar`, and `=12=#####...`.

### 4.2 TEI generation

The TEI generator must preserve editorial structure and mixed XML content:

- acts and scenes;
- cast-on-stage lists;
- speakers and speeches;
- explicit stage directions;
- implicit stage directions;
- apparatus entries `<app>`, `<lem>`, `<rdg>`;
- inline italics;
- non-breaking spaces;
- whole-line variants and lacunae;
- shared verses;
- stanza and metre data.

For shared verses, prefer the natural TEI solution: fragments of `<l>` with the same verse number and `@part` when needed.

### 4.3 LaTeX outputs

LaTeX output is now an active target, not a remote deferred feature.

There are two distinct LaTeX targets:

1. critical dramatic text: TEI → LaTeX-Ekdosis;
2. peritexts and paratexts: TEI → standard LaTeX.

Both must be assembled through a shared PURH print layer.

Do not use Ekdosis for ordinary prose notices, introductions, bibliographies, or peritexts unless a task explicitly asks for it.

See `docs/LATEX_EXPORTS.md`.

## 5. Non-goals

Do not:

- reintroduce the legacy monolithic architecture;
- put parsing, collation, TEI generation, UI code, and publication code in the same module;
- patch generated HTML, TEI, or LaTeX to compensate for invalid input;
- silently normalize editorial data that should remain semi-diplomatic;
- make Codex fix broad unrelated issues in the same patch;
- change public ETS syntax without updating tests and documentation.

## 6. Coding rules

Prefer small, reviewable patches.

Keep layers separate:

```text
src/ets/validation     input validation
src/ets/parser         ETS parsing
src/ets/domain         internal model
src/ets/collation      witness collation
src/ets/tei            TEI generation
src/ets/html           HTML preview/rendering
src/ets/site_builder   static publication
src/ets/ui/tk          Tkinter interface
src/ets/application    service orchestration
```

A future LaTeX layer should be separate, for example:

```text
src/ets/latex/
  ekdosis_from_tei.py
  standard_from_tei.py
  escaping.py
  templates.py
```

Exact names may vary, but the separation must remain.

## 7. Testing rules

Every functional change needs tests.

For LaTeX restoration, use fixtures of the form:

```text
tests/fixtures/latex/ekdosis/<case>/input.xml
tests/fixtures/latex/ekdosis/<case>/expected.tex
```

Start with minimal deterministic cases before using complete acts or plays.

Do not compare large generated documents too early if a smaller structural test would be clearer.

## 8. Legacy material

Legacy code may be mined for:

- Ekdosis macro conventions;
- escaping rules;
- successful examples;
- expected output syntax;
- old user-visible behavior.

Legacy code must not dictate architecture.

## 9. User profile reminder for interface decisions

ETS is used by literary scholars, students, and editors who may not know TEI, LaTeX, Git, Python, or digital humanities markup.

UI and diagnostics must remain explicit, calm, and actionable.

A blocking error should explain what is wrong in the transcription, not expose internal implementation details.
