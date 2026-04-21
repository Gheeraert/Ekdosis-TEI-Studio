# ETS Site Builder

## Purpose

ETS Site Builder is the static publication module of the Ekdosis TEI Studio project.

It generates a complete scholarly website from XML editorial sources.

Its goal is not to replace the TEI engine, but to publish its outputs coherently at site level.

## Current milestone status

The current implementation already provides:
- a dedicated `ets.site_builder` package with typed dataclasses and a simple config loader;
- defensive XML extractors for dramatic TEI and Métopes notices;
- automatic manifest generation for plays, notices, pages, and navigation;
- a static HTML renderer (home, play, notice page) where play pages now publish the dramatic text itself;
- a build orchestrator that cleans the output directory before each regeneration, writes pages, copies optional assets, and returns a structured build result.

This milestone already proves the publication pipeline, but the editorial model for play-level front matter must now be made more explicit.

## Editorial inputs

The module is expected to support two complementary input families:

- dramatic TEI produced by ETS;
- notice-like TEI produced with Métopes or a compatible editorial TEI subset.

A published play may therefore combine:
- one dramatic TEI source for the edited text;
- one separate scholarly notice source;
- one or more separate author-preface sources;
- optional site-level editorial pages independent from any one play.

These are distinct editorial objects and must remain distinct in the internal model.

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

## Editorial publication model

For site publication purposes, a play is no longer only a dramatic text divided into acts and scenes.
It is a **play-level editorial dossier**.

At minimum, a play publication may contain:
- the dramatic text itself;
- a scholarly notice about the play;
- one or more author prefaces;
- a dramatis personae block;
- act and scene navigation inside the dramatic text.

These elements do not all belong to the same editorial family.
Their distinction must stay explicit.

### Distinct editorial roles

#### 1. Scholarly notice
A scholarly notice is an editorial paratext written by the modern edition team.
It is a separate publication object attached to a play.

#### 2. Author preface
An author preface is also a play-level paratext, but it is **not** the same thing as a scholarly notice.
It belongs to the authorial paratext of the work.

For implementation purposes, it may reuse the same rendering pipeline as notices.
However, it must keep its own editorial role in the model and in the documentation.

#### 3. Dramatis personae
The dramatis personae is not a notice-like document.
It belongs to the dramatic text as front matter.

When available, it should preferably be extracted from the dramatic TEI itself, ideally from a `front` section containing a `castList` or an equivalent structured form.

#### 4. Acts and scenes
Acts and scenes remain internal divisions of the dramatic text and must appear after play-level front matter in the reading navigation.

## Publication model

For each play, the site builder should be able to publish:
- a main play page;
- optional act or scene pages, or at least act/scene anchors on the play page;
- a scholarly notice page;
- one or more author-preface pages;
- a dramatis personae anchor or block before Act I;
- XML download links where enabled;
- automatically generated navigation.

At site level, it should also generate:
- a home page;
- section indexes;
- static informational pages;
- a consistent menu and footer.

## Canonical play navigation order

The site builder must treat play-level navigation as an editorially ordered structure.

For each play, the canonical order is:
1. scholarly notice (if present);
2. author preface(s) (if present);
3. dramatis personae (if present);
4. Act I;
5. scenes of Act I;
6. Act II;
7. scenes of Act II;
8. and so on.

Important rules:
- this order must not depend on file discovery order;
- this order must not depend on alphabetical sort;
- this order must not be reconstructed differently in different layers;
- the same ordering rules must be applied everywhere in the generated site.

## Single source of truth for navigation

A major design rule now applies:

**The menu must be derived from one explicit editorial navigation structure, not rebuilt independently in several places.**

In practice, this means:
- `manifest.py` must build a single structured representation of play navigation;
- `render.py` must consume that structure rather than infer its own hierarchy from HTML fragments or partial XML cues;
- tests must assert that play-level front matter appears before acts and scenes.

The renderer may add anchors and presentation details, but it must not invent a different navigation tree.

## Recommended internal model evolution

The current `PlayNavigation` model should evolve so that it can represent both:
- play-level front items;
- dramatic structural items.

A minimal direction would be to support something like:
- `front_items` for notice / preface / dramatis personae;
- `acts` for dramatic divisions;
- `scenes` inside acts.

One possible shape:

```python
@dataclass(frozen=True)
class PlayFrontItemNavigation:
    kind: str  # "piece_notice", "author_preface", "dramatis_personae"
    label: str
    href: str

@dataclass(frozen=True)
class PlayNavigation:
    play_slug: str
    play_title: str
    front_items: tuple[PlayFrontItemNavigation, ...] = ()
    acts: tuple[PlayActNavigation, ...] = ()
```

The exact names may differ, but the conceptual split should remain.

## Configuration expectations

