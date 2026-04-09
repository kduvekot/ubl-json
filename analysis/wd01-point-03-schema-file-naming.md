# Point 3: Schema File Naming Convention

## The question

Two sub-questions:

1. Should document schema files be prefixed with `UBL-` (e.g., `UBL-Invoice-2.5.json`) or not (e.g., `Invoice-2.5.json`)?
2. Should the schema identifier (`$id`) include the minor version or remain major-version-stable?

| Aspect | Our generated schemas | WD01 | UBL XSD |
|--------|----------------------|------|---------|
| File name | `Invoice-2.5.json` | `UBL-Invoice-2.5.json` | `UBL-Invoice-2.5.xsd` |
| Identifier | `urn:...:Invoice-2` (major only) | `https://...UBL-Invoice-2` (major only) | `urn:...:Invoice-2` (major only) |
| UBL- prefix | No | Yes | Yes |
| Version in filename | Yes (`-2.5`) | Yes (`-2.5`) | Yes (`-2.5`) |
| Version in identifier | No (major only) | No (major only) | No (major only) |

Our generator is the only one that drops the `UBL-` prefix. WD01 follows the XSD convention exactly.

## UBL XSD precedent

The UBL XML schemas have used this pattern since UBL 2.0:

- **File:** `xsdrt/maindoc/UBL-Invoice-2.5.xsd`
- **Namespace:** `urn:oasis:names:specification:ubl:schema:xsd:Invoice-2`

The namespace has been stable across all UBL 2.x releases (2.0, 2.1, 2.2, 2.3, 2.4, 2.5). Only the filename changes with each minor version. The `UBL-` prefix is mandated by the UBL Naming and Design Rules (NDR).

Common schemas follow the same pattern:
- **File:** `UBL-CommonAggregateComponents-2.5.xsd`
- **Namespace:** `urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2`

## How other standards name their schema files

### Standards that use a prefix

| Standard | File name pattern | Prefix |
|----------|------------------|--------|
| UBL XML | `UBL-Invoice-2.5.xsd` | `UBL-` |
| UBL JSON (2.1–2.3 published) | `UBL-Invoice-2.1.json` | `UBL-` |
| GS1 EPCIS | `EPCIS-JSON-Schema.json` | `EPCIS-` |

### Standards that do NOT use a prefix

| Standard | File name pattern | Namespacing strategy |
|----------|------------------|---------------------|
| FHIR/HL7 | `Patient.schema.json` | Directory structure (`/fhir/R4/`, `/fhir/R5/`) |
| AsyncAPI | `2.6.0.json`, `3.0.0.json` | Version as filename |
| CloudEvents | `cloudevents.json` | Directory path |
| OpenAPI | Date-based `$id`, no standard filename | URL path (`/oas/3.1/schema/...`) |
| JSON Schema meta-schemas | `schema` (no extension) | URL path (`/draft/2020-12/schema`) |
| W3C Verifiable Credentials | `verifiable-credential-schema.json` | Directory |
| Snowplow/Iglu | `1-0-0` (version as filename) | Deep directory: `vendor/name/format/version` |
| NIEM | `ns.schema.json` | Namespace URIs in `$id` |

**Observation:** The majority of modern JSON-native standards do not prefix filenames with the standard name. They rely on directory structure or URL paths for disambiguation. The prefix approach is a legacy of flat filesystem distribution (ZIP files with schemas in a folder). However, UBL schemas are distributed alongside XML schemas in ZIP packages, making the prefix practical for consistency.

## How standards handle versioning in `$id`

### Does `$id` change between minor versions?

| Standard | Version in `$id`? | Changes on minor version? |
|----------|------------------|--------------------------|
| UBL XML namespace | Major only (`Invoice-2`) | No |
| FHIR (per-resource) | No version | No |
| FHIR (monolithic bundle) | Major only (`4.0`) | No (only on major) |
| GS1 EPCIS | No version | No |
| CloudEvents | No `$id` at all | N/A |
| AsyncAPI | Full semver | Yes |
| OpenAPI | Major + date | Yes (date changes) |
| JSON Schema drafts | Draft identifier | Yes |

**No single consensus**, but standards that promise backward compatibility across minor versions tend to use major-version-stable or unversioned identifiers.

### The XML namespace precedent

The W3C/XML community guidance is clear:

- Minor version changes should be backward-compatible and should NOT change the namespace URI
- Namespace URI changes should be reserved for major (breaking) versions
- Use a `version` attribute on documents to indicate the specific minor version

This is exactly what UBL has done with XML namespaces since 2.0.

