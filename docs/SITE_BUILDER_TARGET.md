# SITE_BUILDER_TARGET.md

## Purpose

This document defines the **next target state** of ETS Site Builder.

It does not replace `docs/ETS_SITE_BUILDER.md`, which documents the current implemented scope.
Instead, it records the next editorial, visual, and functional expectations so future patches remain coherent.

## Why this file exists

ETS Site Builder is no longer only a technical static exporter.
It is now expected to become a convincing publication environment for literary scholarship.

The current implementation already proves:
- XML discovery,
- manifest generation,
- site build orchestration,
- notice rendering,
- dramatic HTML publication,
- navigation generation,
- UI entry points.

But the next work must be guided by a clearer target:
- richer editorial structure,
- reusable configuration,
- legacy-informed visual direction,
- and better reading elegance.

## Guiding principles

1. **One XML play file per play is the preferred publication unit** whenever the TEI pipeline can provide it.
2. **Per-play notices and general notices remain separate editorial objects**.
3. **The real ETS XML -> HTML dramatic rendering engine must remain the source of truth** for dramatic reading pages.
4. **Visual and typographic quality matter** because the audience includes literary scholars accustomed to beautiful editions.
5. **Legacy sites are references for hierarchy and tone, not architecture to copy**.
6. **Work should advance in small, reviewable milestones**.

## Legacy reference policy

Legacy publication files may be added under a clearly documented location such as:
- `legacy/site_racine_reference/`
- or `fixtures/site_builder/legacy_reference/`

These references may include:
- HTML exports,
- CSS files,
- images and logos,
- FTP snapshots,
- example deployed pages.

They should be used to study:
- visual hierarchy,
- primary and secondary navigation,
- collapsible menu behavior,
- page proportions,
- banner/header usage,
- home-page editorial framing,
- color and typographic direction.

They should **not** be copied wholesale as a WordPress/OpenEdition stack.

## Target editorial structure

### 1. Home page

The home page should become a real editorial page, not just a title + short intro.

It should be able to present:
- what corpus or edition is being published,
- under which project title,
- by which editorial team,
- in which institutional context,
- with which financial or institutional support,
- and, where relevant, links toward the corpus structure.

### 2. General notice independent from the plays

The site model should support one **general notice** not attached to a single play.

This may provide:
- a project presentation,
- editorial principles,
- corpus rationale,
- methodological notes,
- bibliography,
- historical framing.

This notice should appear in site-level navigation as a first-class editorial page.

### 3. Per-play publication structure

For each play, the target structure is:
- play reading page,
- optional play-specific notice in Métopes TEI,
- then dramatic divisions by act and scene.

### 4. Navigation target

The navigation should eventually support a coherent hierarchy such as:
- Accueil
- Notice générale
- Pièces
  - Britannicus
    - Notice
    - Acte 1
      - Scène 1
      - Scène 2
    - Acte 2
      - ...
  - Andromaque
    - Notice
    - ...

### 5. Foldable navigation

Acts and scenes should be foldable/unfoldable in the sidebar, in the spirit of the current legacy site.

Implementation may use:
- semantic HTML (`details` / `summary`),
- or a very small JS enhancement,
- but should avoid heavy frameworks.

## Target UI evolution

### Publication dialog persistence

The site generation dialog should support:
- **Load config**
- **Save config**

next to the build action.

Reason:
- publication sites will be regenerated repeatedly,
- editors will need to preserve the chosen files, ordering, assets, notices, and identity settings,
- the JSON config should become a saved project artifact, not a hidden technical afterthought.

This persistence must round-trip cleanly between:
- the Tkinter form,
- the application request model,
- and the serialized config file.

## Target visual direction

### 1. General principle

The target is not a flashy redesign.
The target is a **sober, elegant, literary scholarly presentation**.

### 2. What should improve

- stronger page hierarchy,
- more convincing home page,
- less “iframe pasted inside a shell” feeling,
- better typography and spacing,
- more coherent color palette,
- cleaner relation between sidebar and reading area,
- better integration of the dramatic HTML into the page shell.

### 3. What should be studied in legacy material

- banner/header treatment,
- top-level navigation,
- secondary sidebar behavior,
- collapsible structure of works,
- sense of editorial seriousness,
- how institutional framing is presented.

### 4. What should not be copied

- WordPress chrome,
- OpenEdition technical furniture,
- cookie layers,
- analytics and CMS scripts,
- accidental legacy clutter.

## Implementation order recommended

### Step 1
Persist and reload publication config from the UI.

### Step 2
Extend the publication model to support:
- richer home page content,
- general notice independent from plays,
- clearer site-level editorial pages.

### Step 3
Refine navigation hierarchy and implement foldable act/scene trees.

### Step 4
Perform a dedicated visual pass:
- CSS,
- colors,
- typography,
- proportions,
- better integration of the dramatic HTML rendering.

## Explicit cautions

- Do not mix all of the above in one giant patch.
- Do not sacrifice the real ETS dramatic rendering engine for easier local hacks.
- Do not accept a merely functional layout if it clearly looks crude to the intended public.
- Do not let UI persistence logic drift into business logic.
- Do not reintroduce manual menu maintenance.

## Success criterion

ETS Site Builder should progressively become capable of producing a site that is:
- technically deterministic,
- editorially structured,
- visually respectable,
- and credible for a literary scholarly audience.
