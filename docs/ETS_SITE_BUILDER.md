# ETS Site Builder

## Purpose

ETS Site Builder is the static publication module of the Ekdosis TEI Studio project.

It generates a complete scholarly website from XML editorial sources.

Its goal is not to replace the TEI engine, but to publish its outputs coherently at site level.

## Current milestone status

The first implementation milestone now provides:
- a dedicated `ets.site_builder` package with typed dataclasses and a simple config loader;
- defensive XML extractors for dramatic TEI and Métopes notices;
- automatic manifest generation for plays, notices, pages, and navigation;
- a minimal static HTML renderer (home, play, notice page);
- a build orchestrator that cleans the output directory before each regeneration, writes pages, copies optional assets, and returns a structured build result.

This milestone keeps notice rendering on a dedicated path, now already structured for publication, while remaining intentionally limited to the documented subset.

## Current Métopes notice subset (implemented)

The current ETS Site Builder implementation supports a documented first subset for Métopes notices:
- standalone notice/chapter TEI files (`text` with `front`/`body`);
- master volume TEI files (`text type="book"`) with hierarchical `group` structures;
- optional local `xi:include` resolution with `href` and optional `xpointer="text"` semantics;
- extraction of `titleStmt/title`, optional subtitle, authors, text type, and title page lines;
- extraction of sections and basic table of contents from `group`/`div` hierarchies;
- rendering of `p`, inline `hi` (including italic), `note`, and simple `list`/`item`.

Implemented `xi:include` strategy:
- resolution is local-only (relative paths from the current XML file);
- remote URIs are ignored with warnings;
- missing or unreadable local includes are non-blocking and reported as warnings;
- build remains deterministic and does not fetch network resources.

Out of scope at this stage:
- exhaustive support for all COMMONS/Métopes TEI variants;
- advanced tables, rich figures, full bibliography semantics, and complete publication semantics;
- full XSLT-equivalent rendering parity with existing Métopes publication pipelines.

## Editorial inputs

The module is expected to support two complementary input families:

- dramatic TEI produced by ETS
- notice TEI produced with Métopes

Each play may therefore combine:
- one dramatic TEI source for the edited text
- one separate TEI notice source for scholarly paratexts

These are distinct editorial objects and must remain distinct in the internal model.

## Publication model

For each play, the site builder should be able to publish:
- a main play page
- optional act or scene pages
- a scholarly notice page
- XML download links
- automatically generated navigation

At site level, it should also generate:
- a home page
- section indexes
- static informational pages
- a consistent menu and footer

## Design principles

- XML-first
- static output
- no CMS
- no database
- explicit configuration
- deterministic build
- reusable HTML rendering services where appropriate
- thin UI layer over application services

## Notice rendering

The rendering of scholarly notices may take inspiration from the **Impressions** project.

ETS Site Builder does not need to duplicate Impressions exactly, but it should preserve the same general principles for notice publication.

## Current package structure

```text
src/ets/site_builder/
  __init__.py
  config.py
  models.py
  extractors.py
  manifest.py
  render.py
  builder.py
```

## Current responsibilities

### `config.py`
Publication configuration:
- site title
- subtitle
- input directories
- output directory
- assets and logos
- XML download policy
- navigation options

### `models.py`
Publication dataclasses:
- `SiteConfig`
- `SiteManifest`
- `PlayEntry`
- `NoticeEntry`
- `NoticeDocument`
- `NoticeSection`
- `NoticeTocEntry`
- `NoticeNote`
- `SitePage`
- `NavigationItem`
- `BuildResult`

### `extractors.py`
Metadata extraction from:
- dramatic TEI
- Métopes notice TEI

### `manifest.py`
Builds the internal site manifest from XML inputs and configuration.

### `render.py`
Generates minimal HTML pages for the current milestone.

### `builder.py`
Orchestrates the full static site build:
- clean output directory
- render pages
- copy assets
- copy downloadable XML files

## Explicit non-goals

The first implementation should not:
- collapse dramatic TEI and notice TEI into a single XML source
- depend on a database
- require manual menu maintenance
- reproduce the entire historical website by hand

## Metopes hierarchy refinement (current)

The current refinement keeps master-volume structure explicit instead of flattening included files too early.

Implemented distinction in extraction and rendering:
- structural master groups (`group`) are preserved as container nodes;
- included editorial documents from local `xi:include` are preserved as first-class nodes;
- internal sections of included documents are extracted as nested section nodes;
- TOC is generated from the same nested hierarchy with stable deterministic anchors.

Still intentionally out of scope:
- full generic Commons/Metopes coverage;
- exhaustive handling of complex tables, figures, and bibliography semantics;
- full parity with complete XSLT publication pipelines.

## Editorial rendering refinement (long notices)

Current notice rendering now emphasizes editorial readability for long-form pages:
- clearer title framing (title, subtitle, byline);
- grouped metadata block with stable labels;
- nested TOC with visual distinction between parts (`group`), included documents, and internal sections;
- improved section rhythm and hierarchy for long reading;
- note rendering with simple return links to the first note call.

This remains a lightweight static HTML layer and does not aim at full visual production polish or full XSLT parity.

## Publication configuration layer (current)

ETS Site Builder now exposes a stronger publication configuration layer, loadable from Python dict or JSON file.

Currently configurable:
- site identity: `site_title`, `site_subtitle`, `project_name`, `editor`, `credits`, optional `homepage_intro`;
- source/output paths: `dramatic_xml_dir`, `notice_xml_dir`, `output_dir`;
- branding/assets: `assets.logos` (or `assets.logo_files`), `assets.directories` (or `assets.asset_directories`);
- publication switches: `show_xml_download`, `publish_notices`, `include_metadata`, `resolve_notice_xincludes`;
- explicit play/notice pairing: `play_notice_map`.

