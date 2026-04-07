# Signature Examples: Remediation Status

Reference: `UBL-json.xml` (WD01, UBL 2.5 JSON Syntax Binding Version 1.0)

## Background

The JSON signature examples were originally converted from XML. The XML examples
contained XMLDSig content and XML-era URNs that contradict the WD01 specification,
which mandates JWS (RFC 7515) signatures with HTTPS URIs.

## What has been fixed

The converter (`convert_xml_examples.py`) and checked-in examples now handle
signature content correctly:

1. **XMLDSig content is replaced** — when the converter encounters a
   `UBLExtension` containing `UBLDocumentSignatures` or XMLDSig-namespaced
   content, it replaces the entire extension with a JWS stub using the
   correct `ExtensionURI`.

2. **URIs are correct** — all signature URIs use the spec-mandated values:
   - Enveloped: `https://docs.oasis-open.org/ubl/json/jws/enveloped`
   - Detached: `https://docs.oasis-open.org/ubl/json/jws/detached`

3. **`UBLEntity` added to extensions** — each extension container now includes
   the required `UBLEntity` property per Section 10.1.

4. **Detached signature file reference** — updated from `.xml` to `.jws`.

5. **Signature ABIE ordering** — `Signature` now appears at its GC-defined
   position in document schemas (not hardcoded at the top).

## Remaining work

| File | Location | What needs to be done |
|------|----------|----------------------|
| `UBL-Invoice-2.0-Enveloped.json` | `UBLExtensions[2].ExtensionContent.UBLDocumentSignatures.SignatureInformation._TODO` | Replace stub with a realistic JWS (RFC 7515) JSON Serialization object |
| `UBL-Invoice-2.0-Detached.json` | `Signature.DigitalSignatureAttachment.ExternalReference.Description` | Provide actual detached `.jws` file and remove TODO description |

### What the JWS stub should look like

Per DocBook Section 12.3 (Enveloped signature structure), the `ExtensionContent`
should contain a `signatures` array of JWS objects using the JSON Serialization:

```json
{
  "ExtensionContent": {
    "signatures": [
      {
        "protected": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9",
        "signature": "Z3VhcmQtbWUtd2VsbC4uLg",
        "header": {"kid": "12345"}
      }
    ]
  }
}
```

Note: The current examples use a `UBLDocumentSignatures` / `SignatureInformation`
wrapper around the JWS content, reflecting the XML-era structure from the
`SignatureAggregateComponents` schema. The DocBook Section 12.3 example shows
`signatures` directly in `ExtensionContent` without this wrapper. This needs TC
clarification — whether the wrapper is required or whether the flat `signatures`
array is the correct structure.

## Priority

The `_TODO` marker in the enveloped example is a correctness issue — it contains
placeholder content rather than a valid JWS structure. This should be resolved
before publishing, ideally with a non-verifiable but structurally correct JWS
example that demonstrates the correct format for implementers.
