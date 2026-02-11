# Source file provenance

This document records the origin of all input files used by the JSON schema
generator.  When CSD03 is published the `csd02` URLs below will have `csd03`
equivalents at `https://docs.oasis-open.org/ubl/csd03-UBL-2.5/`.

---

## gc/ — Genericode entity files

These are the authoritative input files for the generator.  All JSON schemas
are derived from these GC files alone; no XSD parsing is required at runtime.

| File | Rows | Origin | Stable URL (CSD02) |
|------|------|--------|---------------------|
| `UBL-Entities-2.5.gc` | 5 854 | CSD03 distribution archive `mod/` | [UBL-Entities-2.5.gc](https://docs.oasis-open.org/ubl/csd02-UBL-2.5/mod/UBL-Entities-2.5.gc) |
| `UBL-Signature-Entities-2.5.gc` | 5 | CSD03 distribution archive `mod/` | [UBL-Signature-Entities-2.5.gc](https://docs.oasis-open.org/ubl/csd02-UBL-2.5/mod/UBL-Signature-Entities-2.5.gc) |
| `UBL-Endorsed-Entities-2.5.gc` | 5 854 | CSD03 distribution archive `endorsed/mod/` | [UBL-Endorsed-Entities-2.5.gc](https://docs.oasis-open.org/ubl/csd02-UBL-2.5/endorsed/mod/UBL-Endorsed-Entities-2.5.gc) |
| `UBL-Extension-Entities-2.5.gc` | 11 | **Derived** — see below | n/a (no official GC exists) |

### UBL-Extension-Entities-2.5.gc

No official Genericode file exists for the UBL Common Extension Components.
This file was generated once (2026-02-11) by manual conversion from the
CSD03 XML Schema definitions listed below.  The extension scaffolding has been
stable since UBL 2.1 and is not expected to change.

**Source XSDs** (retained in `history/` for traceability):

| File | Description | Stable URL (CSD02) |
|------|-------------|---------------------|
| `UBL-CommonExtensionComponents-2.5.xsd` | UBLExtension ABIE + 9 BBIEs + basic-element type declarations | [xsd/common/UBL-CommonExtensionComponents-2.5.xsd](https://docs.oasis-open.org/ubl/csd02-UBL-2.5/xsd/common/UBL-CommonExtensionComponents-2.5.xsd) |
| `UBL-ExtensionContentDataType-2.5.xsd` | ExtensionContent type (`xsd:any` — maps to open JSON object) | [xsd/common/UBL-ExtensionContentDataType-2.5.xsd](https://docs.oasis-open.org/ubl/csd02-UBL-2.5/xsd/common/UBL-ExtensionContentDataType-2.5.xsd) |
| `UBL-CommonSignatureComponents-2.5.xsd` | UBLDocumentSignatures wrapper (kept for completeness) | [xsd/common/UBL-CommonSignatureComponents-2.5.xsd](https://docs.oasis-open.org/ubl/csd02-UBL-2.5/xsd/common/UBL-CommonSignatureComponents-2.5.xsd) |

**Conversion method:**

1. Each `xsd:element` inside `UBLExtensionType` was mapped to a GC row.
2. Element name → `UBLName`, documentation → `Definition`.
3. `minOccurs`/`maxOccurs` → `Cardinality` (`0..1` or `1`).
4. XSD type base (`udt:IdentifierType`, `udt:NameType`, etc.) →
   `RepresentationTerm` and `DataType` following CCTS conventions.
5. `ExtensionContent` (`xsd:any`) mapped as `Content. Type` with cardinality `1`.
6. The column set mirrors `UBL-Signature-Entities-2.5.gc` exactly so the
   generator can treat all GC files uniformly.

---

## history/ — Source XSD files

These files were used to derive `gc/UBL-Extension-Entities-2.5.gc` and are
retained for auditability.  They are **not** read by the generator at runtime.

---

## Additional sources

The UBL 2.5 specification and all distribution artifacts are maintained by the
OASIS UBL Technical Committee:

- **GitHub repository:** <https://github.com/oasis-tcs/ubl> (branch `ubl-2.5`)
- **CSD02 publication:** <https://docs.oasis-open.org/ubl/csd02-UBL-2.5/>
- **CSD03 publication:** (expected ~February 2026 at `https://docs.oasis-open.org/ubl/csd03-UBL-2.5/`)
