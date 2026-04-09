# JSON Schema, URI Design, and UBL JSON Strategy

## Summary of Discussion — March 2026

This document captures a detailed technical discussion covering JSON Schema referencing mechanics, URI and URN design choices, OpenAPI integration challenges, and the strategic considerations for publishing UBL 2.5 as a normative JSON syntax binding. The conversation progressed from foundational JSON Schema concepts through to the practical challenges of bringing UBL into the API-driven world while preserving its semantic rigor.

---

## 1. JSON Schema Referencing: `$defs` vs HTML-style Anchors

### Why `$defs/Something` instead of `#something`

JSON Schema uses **JSON Pointer** (RFC 6901) for fragment references, not HTML-style fragment identifiers. The reason is structural: HTML elements can have an `id` attribute with native browser lookup, but JSON has no built-in identity mechanism on arbitrary nodes. JSON Pointer is a path-based addressing scheme that walks the document structure.

When you write `"$ref": "#/$defs/MyType"`, you're saying: start at the root (`#`), enter the `$defs` key, then enter `MyType`. It's a traversal path, not a named anchor.

`$defs` is simply the conventional key for reusable sub-schemas (previously called `definitions` in older drafts). It has no special technical status — you could place schemas anywhere and point to them — but it's the agreed-upon standard location.

### The `$anchor` alternative

JSON Schema (2019-09 draft onward) supports `$anchor`, which is closer to the HTML pattern:

```json
{
  "$defs": {
    "MyType": {
      "$anchor": "my-type",
      "type": "string"
    }
  }
}
```

Referenced as `"$ref": "#my-type"`. Adoption has been slow due to tooling lag and the entrenchment of the `$defs` pattern.

---

## 2. Cross-Schema References and URI Structure

### The general URI pattern

Cross-schema references follow standard URI structure:

```
schema-identifier#fragment
```

Where the part before `#` is the **schema identifier** (set via `$id`) and the fragment is either a JSON Pointer or an `$anchor`. This mirrors HTML's `resource#fragment` pattern.

### `$id` is not the filename

An important distinction: `$id` is typically a full URI like `https://example.com/schemas/address`, not a filename. A reference like `"$ref": "address.json#street"` is a **relative URI reference** that resolves against the current schema's base URI. It works only if the resolver can map it to the correct target. The `$id` and the file path are separate concepts.

### Relative references and automatic resolution

Relative references between schemas (e.g., `item.json#description` from within `order.json`) resolve through standard URI resolution (RFC 3986) — a pure string operation that does not require network access. However, **schema discovery** is left to the implementation. The spec defines *how* to resolve a reference, not *how to find* the document it points to.

In practice, schemas are discovered through:

- **Schema registries** — tools like AJV let you register schemas by `$id`, and cross-references resolve automatically
- **Directory-based loading** — some tools scan a folder, read each file's `$id`, and build a registry
- **Build-time bundling** — separate source files are bundled into one document for deployment
- **Code generation tools** — tools like `quicktype` handle multi-file resolution internally

### Bundling into a single document

Bundling all schemas into a single document with `$defs` is technically possible but creates a maintenance nightmare. The practical approach is to maintain separate files and let tooling handle resolution. A bundled single-document form is a deployment artifact, not a development workflow.

---

## 3. URNs vs HTTP-style URIs as `$id`

### The relative reference problem with URNs

URNs are opaque identifiers with no hierarchical path structure. This means:

- **No relative references** — every `$ref` must use the full URN (e.g., `"$ref": "urn:example:schemas:item#description"`)
- **No shorthand** — there's no concept like `":item#description"` because URN resolution has no "relative to current namespace" mechanism
- The colon-separated parts in a URN *look* hierarchical but are treated as a single opaque string by URI resolution

### HTTP-style `$id` advantages

HTTP-style URIs provide relative reference resolution for free through RFC 3986, even when nothing is actually hosted at those URLs. The resolution is a pure string operation — the validator computes the full target URI from the base URI and looks it up in its internal registry. No HTTP request is needed.

This is the most common pattern: people use HTTP-style URIs as namespaced identifiers to get relative resolution benefits without actually hosting anything at those URLs.

### The readability trade-off

Relative references are shorter but require mental resolution — you need to know the current schema's base URI to understand where a `$ref` points. URN references are verbose but completely self-contained and immediately understandable.

Many teams use HTTP-style `$id`s for resolution benefits but write full `$ref`s anyway for clarity. For schemas shared across teams or published publicly, explicit references are much friendlier than relative ones.

