# Markdown Editor Module (V1)

## Scope

The `ets.markdown_editor` package adds an editorial Markdown workflow integrated in the Tk UI:

- source editing (left panel),
- read-only styled preview (right panel),
- diagnostics,
- `.md` export,
- XML-TEI export (full document and fragment).

This module is intentionally not a WYSIWYG editor and does not depend on Qt.

## Architecture

Pipeline:

`Markdown source -> parser -> typed AST/dataclasses -> preview renderer + TEI exporter`

Main files:

- `src/ets/markdown_editor/models.py`: AST and diagnostics dataclasses.
- `src/ets/markdown_editor/parser.py`: block + inline parsing and validation diagnostics.
- `src/ets/markdown_editor/preview.py`: AST to Tk `Text` read-only rendering.
- `src/ets/markdown_editor/tei_export.py`: AST to TEI (document and fragment modes).
- `src/ets/markdown_editor/service.py`: orchestration and file I/O helpers.
- `src/ets/markdown_editor/dialogs.py`: source search/replace and preview search dialogs.
- `src/ets/markdown_editor/widget.py`: integrated Tk widget (toolbar, panes, debounce, diagnostics).

## Supported Markdown Dialect (V1)

Standard:

- headings `#` to `####`
- paragraphs
- bullet/ordered lists
- blockquotes (`>`)
- rule (`---`)
- italics (`*...*`)
- bold (`**...**`)
- links (`[label](target)`)
- footnotes (`[^id]` / `[^id]: ...`)

House extensions:

- `[u]...[/u]`
- `[sup]...[/sup]`
- `[sub]...[/sub]`
- `[caps]...[/caps]`
- `[sc]...[/sc]`
- bibliography block:
  - `:::bibl`
  - `- entry`
  - `:::`

## TEI Mapping

- heading -> `<div type="section"><head>...</head></div>`
- paragraph -> `<p>`
- italics -> `<hi rend="italic">`
- bold -> `<hi rend="bold">`
- underline -> `<hi rend="underline">`
- superscript -> `<hi rend="superscript">`
- subscript -> `<hi rend="subscript">`
- capitals -> `<hi rend="caps">`
- small caps -> `<hi rend="smallcaps">`
- quote -> `<quote>`
- list -> `<list>/<item>`
- link -> `<ref target="...">`
- footnote call -> `<note place="foot">...</note>`
- bibliography block -> `<listBibl>/<bibl>`

Export modes:

- full TEI document (`<TEI><teiHeader>...<text><body>...`)
- TEI fragment (`<div type="notice">...</div>`)

## Diagnostics (V1)

The parser reports explicit diagnostics for:

- unclosed house tags,
- invalid links,
- undefined footnote references,
- orphan footnote definitions,
- malformed/unclosed `:::bibl`,
- heading level jumps (warning).

## Bibliography Extensibility

`BibliographyEntry` is intentionally structured for future evolution:

- `raw_text` (used in V1),
- `entry_id`,
- `origin`,
- `source_type`,
- `source_key`,
- `metadata`.

This preserves a clean extension path for future BibTeX/Zotero/CSL integration without redesigning the core model.

## Explicit V1 Limits

Out of scope in this implementation:

- Zotero sync,
- BibTeX import,
- CSL styling engine,
- automatic bibliography generation,
- DOCX/PDF export,
- collaborative editing.
