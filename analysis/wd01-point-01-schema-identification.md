# Point 1: Schema Identification Property in Standalone JSON Instances

## The question

How should a standalone UBL JSON document (sitting on a filesystem, in a message queue, or arriving as a payload) declare which schema governs it? This is the JSON equivalent of XML namespaces — and unlike XML, there is no agreed standard.

Three different names currently exist for this concept in the UBL JSON context:

| Source | Property name | Value style |
|--------|--------------|-------------|
| Previous working draft | `$schema` | Not specified |
| WD01 | `UBLEntity` | HTTPS URL (e.g., `https://docs.oasis-open.org/ubl/2/json/schemas/UBL-Invoice-2`) |
| Generated schemas (this repo) | `$jsonschema` | URN (e.g., `urn:oasis:names:specification:ubl:schema:json:Invoice-2`) |

## The fundamental gap: no JSON equivalent of XML namespaces

There is no standardized way for a JSON instance document to declare its governing schema. This is widely acknowledged as one of the most significant differences between XML and JSON.

Mark Nottingham (2011): *"If you can use JSON without namespaces, you really, really should."*

Source: [Thinking about Namespaces in JSON](https://www.mnot.net/blog/2011/10/12/thinking_about_namespaces_in_json)

## What JSON Schema says

### `$schema` keyword

The `$schema` keyword is defined in JSON Schema Core (Section 8.1.1) as a **schema-level keyword only**. It declares which dialect of JSON Schema a *schema document* was written for. It is **not specified for instance documents**.

The JSON Schema maintainers have explicitly discussed this:

- **jdesrosiers (maintainer):** Opposed making `$schema` special in instances because (a) it would prevent JSON Schema from describing documents that legitimately contain a `$schema` property, and (b) it only works for JSON objects, not arrays or scalars at the root.
- **gregsdennis (maintainer):** Proposed it but acknowledged the community preferred documenting it as a common convention rather than something normative.
- **Security concern:** Allowing instances to self-declare their schema could cause implementations to make HTTP requests based on file contents — unpredictable and potentially dangerous.

**De facto convention:** Despite not being in the spec, many editors (VS Code, JetBrains) and tools support `$schema` in instance documents for validation and autocompletion. The [SchemaStore.org](https://www.schemastore.org/) project catalogs hundreds of schemas used this way. However, schemas using `additionalProperties: false` will reject the `$schema` property unless they explicitly allow it.

Sources:
- [JSON Schema Core 2020-12, Section 8.1.1](https://json-schema.org/draft/2020-12/json-schema-core)
- [json-schema-org Discussion #473: Using `$schema` in JSON documents](https://github.com/orgs/json-schema-org/discussions/473)
- [json-schema-org Issue #1091: How to reference JSON Schema from JSON data](https://github.com/json-schema-org/json-schema-spec/issues/1091)

### `$id` keyword

The `$id` keyword is **exclusively for schema documents**. It provides a canonical URI identifier for a schema resource. The spec explicitly states: *"identifiers are just identifiers"* — JSON Schema does not guarantee that a schema with an HTTP URL identifier is actually resolvable at that URL.

Source: [JSON Schema Core 2020-12, Structuring](https://json-schema.org/understanding-json-schema/structuring)

## How other standards solve this

### FHIR / HL7 (healthcare)

Uses **two mechanisms** in every JSON instance:

| Property | Purpose | Example |
|----------|---------|---------|
| `resourceType` | **Required** top-level property identifying the resource type | `"resourceType": "Patient"` |
| `meta.profile` | **Optional** array of canonical URLs identifying profiles | `"meta": {"profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]}` |

Plus the media type `application/fhir+json` for transport context.

Sources:
- [FHIR JSON Representation](https://www.hl7.org/fhir/json.html)
- [FHIR Base Resource Definitions](https://build.fhir.org/resource.html)

### JSON-LD (W3C Recommendation)

The most comprehensive solution, using two key properties:

| Property | Purpose |
|----------|---------|
| `@context` | Maps short-form property names to full URIs from an ontology |
| `@type` | Identifies the type of the described entity |

JSON-LD effectively solves the namespace problem by using URIs as authoritative names. However, it requires buy-in to the RDF/Linked Data model.

Source: [JSON-LD 1.1 W3C Recommendation](https://www.w3.org/TR/json-ld11/)

### GeoJSON (RFC 7946)

Uses a **`type` property** with a fixed vocabulary:

```json
{ "type": "Feature", "geometry": { "type": "Point", "coordinates": [125.6, 10.1] } }
```

No schema URL — identification relies purely on well-known `type` values and the registered media type `application/geo+json`.

Source: [RFC 7946: The GeoJSON Format](https://datatracker.ietf.org/doc/html/rfc7946)

### CloudEvents (CNCF)

Every CloudEvent **requires** context attributes including:

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `specversion` | Version of the CloudEvents spec | `"1.0"` |
| `type` | Producer-defined event type | `"com.example.order.created"` |
| `dataschema` | **Optional** URI identifying the schema of the `data` attribute | `"https://example.com/schemas/order.json"` |

The `dataschema` attribute is the closest to what UBL needs — an optional, in-document URI pointing to the schema governing the payload.

Source: [CloudEvents Specification](https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md)

### JSON:API

Uses `type` + `id` on every resource object, plus an optional top-level `jsonapi` object with version and profile URIs. Also adopted the `describedby` link relation for pointing to schema documents.

Source: [JSON:API Specification v1.1](https://jsonapi.org/format/)

### W3C Verifiable Credentials

Combines JSON-LD context with an explicit schema reference:

| Property | Purpose |
|----------|---------|
| `@context` | Required. Vocabulary identification |
| `type` | Required. Must include `"VerifiableCredential"` |
| `credentialSchema` | Optional. Object with `id` (URL to schema) and `type` (e.g., `"JsonSchema"`) |

Notable because it uses *both* JSON-LD context for vocabulary identification *and* an explicit `credentialSchema` for structural validation.

Source: [Verifiable Credentials Data Model v2.0](https://www.w3.org/TR/vc-data-model/)

### Apache Avro

The schema is always transmitted *alongside* the data — stored in file metadata or as a fingerprint in the binary header. Avro schemas use `namespace` + `name` for fully qualified type identification, analogous to XML namespaces.

Source: [Apache Avro Specification](https://avro.apache.org/docs/1.11.1/specification/)

### Snowplow / Iglu

Self-describing JSON instances wrap data with a `schema` URI:

```json
{
  "schema": "iglu:com.snowplowanalytics/ad_click/jsonschema/1-0-0",
  "data": { ... }
}
```

Source: [Snowplow: Self-describing JSON Schemas](https://docs.snowplow.io/docs/api-reference/iglu/common-architecture/self-describing-json-schemas/)

### Prior UBL JSON (2.1–2.3)

The OASIS-published UBL JSON alternative representations used namespace-like properties (`_D`, `_S`, `_B`, `_E`) with URI values to identify the document context.

## Media types and HTTP headers

JSON Schema recommends using an HTTP **Link header** with the `describedby` relation:

```
Link: <https://example.com/my-schema>; rel="describedby"
```

Earlier drafts supported a `describedby` MIME type parameter on Content-Type, but Draft 2020-12 dropped it because *"it's caused a lot of confusion and disagreement"* and no evidence of actual use was found.

**Limitation:** Media types and HTTP headers **only work over HTTP**. They are useless for files on disk, messages on queues, documents in databases, or email attachments — all common scenarios for UBL documents.

Sources:
- [JSON Schema Core 2020-12, Section 9.5](https://json-schema.org/draft/2020-12/json-schema-core)
- [RFC 6892: The 'describes' Link Relation Type](https://www.rfc-editor.org/rfc/rfc6892)

## The `describedby` vs `profile` distinction

The JSON Schema community resolved (Issue #9, 2016) that:

- `profile` (RFC 6906) = **identification** — the URI identifies which schema applies but need not be dereferenceable
- `describedby` = **location** — the URI points to a downloadable schema document

Both can be used together.

Source: [json-schema-spec Issue #9](https://github.com/json-schema-org/json-schema-spec/issues/9)

## Emerging work: JSON Structure

An IETF Internet-Draft ([draft-vasters-json-structure-core-00](https://www.ietf.org/archive/id/draft-vasters-json-structure-core-00.html), July 2025) by Clemens Vasters introduces a new JSON schema language with first-class namespace support. It explicitly defines `$schema` for use in instance documents. Status: active draft.

## Summary of approaches across standards

| Specification | Property/Mechanism | In Instance? | Standardized? |
|---|---|---|---|
| JSON Schema (editors) | `$schema` | Convention only | No (convention) |
| FHIR | `resourceType` + `meta.profile` | Yes (required/optional) | Yes (HL7) |
| JSON-LD | `@context` + `@type` | Yes (required) | Yes (W3C Rec) |
| W3C Verifiable Credentials | `@context` + `type` + `credentialSchema` | Yes | Yes (W3C Rec) |
| GeoJSON | `type` | Yes (required) | Yes (IETF RFC) |
| JSON:API | `type` + `id` | Yes (required) | Yes (jsonapi.org) |
| CloudEvents | `specversion` + `type` + `dataschema` | Yes (required/optional) | Yes (CNCF) |
| OpenAPI | `discriminator.propertyName` | In spec only | Yes (OAI) |
| Avro | Schema in file header | Alongside data | Yes (Apache) |
| Snowplow/Iglu | `schema` wrapper | Yes | Proprietary |
| JSON Structure (draft) | `$schema` | Yes (proposed) | Draft (IETF) |
| UBL JSON (this repo) | `$jsonschema` | Yes | OASIS draft |
| UBL JSON WD01 | `UBLEntity` | Yes | OASIS draft |
| UBL JSON (2.1–2.3) | `_D`, `_S`, `_B`, `_E` | Yes | OASIS published |

## Observations for the TC discussion

1. **Every standard invents its own property name.** There is no universal convention. The most common pattern is a `type`-like discriminator property, but the name varies: `resourceType`, `@type`, `type`, `specversion`, etc.

2. **Two distinct functions are often conflated:**
   - **Type identification** — "this is an Invoice" (like FHIR's `resourceType` or GeoJSON's `type`)
   - **Schema location** — "validate against this schema" (like CloudEvents' `dataschema` or Snowplow's `schema`)
   
   UBL's `UBLEntity` / `$jsonschema` attempts to serve both purposes with a single property.

3. **`$schema` in instances is a de facto convention but not standardized** — and it collides with JSON Schema's own keyword. The `$jsonschema` name avoids this collision while signaling purpose.

4. **`UBLEntity` is the least descriptive name** among all the options surveyed. It does not convey that the value is a schema identifier. Names like `$jsonschema`, `schemaUri`, `dataschema`, or even `resourceType` are more self-documenting.

5. **The value format matters too** — URN vs HTTPS URL is a separate but related discussion (see Point 2). Whatever property name is chosen, the value should serve both identification and (ideally) location.

6. **For standalone files, an in-document property is the only viable approach.** HTTP headers, media types, and link relations don't survive when a document is saved to disk, forwarded via email, or stored in a database.
