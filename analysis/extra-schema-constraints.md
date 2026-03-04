# Extra-Schema Constraints — Reference for Future Implementation

These 6 constraints are specified normatively in the UBL 2.5 JSON Syntax Binding
but **cannot be enforced by JSON Schema alone**. Each entry includes the exact spec
text, section reference, and why JSON Schema falls short.

---

## ESC-1: `languageID` uniqueness in repeating Text/Name elements

**Spec section:** 7.4 — Error handling and strictness (`S-ERROR-HANDLING-AND-STRICTNESS`)

**Normative text (lines 378–386):**
> Validation shall fail when … In the case of natural language Text or Name
> elements with repeating cardinality:
> - Any occurrence omits a `languageID`, or
> - Two occurrences share the same `languageID`.

**Example violating this rule:**
```json
"Description": [
  {"value": "My description", "languageID": "EN"},
  {"value": "Another description", "languageID": "EN"}   ← duplicate languageID
]
```

**Why JSON Schema cannot enforce this:**
JSON Schema has no `uniqueItems` variant that operates on a *specific property*
within array objects. `uniqueItems` only checks whole-object equality. Ensuring
that no two array members share the same `languageID` value requires either:
- A custom vocabulary / keyword extension (e.g., `uniqueKeys`)
- A secondary validation layer (code, Schematron-like rules, or a JSON-native
  constraint language like JMESPath assertions)

**Affected schema types:** `TextType`, `NameType` (in `UnqualifiedDataTypes-2.5.json`)

**Affected supplementary component:** `languageID` (see Table in §10.1, lines 501–510)

---

## ESC-2: `oneOf` replaces `_n` suffix convention (functionally equivalent)

**Spec section:** 7.1 — Cardinality and repetition (`S-CARDINALITY-AND-REPETITION`)

**Background:**
The UBL NDR XML binding uses a `_n` suffix naming convention (e.g., `Description_1`,
`Description_2`) to distinguish multiple occurrences of a BBIE. In JSON, this
convention is unnecessary because:
1. Arrays naturally handle repetition
2. The `oneOf` keyword in the schema allows a property to be either a single value
   (scalar/object) or an array

**Schema pattern (from `UnqualifiedDataTypes-2.5.json`):**
```json
"CodeType": {
  "oneOf": [
    { "type": "string", "minLength": 1 },
    { "type": "object", "properties": { "value": {...}, "listID": {...}, ... } }
  ]
}
```

**Why this is an observation, not a constraint:**
This is an architectural decision, not a runtime validation gap. The `oneOf`
pattern is fully enforced by the schema. The observation simply notes that the
naming convention from XML (`_n` suffixes) does not carry over to JSON — the
schema handles it differently but equivalently. No implementation action needed
beyond awareness.

---

## ESC-3: `$jsonschema` in extension containers is a producer obligation

**Spec section:** 9.1 — Schema identification (`S-SCHEMA-IDENTIFICATION`)

**Normative text (lines 410–411):**
> For extensions expressed using the UBL extension mechanism (6.3), each extension
> container shall include a `$jsonschema` property whose value identifies the
> schema context and version governing the extension content. The value shall be
> a stable identifier published by the authority responsible for the extension.

> In all cases, producers shall ensure that instances validate successfully against
> the schema identified in the `$jsonschema` property, and consumers shall apply
> the corresponding rule set.

**Why JSON Schema cannot enforce this:**
The schema can require a `$jsonschema` *property* to be present (via `required`),
but it **cannot**:
1. Resolve the URI in `$jsonschema` to fetch the referenced extension schema
2. Validate the sibling `ExtensionContent` against that dynamically-referenced schema
3. Verify that the URI points to a real, published schema

This is a **producer obligation**: the party creating the document must ensure the
`$jsonschema` value is correct and that the content validates against it. Consumers
must independently fetch and apply the referenced schema — this is a two-party
protocol that JSON Schema's single-document validation model cannot capture.

**Possible implementation approaches:**
- Application-level validation that resolves `$jsonschema` URIs and validates content
- API middleware / gateway validation
- Conformance test suites with known extension schemas

---

## ESC-4: `$jsonschema` in standalone ABIEs is optional in schema

**Spec section:** 9.1 — Schema identification (`S-SCHEMA-IDENTIFICATION`)

**Normative text (lines 406–409):**
> Every conformant UBL JSON instance shall carry a `$jsonschema` property at its
> root identifying the governing schema.

> For standalone Aggregate Business Information Entities (ABIEs) exchanged as
> autonomous root payloads, the instance shall include a `$jsonschema` property
> whose value identifies the Common Aggregate Components schema together with a
> fragment identifier corresponding to the ABIE.

