# WD01 Review Discussion Points

Review of: **UBL 2.5 JSON Syntax Binding Version 1.0, Committee Specification Draft 01 (20 February 2026)**

For a detailed content comparison between the previous working draft and WD01, see [document-comparison.md](document-comparison.md).

---

## 1. Schema identification property naming

WD01 renames `$schema` to `UBLEntity` throughout the specification (sections 6.1, 6.4, 10.1, 13.2, 13.3, 15.1). Our generated schemas use `$jsonschema`.

Three different names now exist for the same concept:

| Source | Property name |
|--------|--------------|
| Previous working draft | `$schema` |
| WD01 | `UBLEntity` |
| Generated schemas (this repo) | `$jsonschema` |

**Discussion:** `$schema` was dropped to avoid collision with JSON Schema's own `$schema` keyword. `UBLEntity` is vague and doesn't convey that it points at a schema. `$jsonschema` signals purpose while avoiding the clash. The TC should align on a single name.

## 2. URN vs HTTPS URL identifiers

Our generated schemas use URN-based identifiers:
```
urn:oasis:names:specification:ubl:schema:json:Invoice-2
```

WD01 specifies HTTPS URL-based identifiers:
```
https://docs.oasis-open.org/ubl/2/json/schemas/UBL-Invoice-2
```

**Discussion:** HTTPS URLs create the expectation of resolvability, but JSON Schema's `$id` is defined as an identifier, not a locator. The JSON Schema specification does not require that identifiers be resolvable. URNs are honest about being abstract identifiers but lack discoverability. If HTTPS URLs are used, they could be made resolvable by hosting schemas at those paths (e.g., via GitHub Pages), but this couples identifiers to hosting infrastructure. This is not just a UBL question — it's a broader OASIS and JSON Schema community issue.

## 3. Schema file naming convention

Document schema filenames differ:

| Generated schemas | WD01 Annex C |
|-------------------|--------------|
| `Invoice-2.5.json` | `UBL-Invoice-2.5.json` |
| `ApplicationResponse-2.5.json` | `UBL-ApplicationResponse-2.5.json` |

WD01 adds a `UBL-` prefix to document schemas. Common schemas (e.g., `CommonAggregateComponents-2.5.json`) match in both.

**Discussion:** The TC should align on whether document schema filenames include the `UBL-` prefix.

## 4. Singleton-or-array vs always-array for repeating elements

WD01 section 8.1 prescribes that repeating elements (0..n, 1..n) may be represented as either a single value or an array:

> "If exactly one occurrence is present, it shall be represented as a single value or object. If more than one occurrence is present, it shall be represented as an array of values or objects."

This means consumers must check whether a value is a scalar or an array before processing every repeating field.

### Industry consensus

Research across major JSON-based standards shows an overwhelming consensus for **always-array**:

| Standard | Approach | Rationale |
|----------|----------|-----------|
| **FHIR/HL7** | Always array | *"An item that may repeat is represented as an array even in the case that it doesn't repeat so that the process of parsing the resource is the same either way"* |
| **JSON:API** | Always array | *"A logical collection of resources MUST be represented as an array, even if it only contains one item or is empty"* |
| **JSON-LD (W3C)** | Always array via `@container: @set` | *"Values of terms associated with a @set container are always represented in the form of an array — even if there is just a single value"* |
| **Linked Art (Getty)** | Always array | *"Consistency is a core feature of usability"* |
| **GeoJSON (RFC 7946)** | Always array | Specification requirement |
| **Google APIs** | Always array | Protobuf repeated fields = JSON array, always |
| **Microsoft APIs** | Always array | Consistency across services |
| **Zalando** | Always array | Cardinality enforced consistently |
| **OpenAPI/AsyncAPI** | Type-consistent | A field defined as array is always array |

The only notable exception using singleton-or-array is **AWS IAM Policies**, which is widely documented as a source of bugs and complexity for consumers. Every tool that processes IAM policies must first normalize fields to arrays before processing.

### FHIR as precedent

FHIR is the closest analogue to UBL — a complex document-exchange standard with XML heritage that added a JSON binding. They chose always-array and noted a forward compatibility benefit: *"Elements may change whether they are allowed to repeat or not between versions... Processors should be prepared to manage such changes."*

### Prior UBL JSON work

The OASIS UBL TC itself offered two approaches for UBL 2.1-2.3 JSON:

- **Legacy-based** (always array): *"future versions of UBL may raise the cardinality of any given object and so this approach is future-proof to revisions. This approach is also consistent and is used without thought of cardinality."*
- **Model-based** (array only when max cardinality > 1): More natural JSON, but *"when a version of UBL changes a construct's maximum cardinality... a past instance no longer will validate with the new schemas. This breaks forward compatibility."*

