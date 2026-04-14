# ANNOTATION_MARKDOWN_V1.md

## 1. Purpose

This document defines the first supported markup subset for **annotation content** in Ekdosis TEI Studio.

The goal is not to make Markdown the internal model of the project.

Instead:

- Markdown is a **lightweight authoring syntax**
- TEI remains the **canonical structured output**
- annotation content may be written with a small Markdown-inspired syntax
- this syntax must be converted to TEI during annotation-to-TEI enrichment

## 2. General principle

For annotation content:

- editors may write a limited Markdown-style syntax in the annotation dialog
- the stored annotation content may remain plain text containing that syntax
- during TEI enrichment, supported Markdown constructs must be converted into TEI elements inside `<note>`
- downstream HTML rendering should consume the resulting TEI, not raw Markdown

Therefore:

- Markdown is an **input convenience**
- TEI is the **output model**
- unsupported Markdown must not silently produce broken TEI

## 3. Scope of V1

### 3.1 Supported inline markup

The first version supports only a small editorially useful subset.

#### Italic
Accepted input:

- `*text*`
- `_text_`

TEI output:

```xml
<hi rend="italic">text</hi>
```

#### Bold
Accepted input:

- `**text**`

TEI output:

```xml
<hi rend="bold">text</hi>
```

#### Small caps
Accepted input:

- `[Text]{.smallcaps}`

TEI output:

```xml
<hi rend="smallcaps">Text</hi>
```

#### Superscript
Accepted input:

- `x^2^`

TEI output:

```xml
x<hi rend="superscript">2</hi>
```

#### Subscript
Accepted input:

- `H~2~O`

TEI output:

```xml
H<hi rend="subscript">2</hi>O
```

#### Hyperlinks
Accepted input:

- `[label](https://example.org)`

TEI output:

```xml
<ref target="https://example.org">label</ref>
```

### 3.2 Paragraphs

Blank lines in annotation content indicate paragraph breaks.

Example input:

```text
Premier paragraphe.

Second paragraphe avec *italique*.
```

TEI output:

```xml
<note>
  <p>Premier paragraphe.</p>
  <p>Second paragraphe avec <hi rend="italic">italique</hi>.</p>
</note>
```

### 3.3 Plain text fallback

Any text without supported markup remains plain text inside the note.

## 4. Out of scope for V1

The following are intentionally out of scope:

- headings
- block quotes
- lists
- tables
- images
- raw HTML
- arbitrary Pandoc attributes/classes
- footnotes inside notes
- nested complex Markdown structures
- general-purpose Markdown parsing

This is a **limited editorial subset**, not full Pandoc Markdown support.

## 5. Canonical TEI mappings

The supported mapping table is:

| Input syntax | TEI output |
|---|---|
| `*text*` or `_text_` | `<hi rend="italic">text</hi>` |
| `**text**` | `<hi rend="bold">text</hi>` |
| `[Text]{.smallcaps}` | `<hi rend="smallcaps">Text</hi>` |
| `^text^` in running text | `<hi rend="superscript">text</hi>` |
| `~text~` in running text | `<hi rend="subscript">text</hi>` |
| `[label](https://...)` | `<ref target="https://...">label</ref>` |

## 6. Escaping and ambiguity policy

Because the project already uses some special characters elsewhere in the transcription workflow, annotation-content parsing must remain local to annotation notes only.

Important rules:

- annotation Markdown parsing applies only to annotation content
- it must not affect witness transcription parsing
- if a construct is malformed, it should remain literal text rather than generating broken TEI
- priority should be given to predictable, conservative parsing over broad syntax support

## 7. Conversion stage

Markdown-to-TEI conversion for annotations must occur during the annotation enrichment step, when annotations are inserted into the TEI document.

Expected sequence:

1. user writes annotation content in the UI
2. annotation content is saved as text in `annotations.json`
3. TEI is generated normally
4. annotation enrichment resolves anchors
5. supported annotation Markdown is converted into TEI nodes inside `<note>`
6. enriched TEI is serialized
7. HTML rendering uses the TEI structure thus produced

## 8. Expected TEI note shape

For plain one-paragraph notes, TEI may remain simple if needed.

For notes containing multiple paragraphs, paragraph elements should be generated.

Example:

Input:

```text
Voir *Bérénice*.

Consulter aussi [ce site](https://example.org).
```

Output:

```xml
<note xml:id="n1" type="explicative" target="#A1S1L42">
  <p>Voir <hi rend="italic">Bérénice</hi>.</p>
  <p>Consulter aussi <ref target="https://example.org">ce site</ref>.</p>
</note>
```

## 9. Validation policy

The Markdown subset should be validated conservatively.

Recommended behavior:

- supported valid syntax -> convert to TEI
- malformed syntax -> preserve as literal text
- never emit malformed TEI because of partial Markdown parsing
- avoid destructive normalization of user content

No heavy Markdown parser is required for V1 if a small safe converter is sufficient.

## 10. UI guidance

The annotation dialog may mention that limited Markdown is accepted in note content.

For V1, the UI does not need live preview.

A simple help text or tooltip is sufficient, for example:

- italic: `*text*`
- bold: `**text**`
- small caps: `[Text]{.smallcaps}`
- superscript: `^text^`
- subscript: `~text~`
- link: `[label](https://example.org)`

## 11. HTML implications

HTML rendering must be based on the TEI structure produced after conversion.

The HTML layer should not be expected to parse raw Markdown embedded in `<note>` text.

This keeps the pipeline coherent:

annotation authoring -> TEI note structure -> HTML rendering

## 12. Testing expectations

Add focused tests for the annotation-content converter, including:

- italic conversion
- bold conversion
- small caps conversion
- superscript conversion
- subscript conversion
- hyperlink conversion
- paragraph splitting
- malformed syntax preserved as literal text
- mixed inline markup in one paragraph

## 13. Acceptance criteria

This feature is considered correctly specified for V1 when:

- a documented limited syntax exists
- editors know what markup is supported
- TEI mappings are fixed and explicit
- unsupported syntax is clearly out of scope
- the TEI layer remains the canonical structured output
