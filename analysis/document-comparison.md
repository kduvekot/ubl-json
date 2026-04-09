# Document Comparison: UBL JSON Syntax Binding

**Previous version:** `UBL JSON Syntax Binding.docx` (working draft, no formal version number)
**New version:** `UBL 2.5 JSON Syntax Binding version 1.0 WD01.docx` (Committee Specification Draft 01, 20 February 2026)

---

## 1. Front Matter

The previous version had only a title. **WD01 adds extensive OASIS front matter:**

- **Title** changed from "UBL 2.5 JSON Syntax Binding" to "UBL 2.5 JSON Syntax Binding Version 1.0"
- **Subtitle:** "Committee Specification Draft 01" with date "20 February 2026"
- **Version URLs** added (docs.oasis-open.org links for .docx, .html, .pdf)
- **Technical Committee** identified: OASIS Universal Business Language TC
- **Chair:** Kenneth Bengtsson
- **Editors:** Kenneth Bengtsson, Erlend Klakegg Bergheim, Kees Duvekot
- **Abstract** added
- **Citation format** added
- **Related Work** section referencing UBL 2.5 CSD03
- **License, Document Status, and Notices** header added

## 2. Structural / Section Numbering Changes

The WD01 inserts new sections, causing a renumbering of most subsequent sections:

| Topic | Previous Section | WD01 Section |
|-------|-----------------|--------------|
| Scope | 1 | 1 |
| Definitions and Acronyms | 2 | 2 |
| Document Conventions | 3 | 3 |
| Introduction | 4 | 4 |
| **UBL Semantic Library** | *(not present)* | **5 (NEW)** |
| Use of UBL JSON | 5 | 6 |
| Document model | 6 | 7 |
| Rules of representation | 7 | 8 |
| Controlled vocabularies | 8 | 9 |
| Versioning and profiles | 9 | 10 |
| Data types | 10 | 11 |
| Digital Signatures | 11 | 12 |
| JSON schemas | 12 | 13 |
| Safety, Security, and Data Protection | 13 | 14 |
| Conformance | 14 | 15 |
| Annex A | Annex A | Annex A |
| Annex B References | Annex B | Annex B |
| **Annex C Normative schemas** | *(not present)* | **Annex C (NEW)** |
| **Appendix 1 Acknowledgments** | *(not present)* | **Appendix 1 (NEW)** |

## 3. New Section: UBL Semantic Library (WD01 Section 5)

Entirely new section with two subsections:

### 5.1 Authoritative semantic definitions
- Establishes the UBL Semantic Library as the authoritative source of business semantics
- References UBL 2.5 Section 4.7 ("Semantic definitions")
- States that JSON Schemas reproduce definitions as annotations for convenience
- Mentions accompanying ODS spreadsheet, XLS spreadsheet, and HTML documentation

### 5.2 Element deprecation
- Addresses deprecated elements from UBL 2.5
- **Key decision:** Deprecated elements are **not included** in the normative JSON Schemas
- JSON instances conformant to this spec shall not contain deprecated elements
- Rationale: first release of JSON binding, no backward compatibility constraints
- Warns that automated XML-to-JSON transformation may not work where deprecated elements are present

## 4. Key Terminology Change: `$schema` replaced by `UBLEntity`

Throughout the document, all references to the `$schema` property have been replaced with `UBLEntity`:

| Previous | WD01 |
|----------|------|
| `$schema` property | `UBLEntity` property |

This affects the following sections:
- **Use of UBL JSON / Exchange of complete UBL documents** (section 5.1 / 6.1): "schema identification via the **$schema** property" -> "schema identification via the **UBLEntity** property"
- **Use of UBL JSON / Use of ABIEs as standalone payloads** (section 5.4 / 6.4): "schema identification through **$schema**" -> "schema identification through **UBLEntity**"
- **Versioning and profiles / Schema identification** (section 9.1 / 10.1): All occurrences of "$schema" changed to "UBLEntity"
- **JSON schemas / Document instances** (section 12.2 / 13.2): "$schema property" -> "UBLEntity property"
- **JSON schemas / Standalone ABIEs** (section 12.3 / 13.3): "$schema property" -> "UBLEntity property"
- **Conformance / Core conformance** (section 14.1 / 15.1): "$schema property" -> "UBLEntity property"

