# TODO — DocBook Validation

## Outstanding verification

1. ~~**Chapters 1-6**~~ — Checked. No issues found. Naming conventions (TitleCase for BIEs, lowerCamelCase for supplementary components), deprecated element exclusion (5.2), standalone ABIE support (6.2), and description annotations (5.1) all verified correct.

2. ~~**SignatureAggregateComponents schema**~~ — Checked field-by-field against GC (`UBL-Signature-Entities-2.5.gc`, 5 rows). Both `UBLDocumentSignaturesType` and `SignatureInformationType` match the GC exactly: correct properties, cardinality, data types, required fields, descriptions, and titles. `SignatureBasicComponents` also verified (2 BBIEs, both `Identifier. Type`). Runtime validation tests pass.

3. ~~**309 ABIE types**~~ — Exhaustively checked all 309 ABIEs against GC. Results: 0 missing/extra types, 0 child name mismatches (2,855 children), 0 cardinality errors, 0 required array mismatches, 0 structural errors (additionalProperties, minProperties, $anchor). UBLEntity is correctly `const`+required on documents and `const`+optional on ABIEs (dual-use: standalone vs embedded).

4. **1197 BBIE mappings** — The mapping logic and data type resolution is verified, but not every individual BBIE has been checked against the GC.

## Points for TC discussion

1. **DateType / TimeType data loss** — JSON patterns are narrower than XSD (no timezone offsets). XML-to-JSON conversion silently drops timezone information.

2. **Repeating languageID uniqueness (8.4.8)** — Cannot be expressed in JSON Schema 2020-12. Requires application-level validation.

3. **Spec inconsistency in Section 13.1 (line 594)** — Example URI missing `/2/` path component and `UBL-` prefix compared to Annex C.

4. **`_n` suffix pattern** — Mentioned in spec but not used. Confirm this is acceptable.

5. **Controlled vocabularies (Chapter 9)** — No code list enforcement in JSON Schema. Confirm this is the intended approach.
