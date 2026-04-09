# UBL JSON Specification Discussion

## Discussion Log — JSON Schema, URNs, and the UBL 2.5 JSON Syntax Binding

*Captured from a conversation exploring JSON Schema design decisions for the OASIS UBL TC*

---

## 1. Should the $id of a JSON Schema always point to a resolvable URL?

**Question:** Should the `$id` of a JSON Schema always point to a resolvable URL?

**Answer:** No. The `$id` serves as a unique identifier, not necessarily a locator. The value is a URI (Uniform Resource Identifier), and the key distinction is between a URI as an identifier vs. a locator. A URL is a specific type of URI that implies retrievability, but JSON Schema only requires a URI.

**Practical considerations:**

- **Why you might want it resolvable:** Some tools and validators will attempt to fetch the URI to resolve `$ref` references. Hosting schemas at their `$id` URI is considered a best practice in collaborative or public-facing environments.
- **Why it doesn't have to be:** The JSON Schema specification (from Draft 6 onward) treats `$id` as a base URI for resolving relative `$ref` references within the schema. Many schemas use URIs under a domain the author controls without ever actually hosting anything there.

**Common patterns include:**
- `https://example.com/schemas/foo.json` — conventional, sometimes resolvable
- `urn:example:foo` — a URN, which by definition is not a locator
- `https://json-schema.org/draft/2020-12/schema` — the meta-schema ID, which does happen to be resolvable

---

## 2. How do JSON Schema validators know where to get schemas for $ref's?

**Resolution mechanisms (varies by validator):**

1. **Local resolution first.** If a `$ref` points to something within the same document (like `#/$defs/Address`), the validator resolves it against the current schema document using JSON Pointer or by matching a `$id`/`$anchor`.

2. **Pre-loaded schema registry.** Most validators let you register schemas ahead of time in a local "store" or "registry," keyed by their `$id`. Examples:
   - Python's `jsonschema`: `RefResolver` or newer `Registry` API
   - JavaScript's `ajv`: `ajv.addSchema(schema)`

3. **Network fetching as a fallback.** Some validators will attempt to HTTP-fetch a `$ref` URI if they can't resolve it locally. However, this behavior is inconsistent and often disabled by default. `ajv` does not fetch remote schemas automatically.

4. **File system resolution.** Some tooling resolves relative path `$ref` values against the file system.

**Practical conclusion:** Don't rely on validators magically fetching schemas from URLs. The typical workflow is:
1. Bundle all schemas together in one document using `$defs`, or
2. Pre-register all schemas with the validator before validation runs, or
3. Use a tool-specific loader/resolver

This is why `$id` doesn't need to be resolvable — most real-world setups never fetch it. It just acts as the key in the registry that `$ref` values match against.

---

## 3. How do you know what schema a JSON instance file needs to be validated against?

JSON itself has no built-in mechanism for this. Unlike XML, which has `xsi:schemaLocation` or DOCTYPE declarations, plain JSON has no standard way to say "validate me against this schema."

**Approaches:**

- **Explicit in your application.** The most common approach: your code simply knows which schema to apply.
- **The `$schema` keyword.** Its official purpose is to declare which meta-schema (draft) the schema itself is written against. It appears in schema documents, not in instance documents. Some repurpose it for instances, but this is convention, not spec.
- **Content-Type and HTTP headers.** Using media type parameters or `Link` headers with `rel="describedby"`. Loosely defined, thin adoption.
- **Convention by file name or location.** Implicit association through project structure.
- **Schema embedded in a wrapper.** Application-specific envelope containing schema metadata.

**Conclusion:** It's a gap in the JSON ecosystem compared to XML. The answer is almost always "your tooling or application decides."

---

## 4. Would it make more sense to use URNs for schema identification than URLs?

### The case for URNs
- **Honesty of intent.** When you use a URL but nothing is hosted there, you create false expectations. A URN makes it immediately clear this is a name, not a location.
- **Decouples identity from infrastructure.** If your domain changes, identifiers don't break.

### The case against URNs
- The JSON Schema ecosystem is heavily URL-oriented by convention.
- Relative `$ref` resolution works more naturally with hierarchical URLs.
- URN namespaces are technically supposed to be registered with IANA.

### A middle ground
A URL under a domain you control, with a clear convention that signals "this is an identifier":
`https://schemas.mycompany.com/order/v1`

Whether anything is hosted there is an implementation detail. It plays nicely with all tooling and could become resolvable later.

---

## 5. The UBL context: keeping URNs when moving from XML to JSON