### Relative references: not discouraged, but "know what you're getting into"

The JSON Schema spec fully supports relative references. The community is divided in practice:

- **Within a tightly coupled schema set** owned by one team: relative references are fine
- **For schemas consumed externally** or published as a standard: prefer full URIs
- **Consistency matters** — mixing relative and absolute in the same schema set causes confusion

### When you have an official URN namespace

Organizations with registered URN namespaces (MPEG, XMPP, OASIS, etc.) have a strong argument to use them. Their schemas are part of a formal identification ecosystem, and using HTTP URIs would be inconsistent. The verbosity is accepted as the cost of correctness, and tooling (registries, editors, autocomplete) manages the ergonomics.

The `$id` style choice depends on ecosystem, audience, and existing identification schemes. HTTP URI convenience is nice, but not always the right fit.

---

## 4. Schema-Instance Association: The Discovery Problem

### No established consensus

There is no single standard way to tell a JSON instance which schema validates it. Existing mechanisms include:

- **`$schema` property in the instance** — works by convention but technically `$schema` is for schemas to declare their meta-schema, not for instances
- **HTTP `Link` header with `rel="describedby"`** — the most "correct" approach for HTTP contexts, but adoption is very low
- **OpenAPI specifications** — the API definition declares which schema applies to which endpoint; by far the most common real-world solution, but only covers APIs
- **Custom media types** — correct in theory, heavy in practice
- **Convention and configuration** — what most people actually do; the application just "knows"

### The `describedby` header and URNs

The `Link` header accepts any URI, including URNs — `Link: <urn:example:schema:order>; rel="describedby"` is valid. But with a URL the client can fetch the schema; with a URN, the client gets an identifier with no built-in resolution mechanism. The header becomes a declaration rather than a discovery mechanism.

### OpenAPI's approach

OpenAPI solves association statically — the spec declares which schema applies to which endpoint, method, and status code. Adding `describedby` headers at runtime would be redundant. Validation happens at a different level: API gateways validate against the spec, client libraries are generated with types baked in. Nobody dynamically discovers schemas per response.

---

## 5. OpenAPI and JSON Schema: The Integration Gap

### OpenAPI's internal referencing model

OpenAPI strongly encourages — almost forces — a single-document model. All reusable schemas live under `components/schemas`, and everything references everything else with local JSON Pointers:

```yaml
$ref: '#/components/schemas/Order'
```

External references are supported in theory but inconsistently across tooling. Most teams keep everything in one file or split during development and bundle for distribution.

### URNs don't fit the OpenAPI world

OpenAPI's `$ref` is fundamentally a document-level referencing mechanism pointing at locations within or between files. URN-based `$id` identifiers don't fit this model. Even though OpenAPI 3.1 aligned with full JSON Schema 2020-12, most tooling still treats schemas as components within a document structure, not independently identified resources.

The philosophical difference: JSON Schema thinks of schemas as independently identifiable resources in a global namespace; OpenAPI thinks of schemas as building blocks within an API definition document.

### The practical impact on well-designed JSON Schemas

Even perfectly designed, properly identified, well-structured JSON Schemas using URNs and clean cross-references are essentially unusable in an OpenAPI implementation without significant reworking:

- URN-based `$ref`s must be rewritten to local references
- Schemas must be consolidated into `components/schemas`
- The clean modular architecture gets flattened

Options for bridging the gap:

1. **Manual bundling** — collapse into one OpenAPI document (tedious, error-prone)
2. **External `$ref`s with URL paths** — spotty tooling support
3. **Automated bundling** — maintain clean source schemas, generate OpenAPI-compatible output as a build artifact

### Two published sets: source of truth matters

Publishing both URN-based schemas and an OpenAPI-compatible version creates a synchronization risk — two sources of truth leads to drift. The correct approach:

- **Maintain only the canonical schemas** (or better: the common model they're generated from) as the single source of truth
- **Automate the conversion** — a build step that resolves URN `$ref`s, replaces them with local references, and bundles into an OpenAPI-compatible structure
- **Publish both, maintain one** — the OpenAPI version is a generated artifact, like compiled code

---

## 6. UBL JSON Syntax Binding: Architecture Review

### Context

The UBL 2.5 JSON Syntax Binding specification (https://kduvekot.github.io/ubl-json/) defines the normative rules for expressing UBL business documents and components in JSON. Key architectural decisions reviewed:

### `$jsonschema` for in-band schema identification

Every conformant UBL JSON instance carries a `$jsonschema` property at its root identifying the governing schema. This solves the schema-instance association problem that JSON Schema itself never standardized. The property is custom (not JSON Schema's `$schema`) to avoid meta-schema confusion.

For document instances:

```
"$jsonschema": "urn:oasis:names:specification:ubl:schema:json:Invoice-2"
```

For standalone ABIEs:

```
"$jsonschema": "urn:oasis:names:specification:ubl:schema:json:CommonAggregateComponents-2#Address"
```

**Status:** This is a suggestion, not final. It is essential for self-describing documents in document exchange contexts but may be redundant in OpenAPI contexts where the API contract already provides schema identification.

### Dual-use design: documents and standalone ABIEs

The specification supports both complete UBL documents and individual ABIEs as standalone JSON payloads. A `Party` embedded inside an `Invoice` is structurally identical to a `Party` served from a `GET /party/{id}` endpoint — same schema, same semantics, same validation rules. This eliminates semantic drift between document models and API models.

### URN-based identifiers with version stability

Schema identifiers use the OASIS URN namespace (e.g., `urn:oasis:names:specification:ubl:schema:json:Invoice-2`). These are stable across minor revisions — a document referencing Invoice-2 remains valid across UBL 2.5, 2.6, etc. This guarantees forward compatibility.

### `$anchor` for ABIE references

Each ABIE in the Common Aggregate Components schema gets an `$anchor` equal to its UBL name, enabling clean URN + fragment references for standalone payloads without relative references.

### Generation pipeline

All JSON schemas are generated from the common UBL model (UBL XSD source). A `catalog.json` provides URN-to-file-location mapping for resolution. This means neither the URN schemas nor any derived OpenAPI version would be hand-maintained — both are generated artifacts.

### Digital signatures

The spec uses JWS (JSON Web Signature) with JCS (JSON Canonicalization Scheme) — the natural JSON equivalent of XMLDSig without the complexity. Both enveloped and detached signature profiles are supported.

---

## 7. The `$jsonschema` Debate

### The tension

`$jsonschema` makes instances self-describing — any system can look at the property and know what it's dealing with. This is essential for document exchange where JSON might arrive via email, file transfer, or message queues with no API contract.

In an OpenAPI context, the API definition already provides schema identification. `$jsonschema` becomes redundant metadata and creates a potential consistency problem (what if the property says Invoice but the endpoint contract says Order?).

### Possible resolution

Make `$jsonschema` normatively required for document exchange but allow communities operating within a defined API contract to waive the requirement when schema identification is unambiguously provided by the transport or API specification. Alternatively, handle this through the layered validation model (see section 8).

---

## 8. Validation Strategy: Spectral as Schematron's Successor

### The multi-level validation model

UBL's XML ecosystem uses multi-level validation: XSD for structure, Schematron for business rules. The JSON equivalent would be:

1. **JSON Schema** — validates structure, types, cardinality
2. **Base UBL ruleset** — enforces cross-field rules that JSON Schema can't express (e.g., "`$jsonschema` must match a known UBL identifier," "AmountType objects must include currencyID")
3. **Community rulesets** — profile-specific constraints (e.g., PEPPOL business rules)

### Spectral as the business rule layer

Spectral (from Stoplight) is a promising candidate for the Schematron role:

- Rule-based and declarative
- Rulesets are shareable as files
- Supports custom functions for complex logic
- Widely adopted in the API world

This layering would allow `$jsonschema` to be optional at the JSON Schema level but mandatory through a Spectral rule — clean separation of concerns.

### Considerations

- **Complexity ceiling** — some PEPPOL Schematron rules involve calculations, cross-element aggregations, or conditional logic that may push Spectral's custom functions hard
- **Normative standing** — Schematron is an ISO standard; Spectral is an open-source project. The spec could define rules normatively and position Spectral as one conformant implementation
- **API overhead** — Spectral works well for document validation (a discrete, deliberate step) but may be too heavy for API validation at scale (thousands of requests per second, where the framework already validates against the OpenAPI spec)

### Two conformance paths

The spec should acknowledge different validation economics:

- **Document exchange** — JSON Schema + business rule layer (Spectral or equivalent); `$jsonschema` required; validation is a deliberate step
- **API implementations** — conformance through the OpenAPI definition; business rules enforced at the application level; `$jsonschema` optional when the API contract provides equivalent identification

The critical requirement across both paths: **instance-level UBL compliance must be identical**. A `Party` from an API endpoint must be structurally identical to a `Party` in a document.

---

## 9. Strategic Imperative: The OpenAPI Component Library

### The fragmentation risk

If UBL only publishes formal JSON schemas with URN identifiers and leaves the OpenAPI story to communities, every implementer will build their own interpretation. Peppol creates one mapping, a fintech startup creates another, a government agency creates a third. They all think they're doing UBL, but the instances aren't interoperable. This is exactly how XML-based standards fragmented in the early days before UBL brought discipline.

### The proposed solution

Publish an official **OpenAPI-ready component library** as a derived artifact alongside the normative schemas:

- **Normative schemas** — URN-based, for document exchange (the authoritative source)
- **OpenAPI component library** — URL-based, bundled for API consumption (derived, generated from the same model)

Both trace back to the same semantic library. If an instance validates against either, it's UBL.

### Why this is feasible

The generation pipeline already exists. One common model produces the URN-based schemas today. Adding an OpenAPI output target is an engineering task, not an architectural change. The maintenance cost is near zero because both outputs are generated.

### Compliance by inclusion

If developers can `$ref` into official UBL components from their OpenAPI definitions, they're using canonical structures by construction. They can't accidentally drift because they didn't write the schema — they referenced it. This is compliance by inclusion rather than compliance by reimplementation.

### Enforcement without Spectral in the API world

The enforcement mechanism for APIs is different from document exchange:

- **Build-time:** Does your OpenAPI spec reference the canonical UBL components?
- **Runtime:** Do your instances validate against those components?
- A lightweight CI-compatible test suite could verify OpenAPI definitions haven't deviated from UBL — not Spectral at runtime, but a build-time check

---

## 10. The Path Forward: Working Implementation

### Committee dynamics

The UBL TC includes members at varying levels of understanding of these issues. Some understand the JSON/API world deeply; others have spent years building the XML ecosystem and see JSON as "just another syntax binding." The JSON specs have not been widely circulated yet.

### Strategy: show, don't tell

A working implementation is worth a thousand position papers in a standards committee. Rather than debating abstract governance, present the TC with a concrete demonstration.

### What the demonstration needs

1. **OpenAPI component library** — generated from the same model that produces the URN-based schemas, URL-based identifiers, packaged so developers can reference components with simple `$ref`
2. **Sample OpenAPI specification** — a familiar use case (e.g., invoice submission and retrieval API) using official UBL components; clean, idiomatic, recognizable to any API developer
3. **Validation demo** — showing that instances produced by the API validate against both the OpenAPI spec and the normative URN-based schema, proving "same data either way" concretely
4. **The generation pipeline itself** — demonstrating this isn't a manual maintenance burden but an automated derivation from the model the TC already governs

### The argument for skeptics

Show the same API three ways:

1. Raw UBL JSON schemas with URN identifiers — correct but awkward to consume in API tooling
2. Someone's ad-hoc attempt to build an invoice API — drifting from UBL in subtle ways
3. The same API using official UBL OpenAPI components — clean, idiomatic, provably compliant

The third version is only possible if the TC publishes it. The gap between the first and third is where fragmentation lives.

---

## 11. Key Takeaways

1. **`$id` style matters** — URNs are conceptually correct for standards bodies with registered namespaces but sacrifice relative reference convenience. This is an accepted trade-off for UBL.

2. **Schema discovery is unsolved in JSON Schema** — `$jsonschema` as a custom in-band property is a pragmatic UBL-specific solution to a gap the JSON Schema spec itself never filled.

3. **OpenAPI and JSON Schema have different worldviews** — JSON Schema sees independently identified resources; OpenAPI sees building blocks in a document. Bridging them requires deliberate architectural work and tooling.

4. **One source of truth, multiple outputs** — the UBL generation pipeline from a common model is the key enabler for serving both the document exchange world and the API world without drift or synchronization risk.

5. **Validation must be layered** — JSON Schema for structure, Spectral (or equivalent) for business rules, with different tooling appropriate for document exchange vs API contexts. The two paths validate differently but enforce identical instance-level compliance.

6. **Instance-level compliance is non-negotiable** — regardless of delivery mechanism (document, API, message queue), UBL data must be structurally identical everywhere. A `Party` is a `Party` is a `Party`.

7. **Meet developers where they are** — publishing an OpenAPI-ready component library isn't optional for UBL's continued relevance; it's how you prevent fragmentation in an increasingly API-driven world.

8. **Show, don't tell** — a working implementation demonstrating the complete pipeline (common model → URN schemas + OpenAPI components → sample API → validation proof) is the most effective way to build consensus in the TC.
