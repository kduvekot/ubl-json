# Towards a Modular NDR Architecture for CCTS-Based Vocabularies

**Working Paper — April 2026**

---

## Abstract

The Business Document Naming and Design Rules (BDNDR) v1.1 added JSON
serialization rules in Section 6, but these rules conflict with the UBL 2.5
JSON Syntax Binding on fundamental design points: value-property naming,
array representation, namespace handling, and JSON Schema version. This
analysis traces the concepts of "Naming and Design Rules" and "Syntax
Binding" back to their origins in CCTS and the UBL TC, surveys how peer
standards handle multi-syntax serialization, and proposes a modular
architecture that separates syntax-neutral core rules from syntax-specific
binding documents. The goal is to enable CCTS-based vocabularies — UBL,
UN/CEFACT, and others — to share a common semantic foundation while
independently evolving their serialization rules for XML, JSON, and future
syntaxes.

---

## 1. CCTS: The Syntax-Neutral Foundation

The UN/CEFACT Core Components Technical Specification (CCTS) 2.01
(ISO 15000-5:2014) provides the meta-model for business information
entities — Core Component Types, Business Information Entities, and their
relationships. Two provisions are central to this analysis:

**Naming Convention** (Section 6.1.4): CCTS defines a naming convention for
core components using "Dictionary Entry Names" composed of Object Class
Term, Property Term, and Representation Term, separated by periods. These
names are syntax-neutral — they describe *what* a component means, not how
it is serialized.

**Syntax Binding** (Section 6.2.1.3, Rule B31): CCTS explicitly defines
the concept of a "Syntax Binding" as the mapping from the abstract CCTS
model to a concrete syntax. Rule B31 states that a syntax binding shall
define the mapping rules from BIE structures to syntax-specific constructs.
This is deliberately separate from the naming convention itself.

Crucially, **CCTS does not use the term "Naming and Design Rules" (NDR)**.
The specification describes:

- A *naming convention* — how to construct dictionary entry names
- A *syntax binding* — how to map those names and structures to a concrete
  syntax

The term "NDR" was coined later, by the UBL Technical Committee.

## 2. Origin of the Term "Naming and Design Rules"

The UBL Technical Committee established a Naming and Design Rules
Subcommittee (NDR SC) in its earliest days (2001–2004). The UBL NDR SC,
chaired by Mark Crawford, developed the first formal document explicitly
titled "Naming and Design Rules." The UBL NDR defined how CCTS constructs
should be realized as XML Schema artifacts — element naming patterns,
type naming conventions, namespace structure, and schema design patterns.

The key insight is that "Naming and Design Rules" was a **UBL invention**
that bundled three concerns into one document:

1. **Syntax-neutral naming** — derived from CCTS Dictionary Entry Names
2. **Syntax-specific naming** — how dictionary entry names become XML
   element/type names (e.g., UpperCamelCase, removing spaces and periods)
3. **Syntax-specific design** — XML Schema patterns (type derivation,
   extension points, namespace partitioning)

When UN/CEFACT published its own XML Naming and Design Rules in 2004, the
document explicitly credited UBL's NDR work as "instrumental in the
development" of the UN/CEFACT rules. Mark Crawford served in leadership
roles on both efforts, and the terminology crossed over directly.

## 3. The NDR Landscape Today

Multiple overlapping NDR documents now govern CCTS-based vocabularies:

| Document | Org | Scope | Current Version | Syntax |
|---|---|---|---|---|
| UN/CEFACT XML NDR | UN/CEFACT | XML schema design for CCL | v3.1 (2017) | XML only |
| BDNDR | OASIS | Business Document NDR | v1.1 (2024) | XML + JSON (Sec 6) |
| UBLNDR | OASIS UBL TC | UBL-specific schema design | v3.0 (2013), v3.1 (draft) | XML only |
| UBL JSON Syntax Binding | OASIS UBL TC | JSON schemas for UBL | v1.0 (CSD01, 2026) | JSON only |
| UBL JSON Alternative Representations | OASIS UBL TC | JSON alternatives study | v1.0 (2018) | JSON (analysis) |
| UN/CEFACT JSON NDR | UN/CEFACT | JSON rules for CCL | In development | JSON only |

The addition of JSON rules to BDNDR v1.1 Section 6 created an overlap —
and a conflict — with the UBL JSON Syntax Binding specification.

## 4. BDNDR v1.1 JSON Rules vs. UBL JSON Syntax Binding

