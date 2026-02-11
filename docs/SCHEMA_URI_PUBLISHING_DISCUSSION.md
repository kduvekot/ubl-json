# Schema URI Publishing Strategy - Discussion Document

## Overview

This document captures the architectural requirements around JSON Schema URIs in UBL as specified in the UBL 2.5 JSON Syntax Binding specification, and identifies key decisions that may require discussion with OASIS regarding publishing and distribution strategy.

## Specification Requirements

### Schema Identification (Section 9.1)

The UBL 2.5 JSON Syntax Binding specification mandates the following:

**Section 9.1.3 - Document Instances:**
> "All normative schemas are published in the json/schemas/ directory of the release package. Each schema is identified by a **stable HTTPS URL that is fixed at the major version level** (e.g., https://docs.oasis-open.org/ubl/json/schemas/Invoice-2). **Minor revisions do not change these identifiers.**"

**Forward/Backward Compatibility Guarantee:**
> "Because the identifiers are stable across all minor revisions of the UBL 2.x line, a document referencing, for example, a UBL Invoice-2 remains valid regardless of whether the schema implementation in use is UBL 2.5, 2.6, or 2.x. This guarantees forward compatibility, thereby protecting investments in existing implementations and reducing the operational risk of upgrading to newer releases."

## Key Architectural Decisions

### 1. **Major Version Pinning in URIs**
- Schema URIs should be pinned at the major version level (e.g., `Invoice-2`, `Order-2`)
- The URI should **not** include minor or patch versions
- This allows the same URI to resolve across all compatible minor releases

### 2. **Backwards Compatibility Across Minor Versions**
- A document that specifies `$schema: https://docs.oasis-open.org/ubl/json/schemas/Invoice-2`
- Must remain valid when validated against:
  - UBL 2.5 release
  - UBL 2.6 release
  - UBL 2.x future releases
- Schema changes in minor versions must be backwards compatible

### 3. **URI Resolution and Publishing**
- The stable HTTPS URL must resolve to the authoritative schema
- The schema should be published in the `json/schemas/` directory of each UBL release package
- The URI must consistently resolve to the appropriate version's schema

## Discussion Points for OASIS

### 1. **URI Resolution Strategy**
**Question:** How should the stable major-version URI resolve across multiple released versions?

**Options:**
- **Option A:** The URI always resolves to the latest compatible schema in the 2.x line
  - Benefit: Automatic access to bug fixes and improvements
  - Risk: Subtle behavioral changes in schema validation

- **Option B:** The URI resolves to a specific pinned version (e.g., 2.5) and doesn't change
  - Benefit: Deterministic, reproducible validation across time
  - Risk: Misses important bug fixes in later versions

- **Option C:** Content negotiation - URI resolves based on client request headers or query parameters
  - Benefit: Flexibility for different use cases
  - Risk: Complexity in implementation and documentation

### 2. **Backwards Compatibility Rules**
**Question:** What constitutes a backwards-compatible change in a minor version release?

**Considerations:**
- Can properties be added without breaking existing documents?
- Can property types be extended (e.g., string → string or number)?
- Can constraints be relaxed (e.g., minLength removed)?
- Can required properties become optional?
- What about deprecations of existing properties?

### 3. **Version Lifecycle**
**Question:** How long must a major version URI remain in service and what is the upgrade path?

**Considerations:**
- When UBL 3.0 is released, will Invoice-2 URIs continue to be supported?
- Is there a deprecation period?
- Should there be a mapping or migration path?

### 4. **Schema Registry and Discovery**
**Question:** How will clients discover the stable URI for a given document type and version?

**Options:**
- Static documentation (HTML page, JSON directory listing)
- Programmatic API for schema discovery
- Well-known configuration files in the release package
- Linked references from the specification

### 5. **Multi-locale and Regional Schemas**
**Question:** Should the URI strategy account for potential regional or locale-specific schema variants?

**Current assumption:** A single Invoice-2 schema serves all locales

## Recommendations for Next Steps

1. **Establish Publishing Infrastructure**
   - Define the hosting location(s) for stable schema URIs
   - Document the URL patterns and naming conventions
   - Establish lifecycle and expiration policies

2. **Formalize Backwards Compatibility Policy**
   - Document what changes are allowed in minor versions
   - Create validation rules for schema evolution
   - Define testing and validation procedures

3. **Create Schema Versioning Guidelines**
   - Update OASIS NDR and specification documents
   - Provide clear guidance for implementers
   - Include versioning examples and best practices

4. **Establish Governance**
   - Define who maintains the stable URIs
   - Establish procedures for schema updates
   - Create deprecation and retirement policies

## Related Sections in Specification

- **Section 9.1:** Versioning and Profiles
- **Section 9.1.1:** Schema Identification
- **Section 9.1.3:** Document Instances
- **Section 10.2:** Normative Status of JSON Schemas

## Status

- **Document Created:** 2026-02-11
- **Scope:** UBL 2.5 JSON Syntax Binding Specification
- **Priority:** High - impacts publishing and implementation strategy
- **Action Required:** Discussion with OASIS Technical Committee
