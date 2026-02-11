# Plan: JSON Schema Generator for UBL 2.5

## Goal

Build a Python script (`generate_json_schemas.py`) and a GitHub Actions workflow that reads `UBL-Entities-2.5.gc` (the Genericode file) and generates all normative JSON Schemas defined in the specification (Section 12.4).

---

## 1. Understand the inputs and outputs

### Input
- **`UBL-Entities-2.5.gc`** — Genericode XML with 5,854 rows, each describing a BIE:
  - `ModelName` — identifies which model/document the row belongs to (e.g. `UBL-Invoice-2.5`, `UBL-CommonLibrary-2.5`)
  - `ComponentName` — the JSON property name (e.g. `ID`, `BuyerCustomerParty`, `Invoice`)
  - `ComponentType` — one of `ABIE` (411), `BBIE` (3,194), `ASBIE` (2,249)
  - `Cardinality` — `1`, `0..1`, `0..n`, `1..n`
  - `RepresentationTerm` — the data type family (e.g. `Identifier`, `Code`, `Amount`, `Text`, `Date`, `Indicator`)
  - `DataType` — the CCTS data type (e.g. `Identifier. Type`, `Code. Type`, `Amount. Type`)
  - `AssociatedObjectClass` — for ASBIEs, the target ABIE name (e.g. `Customer Party`, `Monetary Total`)
  - `ObjectClass` — the owning ABIE name (e.g. `Invoice`, `Activity Data Line`)
  - `Definition` — human-readable description

### Outputs — directory `json/schemas/`

**Common schemas** (`json/schemas/common/`):
| File | Contents |
|------|----------|
| `UnqualifiedDataTypes-2.json` | Base CCTS data types (AmountType, CodeType, DateType, etc.) with scalar/object forms and supplementary components |
| `QualifiedDataTypes-2.json` | UBL-qualified data type aliases (references UnqualifiedDataTypes) |
| `CommonBasicComponents-2.json` | Every distinct BBIE name mapped to its qualified/unqualified data type |
| `CommonAggregateComponents-2.json` | Every ABIE from `UBL-CommonLibrary-2.5` with its BBIEs and ASBIEs; each ABIE also has an `$anchor` for standalone use |
| `CommonExtensionComponents-2.json` | UBLExtensions array schema with ExtensionURI, ExtensionContent, etc. |
| `SignatureAggregateComponents-2.json` | Signature-related ABIEs (Signature ABIE) |
| `SignatureBasicComponents-2.json` | Signature-related BBIEs |

**Document schemas** (`json/schemas/maindoc/`):
One schema per document type (≈100 files), e.g.:
- `Invoice-2.json`
- `Order-2.json`
- `CreditNote-2.json`
- `WorkReport-2.json`
- etc.

Each document schema has:
- `$schema: "https://json-schema.org/draft/2020-12/schema"`
- `$id: "https://docs.oasis-open.org/ubl/2/json/schemas/<DocumentName>-2"` (major-version-pinned)
- A root `type: "object"` with `properties` listing `$schema` + all BBIEs and ASBIEs for that document
- `$ref` links to CommonBasicComponents and CommonAggregateComponents for the property definitions
- `required` array for cardinality `1` and `1..n` properties
- `additionalProperties: false`

---

## 2. Data type mapping (Section 10)

The spec defines 14 unqualified data types. The script needs a mapping table:

| RepresentationTerm | JSON scalar form | Object form properties | Mandatory supplementary |
|---|---|---|---|
| Amount | `number` | `{ value: number, currencyID: string }` | `currencyID` |
| BinaryObject | _(always object)_ | `{ value: string (base64), mimeCode: string }` | `mimeCode` |
| Code | `string` | `{ value: string, listID: string }` | — |
| Date | `string` (pattern: `^[0-9]{4}-[0-9]{2}-[0-9]{2}$`) | — | — |
| Time | `string` (pattern: `^[0-9]{2}:[0-9]{2}:[0-9]{2}(Z\|[+-][0-9]{2}:[0-9]{2})?$`) | — | — |
| Identifier | `string` | `{ value: string, schemeID: string }` | — |
| Indicator | `boolean` | — | — |
| Measure | `number` | `{ value: number, unitCode: string }` | `unitCode` |
| Numeric | `number` | — | — |
| Percent | `number` | — | — |
| Rate | `number` | — | — |
| Quantity | `number` | `{ value: number, unitCode: string }` | — |
| Text | `string` | `{ value: string, languageID: string }` | — |
| Name | `string` | `{ value: string, languageID: string }` | — |