The two specifications take fundamentally different approaches to JSON
serialization of CCTS-based documents. The conflicts are not minor
style differences; they produce **incompatible JSON documents**.

### 4.1 Value Property Naming

| Aspect | BDNDR v1.1 (Section 6) | UBL JSON Syntax Binding |
|---|---|---|
| Property name for text content | `_` (underscore) | `value` |
| Rationale | Follows JSON-LD `@value` convention (shortened) | Explicit, self-documenting name |
| Example | `{"_": "USD", "currencyID": "USD"}` | `{"value": "USD", "currencyID": "USD"}` |

This is the most visible incompatibility. A JSON document valid under one
specification is semantically ambiguous under the other.

### 4.2 Array Representation

| Aspect | BDNDR v1.1 | UBL JSON Syntax Binding |
|---|---|---|
| Repeating elements | Always wrapped in array | Singleton or array depending on occurrence |
| Single-item case | `"Note": [{"_": "one note"}]` | `"Note": "one note"` or `"Note": ["one", "two"]` |
| Design principle | Predictable structure | Compact representation |

The BDNDR requires all potentially-repeating elements to always be
serialized as JSON arrays, even when only one item is present. The UBL
JSON Syntax Binding allows a single value to appear without array wrapping,
with arrays used only when multiple values are present.

### 4.3 Namespace Handling

| Aspect | BDNDR v1.1 | UBL JSON Syntax Binding |
|---|---|---|
| XML namespace preservation | Explicit namespace prefixes or mapping | Namespaces expressed through schema `$id` and `$ref` URIs |
| Namespace in property names | May include namespace indicators | No namespace prefixes in property names |

### 4.4 JSON Schema Version

| Aspect | BDNDR v1.1 | UBL JSON Syntax Binding |
|---|---|---|
| JSON Schema dialect | Draft 2020-12 (referenced) | Draft 2020-12 |
| Schema identification | Not fully specified | `$id` with URN-based identification |
| Schema composition | Not fully specified | `$ref` with modular schema architecture |

While both reference JSON Schema Draft 2020-12, the UBL JSON Syntax
Binding provides a complete, tested schema architecture with URN-based
`$id` values, a modular `$ref` structure, and validated examples.

### 4.5 Design Philosophy

The underlying design philosophies diverge:

- **BDNDR v1.1**: Attempts to define JSON rules as an extension of
  existing XML NDR patterns. JSON is treated as "another serialization"
  within the same document that governs XML. The JSON rules inherit
  assumptions from XML (e.g., namespace-awareness, strict structure).

- **UBL JSON Syntax Binding**: Designed JSON-first, as a standalone
  syntax binding. Leverages JSON idioms (compact representation,
  schema-driven validation) rather than transposing XML patterns.

## 5. How Peer Standards Handle Multiple Syntax Bindings

The tension between XML-centric NDRs and JSON serialization is not unique
to UBL/UN/CEFACT. Other major standards have addressed this by maintaining
**separate documents** for each syntax binding.

### 5.1 HL7 FHIR

FHIR defines a single logical model for healthcare resources, with
separate serialization specifications:

- **FHIR XML Representation** — dedicated chapter with XML-specific rules
- **FHIR JSON Representation** — dedicated chapter with JSON-specific rules
- **FHIR RDF (Turtle) Representation** — dedicated chapter
- **FHIR NDJSON** — separate specification for bulk data

Each syntax representation is a self-contained specification that maps
the same logical model to different concrete syntaxes. They share the
logical model but make no attempt to share serialization rules.

### 5.2 W3C RDF

The W3C maintains the RDF abstract data model separately from its
serializations:

- **RDF 1.1 Concepts and Abstract Syntax** — the model
- **RDF 1.1 XML Syntax** — separate W3C Recommendation
- **RDF 1.1 JSON-LD** — separate W3C Recommendation
- **RDF 1.1 Turtle** — separate W3C Recommendation
- **RDF 1.1 N-Triples** — separate W3C Recommendation

Each serialization is a full W3C Recommendation with its own editors,
its own conformance criteria, and its own versioning lifecycle.

### 5.3 ISO 20022

The ISO 20022 financial messaging standard separates:

- **ISO 20022 Metamodel** — the abstract business model
- **ISO 20022 XML Design Rules** — XML-specific serialization
- **ISO 20022 ASN.1 Design Rules** — ASN.1-specific serialization
- **ISO 20022 JSON Design Rules** — JSON-specific (in development)

The metamodel is versioned independently of the syntax-specific rules.

