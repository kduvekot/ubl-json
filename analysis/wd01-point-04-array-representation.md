# Point 4: Singleton-or-Array vs Always-Array for Repeating Elements

## The question

How should repeating elements (cardinality 0..n or 1..n) be represented in JSON instances?

**WD01 approach (section 8.1):** Allow both a single value and an array:

```json
"Note": "Single note"
```
or:
```json
"Note": ["First note", "Second note"]
```

> "If exactly one occurrence is present, it shall be represented as a single value or object. If more than one occurrence is present, it shall be represented as an array of values or objects."
>
> "Consumers shall implement acceptance of both the singleton and array forms."

**Alternative:** Always use an array for elements that can repeat, even when only one value is present:

```json
"Note": ["Single note"]
```

## Impact on schemas

The dual form requires `oneOf` in the schema for every repeating property:

```json
"Note": {
  "oneOf": [
    { "$ref": "#/$defs/NoteType" },
    { "type": "array", "items": { "$ref": "#/$defs/NoteType" } }
  ]
}
```

Always-array simplifies to:

```json
"Note": {
  "type": "array",
  "items": { "$ref": "#/$defs/NoteType" }
}
```

This also eliminates the need for the `_n` schema pattern described in WD01 section 8.2 (see Point 5).

## Impact on consumers

With the dual form, every consumer must check whether a repeating field is a scalar or an array before processing:

```javascript
// Required with singleton-or-array
const notes = Array.isArray(invoice.Note) ? invoice.Note : [invoice.Note];
```

With always-array, processing is uniform:

```javascript
// Always-array — no type checking needed
for (const note of invoice.Note) { ... }
```

## Industry research

### Standards using always-array

| Standard | Approach | Rationale |
|----------|----------|-----------|
| **FHIR/HL7** | Always array | *"An item that may repeat is represented as an array even in the case that it doesn't repeat so that the process of parsing the resource is the same either way"* |
| **JSON:API** | Always array | *"A logical collection of resources MUST be represented as an array, even if it only contains one item or is empty"* |
| **JSON-LD (W3C)** | Always array via `@container: @set` | *"Values of terms associated with a @set container are always represented in the form of an array — even if there is just a single value that would otherwise be optimized to a non-array form in compact form. This makes post-processing of JSON-LD documents easier as the data is always in array form."* |
| **Linked Art (Getty/CIDOC-CRM)** | Always array | *"Consistency is a core feature of usability"* |
| **GeoJSON (RFC 7946)** | Always array | Specification requirement |
| **Google APIs** | Always array | Protobuf repeated fields = JSON array, always |
| **Microsoft APIs** | Always array | Consistency across services |
| **Zalando API Guidelines** | Always array | Cardinality enforced consistently |
| **OpenAPI / AsyncAPI** | Type-consistent | A field defined as `type: array` is always an array |

### Standards using singleton-or-array