For types with mandatory supplementary components (Amount, BinaryObject, Measure), the schema must **always** use the object form. For optional supplementary types, the schema uses `oneOf` to allow either scalar or object form.

---

## 3. Script architecture — `generate_json_schemas.py`

### Step 1: Parse the GC file
- Use `xml.etree.ElementTree` (stdlib, no dependencies needed)
- Parse all `<Row>` elements into a list of dicts keyed by `ColumnRef`
- Group rows by `ModelName`

### Step 2: Build the ABIE registry
- From `UBL-CommonLibrary-2.5` rows, build a dict of ABIEs:
  - Key: the ABIE's `ObjectClass` (e.g. `"Activity Data Line"`)
  - Value: list of child BBIEs and ASBIEs (their ComponentName, ComponentType, Cardinality, RepresentationTerm, DataType, AssociatedObjectClass)
- Derive the JSON property name from `ComponentName` (already in Title Case per the GC file)

### Step 3: Generate `UnqualifiedDataTypes-2.json`
- Hard-coded definitions for the 14 base types from the mapping table
- Each type defined as a `$defs` entry with scalar and object form variants

### Step 4: Generate `QualifiedDataTypes-2.json`
- Inspect all distinct `DataType` values across the GC (e.g. `"Amount. Type"`, `"Code. Type"`)
- Map each to its corresponding unqualified base via `$ref`

### Step 5: Generate `CommonBasicComponents-2.json`
- Collect all distinct BBIE `ComponentName` values across the entire GC
- For each, determine the data type from `RepresentationTerm` / `DataType`
- Emit a `$defs` entry that `$ref`s the appropriate type in QualifiedDataTypes or UnqualifiedDataTypes

### Step 6: Generate `CommonAggregateComponents-2.json`
- For each ABIE in `UBL-CommonLibrary-2.5`:
  - Create a `$defs/<ABIEName>` definition
  - Add `$anchor: "<ABIEName>"` for standalone ABIE use (Section 12.3)
  - List `properties` from its child BBIEs (→ `$ref` to CommonBasicComponents) and ASBIEs (→ `$ref` to self `$defs`)
  - Build `required` from cardinality `1` / `1..n`
  - Handle cardinality `0..n` / `1..n` using `oneOf: [single, array]` pattern per Section 7.1
  - Set `additionalProperties: false`

### Step 7: Generate `CommonExtensionComponents-2.json`
- Define the UBLExtensions structure per Section 6.3:
  - Array of extension objects with `ExtensionURI` (string, required), `ExtensionContent` (object, required), optional metadata fields

### Step 8: Generate Signature schemas
- `SignatureAggregateComponents-2.json` — Signature ABIE definition
- `SignatureBasicComponents-2.json` — Signature-related BBIEs
- These will reference CommonBasicComponents for standard BBIEs

### Step 9: Generate document schemas
- For each `ModelName` that is NOT `UBL-CommonLibrary-2.5`:
  - Extract the document name (e.g. `UBL-Invoice-2.5` → `Invoice`)
  - Find the root ABIE row (ComponentType=ABIE) and its children
  - Generate `json/schemas/maindoc/<DocName>-2.json` with:
    - `$id`: `https://docs.oasis-open.org/ubl/2/json/schemas/<DocName>-2`
    - `properties.$schema`: const with the `$id` value
    - `properties.UBLExtensions`: `$ref` to CommonExtensionComponents
    - All BBIEs → `$ref` to CommonBasicComponents
    - All ASBIEs → `$ref` to CommonAggregateComponents
    - `required` array
    - `additionalProperties: false`

### Step 10: Validation (optional but recommended)
- After generation, validate a sample of generated schemas using `jsonschema` or `check-jsonschema`
- Optionally generate and validate a minimal sample Invoice instance

---

## 4. Cardinality handling in JSON Schema

Per Section 7.1 of the specification:

| Cardinality | Schema representation |
|---|---|
| `1` (meaning `1..1`) | Property in `required`, single value type |
| `0..1` | Not in `required`, single value type |
| `0..n` | Not in `required`, `oneOf: [single-type, array-of-type]` |
| `1..n` | In `required`, `oneOf: [single-type, array-of-type]` with `minItems: 1` on array |

The `oneOf` pattern allows both `"Description": "text"` and `"Description": ["text1", "text2"]`.

---

## 5. GitHub Actions workflow — `.github/workflows/generate-json-schemas.yml`

