# Point 7: Deprecated Documents and Elements

## The question

Should the UBL JSON schemas include deprecated elements from UBL 2.5 for backward compatibility, or exclude them for a clean start?

## WD01 position (section 5.2)

> "In this JSON syntax binding, deprecated elements defined in UBL 2.5 are not included in the normative JSON Schemas. JSON instances conformant to this specification therefore shall not contain elements that are marked as deprecated in UBL 2.5."

> "This design decision reflects the fact that this is the first release of the UBL JSON binding and does not have backward compatibility constraints across prior JSON minor versions."

> "Implementers should be aware that automated XML-to-JSON transformation of UBL instances may not be possible where deprecated elements are present in the XML source. In such cases, transformation rules or migration logic must be applied in accordance with the guidance provided for deprecated elements in the UBL 2.5 Semantic Library."

## Current state of our schemas

Our generator (`generate_json_schemas.py`) does not read the `DeprecatedDefinition` column from the GC file. All deprecated content is present in our generated schemas.

## Deprecated document types (6)

Six document types are generated as schemas but excluded from WD01's Annex C:

| Document | Description |
|----------|-------------|
| AttachedDocument | A wrapper that allows a document of any kind to be included |
| FreightInvoice | A document requesting payment for freight services |
| OrderResponseSimple | A simple accept/reject response to an Order |
| StockAvailabilityReport | A report on the quantities of each item available for sale |
| TenderStatus | Status of a tendering process |
| TenderStatusRequest | Request for status of a tendering process |

These are present in our schemas on GitHub Pages (`json/schemas/maindoc/`) but not listed in WD01 Annex C.

## Deprecated elements within non-deprecated documents (6)

The GC file (`gc/UBL-Entities-2.5.gc`) marks 6 rows with a `DeprecatedDefinition` value:

| Model | Object Class | Component | Type | Deprecated Definition |
|-------|-------------|-----------|------|----------------------|
| UBL-CommonLibrary-2.5 | Subcontract Terms | UnknownPriceIndicator | BBIE | An indicator that the subcontract price is known (true) or not (false) |
| UBL-CommonLibrary-2.5 | Tendering Process | OpenTenderEvent | ASBIE | Textual description of the legal form required for potential tenderers |
| UBL-DebitNote-2.5 | Debit Note | DebitNote | ABIE | Definition changed |
| UBL-InventoryReport-2.5 | Inventory Report | InventoryReportingParty | ASBIE | Party reference changed |
| UBL-QualificationApplicationRequest-2.5 | Qualification Application Request | QualificationApplicationRequest | ABIE | Definition changed |
| UBL-QualificationApplicationResponse-2.5 | Qualification Application Response | QualificationApplicationResponse | ABIE | Definition changed |

All 6 are present in our generated schemas:
- `SubcontractTermsType.UnknownPriceIndicator` — present in CommonAggregateComponents
- `TenderingProcessType.OpenTenderEvent` — present in CommonAggregateComponents
- `InventoryReport.InventoryReportingParty` — present in InventoryReport document schema
- DebitNote, QualificationApplicationRequest, QualificationApplicationResponse — document schemas exist with their deprecated ABIE definitions

## The backward compatibility concern

### UBL XML tradition

UBL XML has always maintained full backward compatibility. A UBL 2.1 document validates against UBL 2.5 XML schemas. This is a fundamental design principle that the UBL community relies on.

### Real-world impact of excluding deprecated elements

1. **XML-to-JSON conversion**: Organizations converting existing UBL XML documents to JSON will encounter failures if those documents contain deprecated elements. This is not a theoretical concern — many UBL documents in the wild use elements like `FreightInvoice` or `OrderResponseSimple`.

2. **Gradual migration**: Organizations typically migrate to new versions incrementally. Excluding deprecated elements forces an all-or-nothing approach for any document type or element that was deprecated.

3. **Archival and interoperability**: Existing documents in archives or in transit may contain deprecated elements. A JSON binding that cannot represent them creates a gap in the ecosystem.

### WD01's rationale

WD01 argues this is acceptable because:
- This is the first JSON binding, so there are no prior JSON versions to be compatible with
- Deprecated elements can be handled through "transformation rules or migration logic"

### Counter-argument

While there are no prior JSON versions, there are prior UBL XML versions. The JSON binding is not being created in a vacuum — it exists to serve the UBL ecosystem, which includes XML documents containing deprecated elements. The question is not whether the JSON binding has backward compatibility obligations to previous JSON bindings, but whether it should be able to represent the full range of UBL documents that exist in practice.

## Options

1. **Exclude deprecated elements** (WD01 position): Cleaner schemas, forces migration, breaks XML-to-JSON for documents with deprecated content.

2. **Include deprecated elements**: Full interoperability with existing UBL XML documents, larger schemas, preserves UBL's backward compatibility tradition.

3. **Include but mark as deprecated**: Include deprecated elements in schemas with the JSON Schema `deprecated` annotation keyword (`"deprecated": true`). This is a standard JSON Schema keyword (see [Point 8: Schema Annotations](wd01-point-08-semantic-library-annotations.md)) that does not affect validation but signals to tooling and developers that the element should not be used in new documents. Schema validators would accept deprecated elements, but IDEs, linters, and code generators could warn. Example:

```json
"UnknownPriceIndicator": {
  "$ref": "...",
  "description": "An indicator that the subcontract price is known.",
  "deprecated": true
}
```

## Discussion

The TC should consider:
- How many UBL documents in the wild contain deprecated elements?
- What is the practical burden of "transformation rules or migration logic" for implementers?
- Is option 3 (include but mark) a viable compromise?
- Should the 6 deprecated document types and the 6 deprecated elements within documents be treated differently?
