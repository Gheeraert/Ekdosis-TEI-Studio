# SPEC_V2.md

## 1. Purpose of this specification

This document defines the target behavior and architecture of the rewrite of **Ekdosis TEI Studio**.

It is the main functional specification for the modular system.

The rewrite should:
- parse a structured plain-text editorial format,
- collate multiple witnesses,
- produce XML-TEI,
- expose thin service-layer entry points,
- support UI layers without mixing them with business logic,
- support a static publication layer able to publish edited texts and scholarly notices.

## 2. Foundational principles

### 2.1 Separation of responsibilities

The system must keep distinct layers for:
- parsing
- domain model
- collation
- TEI generation
- validation
- application/service orchestration
- UI
- publication rendering
- autonomous editorial utilities

No major feature should be implemented by collapsing these layers into one script.

### 2.2 Determinism

Given the same inputs and the same configuration, the system must produce the same output.

This applies to:
- TEI generation
- XML merge tools
- text merge tools
- site publication builds
- generated navigation
- asset copying
- output file structure

### 2.3 Editorial realism

The rewrite is not only a technical cleanup. It is intended for real scholarly editorial work.

Therefore, the specification must account for:
- difficult dramatic edge cases,
- editorial paratexts,
- repeated publication workflows,
- visual quality expected by literary scholars and editors.

For the publication layer in particular, structural correctness alone is not enough. The rendered result must also be readable, hierarchically clear, typographically decent, and worthy of an audience accustomed to high-quality editions.

## 3. Core text input model

### 3.1 Plain-text transcription syntax

The parser must support, at minimum:
- `####...####` for act headers
- `###...###` for scene headers
- `##...##` for cast on stage
- `#...#` for speaker changes
- `**...**` for explicit stage directions
- `***` for shared verse segmentation
- `#####` for whole-line variant mode
- `$$TYPE$$ ... $$fin$$` for implicit stage direction spans
- `_..._` for italic text
- `~` for bound/non-breaking spacing

### 3.2 Domain model expectation

The internal domain model must represent:
- play
- act
- scene
- cast list
- speech
- verse or prose unit
- stage direction
- shared verse segment
- witness-aligned textual units

The model should make difficult editorial cases explicit rather than hiding them in formatting tricks.

## 4. Parsing requirements

The parser must:
- read structured plain-text inputs,
- detect dramatic hierarchy,
- preserve order,
- preserve witness-line grouping,
- expose structured parsed objects,
- remain independent from TEI serialization and UI logic.

## 5. Collation requirements

The collation subsystem must be separable into:
- tokenization
- alignment
- apparatus construction

The reference witness is the lemma witness.

A first implementation may provide minimal alignment and apparatus generation, but the design must remain open to:
- whole-line variants
- lacunae
- shared verses
- partial rewritings
- difficult segment boundaries

## 6. TEI generation requirements

### 6.1 Minimal first milestone

The first milestone may generate a minimal but valid TEI output.

At minimum, it should support:
- TEI root and header
- witness list
- act and scene divisions
- speeches
- verse lines
- stage directions
- critical apparatus with lemma + readings

### 6.2 Ongoing principle

TEI output should be structurally clean and progressively improved over time.

The TEI layer must not:
- perform UI work,
- depend on global mutable state,
- absorb ad hoc publication styling,
- make layout decisions unrelated to XML semantics.

## 7. Application/service layer requirements

The application layer must provide thin orchestration services for:
- TEI generation workflows,
- site publication workflows,
- dramatic TEI merge workflows,
- transcription text merge workflows,
- future reusable UI entry points.

These services should:
- accept typed requests or normalized config payloads,
- return structured results,
- surface warnings and errors cleanly,
- remain independent from Tkinter details.

## 8. UI requirements

UI code must remain thin.

It may:
- collect user input,
- build request objects,
- call services,
- display success/warning/error feedback.

It must not:
- implement parsing logic,
- implement TEI merge logic,
- implement publication rendering logic,
- duplicate service normalization.

## 9. Publication requirements: ETS Site Builder

### 9.1 Editorial inputs

The site publication layer must support at least two source families:
- dramatic TEI produced by ETS,
- scholarly notice TEI produced with Métopes.

For a given site, the model must be able to support:
- one dramatic TEI per play as the preferred publication unit,
- one per-play notice where applicable,
- one general notice independent from the plays,
- optional static institutional/editorial pages,
- assets such as logos and visual files.

### 9.2 Publication configuration

The publication workflow must support explicit configuration of:
- site identity,
- editorial context,
- dramatic inputs,
- notice inputs,
- play ordering,
- play -> notice associations,
- assets,
- output directory,
- publication switches.

This configuration must be persistable and reloadable from the UI so a site can be regenerated repeatedly after corrections.

### 9.3 Publication structure target

The target site structure is now expected to evolve toward:
- a rich home page explaining the project, the corpus, the team, and the institutional context;
- an optional general notice independent from the plays;
- for each play: a reading page for the dramatic text, plus an optional scholarly notice;
- act/scene navigation under each play;
- coherent global navigation.

### 9.4 Rendering requirements

For dramatic texts:
- the site builder must reuse the real ETS XML -> HTML rendering engine whenever available;
- it must not replace the canonical rendering with a poor local approximation;
- act/scene anchors may be injected or aligned after rendering, but the dramatic HTML engine remains the source of truth.

For notices:
- the builder may follow a dedicated notice rendering path inspired by Impressions and Métopes publication logic.

### 9.5 Navigation requirements

The site should support:
- automatic menu generation,
- one coherent sidebar/navigation model,
- per-play act/scene navigation,
- collapsible or foldable act/scene trees,
- stable deterministic anchors.

### 9.6 Visual requirements

Publication quality is not limited to technical correctness.

The publication layer must also consider:
- typographic tone,
- spacing,
- hierarchy,
- reading comfort,
- colors and page balance,
- visual coherence with the project’s literary and scholarly ambitions.

Legacy sites and archived publication outputs may be used as inspiration for:
- structure,
- collapsible navigation behavior,
- home-page content hierarchy,
- CSS direction,
- overall editorial tone.

They must not be copied as monolithic CMS architecture.

## 10. Autonomous tools

The system may include small independent editorial tools, such as:
- dramatic TEI merge,
- transcription text merge,
- future validators or converters.

These tools must remain modular, testable, and callable from thin UI entry points.

## 11. Testing requirements

The repository must use `pytest` and distinguish between:
- unit tests,
- integration tests,
- publication tests,
- UI bridge tests.

For publication work, tests should include:
- structural assertions on generated HTML,
- deterministic path assertions,
- regression checks for navigation and anchors,
- focused checks that the real rendering engine is being reused,
- visual/UX-sensitive structural checks where appropriate.

## 12. Legacy policy

Legacy code is reference material only.

Use it to:
- understand historical behavior,
- recover useful editorial ideas,
- compare publication targets.

Do not preserve its architecture.

Legacy deployed sites, FTP snapshots, and static exports may be stored under `legacy/` or another documented reference location for comparison and guided redesign.