**Why the schema cannot make this `required`:**
The same ABIE schema definition (`CommonAggregateComponents-2.5.json`) is used in
two contexts:
1. **Embedded** — the ABIE appears as a child within a document (e.g., `Party`
   inside `Invoice`). Here, `$jsonschema` would be redundant/wrong since the
   parent document already declares its schema.
2. **Standalone** — the ABIE is the root payload (e.g., a `Party` served at an
   API endpoint). Here, `$jsonschema` is normatively required.

Since JSON Schema definitions are context-free (the same `$ref` is used in both
cases), making `$jsonschema` `required` in the schema would break embedded usage.
The spec therefore leaves this as a conformance rule rather than a schema constraint.

**Possible implementation approaches:**
- Wrapper schemas for standalone usage that add `$jsonschema` as required
- API-level validation middleware
- Conformance profiles that layer additional constraints

---

## ESC-5: Base64 encoding for `BinaryObjectType.value`

**Spec section:** 10.2 — BinaryObject type (`S-BINARYOBJECT-TYPE`)

**Normative text (lines 518):**
> A BinaryObject is always represented in object form. The value property is
> required and shall contain a base64-encoded string. The mimeCode property is
> required and shall identify the media type of the content using an
> IANA-registered MIME type.

**Example:**
```json
{
  "value": "JVBERi0xLjQKJcfsj6IK...",
  "mimeCode": "application/pdf"
}
```

**Why JSON Schema cannot enforce this:**
JSON Schema's `format` keyword does not include a `base64` format, and the
`contentEncoding` keyword (added in draft 2019-09 / draft 7) is defined as an
**annotation** — validators are not required to actually check that the string is
valid base64. The spec's schema uses `"type": "string"` for the value, which
accepts any string.

Enforcing valid base64 would require either:
- A regex pattern (possible but fragile and expensive for large values)
- Application-level validation
- A custom format validator

**Additionally:** Verifying that the decoded content actually matches the declared
`mimeCode` is entirely a runtime concern.

---

## ESC-6: Safety, security, and data protection considerations are procedural

**Spec section:** 13 — Safety, Security, and Data Protection Considerations
(`S-SAFETY-SECURITY-AND-DATA-PROTECTION-CONSIDERATIONS`)

**Normative text (lines 945–952):**

*Security (§13.1):*
> UBL JSON instances are ordinary JSON documents. Implementers shall therefore
> consider the general security considerations applicable to application/json as
> described in [RFC8259], including validation of input, avoidance of unsafe
> evaluation of textual content, and proper handling of Unicode per [UTR#36].

> The extension mechanism (section 6.3) allows communities to embed additional
> content. Such content is outside the scope of this specification and may
> introduce security risks if not governed by appropriate community rules.

*Data protection (§13.2):*
> UBL JSON instances may contain personally identifiable information (PII) or
> commercially sensitive data, including names, addresses, tax identifiers, and
> financial amounts. This specification does not define mechanisms for redaction,
> encryption, or access control. Implementers and communities of use are
> responsible for ensuring that processing and exchange of UBL JSON documents
> comply with applicable data protection laws and contractual obligations.

**Why this is entirely procedural:**
These requirements address:
- Input sanitization (implementation-level)
- Unicode security (runtime)
- Extension content safety (governance)
- PII handling (legal/organizational policy)
- Access control (infrastructure)

None of these can be expressed as data-shape constraints. They are obligations
on **implementers and organizations**, not on document structure.

**Possible implementation approaches:**
- Security checklists for UBL JSON implementations
- Conformance certification programs
- Community profile requirements documents
- Automated scanning tools (PII detection, extension content analysis)

---

## Summary Matrix

| ID | Constraint | Spec § | Enforceable by | JSON Schema gap |
|----|-----------|--------|----------------|-----------------|
| ESC-1 | `languageID` uniqueness | 7.4 | Custom validator, Schematron-like rules | No cross-item property uniqueness |
| ESC-2 | `_n` → `oneOf` convention | 7.1 | Already enforced by `oneOf` | None (observation only) |
| ESC-3 | `$jsonschema` in extensions | 9.1 | Producer + consumer coordination | No dynamic schema resolution |
| ESC-4 | `$jsonschema` in standalone ABIEs | 9.1 | Wrapper schemas, API validation | Context-dependent `required` |
| ESC-5 | Base64 in `BinaryObjectType` | 10.2 | Runtime validation | `contentEncoding` is annotation-only |
| ESC-6 | Security & privacy | 13 | Organizational policy | Procedural, not structural |