## 5. Definitions and Acronyms (Section 2)

### Changes:
- **WD01** adds a sub-heading "Definitions and Acronyms" under the section heading (creating a Heading 2 under Heading 1)
- Added introductory text: "This document uses the following abbreviations and acronyms:"
- Format changed from tab-separated to colon-separated (e.g., "ABIE\tAggregate..." -> "ABIE: Aggregate...")
- **New definition added:** "UBL Semantic Library: The complete set of UBL business objects and their semantic definitions"

## 6. Typographical Conventions (Section 3.2)

Minor change in the example text:
- Previous: "e.g., **$schema**, currencyID, true, ..."
- WD01: "e.g., **UBLEntity**, currencyID, true, ..."

## 7. Cross-reference Updates

All internal cross-references updated to reflect the new section numbering:
- "section 6.3" -> "section 7.3 (Document extensions)"
- "section 7" -> "section 8 (Rules of representation)"
- "section 7.1" -> "section 8.1 (Cardinality and repetition)"
- "sections 8, 9, and 11" -> "sections 9, 10, and 12"
- "section 12.4 (Normative schemas)" -> "Annex C Normative schemas"
- etc.

## 8. Controlled Vocabularies (Section 8 / 9)

**Significantly rewritten.** The previous version had specific normative requirements inline:

> "...currencyID **shall** follow ISO 4217, unitCode **should** follow UN/ECE Recommendations 20 and 21, and country or region codes **shall** follow ISO 3166."

WD01 softens this to a more general statement and moves the specifics to informative examples:

> "...producers should employ published and stable vocabularies appropriate to their business domain. Conformance to external vocabularies is determined by the profile or community..."
>
> "Common examples of controlled vocabularies include ISO 4217 for currency codes, UN/ECE Recommendations 20 and 21 for units of measure, and ISO 3166 for country and region codes."

## 9. Nullability and Omission (Section 7.2 / 8.2)

**Rewritten for clarity.** The previous version mentioned `_n` suffix variants in a single paragraph. WD01 splits this into two clearer paragraphs:
- First paragraph: unchanged (JSON null prohibition)
- Previous had "Optional properties **should** be omitted" -> WD01 changes to "Optional properties **shall** be omitted"
- Second paragraph: clearer explanation of `_n` schema-level artefacts, explicitly stating they "do not constitute instance property names"
- Third paragraph (new): "The presence of such schema variants does not imply acceptance of the JSON literal null in instance documents."

## 10. Error Handling and Strictness (Section 7.4 / 8.4)

Minor wording change in one bullet point:
- Previous: "...a date or time not matching the prescribed regular expression"
- WD01: "...a date or time not matching the format prescribed in section 11.1 (UBL unqualified data types)"

## 11. Enveloped Signature Structure (Section 11.2.2 / 12.2.2)

### Changes:
- Heading case changed: "Enveloped Signature Structure" -> "Enveloped signature structure"
- **Normative tightening** of ExtensionContent: WD01 adds: "The ExtensionContent member of such an extension shall be a JSON object containing a mandatory property named **signatures**. The value of signatures shall be an array of one or more JSON Web Signature (JWS) objects expressed using the JSON Serialization defined in [RFC7515]. **No other properties shall appear in the ExtensionContent object unless defined by a community profile.**"
- Cross-reference updated: "section 6.3" -> "section 7.3"

## 12. Canonicalization (Section 11.3 / 12.3)

Wording refinement:
- Previous: "The canonicalization input shall exclude the **UBLExtensions element** containing the signature itself."
- WD01: "The canonicalization input shall exclude only the **extension object whose ExtensionURI matches the signature URI** and contains the signature itself."

This is more precise — only the specific extension object with the signature is excluded, not the entire UBLExtensions array.

## 13. JSON Schemas / Normative Schemas (Section 12.4 / 13.4)

