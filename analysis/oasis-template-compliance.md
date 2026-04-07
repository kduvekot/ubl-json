# OASIS Committee Specification Template Compliance Analysis

## Overview

This document compares our UBL JSON Syntax Binding DocBook XML against the
OASIS Committee Specification Template v1.05 (approved 2025-04-24) to identify
gaps and differences.

Source: [OASIS Templates Google Drive](https://drive.google.com/drive/u/0/folders/13rn2fN-6HQJt0uO3xNVM-VL4Sh8qhSoM)

---

## Gaps Ordered by Severity

### HIGH Severity

#### 1. Key Words section uses ISO/IEC Directives instead of RFC 2119/8174

**Template requires (section 3.1):**
> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
> "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this
> document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when,
> and only when, they appear in all capitals, as shown here.

Each keyword must be **bold** in the text.

**Our DocBook uses ISO/IEC Directives language instead:**
> Within the normative text of this specification, the terms "shall", "shall
> not", "should", "should not" and "may" are to be interpreted as described in
> Annex H of ISO/IEC Directives, Part 2...

**Impact:** The keyword set differs (ISO omits REQUIRED, RECOMMENDED, NOT
RECOMMENDED, OPTIONAL), uses lowercase throughout, and does not bold the
keywords. Changing this would require updating all normative language across the
entire document body.

**Note:** This is an editorial/policy decision by the document authors. The WD01
docx deliberately chose ISO/IEC Directives style. This may be intentional given
UBL's ISO/IEC 19845 lineage. Not necessarily a bug.

#### 2. Front matter fields

**Template requires (in order):** OASIS Logo, title, stage line, date, "This
version" URLs, "Previous version" URLs, "Latest version" URLs, Technical
Committee, Chairs, Secretaries, Editors, Abstract, Citation Format, Related
Work, License/Status/Notices reference.

**Our DocBook `<articleinfo>` includes:** Title, editors, pubdate, releaseinfo
(version URLs), abstract, citation, and notices.

**Handled by stylesheets:** Most front matter rendering is driven by the OASIS
XSL stylesheets from `<articleinfo>` metadata. The stylesheets extract editors,
dates, version URLs etc. from `<releaseinfo role="...">` elements and render
them in the correct template order. This is largely **not a gap** -- the
stylesheet does the work.

**Potential gaps:**
- Chairs and Secretaries are not in our `<articleinfo>` (not present in the
  WD01 docx either -- may not be finalized yet)
- Related Work section may need content

#### 3. Annex A (License, Document Status and Notices) content

**Template mandates:** Extensive boilerplate text covering OASIS copyright,
license terms, document status, IPR policy references.

**Our DocBook:** The Annex A appendix exists but its content comes from the WD01
docx. Needs verification that it contains all required boilerplate.

#### 4. Missing Appendix: Acknowledgments

**Template requires:** An informational appendix for Acknowledgments with
subsections for Leadership (Chairs), Special Thanks, and Participants.

**Our DocBook:** Has `<appendix id="A-ACKNOWLEDGMENTS">` -- this exists. Needs
verification that the content is complete.

#### 5. Missing Appendix: Changes From Previous Version

**Template requires:** An informational appendix tracking changes, with a
Revision History table.

**Our DocBook:** This is a WD01 (first version), so there are no previous
changes. This appendix can be added when WD02 is produced.

---

### MEDIUM Severity

#### 6. Missing "Changes From the Previous Version" subsection in Introduction

**Template requires:** Section 4 (Introduction) must have "Changes From the
Previous Version" as its **last subsection**, pointing to the Changes appendix.

**Our DocBook:** Introduction has no such subsection. As WD01, this is expected
-- there is no previous version. Should be added for WD02+.

#### 7. Missing annex/appendix boilerplate text

**Template requires immediately after each annex/appendix heading:**
- Normative annexes: *(This annex forms an integral part of this Specification.)*
- Informative appendices: *(This appendix does not form an integral part of
  this Specification and is informational.)*

**Our DocBook:** Neither boilerplate line is present.

**Note:** The OASIS spec-0.9 stylesheets do NOT auto-generate this text. It
would need to be added manually to the DocBook source, or the stylesheets would
need customization. UBL 2.5 CSD03 (`UBL.xml`) also does NOT include this text.
This may be an area where the template convention is not strictly followed in
practice.

#### 8. Definitions section structure

**Template requires:**
- 2.1 Definitions
  - 2.1.1 Terms Defined Elsewhere (with source references)
  - 2.1.2 Terms Defined in this Document
- 2.2 Abbreviations and Acronyms

**Our DocBook:** Has "Definitions and Acronyms" with a single `<variablelist>`
containing only abbreviations/acronyms. No distinction between terms defined
elsewhere and terms defined in this document.

**Note:** The WD01 docx has this structure. This reflects the source content,
not a conversion error.

#### 9. Section title capitalization

**Template requires:** Title Case for all headings (words of 4+ letters
capitalized).

**Our DocBook:** Inconsistent -- some titles use title case ("Digital
Signatures"), some use sentence case ("Document model", "Aggregate structures
and namespacing").

**Note:** This comes directly from the WD01 docx. A conversion fix could
auto-capitalize, but this is an editorial decision.

#### 10. Hardcoded cross-references

**Template convention:** Cross-references should use section numbers (e.g., "see
section 7").

**Our DocBook:** Most cross-references are written as literal text like "section
6.3", "section 7" rather than DocBook `<xref linkend="..."/>` elements. This
means if sections are renumbered, the references will be wrong.

**Note:** This comes from the WD01 docx which uses plain text references. The
docx doesn't have structured cross-references to convert.

---

### LOW Severity

#### 11. Code examples not numbered

**Template says:** Code snippets MUST be numbered using "Code X.Y" format with
section-dot-code numbering, with title headers and horizontal rules.

**Our DocBook:** Uses `<programlisting>` without numbering or titles. The
programlistings have `language` attributes where detected.

**Note:** The OASIS stylesheets may handle `<example>` elements with numbering.
Currently our code blocks are bare `<programlisting>` without wrapping
`<example>` elements.

#### 12. Table numbering format

**Template says:** Tables should use Roman numeral numbering (Table I, Table
II).

**Our DocBook / stylesheets:** Use Arabic numerals by default (Table 1, Table
2). Only one table exists in our document.

**Note:** This would be a stylesheet parameter change, not a DocBook source
change.

#### 13. Date format

**Template says:** "DD Month YYYY" on the front page (e.g., "23 September
2025").

**Our DocBook:** Uses `<pubdate>` with the date from the docx. The stylesheet
controls rendering format.

#### 14. IEEE reference format

**Template requires:** IEEE citation format with italicized titles: **[TOKEN]**
*Title*, details. [Online]. Available: URL

**Our DocBook:** Reference entries use `<bibliomixed>` with `<emphasis
role="bold">` for the tag. Title italicization is inconsistent.

**Note:** Minor formatting adjustment needed in `render_inline` for bibliography
sections.

#### 15. Annex subsection numbering hardcoded

**Template convention:** Annex subsections use letter-prefixed decimals (A.1,
A.2, B.1, B.2).

**Our DocBook:** Section titles within appendices include hardcoded numbering
like "B.1 Normative References", "B.2 Informative References" rather than
letting the stylesheet auto-generate the numbers.

**Note:** Same issue as body section titles with hardcoded numbers -- we should
strip these and let the stylesheet handle it. However, the WD01 docx includes
these prefixes in the heading text.

---

## Items That Are Correct

| Item | Status |
|---|---|
| Scope as section 1 | OK |
| Document Conventions with Key Words and Typographical Conventions | OK (structure) |
| Introduction as section 4 | OK |
| Safety, Security, and Data Protection Considerations (second-to-last) | OK |
| Conformance section (last numbered section) | OK |
| Annex A: License, Document Status and Notices | OK (exists) |
| Annex B: References with B.1 Normative and B.2 Informative | OK |
| `<appendix>` elements with descriptive titles (no prefix) | OK |
| `role` attribute for normative/informative distinction | Needs adding |
| Inline code with `<literal>` for MonospaceChar | OK |
| Hyperlinks with `<ulink>` | OK |
| Lists with `<itemizedlist>` and `<orderedlist>` | OK |
| Programlisting with CDATA for code blocks | OK |

---

## Recommendations

### Do Now (conversion script fixes)
1. Add `role` attributes to appendices (non-normative for Acknowledgments)
2. Add `conformance="skip"` to References appendix
3. Strip hardcoded subsection numbering from annex subsection titles (B.1, B.2)

### Editorial Decisions (not conversion issues)
4. Annex/appendix boilerplate text -- decide whether to follow template
   strictly (UBL CSD03 does not include this text)
5. Key Words convention (ISO vs RFC 2119) -- document author decision
6. Section title capitalization -- document author decision
7. Hardcoded cross-references -- would require manual editorial work
8. Missing "Changes From Previous Version" -- expected for WD01, add for WD02

### Stylesheet Configuration
9. Table numbering format (Roman vs Arabic) -- stylesheet parameter
10. Date rendering format -- stylesheet parameter
11. Code example numbering -- consider wrapping in `<example>` elements
