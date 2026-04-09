# Point 6: Content Property Naming — `"value"` vs Semantic Names

## The question

When a UBL data type has supplementary components (like a currency code or language identifier), the core content is wrapped in an object. Should the property holding the core content be named generically (`"value"`) or use a type-specific name (`"amount"`, `"text"`, `"id"`, etc.)?

**Current approach (WD01 and our schemas):**
```json
{"value": 100.00, "currencyID": "EUR"}
{"value": "description text", "languageID": "EN"}
{"value": "ABC-123", "schemeID": "GLN"}
```

**Proposed alternative (from earlier TC discussions):**
```json
{"amount": 100.00, "currencyID": "EUR"}
{"text": "description text", "languageID": "EN"}
{"id": "ABC-123", "schemeID": "GLN"}
```

The proposed mapping from the earlier discussion:

| Data type | Proposed content property | Supplementary |
|-----------|--------------------------|---------------|
| AmountType | `amount` | `currencyID` (mandatory) |
| BinaryObjectType | `content` | `mimeCode` (mandatory) |
| CodeType | `code` | `listID` |
| IdentifierType | `id` | `schemeID` |
| MeasureType | `value` (kept) | `unitCode` (mandatory) |
| QuantityType | `quantity` | `unitCode` |
| TextType | `text` | `languageID` |
| NameType | `name` | `languageID` |

## Industry research

### Data interchange standards use generic names

Standards that must represent multiple value-with-metadata types through a uniform structure consistently use a generic property name:

| Standard | Generic property | Used for |
|----------|-----------------|----------|
| **FHIR/HL7** | `value` | Quantity, Money, Identifier |
| **Schema.org** | `value` | MonetaryAmount, QuantitativeValue, PropertyValue |
| **GS1 Web Vocabulary** | `value` | QuantitativeValue (aligned with Schema.org) |
| **UN/CEFACT JSON NDR** | `content` | All CCTS types (amountType, measureType, codeType, etc.) |
| **JSON-LD (W3C)** | `@value` | Language-tagged strings, typed values |
| **UBL 2.3 JSON (OASIS published)** | `_` | All BBIE content |

FHIR is the most instructive precedent — it uses `value` for Quantity, Money, and Identifier, but `code` (not `value`) for Coding, where the semantics genuinely differ from a generic value.

