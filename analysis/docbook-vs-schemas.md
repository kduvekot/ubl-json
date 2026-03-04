# DocBook Spec vs Generated Schemas — Design Decisions

Reference: `UBL-2.5-JSON-Syntax-Binding.xml` (Revision 306, 2025-09-23)

This document records 7 discrepancies found between the DocBook prose and the
initial generated schemas, the decisions taken, and the resolution for each.

---

## 1. Schema Identifiers: HTTPS URLs vs URNs — Done

**DocBook** (Section 12.4, line 612): "Each schema is identified by a stable HTTPS URL
that is fixed at the major version level"

Schema listings use:
- `https://docs.oasis-open.org/ubl/2/json/schemas/CommonAggregateComponents-2`
- `https://docs.oasis-open.org/ubl/2/json/schemas/Invoice-2`
- etc.

**Generated**: Uses URN-based identifiers:
- `urn:oasis:names:specification:ubl:schema:json:CommonAggregateComponents-2`
- `urn:oasis:names:specification:ubl:schema:json:Invoice-2`
- etc.

This affects `$id` in every schema and all `$ref` cross-references.

Note: The prose at line 612 says `https://docs.oasis-open.org/ubl/json/schemas/Invoice-2`
(no `/2/` segment), while schema listings at lines 653, 676, etc. include `/2/` in the path.
Minor editorial inconsistency in the DocBook itself.

**Decision**: Keep URNs. Aligns with XSD convention (`urn:oasis:names:specification:ubl:schema:xsd:*`).

**Resolution**: DocBook updated to use URN identifiers throughout. Schemas use
`URN_BASE = 'urn:oasis:names:specification:ubl:schema:json'` in `generate_json_schemas.py`.

---

## 2. Instance schema identification property — Done

**DocBook** (Section 9.1): "Every conformant UBL JSON instance shall carry a `$schema`
property at its root identifying the governing schema."

- For documents: value is the document schema identifier
- For standalone ABIEs: value is CAC schema + fragment identifier
  (e.g. `https://docs.oasis-open.org/ubl/2/json/schemas/CommonAggregateComponents-2#AddressType`)

**Generated**: Document schemas did not define a `$schema` property in their `properties`
object. ABIE types in CAC also lacked this property.

**Conflict**: Kenneth's email feedback (in `feedback/`) proposed renaming this property
to `UBLEntity`. The DocBook (also authored by Kenneth) says `$schema`. These were
contradictory.

**Decision**: Use `$jsonschema` — a clean JSON-native equivalent of the XML namespace
declaration. Avoids collision with JSON Schema's own `$schema` keyword (which identifies
the meta-schema dialect on schema documents). The `$` prefix signals metadata rather than
business data, and the name clearly communicates its purpose: identifying which JSON
schema governs the instance.

- For documents: `"$jsonschema": "urn:oasis:names:specification:ubl:schema:json:Invoice-2"`
- For standalone ABIEs: `"$jsonschema": "urn:oasis:names:specification:ubl:schema:json:CommonAggregateComponents-2#AddressType"`

**Resolution**: `$jsonschema` added to document schemas (required, with `const`) and all
ABIE types in CAC and SAC (optional, since embedded ABIEs inherit the parent schema).
DocBook updated accordingly.

---

## 3. BinaryObjectType `mimeCode` not mandatory — Done

**DocBook** (Section 10.2): "The mimeCode property is required and shall identify the
media type of the content."

Data type table (Section 10.1): `mimeCode (mandatory)`

**Generated**: `required: ["value"]` — only `value` was required; `mimeCode` was optional.

The initial schema matched the XSD (`BDNDR-CCTS_CCT_SchemaModule-1.1.xsd`)
where `mimeCode` is `use="optional"`. The DocBook explicitly overrides this to mandatory.

**Decision**: Follow the DocBook. Make `mimeCode` required alongside `value`.

**Resolution**: Changed to `required: ['value', 'mimeCode']` in BinaryObjectType
definition in `generate_json_schemas.py`.

