# DocBook Review — Remaining Items

Open items from the review of `UBL-json.xml` (WD01, UBL 2.5 JSON Syntax Binding
Version 1.0). All chapters and annexes have been validated against the generated
schemas — see `todo.md` for the exhaustive verification results.

---

## 1. ~~Signature examples~~ — Resolved

Signature examples now contain structurally valid JWS content per DocBook
Section 12.3. All TODOs removed. See
[signature-examples-remediation.md](signature-examples-remediation.md).

---

## 2. ~~Annex A is empty~~ — Resolved

The WD01 DocBook now has full Annex A content (License, Document Status and
Notices) with OASIS boilerplate, copyright, and IPR information.

---

## 3. Orphan bibliography entry [BDNDR] (Appendix B.2)

"Business Document Naming and Design Rules" is listed in B.2 Informative
References but is never cited in the document body.

**Action**: DocBook editorial — either cite where relevant or remove the entry.

---

## 4. Section 13.1 example URI inconsistency (line 594)

The example URI in Section 13.1 is:
```
https://docs.oasis-open.org/ubl/json/schemas/Invoice-2
```

This is missing the `/2/` path segment and `UBL-` prefix compared to Annex C:
```
https://docs.oasis-open.org/ubl/2/json/schemas/UBL-Invoice-2
```

**Action**: DocBook editorial — fix the example to match Annex C.