**Major restructuring.** The previous version listed all schemas (common + document) inline within section 12.4. WD01 moves this to **Annex C** and replaces section 13.4 with a brief paragraph:

> "A complete and authoritative listing of all normative JSON Schemas distributed with this specification is provided in Annex C Normative schemas..."

## 14. Schema File Naming Convention Change

Schema file names now include the UBL version number:

| Previous | WD01 |
|----------|------|
| `CommonAggregateComponents-2.json` | `CommonAggregateComponents-2.5.json` |
| `CommonBasicComponents-2.json` | `CommonBasicComponents-2.5.json` |
| `QualifiedDataTypes-2.json` | `QualifiedDataTypes-2.5.json` |
| `UnqualifiedDataTypes-2.json` | `UnqualifiedDataTypes-2.5.json` |
| `CommonExtensionComponents-2.json` | `CommonExtensionComponents-2.5.json` |
| `SignatureAggregateComponents-2.json` | `SignatureAggregateComponents-2.5.json` |
| `SignatureBasicComponents-2.json` | `SignatureBasicComponents-2.5.json` |
| `ApplicationResponse-2.json` | `UBL-ApplicationResponse-2.5.json` |
| `Invoice-2.json` *(implied)* | `UBL-Invoice-2.5.json` |
| etc. | etc. |

Document schemas also gain a `UBL-` prefix.

## 15. Schema Descriptions (Annex C)

WD01 adds descriptions for schemas that were previously blank:
- **Qualified Data Types:** Now includes a full description explaining CCTS qualified types
- **Unqualified Data Types:** Now includes a description explaining CCTS derivation
- **Common Extension Components:** Now includes a description referencing section 7.3

## 16. Document Schema Listing

- Previous version had a placeholder "[...]" between Bill of Lading and Work Report, implying the full list was elided
- WD01 **lists all 95 document schemas** in full (C.2.1 through C.2.95), with numbered sub-headings, descriptions, normative schema paths, and identifiers
- **New document types** not in the previous abbreviated list include: BusinessCard, BusinessInformation, DeliveryNote, InvoiceStatusRequest, InvoiceStatusResponse, Manifest, PurchaseReceipt, WasteMovement, WasteNotification, and many others

## 17. New Section: Conformance / Semantic Conformance (WD01 Section 15.2)

Entirely new conformance clause:

> "A UBL JSON instance is considered semantically conformant when it correctly represents business information in accordance with the semantic definitions of the UBL data model as described in section 5 UBL Semantic Library."

Requirements:
- Each element/component used consistently with its normative definition in the JSON schemas and documentation
- The instance conveys information consistent with the business semantics of the UBL data model

## 18. Annex A: License, Document Status and Notices

Previously empty/minimal. WD01 adds full OASIS boilerplate:
- A.1 Document Status
- A.2 License and Notices (full OASIS IPR policy text, copyright, disclaimers)

## 19. Annex B: References

### Changes:
- Added introductory text about normative vs. informative references and hyperlink validity
- **[UBL] reference updated:** "Committee Specification Draft 01, August 2025" -> "Committee Specification Draft 03, February 2026"
- **Normative references reorganized:**
  - Removed from normative: [ISO 4217], [ISO 3166], [UNECE Rec 20/21] (moved to informative, consistent with the controlled vocabularies softening in section 9)
  - **Added to normative:** [ISO-8601] (ISO 8601-1:2019, date and time representations)
- **Informative references reorganized:**
  - Added: [ISO 4217], [ISO 3166], [UNECE Rec 20/21] (moved from normative)
  - Removed from informative: [BDNDR] is still present but reordered

## 20. New: Appendix 1 Acknowledgments

Lists **Special Thanks** (17 individuals) and **Participants** (27 individuals) with their affiliations. This section is informational and does not form part of the specification.

## 21. Code Example Formatting

WD01 wraps JSON code examples in markdown-style fenced code blocks (` ```json `) which was not present in the previous version. The actual content of the examples is unchanged.

## 22. Heading Case Changes

Several heading titles changed from Title Case to Sentence case:
- "Enveloped Signature Structure" -> "Enveloped signature structure"
- "Detached Signatures" -> "Detached signatures"
