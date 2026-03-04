# Signature Examples: Remediation Plan

## Problem

The current JSON signature examples were mechanically converted from XML and contain
XMLDSig content and XML-era URNs that contradict the normative specification.

### Current state of the examples

**`UBL-Invoice-2.0-Enveloped.json`** has two issues:

1. **ExtensionURI** uses `urn:oasis:names:specification:ubl:schema:json:extension:undefined`
   — the spec (Section 11.3) requires `https://docs.oasis-open.org/ubl/json/jws/enveloped`

2. **ExtensionContent** contains a literal XMLDSig structure (`SignedInfo`,
   `CanonicalizationMethod`, `SignatureValue`, `KeyInfo`, etc.) — the spec requires
   a JWS (RFC 7515) object

3. **Signature ABIE** uses `SignatureMethod: "urn:oasis:names:specification:ubl:dsig:enveloped"`
   — the spec requires `https://docs.oasis-open.org/ubl/json/jws/enveloped`

**`UBL-Invoice-2.0-Detached.json`** has one issue:

1. **SignatureMethod** uses `urn:oasis:names:specification:ubl:dsig:detached`
   — the spec requires `https://docs.oasis-open.org/ubl/json/jws/detached`

2. **ExternalReference URI** points to `UBL-Invoice-2.0-Detached-Signature.xml`
   — should reference a JWS file, not an XML signature file

### What the spec says (Section 11, normative)

| Element | Spec-mandated value |
|---------|-------------------|
| Enveloped ExtensionURI | `https://docs.oasis-open.org/ubl/json/jws/enveloped` |
| Enveloped SignatureMethod | `https://docs.oasis-open.org/ubl/json/jws/enveloped` |
| Enveloped ExtensionContent | A JWS Compact Serialization or JWS JSON Serialization object |
| Detached SignatureMethod | `https://docs.oasis-open.org/ubl/json/jws/detached` |
| Detached ExternalReference | Reference to a JWS object (not an XMLDSig file) |

---

## Required changes

### 1. Update the signature examples manually

The signature examples (`UBL-Invoice-2.0-Enveloped.json` and
`UBL-Invoice-2.0-Detached.json`) need to be manually updated — not auto-generated
from XML — because valid JWS content cannot be derived from XMLDSig content.

**Enveloped example** — replace:
- The `ExtensionURI` with `https://docs.oasis-open.org/ubl/json/jws/enveloped`
- The entire `ExtensionContent` XMLDSig structure with a valid JWS representation
- The `SignatureMethod` in the Signature ABIE with `https://docs.oasis-open.org/ubl/json/jws/enveloped`

**Detached example** — replace:
- `SignatureMethod` with `https://docs.oasis-open.org/ubl/json/jws/detached`
- The external reference URI to point to a `.jws` file instead of `.xml`

### 2. Skip signature content during XML-to-JSON conversion

The `convert_xml_examples.py` script currently converts the XML signature examples
by mechanically translating every XML element to JSON, including the XMLDSig payload.
This produces invalid JSON signature content.

The converter should be modified to:

1. **Skip the UBLExtensions entry that contains the signature** in the enveloped example.
   When converting `UBL-Invoice-2.0-Enveloped.xml`, detect the extension containing
   `UBLDocumentSignatures` and replace it with a placeholder comment or a valid
   JWS stub, rather than converting the XMLDSig tree verbatim.

2. **Update the Signature ABIE URIs** during conversion. When the converter encounters
   `SignatureMethod` values like `urn:oasis:names:specification:ubl:dsig:enveloped`
   or `urn:oasis:names:specification:ubl:dsig:detached`, map them to the spec-mandated
   HTTPS URIs.

3. **Update the external reference** in the detached example to point to a `.jws`
   file instead of an `.xml` file.

Alternatively, the signature examples can be excluded from automatic conversion
entirely and maintained as hand-crafted files, since the JWS content must be
authored separately anyway.

### 3. Create valid JWS example content

The enveloped example needs a realistic (though not cryptographically verifiable)
JWS structure to demonstrate the correct format. This should use JWS JSON
Serialization and include:

- `protected` header with `alg` and optionally `kid` or `x5c`
- `payload` (empty string for enveloped, since the canonicalized document *is*
  the payload and is excluded from the extension)
- `signature` (a base64url-encoded placeholder)

Example structure for the enveloped ExtensionContent:
```json
{
  "ExtensionURI": "https://docs.oasis-open.org/ubl/json/jws/enveloped",
  "ExtensionContent": {
    "UBLDocumentSignatures": {
      "SignatureInformation": {
        "ID": "urn:oasis:names:specification:ubl:signature:1",
        "JWS": {
          "protected": "eyJhbGciOiJSUzI1NiIsIng1YyI6WyJNSUlDY1RDQ0FkLi4uIl19",
          "payload": "",
          "signature": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk..."
        }
      }
    }
  }
}
```

> Note: The exact JWS structure within `ExtensionContent` needs to be confirmed
> against the DocBook's UBLDocumentSignatures schema definition.

---

## What has been implemented

The converter (`convert_xml_examples.py`) now handles signature content correctly:

1. **XMLDSig content is skipped** — when the converter encounters a `UBLExtension`
   containing `UBLDocumentSignatures` or XMLDSig-namespaced content, it replaces
   the entire extension with a JWS stub using the correct `ExtensionURI`.

2. **Legacy URNs are mapped** — `SignatureMethod` values like
   `urn:oasis:names:specification:ubl:dsig:enveloped` are automatically mapped to
   the spec-mandated `https://docs.oasis-open.org/ubl/json/jws/enveloped`.

3. **Detached signature file refs are updated** — `.xml` → `.jws`.

4. **`_TODO` markers** signal which examples still need manual work. Since JSON has
   no comments, the `_TODO` property serves as a grep-able, visible marker.
   Run `grep -rn _TODO json/examples/` to find all instances.

### Current `_TODO` markers

| File | Location | What needs to be done |
|------|----------|----------------------|
| `UBL-Invoice-2.0-Enveloped.json` | `UBLExtensions[2].ExtensionContent.UBLDocumentSignatures.SignatureInformation._TODO` | Replace with valid JWS (RFC 7515) object |
| `UBL-Invoice-2.0-Detached.json` | `Signature.DigitalSignatureAttachment.ExternalReference._TODO` | Provide actual detached JWS file |

## Remaining work

| File | Action needed |
|------|--------------|
| `json/examples/UBL-Invoice-2.0-Enveloped.json` | Replace `_TODO` stub with valid JWS content |
| `json/examples/UBL-Invoice-2.0-Detached.json` | Provide actual `.jws` file and remove `_TODO` |
| `json/schemas/common/SignatureAggregateComponents-2.5.json` | Verify schema accommodates JWS content |

## Priority

This is a correctness issue — the current examples violate the normative spec.
Implementers reading these examples will either copy the wrong pattern or lose
trust in the specification. This should be addressed before publishing.