### Impact on `_n` pattern

If always-array is adopted, the `_n` schema pattern described in WD01 becomes unnecessary entirely (see point 5).

**Discussion:** The TC should consider adopting always-array for repeating elements, aligning with industry consensus and simplifying both schemas and consumer implementations.

## 5. The `_n` schema pattern — merged into Point 4

This point has been merged into [Point 4: Array representation](wd01-point-04-array-representation.md) as the `_n` pattern is directly tied to the singleton-or-array design decision. If always-array is adopted, `_n` becomes unnecessary.

## 6. `"value"` as the generic property name

All schemas use `"value"` as the property name for the core content in object form:

```json
{"value": 100.00, "currencyID": "EUR"}
{"value": "description text", "languageID": "EN"}
{"value": "ABC-123", "schemeID": "GLN"}
```

Earlier TC discussions considered using type-specific names (e.g., `"amount"`, `"text"`, `"identifier"`) instead of generic `"value"`. This has not been implemented in any branch or schema.

**Discussion:** Should the property name reflect the type (more descriptive, potentially easier for developers to understand) or remain generic `"value"` (simpler schema design, consistent across all types)?

## 7. Deprecated documents and elements

WD01 section 5.2 states: *"deprecated elements defined in UBL 2.5 are not included in the normative JSON Schemas."*

Our generator does not handle deprecation — it does not read the `DeprecatedDefinition` column from the GC file. All deprecated content is present in our schemas.

### Deprecated document types (6)

These are generated as schemas but excluded from WD01's Annex C:

- AttachedDocument
- FreightInvoice
- OrderResponseSimple
- StockAvailabilityReport
- TenderStatus
- TenderStatusRequest

### Deprecated elements within non-deprecated documents (6)

| Location | Element | Type |
|----------|---------|------|
| SubcontractTermsType | UnknownPriceIndicator | BBIE |
| TenderingProcessType | OpenTenderEvent | ASBIE |
| InventoryReport | InventoryReportingParty | ASBIE |
| DebitNote | ABIE definition changed | ABIE |
| QualificationApplicationRequest | ABIE definition changed | ABIE |
| QualificationApplicationResponse | ABIE definition changed | ABIE |

### Backward compatibility concern

UBL XML has always maintained full backward compatibility — a UBL 2.1 document validates against UBL 2.5 XML schemas. WD01 argues that since this is the first JSON binding, there is no backward compatibility obligation. However:

- People will want to convert existing XML documents to JSON. Those documents may contain deprecated elements.
- WD01 acknowledges this: *"Implementers should be aware that automated XML-to-JSON transformation of UBL instances may not be possible where deprecated elements are present in the XML source."*
- Acknowledging the problem does not solve it for implementers who need to do exactly that.

**Discussion:** Should the JSON schemas include deprecated elements for interoperability with existing UBL documents, or should they enforce a clean break? What guidance should be provided for XML-to-JSON conversion of documents containing deprecated elements?

## 8. New section: UBL Semantic Library (WD01 section 5)

WD01 adds a new section establishing:
- The UBL Semantic Library as the authoritative source of business semantics (section 5.1)
- Element deprecation policy (section 5.2)
- References to accompanying ODS spreadsheet, XLS spreadsheet, and HTML documentation

**Discussion:** Review whether the deprecation policy implications (see point 7) and the relationship to schema annotations are correctly specified.

## 9. Controlled vocabularies softened

WD01 moves ISO 4217, ISO 3166, and UN/ECE Rec 20/21 from normative "shall" requirements to informative examples:

**Previous:** *"currencyID **shall** follow ISO 4217, unitCode **should** follow UN/ECE Recommendations 20 and 21, and country or region codes **shall** follow ISO 3166"*

**WD01:** *"producers should employ published and stable vocabularies appropriate to their business domain. Conformance to external vocabularies is determined by the profile or community..."*

These references also moved from normative to informative in Annex B.

**Discussion:** This loosens conformance requirements. Is this intentional? Should certain vocabularies (at minimum ISO 4217 for currency codes) remain normative?

## 10. New semantic conformance clause (WD01 section 15.2)

WD01 adds a new conformance level:

> "A UBL JSON instance is considered semantically conformant when it correctly represents business information in accordance with the semantic definitions of the UBL data model."

This is softer than schema validation — it requires elements to be used consistently with their normative definitions and convey information consistent with UBL business semantics.

**Discussion:** How is semantic conformance verified in practice? Is this testable, or purely aspirational?

## 11. ~~Embedded fonts in WD01 document~~ — Removed

Not relevant to the specification content. Editorial note only.
