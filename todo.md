# TODO — DocBook Validation

## Outstanding verification

1. **Chapters 1-6** — Not explicitly checked against the implementation. May contain requirements in the introduction, scope, terminology, or UBL Semantic Library description that affect schema generation.

2. **SignatureAggregateComponents schema** — Chapter 12 describes `UBLDocumentSignatures` and `SignatureInformation` types. Schemas exist and pass metaschema validation, but a field-by-field check against the spec and GC data has not been done.

3. **309 ABIE types** — The overall pattern is verified (UBLEntity, additionalProperties: false, minProperties: 1, correct cardinality handling), but individual ABIE children have not been exhaustively checked against the GC.

4. **1197 BBIE mappings** — The mapping logic and data type resolution is verified, but not every individual BBIE has been checked against the GC.

## Points for TC discussion

1. **DateType / TimeType data loss** — JSON patterns are narrower than XSD (no timezone offsets). XML-to-JSON conversion silently drops timezone information.

2. **Repeating languageID uniqueness (8.4.8)** — Cannot be expressed in JSON Schema 2020-12. Requires application-level validation.

3. **Spec inconsistency in Section 13.1 (line 594)** — Example URI missing `/2/` path component and `UBL-` prefix compared to Annex C.

4. **`_n` suffix pattern** — Mentioned in spec but not used. Confirm this is acceptable.

5. **Controlled vocabularies (Chapter 9)** — No code list enforcement in JSON Schema. Confirm this is the intended approach.
