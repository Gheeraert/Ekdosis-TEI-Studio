# SITE_BUILDER_TARGET.md

## Purpose

This document defines the **next target state** of ETS Site Builder.

It does not replace `docs/ETS_SITE_BUILDER.md`, which documents the current implemented scope.
Instead, it records the next editorial, visual, and functional expectations so future patches remain coherent.

## Why this file exists

ETS Site Builder is no longer only a technical static exporter.
It is expected to become a convincing publication environment for literary scholarship.

The next work must therefore be guided by a clearer target:
- richer editorial structure;
- better play-level front matter handling;
- reusable configuration;
- legacy-informed visual direction;
- and better reading elegance.

## Guiding principles

1. **One XML play file per play is the preferred publication unit** whenever the TEI pipeline can provide it.
2. **Per-play notices and author prefaces remain separate editorial objects**.
3. **Dramatis personae belongs to the dramatic publication layer, not to notice rendering.**
4. **The real ETS XML -> HTML dramatic rendering engine must remain the source of truth** for dramatic reading pages.
5. **Visual and typographic quality matter** because the audience includes literary scholars accustomed to beautiful editions.
6. **Legacy sites are references for hierarchy and tone, not architecture to copy**.
7. **Work should advance in small, reviewable milestones**.

## Next editorial target: the play as publication dossier

The next target state must treat each play as a structured publication dossier rather than as a bare dramatic text.

For each play, the target publication structure is:
- main play entry;
- optional scholarly notice;
- optional author preface(s);
- optional dramatis personae section;
- dramatic text;
- acts and scenes.

This is the key conceptual shift.

The play page is not only the container of acts and scenes.
It is the publication home of all play-level editorial materials.

## Canonical menu order for a play

For each play, the target navigation order is:
1. notice of the play, if present;
2. author preface(s), if present;
3. dramatis personae, if present;
4. Act I and its scenes;
5. Act II and its scenes;
6. and so on.

This order is editorial, not technical.

Therefore:
- it must be explicit;
- it must be deterministic;
- it must not depend on file discovery order;
- it must not be rebuilt differently by multiple modules.

## Target navigation architecture

The site should expose:
- one coherent global navigation model;
- one per-play navigation model;
- stable anchors for dramatic front matter and dramatic divisions;
- foldable or collapsible act/scene trees where useful.

### Required design rule

The menu must be generated from **one explicit intermediate navigation structure**.

That structure should represent, for a play:
- front items;
- acts;
- scenes.

The renderer may style or display that structure in different ways, but it must not invent a second hierarchy from the HTML alone.

## Target handling of notices, prefaces, and dramatis personae

### 1. Scholarly notice
A scholarly notice is a separate editorial document attached to a play.
It may be rendered in a dedicated notice-like pipeline.

### 2. Author preface
An author preface is also a separate play-level editorial document.
It may reuse the same TEI extraction and rendering family as notices, but it must retain its own editorial label and its own position in navigation.

### 3. Dramatis personae
The dramatis personae should be treated as dramatic front matter.

Preferred target:
- encoded in the dramatic TEI;
- extracted from `front` / `castList` or an equivalent structured form;
- rendered on the play page before Act I;
- linked by a stable menu entry such as “Personnages”.

## Configuration target

The publication configuration should explicitly support:
- play ordering;
- play -> notice mapping;
- play -> preface(s) mapping;
- publication switches for notices and prefaces;
- optional handling policies for missing front matter;
- stable asset and branding configuration.

No fuzzy matching should be relied on for editorial associations.

## Legacy reference policy

Legacy publication files may be added under a clearly documented location such as:
- `legacy/site_racine_reference/`
- or `fixtures/site_builder/legacy_reference/`

These references may include:
- HTML exports;
- CSS files;
- images and logos;
- FTP snapshots;
- example deployed pages.

They should be used to study:
- visual hierarchy;
- primary and secondary navigation;
- collapsible menu behavior;
- editorial tone;
- placement of front matter before dramatic divisions.

They must not be copied as a monolithic technical architecture.

## Target home-page direction

The target home page should eventually be able to present:
- the editorial project;
- the corpus;
- the team;
- the institutional context;
- editorial principles;
- links to major editorial sections.

It should feel like the front page of a serious scholarly digital edition rather than a thin technical export.

## Target per-play page direction

The target per-play page should eventually offer:
- the title and key metadata of the play;
- access to notice and preface material;
- a visible dramatis personae section when available;
- the dramatic text rendered with the real ETS HTML engine;
- clear anchors for acts and scenes;
- XML access where enabled.

The result should feel like a coherent critical-edition environment, not a shell wrapped around disconnected fragments.

## Target visual direction

### 1. General principle

The target is not a flashy redesign.
The target is a **sober, elegant, literary scholarly presentation**.

### 2. What should improve

- stronger page hierarchy;
- more convincing home page;
- less “HTML fragment pasted inside a shell” feeling;
- better typography and spacing;
- more coherent color palette;
- cleaner relation between sidebar and reading area;
- better integration of dramatic front matter with the dramatic reading surface.

### 3. What should be studied in legacy material

- banner/header treatment;
- top-level navigation;
- secondary sidebar behavior;
- collapsible structure of works;
- sense of editorial seriousness;
- how institutional framing is presented.

### 4. What should not be copied

- WordPress chrome;
- OpenEdition technical furniture;
- cookie layers;
- analytics and CMS scripts;
- accidental legacy clutter.

## Recommended implementation order

### Step 1
Stabilize the editorial navigation model for one play:
- notice;
- preface(s);
- dramatis personae;
- acts;
- scenes.

### Step 2
Extend configuration to support explicit preface mapping and predictable warnings.

### Step 3
Add extraction and rendering of dramatis personae before Act I.

### Step 4
Add regression tests dedicated to canonical menu order and stable anchors.

### Step 5
Perform a visual pass once the structure is stable:
- CSS;
- colors;
- typography;
- proportions;
- better integration of the dramatic HTML rendering.

## Explicit cautions

- Do not mix all of the above in one giant patch.
- Do not sacrifice the real ETS dramatic rendering engine for easier local hacks.
- Do not let configuration drift into implicit conventions.
- Do not accept a merely functional menu if it misrepresents the editorial structure.
- Do not reintroduce manual menu maintenance.
- Do not treat the preface as an accidental notice clone.
- Do not treat dramatis personae as a notice.

## Success criterion

ETS Site Builder should progressively become capable of producing a site that is:
- technically deterministic;
- editorially structured;
- visually respectable;
- and credible for a literary scholarly audience.

At the play level in particular, success means that a user can immediately perceive the order:
- editorial paratexts first,
- dramatic front matter next,
- dramatic text after that.