### 5.4 GS1 EPCIS

The GS1 EPCIS standard for supply chain event data:

- **EPCIS 2.0 Core** — abstract event model
- **EPCIS 2.0 XML Binding** — XML-specific rules and schemas
- **EPCIS 2.0 JSON/JSON-LD Binding** — JSON-specific rules and schemas

The JSON/JSON-LD binding was developed as a separate document when JSON
support was added in EPCIS 2.0, rather than appending JSON rules to the
existing XML specification.

### 5.5 The Pattern

The pattern is consistent across domains:

1. **Separate the abstract model from syntax-specific rules**
2. **Give each syntax binding its own document** with its own lifecycle
3. **Allow each syntax to use its own idioms** rather than forcing one
   syntax's patterns onto another
4. **Version syntax bindings independently** from the core model

## 6. The Semantic Chain: From CCTS to JSON Schema

A key architectural question is how semantic meaning flows from the
abstract CCTS model through to a concrete JSON document. The UBL JSON
Syntax Binding establishes this chain:

```
CCTS Meta-Model
    ↓ defines
UBL Semantic Library (BIEs, ABIEs, BBIEs)
    ↓ mapped by
UBL JSON Syntax Binding (rules)
    ↓ produces
JSON Schemas ($id, $ref, descriptions, constraints)
    ↓ validates
JSON Instance Documents
```

The JSON Schema `$id` (a URN like
`urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2`)
serves as the **semantic anchor** — it uniquely identifies which vocabulary
component defines the structure. The `description` annotations in the
schema carry the CCTS definition text. The `$ref` linkages preserve the
composition relationships from the UBL model.

This means a JSON Schema *already carries the semantic chain* from CCTS
through to validation. A conformant JSON document validated against these
schemas has unambiguous meaning — the schema tells you exactly which UBL
BIE each JSON property corresponds to.

**JSON-LD** is complementary but not required for semantic interoperability
within the UBL ecosystem. JSON-LD adds value when:

- Linking UBL data to external ontologies (schema.org, Dublin Core)
- Publishing UBL data as Linked Data
- Merging UBL data with data from other vocabularies

But for the core use case — exchanging UBL business documents between
trading partners — the JSON Schema itself provides sufficient semantic
grounding.

## 7. Proposed Modular Architecture

Based on the analysis above, we propose restructuring the NDR landscape
into modular, syntax-specific documents:

### 7.1 Document Structure

```
┌───────────────────────────────────────────────────────────┐
│                  CCTS 2.01 (ISO 15000-5)                  │
│              Naming Convention + Meta-Model                │
└─────────────────────────┬─────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────────┐ ┌──────────┐ ┌────────────────────┐
│   BDNDR-Core    │ │ UBLNDR   │ │  UN/CEFACT NDR     │
│ Syntax-neutral  │ │ -Core    │ │  (Core)            │
│ naming rules    │ │          │ │                    │
└────────┬────────┘ └────┬─────┘ └─────────┬──────────┘
         │               │                 │
    ┌────┴────┐     ┌────┴────┐      ┌─────┴─────┐
    ▼         ▼     ▼         ▼      ▼           ▼
┌───────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌───────┐ ┌──────┐
│BDNDR  │ │BDNDR │ │UBLNDR│ │UBLNDR│ │UNCEF. │ │UNCEF.│
│-XML   │ │-JSON │ │-XML  │ │-JSON │ │XML NDR│ │JSON  │
│       │ │      │ │      │ │      │ │       │ │NDR   │
└───────┘ └──────┘ └──────┘ └──────┘ └───────┘ └──────┘
```

### 7.2 Document Responsibilities

| Document | Scope | Content |
|---|---|---|
| **BDNDR-Core** | Syntax-neutral | CCTS-derived naming conventions, dictionary entry name rules, component identification |
| **BDNDR-XML** | XML binding | XML element/type naming, XML Schema design patterns, namespace rules |
| **BDNDR-JSON** | JSON binding | JSON property naming, JSON Schema design patterns, value representation |
| **UBLNDR-XML** | UBL XML specifics | UBL-specific XML Schema extensions, customization rules |
| **UBLNDR-JSON** | UBL JSON specifics | UBL-specific JSON Schema patterns, the current UBL JSON Syntax Binding |
| **UBL Semantic Model** | Vocabulary | The UBL component library, independent of any syntax |

### 7.3 Benefits

**For specification editors:**
- Each document has a focused scope and a clear owner
- JSON rules can evolve without re-balloting XML rules (and vice versa)
- New syntaxes (YAML, Protocol Buffers, etc.) can be added as new
  documents without modifying existing ones