### The situation
The project (OASIS UBL TC) has a long history with XML and uses IANA-registered URNs for XML namespaces. When switching to JSON/JSON Schema, some members wanted to move to resolvable URLs, while the proposal was to keep URNs and simply replace the `:xml:` segment with `:json:`.

### Why URNs should be kept

1. **You already have a well-designed naming system.** IANA-registered URNs are not trivial to get. That's an asset, not something to throw away.
2. **The `:xml:` to `:json:` swap is elegant.** It maintains continuity and traceability.
3. **Switching to URLs introduces problems you don't currently have.** Domain ownership, hosting, 404 confusion.
4. **The "tooling wants URLs" argument is weak.** Any correct JSON Schema validator must accept any valid URI as a `$id`. URNs are valid URIs.

### The key question for URL advocates
What concrete benefit do resolvable URLs give you that you don't already have?

---

## 6. The complete infrastructure: catalogs and self-describing instances

### Existing infrastructure
- Schema files are available on the official website (both XSD and JSON Schema)
- `catalog.xml` handles URN-to-schema-file mapping for XML
- `catalog.json` does the same for JSON Schema
- Both are resolvable, subversion-specific, with major-version URNs

### The parallel structure
- `urn:...:xml:...` → `catalog.xml` → XSD file on website
- `urn:...:json:...` → `catalog.json` → JSON Schema file on website

### The $jsonschema proposal
A mandatory `$jsonschema` property in JSON schema definitions that points to the `$id` of the schema, so every instance directly indicates what schema it should validate against.

**Why `$jsonschema` and not `$schema`:** Using `$schema` would conflict with its defined meaning in JSON Schema spec (identifying the meta-schema draft). A distinct property name avoids ambiguity.

**The chain from instance to validation:**
instance `$jsonschema` → catalog.json → schema file → validate

**No guessing, no application-specific wiring, no magic.**

---

## 7. Ammunition for the TC debate

### Counter-arguments prepared for likely objections:

**"$jsonschema isn't part of the JSON Schema spec"**
Neither is any other business property in your schema. The spec explicitly allows additional properties, and `$jsonschema` doesn't conflict with any reserved keyword.

**"We should use URLs like everyone else"**
"Everyone else" doesn't have IANA-registered URN namespaces. Most projects use URLs as path of least resistance. Switching to URLs would be a downgrade.

**"It adds bloat to every instance"**
One small string property. Compare that to XML namespace declarations and `xsi:schemaLocation` attributes.

**"Tooling won't understand $jsonschema"**
It doesn't need to. To a standard validator, it's just a regular required property with a `const` constraint.

**"We should modernize, not carry XML patterns forward"**
The question isn't "is it from XML" but "does it solve a real problem well." Self-describing documents are a good idea regardless of origin.

**"We can just handle schema selection in application code"**
Sure, for one application. Embedding the schema reference in the instance scales across tools, teams, and systems.

**"Nobody else does it this way"**
GeoJSON has required `type`. AWS CloudFormation has `AWSTemplateFormatVersion`. Kubernetes has `apiVersion` and `kind`. OpenAPI has `openapi: "3.1.0"`. Self-describing instances are well-established.

---

## 8. The OASIS UBL TC context

This is a decision for an international standard (ISO/IEC 19845) used in government procurement, e-invoicing, and supply chain systems worldwide.

### Key points for a standards context:

- **Continuity is a feature.** The `urn:oasis:names:tc:ubl:schema:xsd:...` URNs are already embedded in legislation, government procurement systems, and e-invoicing platforms.
- **The `urn:oasis:...` namespace is governed by RFC 3121.** IETF-level backing. URL-based schemes have weaker governance.
- **The `:xsd:` to `:json:` pattern is already established in spirit.**
- **UBL's implementer base is conservative by necessity.** Tax authorities, customs systems, financial institutions value stability.
- **UBL is ISO/IEC 19845.** Decisions will be embedded in national legislation for decades. URN persistence is guaranteed by IANA registration; URL persistence depends on domain renewal.

---

## 9. Review of the UBL 2.5 JSON Syntax Binding draft

### Source
https://kduvekot.github.io/ubl-json/

### What's strong

- **`$jsonschema` design:** Major-version-stable URN pattern like `urn:oasis:names:specification:ubl:schema:json:Invoice-2` means documents remain valid across minor versions.
- **Dual-use model (sections 5.1–5.3):** ABIEs as valid root payloads serves both document exchange and API-driven worlds without semantic drift.
- **Data type simplification (section 10):** Collapsing verbose CCTS attribute sets to single supplementary components strikes a good balance.
- **Digital signatures:** JWS + JCS canonicalization is the right call for JSON-native signing.