---

## 4. No empty string prohibition (`minLength: 1`) — Done

**DocBook** (Section 7.4): "Validation shall fail when ... a property is present with
an empty string as its value."

**Generated**: String-based types (TextType, NameType, CodeType, IdentifierType, DateType,
TimeType, and string properties like `currencyID`, `unitCode`, `schemeID`) did not enforce
`minLength: 1`.

**Decision**: Enforce in the JSON schemas. JSON Schema natively supports `minLength: 1`,
unlike XSD which required separate IND/Schematron rules for this. Folding these constraints
directly into the schema eliminates the need for a separate validation layer — any standard
JSON Schema validator will enforce them.

**Resolution**: Added `minLength: 1` to all string `value` properties and supplementary
component properties via a `_str` helper in `generate_json_schemas.py`. DateType and
TimeType already have `pattern` constraints which implicitly prevent empty strings.

---

## 5. No empty object prohibition (`minProperties: 1`) — Done

**DocBook** (Section 7.4): "Validation shall fail when ... an object defined by the
Semantic Library is present but empty (i.e., contains no members)."

**Generated**: ABIE types did not enforce `minProperties: 1`. An empty `{}` would
pass validation if the ABIE had no required properties.

**Decision**: Enforce in the JSON schemas. Same rationale as point 4 — JSON Schema can
express this natively via `minProperties: 1`.

**Resolution**: Added `minProperties: 1` to all ABIE type definitions in CAC, SAC,
extension components, and document schemas in `generate_json_schemas.py`.

---

## 6. `ExtensionURI` not required on extensions — Done

**DocBook** (Section 6.3): "Each extension shall be a JSON object containing **at least**
the following members: ExtensionURI ... ExtensionContent"

**Generated**: `UBLExtensionType` only had `required: ["ExtensionContent"]`. `ExtensionURI`
was defined as a property but was not required.

**Decision**: Follow the DocBook. Make `ExtensionURI` required alongside `ExtensionContent`.

**Resolution**: Changed to `required: ['ExtensionURI', 'ExtensionContent']` in
`generate_json_schemas.py` CommonExtensionComponents generation.

---

## 7. Single supplementary component per data type — Done

**DocBook** (Table T-UBL-UNQUALIFIED-DATA-TYPES): Each data type lists exactly one
supplementary component (or none). For example, CodeType has `listID`, IdentifierType
has `schemeID`, QuantityType has `unitCode`.

**Generated (before)**: Schemas included the full CCTS attribute sets from the XSD
(e.g., CodeType had 9 attributes: listID, listAgencyID, listAgencyName, listName,
listVersionID, name, languageID, listURI, listSchemeURI).

**Decision**: Align with the DocBook. Each type gets exactly one supplementary component.
When converting from XML, agency identifiers are merged into the primary attribute using
the `agencyID:value` convention (e.g., `"schemeID": "9:GLN"`, `"listID": "6:UN/ECE 1001"`).
Descriptive metadata (listName, schemeAgencyName, listVersionID, etc.) is dropped since
it can be resolved from the primary identifier.

**Resolution**: Simplified all UDT definitions in `generate_json_schemas.py`. Updated
`convert_xml_examples.py` with `_merge_code_attrs()` and `_merge_id_attrs()` functions.
All 75 examples pass validation against the simplified schemas.

---

## Design principle: IND rules in JSON Schema

Points 4 and 5 establish a broader principle: where the UBL "Additional Document Constraints"
(IND rules) can be expressed natively in JSON Schema, they should be encoded directly in
the schemas. This gives JSON an advantage over XML — a single validation step using any
standard JSON Schema 2020-12 validator, with no need for a Schematron-equivalent toolchain.

Constraints that **cannot** be expressed in JSON Schema (e.g. Section 7.4's rule that
repeating Text/Name elements must each carry a unique `languageID`) are documented in
`extra-schema-constraints.md` and must be enforced by an external validation layer or
application logic.