Publication configuration should now explicitly support:
- play -> notice association;
- play -> preface association(s);
- optional switches for publishing notices and prefaces;
- stable play ordering;
- predictable handling of missing references as warnings.

Examples of expected explicit mappings:
- `play_notice_map`: `play_slug -> notice_slug`
- `play_preface_map`: `play_slug -> [preface_slug1, preface_slug2, ...]`

No fuzzy matching should be introduced for these associations.

## Dramatis personae policy

The preferred policy is:
- keep dramatis personae inside the dramatic TEI domain;
- extract it from `front` / `castList` when present;
- render it on the play page before Act I;
- expose a stable anchor so the play menu can point to it.

If the corpus temporarily uses a provisional encoding, that provisional rule must be documented explicitly rather than inferred silently.

## Design principles

- XML-first;
- static output;
- no CMS;
- no database;
- explicit configuration;
- deterministic build;
- reusable HTML rendering services where appropriate;
- thin UI layer over application services;
- one source of truth for publication navigation.

## Notice and preface rendering

The rendering of scholarly notices and author prefaces may follow the same general HTML publication path.

That shared path may take inspiration from the **Impressions** project.

However:
- the implementation must preserve the editorial distinction between notice and preface;
- labels, grouping, and menu positions must reflect that distinction;
- a preface must never be silently collapsed into a generic notice in the navigation model.

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
- site title;
- subtitle;
- input directories;
- output directory;
- assets and logos;
- XML download policy;
- navigation options;
- explicit play-level editorial associations.

### `models.py`
Publication dataclasses:
- `SiteConfig`;
- `SiteManifest`;
- `PlayEntry`;
- `NoticeEntry` or a future generalized paratext entry type;
- `NoticeDocument`;
- `NoticeSection`;
- `NoticeTocEntry`;
- `NoticeNote`;
- `SitePage`;
- `NavigationItem`;
- `BuildResult`;
- play-level editorial navigation structures.

### `extractors.py`
Metadata extraction from:
- dramatic TEI;
- Métopes notice-like TEI;
- dramatic front matter such as dramatis personae when available.

### `manifest.py`
Builds the internal site manifest from XML inputs and configuration.

It must be the main place where the play-level editorial order is normalized.

### `render.py`
Generates minimal HTML pages for the current milestone.

It must render the dramatic text while respecting the editorial navigation structure already established upstream.

### `builder.py`
Orchestrates the full static site build:
- clean output directory;
- render pages;
- copy assets;
- copy downloadable XML files.

## Explicit non-goals

The first implementation should not:
- collapse dramatic TEI and notice-like TEI into a single XML source;
- depend on a database;
- require manual menu maintenance;
- reproduce the entire historical website by hand;
- infer play front matter ordering from accidental file system order.

## Notice hierarchy refinement (current)

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

## Editorial rendering refinement (long notices and prefaces)

Current notice-like rendering should emphasize editorial readability for long-form pages:
- clearer title framing (title, subtitle, byline);
- grouped metadata block with stable labels;
- nested TOC with visual distinction between parts (`group`), included documents, and internal sections;
- improved section rhythm and hierarchy for long reading;
- note rendering with simple return links to the first note call.

This remains a lightweight static HTML layer and does not aim at full visual production polish or full XSLT parity.

The same rendering family may be used for author prefaces when they are provided as separate TEI documents.

## Publication configuration layer (current)

ETS Site Builder now exposes a stronger publication configuration layer, loadable from Python dict or JSON file.

Currently configurable or expected to become configurable:
- site identity: `site_title`, `site_subtitle`, `project_name`, `editor`, `credits`, optional `homepage_intro`;
- source/output paths: `dramatic_xml_dir`, `notice_xml_dir`, `output_dir`;
- branding/assets: `assets.logos` (or `assets.logo_files`), `assets.directories` (or `assets.asset_directories`);
- publication switches: `show_xml_download`, `publish_notices`, `publish_prefaces`, `include_metadata`, `resolve_notice_xincludes`;
- explicit play-level associations: `play_notice_map`, `play_preface_map`.

Invalid mapping references should be reported as manifest warnings.

Still deferred:
- UI-driven config editing;
- advanced schema/validation system beyond typed loading and explicit runtime checks;
- complex publication orchestration beyond current builder flow.

## Testing expectations for the next navigation pass

The next pass should include regression coverage for at least these editorial situations:
- play with notice + preface + dramatis personae + acts/scenes;
- play with preface but no notice;
- play with notice but no preface;
- play with neither preface nor dramatis personae;
- stability of the canonical order in the generated menu;
- stability of the anchor used for the dramatis personae block.

## Success criterion for the next step

ETS Site Builder will be on the right path when it can publish a play not merely as “text with acts and scenes”, but as a coherent editorial object containing:
- play-level paratexts;
- dramatic front matter;
- dramatic divisions;
- one deterministic navigation model shared by manifest and rendering.