### Observations

- **URN rationale:** Section 12.4 is the strongest evidence for URNs. Consider adding an explicit paragraph explaining why URNs were chosen.
- **Cardinality (section 7.1):** The scalar-or-array pattern for 0..n creates implementation burden. Consider whether this needs addressing.
- **"Resolve" language (section 9.1):** The word "resolve" might give URL advocates an opening. Consider "shall correspond to" or "shall identify" instead.

---

## 10. Devil's advocate: objections from a pure JSON/API developer

### Objection 1: "What on earth is $jsonschema?"
JSON Schema has `$schema`. The `$` prefix carries expectations. `ajv` won't recognize it. Why invent a new keyword?

### Objection 2: "These URNs mean nothing to me"
Can't put it in a browser. Can't fetch it. Where do I get the schema? If this were a URL, I could just fetch it.

### Objection 3: "The cardinality rules will break my code"
A field with 0..n can be scalar, object, or array. Every major API style guide says: if it can be an array, always an array. The "sometimes scalar, sometimes array" pattern is hated for good reason.

### Objection 4: "The data types feel XML-ish"
`currencyID`, `mimeCode`, `value` as generic carrier — smells like mechanical XML translation. In JSON-native APIs you'd use semantic field names.

### Objection 5: "Why can't I use null?"
JavaScript and most JSON APIs use `null` normally. Many serializers emit `null` by default. Custom serialization logic to strip nulls is unnecessary burden.

### Objection 6: "Fragment identifiers for standalone ABIEs are awkward"
Referencing `urn:...CommonAggregateComponents-2#AddressType` is pointing to a fragment inside a monolithic schema. Modern practice prefers individual type schemas.

### Objection 7: "Where's the OpenAPI integration story?"
The spec talks about standalone ABIEs for APIs but provides no guidance on OpenAPI integration.

### Objection 8: "Digital signatures section is over-specified"
Section 5.4 excludes security frameworks, but section 11 goes deep into JWS. This couples the syntax binding to specific security choices.

### Objection 9: "This could just be a JSON Schema + style guide"
Most of what the spec prescribes could be expressed as well-structured JSON Schemas with a few pages of conventions.

---

## 11. Systematic responses and spec improvements

### 1. $jsonschema

**Defense:** The `$` prefix signals "metadata, not business content." It doesn't conflict with any reserved JSON Schema keyword. It appears in instances, not schemas.

**Spec improvement:** Add a rationale note in section 9.1 explaining the naming choice. Consider engaging with the JSON Schema community to propose `$jsonschema` as a formal convention or vocabulary.

### 2. URNs

**Defense:** Developers can't click on most `$id` values in JSON Schemas either — even URL-shaped ones often 404. The real workflow is always: get schema, load into validator, validate.

**Spec improvement:** Add an "Implementer's Quick Start" appendix showing:
- catalog.json structure and usage
- Concrete examples of loading UBL JSON schemas into ajv, Python's jsonschema, etc.
- How the URN maps to the actual file in the distribution ZIP
- One-liner showing: `urn:oasis:...:Invoice-2` → `json/schemas/maindoc/Invoice-2.5.json`

Also: publish schemas at resolvable URLs alongside the URN identifiers (as already done for XSDs). The URN remains the `$id` and authoritative name; the URL is a convenience.

### 3. Cardinality (highest impact change for adoption)

**Defense:** The pattern exists because UBL is an interchange format optimizing for concise common cases and lossless XML round-tripping.

**Spec improvement:** Define two conformance profiles for producers:

- **Concise profile** (current behavior): scalar for singletons, array for multiples. Optimized for human readability and wire size.
- **Strict profile** (always-array for repeating fields): any field with cardinality 0..n or 1..n is always an array. Any BBIE with supplementary components is always object form.

Consumers required to accept both. Strict profile recommended for API contexts, concise for document interchange. This removes the single biggest barrier to TypeScript/OpenAPI/code-generation integration.

### 4. Data types naming

**Defense:** Naming comes from CCTS, the underlying data model shared with XML. Changing names would break semantic correspondence.

**Spec improvement:** Explicitly state the rationale in section 10. Add a non-normative mapping table showing correspondence between UBL names and common JSON/REST conventions.

### 5. Null prohibition

**Defense:** Well-established best practice in interchange formats. `null` creates ambiguity between "absent" and "explicitly unknown."

