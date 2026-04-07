# DocBook Spec vs Generated Schemas — Design Decisions

Reference: `UBL-json.xml` (WD01, UBL 2.5 JSON Syntax Binding Version 1.0)

This document records 7 discrepancies found between the DocBook prose and the
initial generated schemas, the decisions taken, and the resolution for each.

---

## 1. Schema Identifiers: HTTPS URLs vs URNs — Done

**DocBook** (Section 13.1, Annex C): Schemas are identified by stable HTTPS URLs
fixed at the major version level.

Annex C listings use:
- `https://docs.oasis-open.org/ubl/2/json/schemas/CommonAggregateComponents-2`
- `https://docs.oasis-open.org/ubl/2/json/schemas/UBL-Invoice-2`
- etc.

**Generated (before)**: Used URN-based identifiers:
- `urn:oasis:names:specification:ubl:schema:json:CommonAggregateComponents-2`

**Decision**: Follow the DocBook WD01. Use HTTPS URLs as prescribed by Annex C.

**Resolution**: Changed `URN_BASE` to `SCHEMA_BASE` with value
`https://docs.oasis-open.org/ubl/2/json/schemas` in `generate_json_schemas.py`.
Document schemas use `UBL-` prefix (e.g. `UBL-Invoice-2`), common schemas do not.

Note: Section 13.1 line 594 has a minor inconsistency — the example URI
`https://docs.oasis-open.org/ubl/json/schemas/Invoice-2` is missing the `/2/`
path segment and the `UBL-` prefix compared to Annex C. Our implementation
follows Annex C which is the normative reference.

---

## 2. Instance schema identification property — Done

**DocBook** (Section 10.1): "Every conformant UBL JSON instance shall carry a
`UBLEntity` property at its root identifying the governing schema."

- For documents: value is the document schema identifier
  (e.g. `https://docs.oasis-open.org/ubl/2/json/schemas/UBL-Invoice-2`)
- For standalone ABIEs: value is CAC schema + fragment identifier
  (e.g. `https://docs.oasis-open.org/ubl/2/json/schemas/CommonAggregateComponents-2#AddressType`)
- For extensions: value identifies the schema governing the extension content

**Generated (before)**: Used `$jsonschema` as the property name, based on an
earlier draft of the specification.

**Decision**: Follow the DocBook WD01. Use `UBLEntity`.

**Resolution**: Property renamed to `UBLEntity` throughout. For document schemas
it is `required` with `const`. For ABIEs in CommonAggregateComponents it is
`const` but not `required` (optional when embedded, used when standalone). For
extensions it is `required` as a free-form `string` with `minLength: 1`.

---

## 3. BinaryObjectType `mimeCode` not mandatory — Done

**DocBook** (Section 11.2): "The mimeCode property is required and shall identify
the media type of the content."

Data type table (Section 11.1): `mimeCode (mandatory)`

**Generated (before)**: `required: ["value"]` — only `value` was required;
`mimeCode` was optional.

The initial schema matched the XSD where `mimeCode` is `use="optional"`. The
DocBook explicitly overrides this to mandatory.

**Decision**: Follow the DocBook. Make `mimeCode` required alongside `value`.

**Resolution**: Changed to `required: ['value', 'mimeCode']` in BinaryObjectType
definition in `generate_json_schemas.py`.

---

## 4. No empty string prohibition (`minLength: 1`) — Done

**DocBook** (Section 8.4): "Validation shall fail when … a property is present
with an empty string as its value."

**Generated (before)**: String-based types did not enforce `minLength: 1`.

**Decision**: Enforce in the JSON schemas. JSON Schema natively supports
`minLength: 1`, unlike XSD which required separate IND/Schematron rules.

**Resolution**: Added `minLength: 1` to all string `value` properties and
supplementary component properties. DateType and TimeType already have `pattern`
constraints which implicitly prevent empty strings.

---

## 5. No empty object prohibition (`minProperties: 1`) — Done

**DocBook** (Section 8.4): "Validation shall fail when … an object defined by
the Semantic Library is present but empty."

**Generated (before)**: ABIE types did not enforce `minProperties: 1`.

**Decision**: Enforce in the JSON schemas via `minProperties: 1`.

**Resolution**: Added `minProperties: 1` to all ABIE type definitions in CAC,
SAC, extension components, and document schemas in `generate_json_schemas.py`.

---

## 6. `ExtensionURI` not required on extensions — Done

**DocBook** (Section 7.3): "Each extension shall be a JSON object containing
**at least** the following members: ExtensionURI … ExtensionContent"

**Generated (before)**: `UBLExtensionType` only had
`required: ["ExtensionContent"]`.

**Decision**: Follow the DocBook. Make `ExtensionURI` required.

**Resolution**: Changed to `required: ['ExtensionURI', 'ExtensionContent']` in
`generate_json_schemas.py` CommonExtensionComponents generation.

---

## 7. Single supplementary component per data type — Done

**DocBook** (Table in Section 11.1): Each data type lists exactly one
supplementary component (or none). For example, CodeType has `listID`,
IdentifierType has `schemeID`, QuantityType has `unitCode`.

**Generated (before)**: Schemas included the full CCTS attribute sets from the
XSD (e.g., CodeType had 9 attributes).

**Decision**: Align with the DocBook. Each type gets exactly one supplementary
component as specified in the Section 11.1 table.

**Resolution**: Simplified all UDT definitions in `generate_json_schemas.py`.
Updated `convert_xml_examples.py` with `_merge_code_attrs()` and
`_merge_id_attrs()` functions to merge multiple XML attributes into the single
JSON supplementary component.

---

## Design principle: IND rules in JSON Schema

Points 4 and 5 establish a broader principle: where the UBL "Additional Document
Constraints" (IND rules) can be expressed natively in JSON Schema, they should be
encoded directly in the schemas. This gives JSON an advantage over XML — a single
validation step using any standard JSON Schema 2020-12 validator, with no need for
a Schematron-equivalent toolchain.

Constraints that **cannot** be expressed in JSON Schema (e.g. Section 8.4's rule
that repeating Text/Name elements must each carry a unique `languageID`) are
documented in `extra-schema-constraints.md` and must be enforced by an external
validation layer or application logic.
