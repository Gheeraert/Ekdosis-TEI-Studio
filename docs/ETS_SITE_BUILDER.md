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
- a minimal static HTML renderer (home, play, notice placeholder page);
- a build orchestrator that cleans the output directory before each regeneration, writes pages, copies optional assets, and returns a structured build result.

This milestone intentionally keeps notice rendering as a separate path prepared for a later dedicated transformation.

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
