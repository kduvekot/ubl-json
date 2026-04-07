# Signature Examples: Remediation Status

Reference: `UBL-json.xml` (WD01, UBL 2.5 JSON Syntax Binding Version 1.0)

## Background

The JSON signature examples were originally converted from XML. The XML examples
contained XMLDSig content and XML-era URNs that contradict the WD01 specification,
which mandates JWS (RFC 7515) signatures with HTTPS URIs.

## Status: Complete

All signature-related issues have been resolved.

### What was fixed

1. **JWS content** — The enveloped example now contains a structurally valid JWS
   object per DocBook Section 12.3, using the spec-prescribed `signatures` array
   in `ExtensionContent`:
   - `protected` header: base64url-encoded `{"alg":"RS256","kid":"ubl-example-key-1"}`
   - `signature`: 256 bytes base64url (correct length for RS256)
   - `header.kid`: matching key identifier in unprotected header

2. **URIs are correct** — all signature URIs use the spec-mandated values:
   - Enveloped: `https://docs.oasis-open.org/ubl/json/jws/enveloped`
   - Detached: `https://docs.oasis-open.org/ubl/json/jws/detached`

3. **`UBLEntity` added to extensions** — each extension container includes
   the required `UBLEntity` property per Section 10.1.

4. **Detached signature file reference** — updated from `.xml` to `.jws` with
   a proper description.

5. **Signature ABIE ordering** — `Signature` appears at its GC-defined
   position in document schemas (not hardcoded at the top).

6. **Structure matches spec** — `ExtensionContent` uses the flat `signatures`
   array as shown in DocBook Section 12.3, not the old XML-era
   `UBLDocumentSignatures` / `SignatureInformation` wrapper.

7. **Hand-crafted examples preserved** — The converter skips
   `UBL-Invoice-2.0-Enveloped.json` and `UBL-Invoice-2.0-Detached.json`
   during XML→JSON conversion so the manually authored JWS content is not
   overwritten. Both are still included in validation and the index.

### No remaining TODOs

All `_TODO` markers and placeholder text have been removed. Both examples
validate against the Invoice schema (72/72 pass).
