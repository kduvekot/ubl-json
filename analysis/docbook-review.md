# DocBook Review — Remaining Items

Open items from the chapter-by-chapter review of `UBL-2.5-JSON-Syntax-Binding.xml`
(Revision 306, 2025-09-23). All other chapters passed without issues.

---

## 1. Signature examples use wrong URIs and XMLDSig content (Ch. 11 / 14)

The two signature example files use legacy XML-era identifiers and content
instead of the DocBook-prescribed values:

| Issue | Expected | Actual |
|-------|----------|--------|
| Enveloped `ExtensionURI` | `https://docs.oasis-open.org/ubl/json/jws/enveloped` | `urn:oasis:names:specification:ubl:schema:json:extension:undefined` |
| Enveloped `SignatureMethod` | `https://docs.oasis-open.org/ubl/json/jws/enveloped` | `urn:oasis:names:specification:ubl:dsig:enveloped` |
| Detached `SignatureMethod` | `https://docs.oasis-open.org/ubl/json/jws/detached` | `urn:oasis:names:specification:ubl:dsig:detached` |
| Enveloped `ExtensionContent` | JWS object (RFC 7515) | XMLDSig structure |

**Status**: Converter fixed (maps URIs, stubs JWS). Manual work remains —
see [signature-examples-remediation.md](signature-examples-remediation.md).

---

## 2. Annex A is empty (Appendix A)

The appendix "License, Document Status and Notices" is a placeholder with no
content. No license or copyright information appears anywhere in the DocBook
source, schemas, or examples. Expected for a working draft but must be
populated before advancing to a formal committee stage.

**Action**: DocBook editorial — fill in OASIS boilerplate.

---

## 3. Orphan bibliography entry [BDNDR] (Annex B.2)

"Business Document Naming and Design Rules" is listed in B.2 Informative
References but is never cited in the document body.

**Action**: DocBook editorial — either cite where relevant or remove the entry.