| Standard | Approach | Notes |
|----------|----------|-------|
| **AWS IAM Policies** | Singleton-or-array | Widely documented as a source of bugs and complexity. Every tool that processes IAM policies must first normalize fields to arrays before processing. See [Steampipe: Normalizing AWS IAM Policies](https://steampipe.io/blog/normalizing-aws-iam-policies-for-automated-analysis). |

### FHIR as precedent

FHIR is the closest analogue to UBL — a complex document-exchange standard with XML heritage that added a JSON binding. They explicitly chose always-array and documented a forward compatibility benefit:

> "Elements may change whether they are allowed to repeat or not between versions... Processors should be prepared to manage such changes."

Source: [FHIR JSON Representation](https://build.fhir.org/json.html)

### Prior UBL JSON work (UBL 2.1–2.3)

The OASIS UBL TC itself offered two approaches for previous UBL versions:

**Legacy-based (always array):**
> "future versions of UBL may raise the cardinality of any given object and so this approach is future-proof to revisions. This approach is also consistent and is used without thought of cardinality."

**Model-based (array only when max cardinality > 1):**
More natural JSON, but:
> "when a version of UBL changes a construct's maximum cardinality... a past instance no longer will validate with the new schemas. This breaks forward compatibility."

Sources:
- [UBL 2.1 JSON v2.0](https://docs.oasis-open.org/ubl/UBL-2.1-JSON/v2.0/cnd01/UBL-2.1-JSON-v2.0-cnd01.html)
- [UBL 2.3 JSON v1.0](https://docs.oasis-open.org/ubl/UBL-2.3-JSON/v1.0/UBL-2.3-JSON-v1.0.html)

The UBL 2.5 WD01 introduced a third option (singleton-or-array) that differs from both prior approaches.

### The XML-to-JSON conversion problem

The singleton-or-array pattern is a well-known problem in XML-to-JSON conversion. When naively converting XML to JSON:

- XML represents repetition by repeating sibling elements: `<item>A</item><item>B</item>`
- A naive converter produces an object for one element but an array for multiple
- This creates inconsistent typing

Multiple libraries document this as a problem:
- [JSON-java issue #330](https://github.com/stleary/JSON-java/issues/330)
- The universal recommendation is to configure converters to always produce arrays for elements that can repeat

### JSON Schema implications

JSON Schema's type system is strict: a field is either `type: array` or it is not. The "sometimes scalar, sometimes array" pattern requires `oneOf`/`anyOf`, which:

- Complicates validation
- Complicates code generation
- Is widely considered an anti-pattern in JSON Schema design

## Current state of our schemas

Our generated schemas implement the singleton-or-array pattern using inline `oneOf` at each repeating property, based on per-context cardinality from the GC file. This is functionally correct but aligns with neither the industry consensus (always-array) nor the `_n` pattern described in the WD01 spec text.

## The `_n` schema pattern (formerly Point 5)

WD01 section 8.2 describes `_n` suffixed definitions in `$defs` to denote repeatable constructs:

> "Within the JSON schemas, certain internal definition names (for example in $defs) use the suffix _n to denote repeatable constructs corresponding to cardinalities of 0..n or 1..n."

### Current reality

No implementation of `_n` definitions exists — not in our generated schemas, and not in any schemas produced so far. Our generator handles repeating cardinality by inlining `oneOf` (singleton or array) at each property reference.

### Why the `_n` pattern exists

88 of 2,083 component names (4%) appear with both singular and repeating cardinalities in different contexts. For example:

| Component | Singular context | Repeating context |
|-----------|-----------------|-------------------|
| AllowanceCharge | 0..1 on Delivery Terms | 0..n on Invoice |
| TaxTotal | 0..1 on AllowanceCharge | 0..n on InvoiceLine |
| Delivery | 0..1 on Shipment | 0..n on InvoiceLine |
| Name | 0..1 on Branch | 0..n on Awarding Criterion |
| Contact | 0..1 on Party | 0..n on Event |

The `_n` variant would be referenced where the cardinality is 0..n or 1..n, while the base definition would be referenced where it's 0..1 or 1..1. Our schemas handle this correctly by inlining the `oneOf` only at repeating usage points.

### The `_n` naming convention is not a standard JSON Schema pattern

It appears to be specific to this UBL binding. No other JSON Schema specification or ecosystem surveyed uses this convention.

### If always-array is adopted, `_n` becomes unnecessary

With always-array, repeating properties are simply `"type": "array"` — no `oneOf`, no `_n` definitions, no dual-form complexity. The 88 components with mixed cardinalities would just use the base type definition everywhere, with the property declaration determining whether it's an array or a single object:

```json
"TaxTotal": {
  "$ref": "#/$defs/TaxTotalType"
}
```
vs:
```json
"TaxTotal": {
  "type": "array",
  "items": { "$ref": "#/$defs/TaxTotalType" }
}
```

The spec text about `_n` should either be removed (if always-array is adopted) or updated to match the actual inline `oneOf` implementation (if the dual form is retained).

## Recommendation

Adopt always-array for repeating elements, aligning with the overwhelming industry consensus. This would:

1. Simplify schemas (no `oneOf` needed for cardinality)
2. Simplify consumer implementations (no type-checking per field)
3. Eliminate the `_n` pattern discussion entirely
4. Provide forward compatibility if cardinalities change in future UBL versions
5. Align with FHIR, JSON:API, JSON-LD, and every other major standard surveyed

Sources:
- [FHIR JSON Representation (R6 Build)](https://build.fhir.org/json.html)
- [JSON:API Specification v1.1](https://jsonapi.org/format/)
- [JSON:API Issue #1275 — Array vs Single Object](https://github.com/json-api/json-api/issues/1275)
- [JSON-LD 1.1 (W3C)](https://www.w3.org/2018/jsonld-cg-reports/json-ld/)
- [Linked Art JSON-LD Serialization](https://linked.art/api/1.0/json-ld/)
- [RFC 7946 — The GeoJSON Format](https://datatracker.ietf.org/doc/html/rfc7946)
- [Google AIP-144: Repeated Fields](https://google.aip.dev/144)
- [Microsoft REST API Guidelines](https://github.com/microsoft/api-guidelines/blob/vNext/Guidelines.md)
- [Zalando RESTful API Guidelines](http://opensource.zalando.com/restful-api-guidelines/)
- [AWS IAM Policy Grammar](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_grammar.html)
- [Steampipe: Normalizing AWS IAM Policies](https://steampipe.io/blog/normalizing-aws-iam-policies-for-automated-analysis)
- [AusDigital UBL JSON Specification Review](https://github.com/ausdigital/ausdigital-syn-json/blob/master/OASIS-UBL-JSON-Specification-Review.md)