```yaml
name: Generate JSON Schemas

on:
  push:
    branches: [main]
    paths:
      - 'UBL-Entities-2.5.gc'
      - 'generate_json_schemas.py'
      - '.github/workflows/generate-json-schemas.yml'
  workflow_dispatch:

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Generate JSON Schemas
        run: python generate_json_schemas.py

      - name: Validate generated schemas
        run: |
          pip install check-jsonschema
          # Validate that each generated schema is valid JSON Schema
          for f in json/schemas/common/*.json json/schemas/maindoc/*.json; do
            python -c "import json; json.load(open('$f'))" || exit 1
          done

      - name: Commit generated schemas
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add json/schemas/
          git diff --cached --quiet || git commit -m "Regenerate JSON schemas from GC file"
          git push
```

---

## 6. Key design decisions to discuss

1. **JSON Schema dialect**: Use `https://json-schema.org/draft/2020-12/schema` (the latest stable draft, which supports `$anchor`, `$dynamicRef`, and prefixItems). This aligns with RFC 8927 referenced in the spec.

2. **Cardinality `oneOf` pattern**: The spec says `0..n`/`1..n` properties accept either a single value or an array. The schema will use `oneOf: [{single}, {type: "array", items: {single}}]`. This is the most accurate representation per Section 7.1.

3. **`$anchor` for standalone ABIEs**: Each ABIE in CommonAggregateComponents gets a `$anchor` so standalone payloads can reference it as `CommonAggregateComponents-2#PartyType` (Section 12.3).

4. **Extension and Signature schemas**: The GC file does not contain rows for `UBL-CommonExtensionComponents` or `UBL-SignatureComponents` models. These schemas will be generated from hard-coded definitions based on the specification text (Sections 6.3 and 11).

5. **No external dependencies**: The generator script uses only Python stdlib (`xml.etree.ElementTree`, `json`, `os`, `pathlib`, `re`, `collections`). No pip install needed for generation.

6. **Schema file naming**: Uses major-version-pinned names per spec (e.g. `Invoice-2.json`, not `Invoice-2.5.json`).

---

## 7. File tree after implementation

```
ubl-json/
├── generate_json_schemas.py          # NEW — the generator script
├── json/
│   └── schemas/
│       ├── common/
│       │   ├── UnqualifiedDataTypes-2.json
│       │   ├── QualifiedDataTypes-2.json
│       │   ├── CommonBasicComponents-2.json
│       │   ├── CommonAggregateComponents-2.json
│       │   ├── CommonExtensionComponents-2.json
│       │   ├── SignatureAggregateComponents-2.json
│       │   └── SignatureBasicComponents-2.json
│       └── maindoc/
│           ├── ApplicationResponse-2.json
│           ├── AwardedNotification-2.json
│           ├── BillOfLading-2.json
│           ├── ... (~100 document schemas)
│           └── WorkReport-2.json
├── .github/
│   └── workflows/
│       ├── generate-html.yml         # existing
│       └── generate-json-schemas.yml # NEW
├── UBL-Entities-2.5.gc              # existing input
├── UBL-2.5-JSON-Syntax-Binding.xml  # existing spec
└── ...
```

---

## 8. Implementation order

1. **`generate_json_schemas.py`** — the core script (Steps 1–9 above)
2. **Manual verification** — run locally, spot-check Invoice schema against the XSD
3. **`.github/workflows/generate-json-schemas.yml`** — CI workflow
4. **Update `.gitignore`** if needed (generated schemas should be committed)

---

## 9. Open questions for discussion

1. **Should generated schemas be committed to the repo, or only produced as CI artifacts?** The plan above commits them so they are available in the repository directly.

2. **Extension schema details**: The GC file has no rows for extension components. Should we model the full extension structure from Section 6.3, or keep it minimal (just the scaffolding)?

3. **Signature schemas**: Similarly, the GC has no dedicated Signature model. The spec mentions a `Signature` ABIE exists in `CommonAggregateComponents`. Should `SignatureAggregateComponents-2.json` and `SignatureBasicComponents-2.json` be separate files, or is it sufficient to include signature support within the main CommonAggregateComponents schema?

4. **`BusinessInformation` model**: The GC contains a `UBL-BusinessInformation-2.5` model that doesn't appear in the spec's document schema list. Should this be treated as a document schema or skipped?

5. **Validation tooling**: Should we add a validation step that creates a sample JSON instance (e.g. minimal Invoice) and validates it against the generated schema?