Source: [IVOA XML Schema Versioning Policies](http://www.ivoa.net/documents/Notes/XMLVers/20180529/EN-schemaVersioning-1.0-20180529.html)

### FHIR as precedent

FHIR's per-resource JSON Schema identifiers have no version at all:

```json
"id": "http://hl7.org/fhir/json-schema/Patient"
```

This is stable across R4 and R5. Versioning is handled through the hosting URL path (`/fhir/R4/` vs `/fhir/R5/`), not through the identifier.

Source: [FHIR JSON Schema documentation](https://fhir.hl7.org/fhir/json.html)

## Major-version-stable identifiers: trade-offs

### Pros (the `Invoice-2` pattern)

- Existing tooling and references don't break on minor updates
- Aligns with UBL's own XML namespace convention (proven over 20+ years)
- Follows W3C/XML best practice for namespace stability
- Simpler for consumers who just need "an Invoice schema"
- Consistent with FHIR's approach
- Reflects UBL's backward compatibility promise: a 2.5 document should validate against 2.6 schemas

### Cons

- A consumer cannot tell from the identifier alone which exact schema version is in use
- Caching may serve stale schemas if the URL doesn't change
- Tooling that relies on `$id` for schema resolution may get the wrong version

### The minor-version-in-filename, major-version-in-identifier pattern

Both UBL XSD and WD01 use a split approach:
- **Filename:** includes minor version (`UBL-Invoice-2.5.json`) — for distribution and file management
- **Identifier:** major version only (`Invoice-2`) — for referencing and validation

This is a pragmatic compromise: you know which version of the file you have on disk, but schema references in documents and cross-references between schemas remain stable across minor versions.

## The prefix question

### Arguments for keeping `UBL-` prefix

1. **Consistency with XSD:** UBL XML has used `UBL-` since 2.0. The NDR mandates it.
2. **Distribution packaging:** UBL artifacts are distributed in ZIP files. Prefixed filenames are self-identifying even outside their directory structure.
3. **Coexistence:** When XML and JSON schemas are in the same distribution, `UBL-Invoice-2.5.xsd` and `UBL-Invoice-2.5.json` clearly pair up.
4. **Prior UBL JSON work:** The published UBL 2.1–2.3 JSON alternative representations used the `UBL-` prefix.

### Arguments for dropping the prefix

1. **Modern convention:** Most JSON-native standards don't prefix. Directory structure handles namespacing.
2. **Redundancy:** The files are already in a `json/schemas/maindoc/` directory — the `UBL-` prefix is redundant with the directory context.
3. **Cleaner `$ref` paths:** `../common/CommonAggregateComponents-2.5.json` is cleaner than `../common/UBL-CommonAggregateComponents-2.5.json`.
4. **Common schemas don't have it in our generator:** Our generated common schemas already omit `UBL-` (e.g., `CommonAggregateComponents-2.5.json`), matching WD01. Only document schemas differ.

### What WD01 does

WD01 adds `UBL-` to document schemas only:
- Document: `UBL-Invoice-2.5.json`
- Common: `CommonAggregateComponents-2.5.json`

This is consistent with the XSD convention where common schemas also have the `UBL-` prefix (`UBL-CommonAggregateComponents-2.5.xsd`), though WD01 only applies it to document schemas.

## Discussion

The TC should consider:

1. **Should JSON schema naming follow the XSD convention?** The strongest argument for the `UBL-` prefix is consistency with 20+ years of XSD naming. The strongest argument against is that modern JSON ecosystems don't use this pattern.

2. **Is the split versioning approach correct?** Minor version in filenames, major version in identifiers. This is well-precedented in both UBL XML and FHIR.

3. **If the prefix is adopted, should it apply to common schemas too?** WD01 only prefixes document schemas, while XSD prefixes everything. This inconsistency should be resolved.

Sources:
- [UBL Naming and Design Rules v3.0](https://docs.oasis-open.org/ubl/UBL-NDR/v3.0/UBL-NDR-v3.0.html)
- [Business Document NDR v1.1](https://docs.oasis-open.org/ubl/Business-Document-NDR/v1.1/Business-Document-NDR-v1.1.html)
- [FHIR JSON Schema documentation](https://fhir.hl7.org/fhir/json.html)
- [AsyncAPI spec-json-schemas repository](https://github.com/asyncapi/spec-json-schemas)
- [OpenAPI 3.1 Specification](https://spec.openapis.org/oas/v3.1.0.html)
- [JSON Schema specification links](https://json-schema.org/specification-links)
- [GS1 EPCIS JSON Schema](https://github.com/gs1/EPCIS/blob/master/EPCIS-JSON-Schema.json)
- [W3C Verifiable Credentials JSON Schema](https://www.w3.org/TR/vc-json-schema/)
- [Snowplow SchemaVer documentation](https://docs.snowplow.io/docs/api-reference/iglu/common-architecture/schemaver/)
- [IVOA XML Schema Versioning Policies](http://www.ivoa.net/documents/Notes/XMLVers/20180529/EN-schemaVersioning-1.0-20180529.html)
- [UBL 2.3 JSON Alternative Representation](https://docs.oasis-open.org/ubl/UBL-2.3-JSON/v1.0/UBL-2.3-JSON-v1.0.html)