`play_notice_map` is explicit and deterministic (`play_slug -> notice_slug`) and intentionally avoids fuzzy matching.
Invalid mapping references are reported as manifest warnings.

Still deferred:
- UI-driven config editing;
- advanced schema/validation system beyond typed loading and explicit runtime checks;
- complex publication orchestration beyond current builder flow.

## Dramatic TEI act merge module (current)

ETS now includes a dedicated XML-aware merge module for dramatic TEI act files.

Purpose:
- merge multiple act-level dramatic TEI files into one play-level dramatic TEI file;
- provide a fallback when full-play generation in one run is not yet stable;
- support migration of existing act-level TEI corpora before site publication.

Current strategy:
- parser-based merge with `lxml` (no regex or string concatenation);
- explicit input order is respected exactly;
- first file `teiHeader` is kept as merge base;
- later header differences are reported as warnings;
- incompatible title/author metadata causes a clear merge failure.

`xml:id` handling:
- deterministic collision strategy (default: rename only on collision);
- renamed IDs are prefixed by ordered input index (for example `a2_...`);
- TEI reference attributes (`target`, `wit`, `ana`, `who`, etc.) are updated when internal IDs are renamed;
- merged output prevents accidental duplicate `xml:id`.

Public API:
- core merge: `ets.site_builder.merge_dramatic_tei_acts(DramaticTeiMergeRequest)`;
- application service wrapper: `ets.application.merge_dramatic_tei_files(...)` / `DramaticTeiMergeService`.

Deliberate limits (current):
- no GUI dialog in this milestone;
- no automatic act order inference from filenames;
- no advanced bibliographic reconciliation between headers;
- no broad site builder redesign in this scope.

## Site-level publication build (current)

The builder now produces a coherent static publication tree from config + XML sources:
- `index.html` home page with site identity, optional subtitle, and optional `homepage_intro`;
- one page per dramatic TEI play under `plays/`;
- one page per notice under `notices/` when notice publication is enabled.

Navigation is generated from the manifest and remains deterministic.

Explicit play/notice association uses `play_notice_map` from configuration:
- play pages link to their associated notice when available;
- notice pages link back to the associated play;
- invalid mapping entries produce warnings without stopping the build.

When `show_xml_download` is enabled, XML sources are copied into:
- `xml/dramatic/`
- `xml/notices/`

and pages expose deterministic download links.

Branding assets are also copied deterministically:
- logo files to `assets/logos/`;
- configured asset directories to `assets/<directory-name>/`.

Still intentionally deferred:
- advanced visual design and final publication styling;
- richer asset pipeline (fingerprinting, transformations, CDN logic);
- UI integration and end-user publication wizard.

## Realistic integration coverage (current)

The test suite now includes realistic integration validation against `fixtures/metopes/realistic/`:
- a real master-volume notice (`text type="book"`) with hierarchical `group` and local `xi:include`;
- a real standalone introduction notice.

Current validation covers end-to-end publication flow (config -> manifest -> extraction -> rendering -> static build),
including explicit play/notice mapping, page generation, links between play and notice pages, and deterministic output paths.

## Application service entry point (current)

ETS Site Builder now also exposes an application/service entry point intended for future UI integration:
- a thin service wrapper around existing config + builder logic;
- structured request/result objects with explicit success/error state;
- stable access to output directory, generated pages, copied assets, counts, and warnings.

This remains fully UI-independent. UI integration itself is still deferred.

The service layer now supports two complementary entry styles:
- JSON/dict config entry points (`build_site_from_config_file`, `build_site_from_config_dict`) kept for backward compatibility;
- a richer structured publication request (`SitePublicationRequest`) intended as the primary base for future Tkinter publication dialogs.

Current structured-request normalization supports:
- explicit play grouping with one or more dramatic XML files per play (current builder scope uses the first file per play and reports a warning when extras are provided);
- explicit play ordering (`play_order`);
- multiple notice XML inputs (master volume and/or standalone notice files);
- explicit play/notice associations;
- site identity, assets, publication options, and output directory wiring.

## First Tkinter publication dialog (current)

The Tkinter application now includes a first real publication dialog:
- site identity fields (title, subtitle, intro, editor/credits);
- dramatic XML inputs with explicit play grouping;
- explicit play ordering controls;
- notice XML inputs (master + optional additional files);
- output directory and optional assets/logos;
- optional explicit play/notice mapping lines.

The dialog builds a rich in-memory `SitePublicationRequest` and calls the application service layer (`build_site_from_publication_request`).
The previous JSON config loading path remains supported as a transitional/developer workflow, but it is no longer the primary end-user path.

This UI remains intentionally limited and is not yet a full publication wizard.
Recent ergonomic refinements keep the main form scrollable while preserving a fixed bottom action bar,
so `Annuler` / `Générer le site` remain accessible on limited-height screens.
Key labels and inline hints were also clarified for play slug grouping, notice master vs additional files,
play ordering, assets directory purpose, and play/notice mapping syntax.

## First Tkinter dramatic merge entry point (current)

The Tkinter UI now also exposes a lightweight action for dramatic TEI act merge:
- menu entry under `Outils`: `Fusionner des XML dramatiques…`;
- compact dedicated dialog to:
  - select multiple dramatic XML files,
  - reorder files explicitly (up/down),
  - remove selected files,
  - choose one output XML file path.

The dialog remains intentionally thin and calls the application service layer (`merge_dramatic_tei_files`) rather than merge core internals.
User feedback is explicit and structured (`success`, `warnings`, `failure`) via standard message boxes.

Still intentionally out of scope:
- advanced merge options in UI (metadata reconciliation, xml:id policy controls);
- automatic chronology inference from filenames;
- publication builder integration beyond this standalone merge bridge.
