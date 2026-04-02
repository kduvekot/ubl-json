# Annex vs Appendix: Implementation Design

## Problem Statement

The OASIS Word template distinguishes between:
- **Annex** (normative, letter-labeled: A, B, C)
- **Appendix** (informational, number-labeled: 1, 2, 3)

The OASIS DocBook stylesheets (spec-0.9) currently treat all `<appendix>`
elements uniformly as "Appendix A, B, C, D..." with sequential letters. This
document describes what changes would be needed across the DocBook source,
XSL stylesheets, and validation to support the distinction.

---

## 1. DocBook Source Marking

### Approach: Use the existing `role` attribute

DocBook 4.5 has no `<annex>` element. All back matter uses `<appendix>`. The
`role` attribute is already the established OASIS convention for marking
normative/informative intent. No custom attributes or processing instructions
are needed.

### Convention

| `role` value | Classification | Label | Numbering |
|---|---|---|---|
| *(none)* | Normative (default) | Annex | Letter (A, B, C) |
| `normative` | Normative (explicit) | Annex | Letter (A, B, C) |
| `iso-normative` | Normative (ISO style) | Annex | Letter (A, B, C) |
| `non-normative` | Informational | Appendix | Number (1, 2, 3) |
| `informative` | Informational | Appendix | Number (1, 2, 3) |
| `iso-informative` | Informational (ISO style) | Appendix | Number (1, 2, 3) |

### Example DocBook source

```xml
<appendix id="A-LICENSE-DOCUMENT-STATUS-AND-NOTICES">
  <title>License, Document Status and Notices</title>
  <!-- no role = normative = "Annex A" -->

<appendix id="A-REFERENCES" conformance="skip">
  <title>References</title>
  <!-- no role = normative = "Annex B" -->

<appendix id="A-NORMATIVE-SCHEMAS">
  <title>Normative schemas</title>
  <!-- no role = normative = "Annex C" -->

<appendix id="A-ACKNOWLEDGMENTS" role="non-normative">
  <title>Acknowledgments</title>
  <!-- role="non-normative" = informational = "Appendix 1" -->
```

### Policy decision needed

What should `<appendix>` with no `role` default to? Options:
- **Normative (annex)** — matches OASIS convention where annexes are the
  default and appendices are the exception. This is the recommended approach.
- **Current behavior (plain "Appendix")** — safer for backward compatibility.

---

## 2. Stylesheet Changes

### 2.1 Numbering: `label.markup` template

**Currently** (in `db/spec-0.9/docbook/xsl/common/labels.xsl:152-188`):

```xml
<xsl:template match="appendix" mode="label.markup">
  <xsl:number from="book|article" count="appendix" format="{$format}" level="any"/>
</xsl:template>
```

This counts ALL `<appendix>` elements sequentially in a single sequence.

**Needed**: Override in the OASIS customization stylesheets to split into two
independent sequences:

```xml
<xsl:template match="appendix" mode="label.markup">
  <xsl:choose>
    <xsl:when test="@label">
      <xsl:value-of select="@label"/>
    </xsl:when>
    <xsl:when test="@role='non-normative' or @role='informative'
                    or @role='iso-informative'">
      <!-- Informational: number sequence -->
      <xsl:number from="book|article"
                  count="appendix[@role='non-normative'
                         or @role='informative'
                         or @role='iso-informative']"
                  format="1" level="any"/>
    </xsl:when>
    <xsl:otherwise>
      <!-- Normative (or no role): letter sequence -->
      <xsl:number from="book|article"
                  count="appendix[not(@role='non-normative'
                         or @role='informative'
                         or @role='iso-informative')]"
                  format="A" level="any"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>
```

The `count` attribute in `<xsl:number>` supports XPath predicates, so each
sequence counts independently. Subsection numbering (A.1, A.2 vs 1.1, 1.2)
inherits automatically via the parent component's `label.markup` call in the
section template.

### 2.2 Title prefix: `object.title.template`

**Currently** (in `oasis-specification-html.xsl:534-537`):

```xml
<xsl:template match="appendix" mode="object.title.template">
  <xsl:text>Appendix </xsl:text>
  <xsl:apply-imports/>
</xsl:template>
```

**Needed**: Conditional prefix:

```xml
<xsl:template match="appendix" mode="object.title.template">
  <xsl:choose>
    <xsl:when test="@role='non-normative' or @role='informative'
                    or @role='iso-informative'">
      <xsl:text>Appendix </xsl:text>
    </xsl:when>
    <xsl:otherwise>
      <xsl:text>Annex </xsl:text>
    </xsl:otherwise>
  </xsl:choose>
  <xsl:apply-imports/>
</xsl:template>
```

The `<xsl:apply-imports/>` resolves to the base DocBook template which looks up
the `article/appendix` L10n context, returning `"%n %t"` (no prefix). So the
final result is `"Annex A. Title"` or `"Appendix 1. Title"`.

### 2.3 Title annotations: `title.markup` (no change needed)

The existing `title.markup` template already handles the `(Normative)` /
`(Non-Normative)` / `(Informative)` annotations via `@role`. No changes needed
— these annotations are independent of the Annex/Appendix label.

### 2.4 TOC heading

**Currently** (in `oasis-specification-html.xsl:522`):

```xml
<h3>Appendixes</h3>
```

**Needed**: Either split into two headings or use a combined heading:

Option A — Two separate headings:
```xml
<xsl:if test="$apps[not(@role='non-normative' or @role='informative'
              or @role='iso-informative')]">
  <h3>Annexes</h3>
  <!-- render normative appendix TOC entries -->
</xsl:if>
<xsl:if test="$apps[@role='non-normative' or @role='informative'
              or @role='iso-informative']">
  <h3>Appendixes</h3>
  <!-- render informative appendix TOC entries -->
</xsl:if>
```

Option B — Single combined heading (simpler):
```xml
<h3>Annexes and Appendixes</h3>
```

### 2.5 Cross-references (`<xref>`)

The L10n templates for cross-references are static per element name:

| Context | Current value |
|---|---|
| `xref-number` | `"Appendix %n"` |
| `xref-number-and-title` | `"Appendix %n, %t"` |

These cannot vary per element instance. Solution: override the
`object.xref.markup` template for `<appendix>` to dynamically choose "Annex"
vs "Appendix" rather than relying on L10n lookup.

### 2.6 FO (PDF) stylesheets

The same changes are needed in the FO stylesheets:
- `oasis-specification-fo-a4.xsl` lines 650-653 (`object.title.template`)
- `oasis-specification-fo-a4.xsl` lines 639-640 (TOC heading)

---

## 3. Files Requiring Modification

| File | Changes |
|---|---|
| `oasis-specification-html.xsl` | `object.title.template`, TOC heading, `label.markup` override, xref override |
| `oasis-specification-fo-a4.xsl` | Same as HTML |
| `oasis-2020-specification-html.xsl` | Same pattern |
| `oasis-2025-spec-note-html.xsl` | Same pattern |
| `oasis-2025-spec-note-fo-a4.xsl` | Same pattern |
| `oasis-spec-note.sch` | Add ordering validation rule |
| CSS files | Likely no changes (styles use class names, not text content) |

Each stylesheet file needs the same three changes:
1. Add `label.markup` override (split numbering)
2. Modify `object.title.template` (conditional prefix)
3. Add xref override (conditional prefix in cross-references)

---

## 4. Ordering Validation

### 4.1 Schematron (recommended)

The spec-0.9 already has `oasis-spec-note.sch` (494 lines, XSLT2 query
binding). A new pattern can enforce that informational appendices always come
after normative annexes:

```xml
<pattern>
  <rule context="appendix[@role='non-normative' or @role='informative'
                           or @role='iso-informative']">
    <assert test="not(following-sibling::appendix[
                    not(@role='non-normative'
                        or @role='informative'
                        or @role='iso-informative')])"
    >ERROR: Informative appendixes must come after all normative
     annexes. Found normative annex after informative appendix
     "<value-of select="title"/>".</assert>
  </rule>
</pattern>
```

This checks that no informative appendix has a normative sibling after it.

### 4.2 DTD/RelaxNG (not viable)

DocBook 4.5's DTD cannot constrain element ordering based on attribute values.
All back matter uses `<appendix>` regardless of role. RelaxNG could
theoretically define separate patterns, but this would break DocBook
compatibility.

### 4.3 XSLT warnings (supplementary)

An `<xsl:message>` warning can be added to the appendix processing template:

```xml
<xsl:if test="self::appendix[not(@role='non-normative'
              or @role='informative' or @role='iso-informative')]
              and preceding-sibling::appendix[@role='non-normative'
              or @role='informative' or @role='iso-informative']">
  <xsl:message>WARNING: Normative annex after informative appendix</xsl:message>
</xsl:if>
```

This provides runtime warnings during XSLT processing but is less rigorous
than Schematron validation.

### Recommendation

Use **Schematron** as the primary validation mechanism (catches errors before
processing) and **XSLT `<xsl:message>`** as a supplementary warning (catches
errors if Schematron is skipped).

---

## 5. Backward Compatibility

### Existing documents without `role` attributes

If `<appendix>` with no `role` defaults to normative (annex), existing
documents that don't use `role` attributes will render as "Annex A, B, C..."
instead of the current "Appendix A, B, C...". This is a breaking change.

### Mitigation options

1. **Opt-in via parameter**: Add an `appendix.annex.distinction` parameter
   (default `0`). When `0`, all appendices behave as today. When `1`, the
   role-based distinction is active. Existing documents are unaffected.

2. **Require explicit `role`**: Only change behavior when `role` is explicitly
   set. No `role` = current behavior ("Appendix" with letters). This is the
   safest option but means authors must explicitly mark normative annexes.

3. **Breaking change**: Accept that all appendices without `role` become
   annexes. Simple but requires updating existing documents.

---

## 6. Summary

### Minimal change set for the DocBook source
- Add `role="non-normative"` to informational appendices
- Add `conformance="skip"` to References appendix
- Normative annexes need no `role` (or explicit `role="normative"`)

### Minimal change set for stylesheets
- One new template: `label.markup` override (~20 lines per stylesheet)
- One modified template: `object.title.template` (~10 lines per stylesheet)
- One new template: xref override (~15 lines per stylesheet)
- One TOC heading change per stylesheet
- One Schematron rule (~8 lines)
- Applied across ~5 stylesheet files

### Total estimated scope
- ~45 lines of XSL per stylesheet file x 5 files = ~225 lines of XSL
- ~8 lines of Schematron
- ~4 attribute additions in DocBook source