Sources:
- [FHIR v5.0.0 Datatypes](https://www.hl7.org/fhir/datatypes.html)
- [Schema.org MonetaryAmount](https://schema.org/MonetaryAmount)
- [Schema.org QuantitativeValue](https://schema.org/QuantitativeValue)
- [GS1 Web Vocabulary QuantitativeValue](https://www.gs1.org/1/gs1-smartsearch-vocab/QuantitativeValue)
- [UN/CEFACT JSON Schema NDR V1.0 (PDF)](https://unece.org/sites/default/files/2023-11/API-TECH-SPEC_JSON_Schema_NDR_version1p0.pdf)
- [JSON-LD 1.1 Specification](https://w3c.github.io/json-ld-syntax/)
- [UBL 2.3 JSON Alternative Representation v1.0](https://docs.oasis-open.org/ubl/UBL-2.3-JSON/v1.0/UBL-2.3-JSON-v1.0.html)

### Domain-specific APIs use semantic names

APIs that deal primarily with a single value-with-metadata pattern (usually money) tend to use semantic names:

| API | Property | Currency property | Notes |
|-----|----------|------------------|-------|
| **Stripe** | `amount` | `currency` | Integer minor units |
| **Square** | `amount` | `currency` | Integer minor units |
| **UK Open Banking** | `Amount` | `Currency` | String for precision |
| **Zalando** | `amount` | `currency` | |
| **Google Money** | `units` / `nanos` | `currencyCode` | Split representation |

But even among payment APIs, several use generic `value`:

| API | Property | Currency property |
|-----|----------|------------------|
| **PayPal** | `value` | `currency_code` |
| **Adyen** | `value` | `currency` |
| **Belgian Government** | `value` | `currency` |

Sources:
- [Stripe API Reference](https://docs.stripe.com/api)
- [Square Money Object](https://developer.squareup.com/reference/square/objects/Money)
- [UK Open Banking Read-Write API](https://openbankinguk.github.io/read-write-api-site3/)
- [Zalando RESTful API Guidelines](http://opensource.zalando.com/restful-api-guidelines/)
- [PayPal Payments API v2](https://developer.paypal.com/docs/api/payments/v2/)
- [Adyen Currency Codes](https://docs.adyen.com/development-resources/currency-codes)
- [Belgian Government openapi-money](https://github.com/belgif/openapi-money/blob/main/src/main/openapi/money/v1/money-v1.yaml)

### ISO 20022 uses abbreviated semantic names

ISO 20022's JSON Schema guidance uses `amt` paired with `Ccy` for amounts — an abbreviated but semantically specific name.

Source: [ISO 20022 Generation of JSON Schema (PDF)](https://www.iso20022.org/sites/default/files/media/file/ISO_20022_Generation_of_JSON_Schema_Draft_2020_12_for_ISO_20022_2013_10June2025.pdf)

## The pattern split

The split is domain-contextual:

- **Multi-type data interchange standards** (FHIR, Schema.org, GS1, UN/CEFACT, JSON-LD) → **generic names** (`value`, `content`, `@value`)
- **Single-purpose payment APIs** (Stripe, Square) → **semantic names** (`amount`)

UBL is a multi-type data interchange standard. It has 8+ typed value patterns (Amount, Quantity, Measure, Code, Identifier, Text, Name, BinaryObject), not just one. This places it firmly in the first category.

## Arguments for keeping generic `"value"`

1. **Alignment with peer standards.** FHIR, Schema.org, GS1, and UN/CEFACT all use this pattern. No major data interchange standard uses type-specific names.

2. **Consistency and predictability.** One pattern to learn. Every typed object has `value` plus metadata. No need to remember whether it's `amount`, `text`, `id`, or `code` for each type.

3. **UBL already provides semantic context at the parent level.** The parent property name is always specific: `TaxAmount`, `InvoicedQuantity`, `LineExtensionAmount`. Adding `amount` inside `TaxAmount` creates redundancy: `"TaxAmount": {"amount": 100}` says "amount" twice.

4. **Simpler tooling.** Generic accessors (`obj.value`) work regardless of type. Code generation and validation are simpler with a single property name.

5. **CCTS heritage.** UBL is built on UN/CEFACT CCTS, which defines a "content component" that has the same structural role across all core component types.

6. **Improvement over status quo.** The existing OASIS UBL JSON representation uses `"_"` — the most opaque possible name. `"value"` is already a significant improvement.

## Arguments for semantic names

1. **Self-documenting JSON.** `{"amount": 100, "currencyID": "EUR"}` is more readable in isolation than `{"value": 100, "currencyID": "EUR"}`.

2. **API design guidelines favor semantic names.** Zalando, Google, and Microsoft guidelines recommend meaningful property names.

3. **Disambiguation in debugging.** When `"value": 100` appears in logs without parent context, it's ambiguous. `"amount": 100` is immediately interpretable.

4. **The type system is closed and small.** Only 8 types need the object form. The mapping is finite and static — a small lookup table in the generator.

5. **TextType vs NameType disambiguation.** Different content names (`text` vs `name`) help distinguish types even without schema context.

Sources for API design guidelines:
- [Zalando RESTful API Guidelines](http://opensource.zalando.com/restful-api-guidelines/)
- [Google JSON Style Guide](https://google.github.io/styleguide/jsoncstyleguide.xml)

## Arguments against semantic names (specific to UBL)

1. **Redundancy with parent property names.** `"TaxAmount": {"amount": 100}` and `"Description": {"text": "..."}` repeat the type semantics at two levels.

2. **Five+ different names to learn.** Developers would need `amount`, `quantity`, `value` (for Measure), `text`, `name`, `id`, `code`, `content` — versus just `value` for everything.

3. **Mixed-type processing becomes harder.** Code that extracts the core value from any typed object must know the type-specific property name rather than always accessing `.value`.

4. **No peer precedent.** No major data interchange standard uses this pattern. UBL would be unique, which is a risk for interoperability tooling and developer expectations.

## Discussion

The research suggests that UBL's current use of `"value"` is well-aligned with industry norms for multi-type data interchange standards. The semantic names approach, while more readable in isolation, goes against the established pattern of peer standards and introduces complexity for a modest readability gain that is largely redundant with the parent property name.

The TC should consider:
- Is the readability gain of semantic names worth diverging from FHIR, Schema.org, GS1, and UN/CEFACT?
- Does the redundancy argument (`"TaxAmount": {"amount": 100}`) weaken the case for semantic names?
- Would a hybrid approach work — semantic names for some types (e.g., `code` for CodeType, following FHIR's precedent) but `value` for the rest?
- Is alignment with UN/CEFACT's `content` worth considering, given shared CCTS heritage?