**Spec improvement:** Add rationale note. Acknowledge that serializers emit nulls and tell developers what to do about it: "Producers whose serialization frameworks emit null for absent fields shall apply a post-processing step to remove such properties before transmission."

### 6. Fragment identifiers for ABIEs

**Defense:** Monolithic schema with fragments is standard JSON Schema pattern. Draft 2020-12 supports `$anchor` for this purpose.

**Spec improvement:** Include concrete examples of referencing standalone ABIEs. Ensure every ABIE has a properly defined `$anchor`. Provide a table listing all available ABIE anchors.

### 7. OpenAPI integration

**Defense:** The spec is right to stay out of API design.

**Spec improvement:** Publish a non-normative OpenAPI companion Committee Note covering:
- How to reference UBL JSON schemas from OpenAPI 3.1 documents
- How to configure schema resolution for URN-based `$id` values
- Example OpenAPI snippets for common patterns
- How the strict producer profile maps to OpenAPI type generation

### 8. Digital signatures

**Spec improvement:** Consider restructuring section 11 as a normative but optional annex. Or add a clear note: "This section is normative only for implementations that require digital signatures."

### 9. "Just a schema + style guide"

**Defense:** JSON Schema alone cannot express several critical requirements: cardinality duality, `$jsonschema` binding, null prohibition rationale, extension semantics, signature canonicalization, conformance requirements.

**Spec improvement:** Lean harder into schemas as the primary artifact. Each normative rule should reference the schema construct that implements it. Add a "Conformance Checklist" appendix — single-page summary of all SHALL requirements.

### Priority order of spec changes for adoption:
1. Define strict producer profile (always-array, always-object) — removes biggest TypeScript/OpenAPI barrier
2. Add implementer's quick start appendix with practical validator setup
3. Add rationale notes throughout for $jsonschema, URN choice, null prohibition, CCTS naming
4. Publish OpenAPI companion Committee Note
5. Ensure schemas available at resolvable URLs alongside URN identifiers

---

## 12. Replacing the generic "value" property with semantic names

### The insight
The type system is closed — exactly 14 unqualified data types. Only 8 ever need the object form (types without supplementary components are always scalar). Each can get a semantic content property name.

### Proposed mapping

| Data type | Content property | Supplementary |
|---|---|---|
| AmountType | `amount` | `currencyID` (mandatory) |
| BinaryObjectType | `content` | `mimeCode` (mandatory) |
| CodeType | `code` | `listID` |
| IdentifierType | `id` | `schemeID` |
| MeasureType | `value` | `unitCode` (mandatory) |
| QuantityType | `quantity` | `unitCode` |
| TextType | `text` | `languageID` |
| NameType | `name` | `languageID` |

### Why this works

- No ambiguity: within any given object form, the content property name is determined by the data type, which is determined by the BBIE's position in the schema.
- Schema implementation is straightforward: each type definition uses the specific property name.
- TextType vs NameType: different content names (`text` vs `name`) actually help — you can tell which type you're dealing with even without schema context.

### Examples

Instead of `{"value": 100.00, "currencyID": "EUR"}`:
```json
{"amount": 100.00, "currencyID": "EUR"}
```

Instead of `{"value": "Acme Corp", "languageID": "en"}`:
```json
{"name": "Acme Corp", "languageID": "en"}
```

### Why MeasureType keeps `value`

Alternatives considered:
- `magnitude` — carries earthquake/physics baggage, feels wrong for 0.3 millimeters
- `measurement` — technically includes both number and unit, slightly redundant alongside `unitCode`
- `measured` — grammatically unusual as standalone noun

"The value is 0.3 millimeters" is exactly what anyone would say. For MeasureType, `value` is genuinely the right word.

### Impact on spec and tooling

- Section 10.1 Table 1 gets an additional "Content property" column
- Normative rule changes from "a `value` property" to "a content property whose name is determined by the data type as listed in Table 1"
- Schema generator needs only an 8-row lookup table
- Change propagates automatically to every BBIE in every schema

### The argument for the TC

Costs almost nothing in complexity — static, finite mapping in the type system. Yields significant improvement in readability and developer experience. Makes UBL JSON instances self-documenting at the property level. Addresses the "mechanical XML translation" criticism head-on. The generic `value` pattern comes from XML's text content model where element text nodes don't have names. In JSON, every value has a key — using that key to carry meaning is one of JSON's fundamental strengths.

---

*This document captures the discussion as of March 2026. The UBL 2.5 JSON Syntax Binding draft is available at https://kduvekot.github.io/ubl-json/ (pending move to OASIS TC repository).*
