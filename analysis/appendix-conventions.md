# OASIS Appendix Conventions: Word Templates vs DocBook Stylesheets

## Overview

This document describes the differences between how the OASIS Word document
templates and the OASIS DocBook XSL stylesheets handle appendices (annexes).
Understanding these differences is essential for correct conversion from the
Word-based authoring format to DocBook XML.

## Source Materials

- **OASIS Word Templates**: Committee Specification Templates v1.05 (approved
  2025-04-24), from the [OASIS Google Drive](https://drive.google.com/drive/u/0/folders/13rn2fN-6HQJt0uO3xNVM-VL4Sh8qhSoM)
- **OASIS DocBook Stylesheets**: spec-0.9, from the `ubl-2.5` branch of
  `kduvekot/ubl` (`db/spec-0.9/stylesheets/`)
- **UBL 2.5 DocBook source**: `UBL.xml` on the `ubl-2.5` branch of
  `kduvekot/ubl`

---

## Word Template Conventions

### Annex vs Appendix Distinction

The OASIS Word templates define two categories of back matter:

| Type | Labeling | Meaning |
|---|---|---|
| **Annex** | Letters (A, B, C, ...) | **Normative** -- forms an integral part of the specification |
| **Appendix** | Numbers (1, 2, 3, ...) | **Informational** -- supplemental, not required |

### Required Subtitle Text

The Word templates mandate subtitle text under every annex and appendix heading:

- **Under each Annex:**
  > *(This annex forms an integral part of this Specification.)*

- **Under each Appendix:**
  > *(This appendix does not form an integral part of this Specification and is informational.)*

For Committee Notes, "Specification" is replaced with "document".

### Mandatory Ordering

| Position | Content | Type |
|---|---|---|
| Annex A | License, Document Status and Notices | Normative |
| Annex B | References | Normative |
| Annex C+ | Additional annexes as needed | Normative |
| Appendix 1 | Acknowledgments | Informational |
| Appendix 2 | Changes From Previous Version | Informational |
| Appendix 3+ | Additional appendices as needed | Informational |

### Subsection Numbering

- Annex subsections use letter-prefixed decimals: A.1, A.2, B.1, B.2, C.1.1
- Appendix subsections use unnumbered sub-headings

### Heading Style

All annex and appendix headings use **Heading 1** style. Their titles include the
prefix in the text itself:
- `[Heading1] Annex A License, Document Status and Notices`
- `[Heading1] Appendix 1 Acknowledgments`

---

## DocBook Stylesheet Conventions (spec-0.9)

### Single Element Type

DocBook uses a single `<appendix>` element for all back matter. There is **no
separate element** for normative annexes vs informational appendices.

### Labeling: Always Letters, Always "Appendix"

The `appendix.autolabel` parameter defaults to `'A'` (uppercase letters).
Every `<appendix>` is rendered with a sequential letter label:

- `Appendix A. Title`
- `Appendix B. Title`
- `Appendix C. Title`
- `Appendix D. Title`

The stylesheets **never** use the word "Annex" and **never** use numeric
labeling. The L10n templates confirm:

- title context: `"Appendix %n. %t"`
- title-numbered: `"Appendix %n %t"`
- xref-number: `"Appendix %n"`
- TOC heading: `"Appendixes"`

### Normative/Informative Distinction via `role` Attribute

The distinction between normative and informative is handled entirely through
the `role` attribute on `<appendix>`, which causes the stylesheet to append or
prepend an annotation:

| `role` value | Rendered text | Position | Style |
|---|---|---|---|
| *(none)* | *(no annotation)* | -- | Implicitly normative |
| `normative` | `(Normative)` | After title | OASIS |
| `non-normative` | `(Non-Normative)` | After title | OASIS |
| `informative` | `(Informative)` | After title | OASIS |
| `iso-normative` | `(normative)` | Before title | ISO |
| `iso-informative` | `(informative)` | Before title | ISO |

Example rendered output from the spec-0.9 template:
```
Appendix A. An Annex
Appendix B. A Normative Annex (Normative)
Appendix C. A Non-normative Annex (Non-Normative)
Appendix D. An Informative Annex (Informative)
Appendix E. (normative) An ISO-normative Annex
Appendix F. (informative) An ISO-informative Annex
Appendix G. Acknowledgements (Non-Normative)
Appendix H. Revision History
```

### No Automatic Subtitle Text

The stylesheets do **not** generate the normative/informative subtitle text
("This annex forms an integral part..."). This text would need to be included
manually in the DocBook source if desired, or added as a stylesheet
customization.

### Other Relevant Attributes

| Attribute | Purpose | Used by |
|---|---|---|
| `conformance="skip"` | Excludes the appendix from Schematron validation; allows mixed content alongside subsections | References appendix |
| `condition="oasis"` | Marks content as OASIS-specific (not included in ISO rendering) | Notices appendix |

---

## How UBL 2.5 Uses These Conventions

The UBL 2.5 DocBook source (`UBL.xml` on the `ubl-2.5` branch) has 11 active
appendices, all using letter labels:

| Label | ID | Title | Attributes |
|---|---|---|---|
| A | `A-REFERENCES` | References | `conformance="skip"` |
| B | `A-RELEASE-NOTES` | Release Notes | `role="non-normative"` |
| C | `A-REVISION-HISTORY` | Revision History | `role="non-normative"` |
| D | `A-THE-UBL-DATA-MODEL` | The UBL 2.5 Data Model | `role="non-normative"` |
| E | `A-DATA-TYPE-QUALIFICATIONS-IN-UBL` | Data Type Qualifications in UBL | `role="non-normative"` |
| F | `A-UBL-CODE-LISTS-AND-TWO-PHASE-VALIDATION` | UBL 2.5 Code Lists and Two-phase Validation | `role="non-normative"` |
| G | `A-UBL-EXAMPLE-DOCUMENT-INSTANCES` | UBL 2.5 Example Document Instances | `role="non-normative"` |
| H | `A-ALTERNATIVE-REPRESENTATIONS...` | Alternative Representations of the UBL 2.5 Schemas | `role="non-normative"` |
| I | `A-THE-OPEN-EDI-REFERENCE-MODEL...` | The Open-edi reference model perspective of UBL | `role="non-normative"` |
| J | `A-ACKNOWLEDGEMENTS` | Acknowledgements | `role="non-normative"` |
| K | `A-NOTICES` | Notices | `condition="oasis"` |

Pattern: References (A) has no `role` (implicitly normative). All other content
appendices use `role="non-normative"`. Notices uses `condition="oasis"`.

---

## Mapping: Word Template to DocBook

When converting from the Word template format to DocBook:

| Word source | DocBook target |
|---|---|
| `Annex A License, Document Status and Notices` | `<appendix id="A-LICENSE-DOCUMENT-STATUS-AND-NOTICES"><title>License, Document Status and Notices</title>` |
| `Annex B References` | `<appendix id="A-REFERENCES" conformance="skip"><title>References</title>` |
| `Annex C Normative schemas` | `<appendix id="A-NORMATIVE-SCHEMAS"><title>Normative schemas</title>` |
| `Appendix 1 Acknowledgments` | `<appendix id="A-ACKNOWLEDGMENTS" role="non-normative"><title>Acknowledgments</title>` |

Key transformations:
1. **Strip the "Annex X" / "Appendix N" prefix** from the title -- the label is auto-generated
2. **Do not reproduce the letter/number distinction** -- DocBook uses sequential letters for all
3. **Map normative/informative intent to `role` attribute:**
   - Normative annexes: no `role` attribute (or `role="normative"` if explicit marking desired)
   - Informative appendices: `role="non-normative"`
4. **References appendix**: add `conformance="skip"` (allows mixed content structure)
5. **The normative/informative subtitle text** is not generated by the stylesheets and must be
   included in the DocBook source if desired

---

## Schematron Validation (spec-0.9)

The `oasis-spec-note.sch` Schematron file in spec-0.9 enforces:

1. **No hanging content**: `appendix[section]` elements must not contain direct
   child elements other than `<section>` and `<title>` (unless
   `conformance='skip'`)
2. **ID validation**: `appendix[not(@conformance='skip')]` elements must have
   valid identifiers matching the expected pattern