**For implementers:**
- Clear normative reference: "My JSON implementation conforms to
  UBLNDR-JSON v1.0" (not "BDNDR v1.1 Section 6, except where UBL
  JSON Syntax Binding overrides it")
- No ambiguity about which rules apply to which syntax
- Each syntax binding can provide complete, tested examples

**For the standards ecosystem:**
- UN/CEFACT's separate JSON NDR effort validates this direction
- Aligns with how every major peer standard handles the problem
- Reduces cross-TC coordination friction (JSON changes don't block
  XML maintenance releases)

## 8. Implications and Next Steps

### 8.1 For the UBL TC

The UBL 2.5 JSON Syntax Binding specification (currently at CSD01) should
proceed as the authoritative JSON binding for UBL. Its design decisions —
`value` property naming, schema-driven validation, compact representation
— are well-founded and aligned with JSON ecosystem conventions.

The TC should consider:

- Positioning the JSON Syntax Binding as the first "UBLNDR-JSON" —
  the UBL-specific JSON binding document
- Keeping it independent of BDNDR Section 6 until/unless BDNDR is
  modularized
- Continuing to develop the JSON Schema suite as the primary validation
  and semantic tool

### 8.2 For BDNDR

The BDNDR editors should consider:

- **Extracting** Section 6 (JSON rules) into a separate BDNDR-JSON
  document
- **Revising** the JSON rules to be vocabulary-neutral — they should
  provide framework-level guidance that any CCTS-based vocabulary can
  adopt or profile, rather than prescribing a single serialization
  pattern
- **Aligning** with UN/CEFACT's emerging JSON NDR work to avoid yet
  another incompatible set of rules

### 8.3 For UN/CEFACT Coordination

The development of a separate UN/CEFACT JSON NDR confirms that the
community recognizes JSON requires its own treatment. Coordination
between the UBL TC and UN/CEFACT on JSON serialization patterns would
benefit both communities, particularly on:

- Value property naming convention
- Array representation strategy
- JSON Schema identification patterns
- Relationship between JSON Schema and JSON-LD

### 8.4 For Implementers

Until the modular architecture is adopted, implementers should:

- Follow the UBL JSON Syntax Binding for UBL JSON documents
- Use the provided JSON Schemas as the normative validation tool
- Not assume compatibility between BDNDR v1.1 Section 6 JSON and
  UBL JSON Syntax Binding JSON

## 9. References

1. **CCTS 2.01** — UN/CEFACT Core Components Technical Specification,
   Version 2.01 (ISO 15000-5:2014).

2. **BDNDR v1.1** — OASIS Business Document Naming and Design Rules,
   Version 1.1. OASIS Standard, 2024.
   https://docs.oasis-open.org/bdndr/BDNDR/v1.1/os/BDNDR-v1.1-os.html

3. **UBLNDR v3.0** — UBL Naming and Design Rules, Version 3.0. OASIS
   Standard, 2013.

4. **UBL 2.5 JSON Syntax Binding** — UBL 2.5 JSON Syntax Binding,
   Version 1.0, CSD01. OASIS Committee Specification Draft, 2026.

5. **UBL JSON Alternative Representations** — UBL 2.1/2.2 JSON
   Alternative Representations, Version 1.0. OASIS Committee Note, 2018.
   https://docs.oasis-open.org/ubl/UBL-2.1-JSON/v2.0/UBL-2.1-JSON-v2.0.html

6. **UN/CEFACT XML NDR** — UN/CEFACT XML Naming and Design Rules,
   Technical Specification, Version 3.1, 2017.

7. **HL7 FHIR R5** — HL7 FHIR Release 5, Serialization Formats.
   https://hl7.org/fhir/R5/

8. **W3C RDF 1.1** — RDF 1.1 Concepts and Abstract Syntax. W3C
   Recommendation, 2014.
   https://www.w3.org/TR/rdf11-concepts/

9. **ISO 20022** — ISO 20022 Financial Services — Universal financial
   industry message scheme.
   https://www.iso20022.org/

10. **GS1 EPCIS 2.0** — GS1 EPCIS Standard, Version 2.0, 2022.
    https://ref.gs1.org/standards/epcis/

---

*This document was produced as part of the UBL 2.5 JSON Syntax Binding
development effort. It represents analysis and proposals for discussion
within the OASIS UBL Technical Committee and is not itself a normative
specification.*
