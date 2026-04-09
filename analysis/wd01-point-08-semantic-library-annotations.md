# Point 8: UBL Semantic Library and Schema Annotations

## The question

WD01 adds a new section 5 ("UBL Semantic Library") that establishes the UBL Semantic Library as the authoritative source of business semantics and states that the JSON schemas reproduce these definitions as "schema annotations." What does this mean in practice, and what is the current state of our generated schemas?

## What WD01 says (section 5.1)

> "The authoritative semantic definitions are those defined in UBL 2.5 [UBL], specifically as described in Section 4.7 ('Semantic definitions') of that specification."
>
> "This JSON syntax binding adopts the UBL Semantic Library as its authoritative source of business semantics. The normative JSON Schemas distributed with this specification **reproduce these definitions as schema annotations for convenience**, and the semantic definitions are also provided in the accompanying ODS spreadsheet, XLS spreadsheet, and HTML documentation included with this specification."

## What are JSON Schema annotations?

In JSON Schema, **annotations** are keywords that attach metadata to a schema but do not affect validation. They pass through the validation process and are collected as output for use by applications. The JSON Schema specification defines these annotation keywords:

| Keyword | Purpose |
|---------|---------|
| `title` | Short human-readable label |
| `description` | Longer explanation of the schema |
| `default` | A default value hint |
| `examples` | Array of example values |
| `readOnly` / `writeOnly` | Usage hints for forms/APIs |
| `deprecated` | Marks a schema as deprecated |
| `$comment` | Notes for schema maintainers (not end users) |

A validator **ignores** these when determining whether an instance is valid, but **collects** them and makes them available to the consuming application. This is the key distinction: annotations are metadata carried through validation as output, not used as input to validation logic.

Source: [JSON Schema 2020-12: Annotations](https://json-schema.org/draft/2020-12/json-schema-validation#section-9)

## Practical impact

Schema annotations — particularly `description` — are used by developer tooling:

- **IDE support:** VS Code, JetBrains IDEs, and other editors show `description` values as tooltips when editing JSON files validated against a schema
- **Documentation generation:** Tools can generate human-readable documentation from schema annotations
- **Code generation:** Tools like `quicktype`, `json-schema-to-typescript`, etc. can include descriptions as code comments
- **API documentation:** OpenAPI tooling renders `description` values in interactive API documentation (Swagger UI, Redoc, etc.)

For a standard like UBL, rich annotations mean developers working with an Invoice schema would see inline documentation like:

```
InvoicedQuantity: "The quantity (of items) on this invoice line."
LineExtensionAmount: "The total amount for this invoice line, including 
                      allowance charges but net of taxes."
TaxPointDate: "The date of the invoice, used to determine the applicable 
               tax rate."
```

This significantly improves developer experience without adding any validation overhead.

## Current state of our generated schemas

### What we have

Our generator puts `description` annotations on:

- **ABIE type definitions** — e.g., `InvoiceLineType: "A class to define a line in an Invoice."`
- **Unqualified data types** — e.g., `AmountType: "A number of monetary units specified using a given unit of currency."`
- **Document schemas** — top-level `description` on each document schema

### What we don't have

Individual **BBIEs and ASBIEs** within type definitions carry no descriptions. Properties like `ID`, `Note`, `TaxAmount`, `InvoicedQuantity` are bare `$ref` entries with no `description`:

```json
"InvoicedQuantity": {
  "$ref": "urn:oasis:names:specification:ubl:schema:json:CommonBasicComponents-2#/$defs/InvoicedQuantity"
}
```

### What the GC source data provides

The GC file (`gc/UBL-Entities-2.5.gc`) has a `Definition` column for every row, including BBIEs and ASBIEs. Examples from Invoice Line:

| Component | Definition |
|-----------|-----------|
| ID | An identifier for this invoice line |
| UUID | A universally unique identifier for this invoice line |
| Note | Free-form text conveying information that is not contained explicitly in other structures |
| InvoicedQuantity | The quantity (of items) on this invoice line |
| LineExtensionAmount | The total amount for this invoice line, including allowance charges but net of taxes |

This data is available but our generator does not propagate it to the schema properties.

## The `deprecated` annotation

JSON Schema's `deprecated` annotation keyword is directly relevant to the deprecation discussion (see Point 7). If deprecated elements are included in the schemas for backward compatibility, they could be marked with `"deprecated": true`, which:

- Does not affect validation (deprecated elements would still validate)
- Signals to tooling and developers that the element should not be used in new documents
- Is a standard JSON Schema keyword understood by all compliant tooling

Example:

```json
"UnknownPriceIndicator": {
  "$ref": "...",
  "description": "An indicator that the subcontract price is known.",
  "deprecated": true
}
```

This could serve as a compromise for Point 7: include deprecated elements for backward compatibility but mark them with the `deprecated` annotation.

## Discussion

1. **Schema annotations are a significant developer experience feature.** WD01 states the schemas should contain them. Our generator should be updated to propagate definitions from the GC data to schema properties.

2. **The `deprecated` annotation provides a potential solution for Point 7** — include deprecated elements but mark them, letting tooling warn developers while maintaining backward compatibility.

3. **Additional annotations to consider:**
   - `title` — could carry the UBL Dictionary Entry Name
   - `examples` — could include example values from the GC `Examples` column
   - `$comment` — could reference the CCTS component type (BBIE, ASBIE, etc.)
