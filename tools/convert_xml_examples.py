#!/usr/bin/env python3
"""Convert UBL 2.5 XML example instances to JSON.

Reads UBL XML documents from the OASIS UBL 2.5 distribution and produces
equivalent JSON instances that validate against the generated JSON schemas.

The conversion traces each XML element back through the UBL semantic model:
  XML element → CBC/CAC component → QualifiedDataType → UnqualifiedDataType
and applies the correct JSON representation for each UDT per the DocBook
data-type table (one supplementary component per type):

  - AmountType     → {"value": number, "currencyID": "..."}
  - MeasureType    → {"value": number, "unitCode": "..."}
  - BinaryObjectType → {"value": "...", "mimeCode": "..."}
  - QuantityType   → number | {"value": number, "unitCode": "..."}
  - CodeType       → string | {"value": "...", "listID": "..."}
  - IdentifierType → string | {"value": "...", "schemeID": "..."}
  - TextType/NameType → string | {"value": "...", "languageID": "..."}
  - IndicatorType  → boolean
  - DateType       → string (YYYY-MM-DD)
  - TimeType       → string (HH:MM:SS)
  - NumericType/PercentType/RateType → number

Extra CCTS attributes from the XML (listAgencyID, schemeAgencyID, etc.)
are merged into the single allowed attribute using the agencyID:value
convention so that no information is silently lost.

Usage:
    uv run python convert_xml_examples.py
    uv run python convert_xml_examples.py --xml-dir /path/to/xml
    uv run python convert_xml_examples.py --validate
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path

SCHEMAS_DIR = Path("json/schemas")
EXAMPLES_DIR = Path("json/examples")
GC_DIR = Path(__file__).resolve().parent.parent / "gc"
# XML examples are fetched from oasis-tcs/ubl (branch ubl-2.5, path raw/xml/)
# at CI time. For local runs, clone the repo or pass --xml-dir explicitly.
DEFAULT_XML_DIR = Path("xml/UBL-2.5")

# URL base for JSON schema identifiers (must match generate_json_schemas.py)
SCHEMA_BASE = 'https://docs.oasis-open.org/ubl/2/json/schemas'

# Spec-mandated signature URIs (DocBook Section 11)
SIG_ENVELOPED_URI = 'https://docs.oasis-open.org/ubl/json/jws/enveloped'
SIG_DETACHED_URI = 'https://docs.oasis-open.org/ubl/json/jws/detached'

# Legacy XML-era URNs that must be replaced during conversion
_SIG_URI_MAP = {
    'urn:oasis:names:specification:ubl:dsig:enveloped': SIG_ENVELOPED_URI,
    'urn:oasis:names:specification:ubl:dsig:detached': SIG_DETACHED_URI,
    'urn:oasis:names:specification:ubl:dsig:enveloped:xades': SIG_ENVELOPED_URI,
}


def local_name(tag):
    """Strip namespace from {ns}local tag."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def build_deprecated_set():
    """Build a mapping of deprecated elements from the UBL Entities GC file.

    DocBook Section 5.2: deprecated elements shall not appear in JSON instances.
    This parses the GC to identify which child elements are deprecated within
    each parent ABIE type, so the converter can strip them during XML→JSON
    conversion.

    Also builds an element-name → ABIE-type mapping from ASBIEs so that
    elements like SenderParty (of type Party) inherit Party's deprecated
    children.

    Returns:
        dict mapping parent element name → set of deprecated child element names
        (resolved through the ASBIE type chain)
    """
    gc_path = GC_DIR / "UBL-Entities-2.5.gc"
    if not gc_path.exists():
        return {}

    tree = ET.parse(gc_path)
    root = tree.getroot()

    scl = root.find('SimpleCodeList')
    if scl is None:
        return {}

    # First pass: collect all rows
    all_rows = []
    for row in scl.findall('Row'):
        vals = {}
        for v in row.findall('Value'):
            col = v.get('ColumnRef')
            sv = v.find('SimpleValue')
            if sv is not None and sv.text:
                vals[col] = sv.text
        if vals:
            all_rows.append(vals)

    # Build deprecated set by ABIE type name
    deprecated_by_type = {}  # ABIE_type → {child_names}
    for vals in all_rows:
        if not vals.get('Definition', '').startswith('(Deprecated)'):
            continue
        comp_type = vals.get('ComponentType')
        if comp_type in ('BBIE', 'ASBIE'):
            parent = vals.get('ObjectClass', '').replace(' ', '')
            child = vals.get('ComponentName', '').replace(' ', '')
            if parent and child:
                deprecated_by_type.setdefault(parent, set()).add(child)

    # Build element name → ABIE type mapping from ASBIEs
    # e.g., SenderParty → Party, AccountingSupplierParty → SupplierParty
    elem_to_type = {}
    for vals in all_rows:
        if vals.get('ComponentType') == 'ASBIE':
            elem_name = vals.get('ComponentName', '').replace(' ', '')
            assoc_class = vals.get('AssociatedObjectClass', '').replace(' ', '')
            if elem_name and assoc_class:
                elem_to_type[elem_name] = assoc_class

    # Resolve: for each element that maps to a type with deprecated children,
    # propagate those deprecations. Also keep direct ABIE-name lookups.
    deprecated = dict(deprecated_by_type)
    for elem_name, abie_type in elem_to_type.items():
        if abie_type in deprecated_by_type and elem_name not in deprecated:
            deprecated[elem_name] = deprecated_by_type[abie_type]

    return deprecated


def build_type_map():
    """Build element name → UDT type name mapping from generated JSON schemas.

    Traces the full semantic model chain:
      CBC element → QDT type → UDT type
    to determine the JSON representation for each basic component.

    Also loads SBC (Signature Basic Components) for signature elements.
    """
    # Load QDT schema: maps qualified type names → UDT type names
    qdt_path = SCHEMAS_DIR / "common" / "QualifiedDataTypes-2.5.json"
    with open(qdt_path, encoding="utf-8") as f:
        qdt = json.load(f)

    qdt_to_udt = {}
    for name, defn in qdt.get("$defs", {}).items():
        if "$ref" in defn:
            udt_type = defn["$ref"].rsplit("/", 1)[-1]
            qdt_to_udt[name] = udt_type

    # Load CBC schema: maps element names → QDT type names → resolve to UDT
    cbc_path = SCHEMAS_DIR / "common" / "CommonBasicComponents-2.5.json"
    with open(cbc_path, encoding="utf-8") as f:
        cbc = json.load(f)

    type_map = {}
    for name, defn in cbc.get("$defs", {}).items():
        if "$ref" in defn:
            qdt_type = defn["$ref"].rsplit("/", 1)[-1]
            udt_type = qdt_to_udt.get(qdt_type, qdt_type)
            type_map[name] = udt_type

    # Load SBC schema: signature-specific basic components
    sbc_path = SCHEMAS_DIR / "common" / "SignatureBasicComponents-2.5.json"
    if sbc_path.exists():
        with open(sbc_path, encoding="utf-8") as f:
            sbc = json.load(f)
        for name, defn in sbc.get("$defs", {}).items():
            if "$ref" in defn and name not in type_map:
                qdt_type = defn["$ref"].rsplit("/", 1)[-1]
                udt_type = qdt_to_udt.get(qdt_type, qdt_type)
                type_map[name] = udt_type

    return type_map


def to_number(text):
    """Parse a numeric string, preferring int when the value is integral."""
    text = text.strip()
    try:
        if "." in text or "e" in text.lower():
            return float(text)
        return int(text)
    except ValueError:
        return text


def _merge_code_attrs(attrs):
    """Merge XML CodeType attributes into the single DocBook supplementary: listID.

    The DocBook data-type table prescribes only ``listID`` for CodeType.
    When the XML carries additional CCTS attributes (listAgencyID, listName,
    etc.), they are merged using the ``agencyID:listID`` convention so that
    no information is silently lost.
    """
    list_id = attrs.get("listID", "")
    agency = attrs.get("listAgencyID", "")
    if agency and list_id:
        return {"listID": f"{agency}:{list_id}"}
    if agency:
        return {"listID": agency}
    if list_id:
        return {"listID": list_id}
    return {}


def _merge_id_attrs(attrs):
    """Merge XML IdentifierType attributes into the single DocBook supplementary: schemeID.

    When the XML carries additional CCTS attributes (schemeAgencyID,
    schemeName, etc.), the agencyID is merged as a prefix using the
    ``agencyID:schemeID`` convention.
    """
    scheme_id = attrs.get("schemeID", "")
    agency = attrs.get("schemeAgencyID", "")
    if agency and scheme_id:
        return {"schemeID": f"{agency}:{scheme_id}"}
    if agency:
        return {"schemeID": agency}
    if scheme_id:
        return {"schemeID": scheme_id}
    return {}


def convert_leaf_value(text, attrs, udt_type, tag=None):
    """Convert a leaf element's text and XML attributes to a JSON value.

    Uses the resolved UDT type to determine the correct JSON representation.
    The DocBook data-type table prescribes one supplementary component per
    type.  Extra CCTS attributes from the XML are merged into the single
    allowed attribute using the ``agencyID:value`` convention so that no
    information is silently lost.
    """
    text = (text or "").strip()

    if udt_type == "IndicatorType":
        return text.lower() == "true"

    if udt_type == "DateType":
        return text

    if udt_type == "TimeType":
        return text

    if udt_type in ("NumericType", "PercentType", "RateType"):
        return to_number(text)

    if udt_type == "AmountType":
        return {"value": to_number(text), "currencyID": attrs.get("currencyID", "")}

    if udt_type == "MeasureType":
        return {"value": to_number(text), "unitCode": attrs.get("unitCode", "")}

    if udt_type == "BinaryObjectType":
        result = {"value": text}
        if "mimeCode" in attrs:
            result["mimeCode"] = attrs["mimeCode"]
        return result

    if udt_type == "QuantityType":
        val = to_number(text)
        unit = attrs.get("unitCode", "")
        if unit:
            return {"value": val, "unitCode": unit}
        return val

    if udt_type == "CodeType":
        extra = _merge_code_attrs(attrs)
        if extra:
            return {"value": text, **extra}
        return text

    if udt_type == "IdentifierType":
        extra = _merge_id_attrs(attrs)
        if extra:
            return {"value": text, **extra}
        return text

    if udt_type in ("TextType", "NameType"):
        lang = attrs.get("languageID", "")
        if lang:
            return {"value": text, "languageID": lang}
        # When text is empty but XML attributes are present (e.g., a
        # self-closing element like <ds:DigestMethod Algorithm="..."/>),
        # use the first non-namespace attribute value so we don't produce
        # an empty string.
        if not text and attrs:
            non_ns = {k: v for k, v in attrs.items()
                      if not k.startswith("{") and not k.startswith("xmlns")}
            if non_ns:
                return next(iter(non_ns.values()))
        # For genuinely empty elements, use the element's namespace URI as
        # the value (if available).  This preserves semantic information
        # from the XML source rather than producing an empty string.
        if not text and tag and "{" in tag:
            return tag[1:tag.index("}")]
        return text

    if udt_type == "ContentType":
        # Extension content: return as generic object
        return text if text else {}

    # Fallback: return as string
    return text


def _is_signature_extension(ext_elem):
    """Check whether a UBLExtension element contains a digital signature.

    Returns True if any child of ExtensionContent is UBLDocumentSignatures
    or lives in the XML-DSig / XAdES namespace.
    """
    for child in ext_elem:
        cname = local_name(child.tag)
        if cname == "ExtensionContent":
            for grandchild in child:
                gc_name = local_name(grandchild.tag)
                gc_ns = grandchild.tag[1:grandchild.tag.index("}")] if "{" in grandchild.tag else ""
                if gc_name == "UBLDocumentSignatures":
                    return True
                if "xmldsig" in gc_ns or "w3.org/2000/09/xmldsig" in gc_ns:
                    return True
    return False


def _jws_stub_extension():
    """Return a placeholder enveloped-signature extension using the spec URIs.

    Per DocBook Section 12.3, ExtensionContent contains a "signatures" array
    of JWS objects using the JSON Serialization (RFC 7515).
    """
    return {
        "UBLEntity": SIG_ENVELOPED_URI,
        "ExtensionURI": SIG_ENVELOPED_URI,
        "ExtensionContent": {
            "signatures": [
                {
                    "protected": "eyJhbGciOiJSUzI1NiIsImtpZCI6InVibC1leGFtcGxlLWtleS0xIn0",
                    "signature": "RJiAVDGVtMJWSn-hGQoaGTQMMWFaw0VP1vfvavrPas1EmIBUMZW0wlZKf6EZChoZNAwxYVrDRU_W9-9q-s9qzUSYgFQxlbTCVkp_oRkKGhk0DDFhWsNFT9b372r6z2rNRJiAVDGVtMJWSn-hGQoaGTQMMWFaw0VP1vfvavrPas1EmIBUMZW0wlZKf6EZChoZNAwxYVrDRU_W9-9q-s9qzUSYgFQxlbTCVkp_oRkKGhk0DDFhWsNFT9b372r6z2rNRJiAVDGVtMJWSn-hGQoaGTQMMWFaw0VP1vfvavrPas1EmIBUMZW0wlZKf6EZChoZNAwxYVrDRU_W9-9q-s9qzQ",
                    "header": {"kid": "ubl-example-key-1"}
                }
            ]
        }
    }


def _map_signature_method(value):
    """Map legacy XML-era signature URNs to the spec-mandated HTTPS URIs."""
    return _SIG_URI_MAP.get(value, value)


def convert_element(elem, type_map, deprecated=None):
    """Recursively convert an XML element to a JSON-compatible structure.

    - Leaf elements (no child elements): resolved via the semantic type map
    - Aggregate elements (with children): recursed into, grouping repeated
      child elements as JSON arrays
    - Deprecated elements (per DocBook Section 5.2) are silently stripped
    """
    children = list(elem)
    name = local_name(elem.tag)

    # Special case: UBLExtensions is a container element that maps to a
    # JSON array of UBLExtensionType objects (not a wrapper object).
    # XML: <UBLExtensions><UBLExtension>...</UBLExtension></UBLExtensions>
    # JSON: "UBLExtensions": [{ "ExtensionURI": "...", "ExtensionContent": ... }, ...]
    if name == "UBLExtensions":
        result = []
        for child in children:
            # Skip XMLDSig signature content — replace with a JWS stub.
            # The XML examples carry XMLDSig payloads that have no valid JSON
            # equivalent.  Section 11 requires JWS (RFC 7515) content instead.
            if _is_signature_extension(child):
                result.append(_jws_stub_extension())
                continue

            ext = convert_element(child, type_map, deprecated)
            # DocBook Section 7.3: ExtensionURI is required.
            # Some legacy XML examples omit it; add a placeholder.
            if isinstance(ext, dict) and "ExtensionURI" not in ext:
                ext = {"ExtensionURI": "urn:oasis:names:specification:ubl:schema:json:extension:undefined", **ext}
            # DocBook Section 10.1: UBLEntity is required, identifies the
            # schema governing the extension content.
            if isinstance(ext, dict) and "UBLEntity" not in ext:
                ext = {"UBLEntity": ext.get("ExtensionURI", ""), **ext}
            result.append(ext)
        return result

    # Map legacy signature URNs to spec-mandated HTTPS URIs
    if not children and name == "SignatureMethod":
        text = (elem.text or "").strip()
        return _map_signature_method(text)

    if not children:
        # Leaf element: look up UDT type from semantic model
        udt_type = type_map.get(name, None)

        if udt_type is None:
            # Unknown element: infer type from attributes
            attrs = elem.attrib
            if "currencyID" in attrs:
                udt_type = "AmountType"
            elif "unitCode" in attrs:
                # Could be MeasureType or QuantityType; default to QuantityType
                udt_type = "QuantityType"
            elif "mimeCode" in attrs:
                udt_type = "BinaryObjectType"
            elif "schemeID" in attrs:
                udt_type = "IdentifierType"
            elif "listID" in attrs:
                udt_type = "CodeType"
            elif "languageID" in attrs:
                udt_type = "TextType"
            else:
                udt_type = "TextType"

        return convert_leaf_value(elem.text, elem.attrib, udt_type, tag=elem.tag)

    # Aggregate element: group children by local name (preserving order)
    # Strip deprecated children (DocBook Section 5.2)
    deprecated_children = deprecated.get(name, set()) if deprecated else set()

    result = OrderedDict()
    child_groups = OrderedDict()
    for child in children:
        child_name = local_name(child.tag)
        if child_name in deprecated_children:
            continue
        if child_name not in child_groups:
            child_groups[child_name] = []
        child_groups[child_name].append(child)

    for child_name, child_elems in child_groups.items():
        if len(child_elems) == 1:
            result[child_name] = convert_element(child_elems[0], type_map, deprecated)
        else:
            result[child_name] = [
                convert_element(c, type_map, deprecated) for c in child_elems
            ]

    return dict(result)


def convert_xml_to_json(xml_path, type_map, deprecated=None):
    """Convert a UBL XML file to a JSON object.

    Returns (doc_type, json_object) where doc_type is the root element's
    local name (e.g., 'Invoice', 'CreditNote').

    Adds UBLEntity as the first property of the root object to identify
    the governing JSON schema (the JSON equivalent of the XML namespace).
    Deprecated elements (DocBook Section 5.2) are stripped during conversion.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    doc_type = local_name(root.tag)
    json_obj = convert_element(root, type_map, deprecated)

    # Add UBLEntity as the first property (Annex C: UBL-{DocType}-2)
    if isinstance(json_obj, dict):
        schema_url = f"{SCHEMA_BASE}/UBL-{doc_type}-2"
        json_obj = {"UBLEntity": schema_url, **json_obj}

    # Post-process: fix detached signature external references
    # (e.g., .xml → .jws for signature attachment URIs)
    _fix_detached_sig_refs(json_obj)

    return doc_type, json_obj


def _fix_detached_sig_refs(obj):
    """Walk the Signature ABIE and fix external reference URIs.

    Replaces references to XML signature files with .jws equivalents and
    adds a _TODO marker so the file reference can be reviewed.
    """
    if not isinstance(obj, dict):
        return
    sig = obj.get("Signature")
    if sig is None:
        return
    # Handle both single Signature and array of Signatures
    sigs = sig if isinstance(sig, list) else [sig]
    for s in sigs:
        if not isinstance(s, dict):
            continue
        att = s.get("DigitalSignatureAttachment")
        if not isinstance(att, dict):
            continue
        ext_ref = att.get("ExternalReference")
        if not isinstance(ext_ref, dict):
            continue
        uri = ext_ref.get("URI", "")
        if uri.endswith(".xml"):
            ext_ref["URI"] = uri.replace(".xml", ".jws")
            ext_ref["Description"] = "Detached JWS signature file (RFC 7515) covering the JCS-canonicalized invoice"


def validate_examples(schemas_dir, examples_dir):
    """Validate all JSON examples against their document schemas.

    Uses the jsonschema library with a URI-based registry to resolve
    cross-schema $ref references.
    """
    try:
        import jsonschema
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012
    except ImportError:
        print("\nValidation requires 'jsonschema' and 'referencing' packages.")
        print("Install with: uv pip install jsonschema referencing")
        return False

    # Load all schemas into a registry
    schema_resources = []
    schemas_by_id = {}
    for schema_file in sorted(
        list((schemas_dir / "common").glob("*.json"))
        + list((schemas_dir / "maindoc").glob("*.json"))
    ):
        with open(schema_file, encoding="utf-8") as f:
            schema = json.load(f)
        schema_id = schema.get("$id", "")
        if schema_id:
            schemas_by_id[schema_id] = schema
            schema_resources.append(
                (schema_id, Resource.from_contents(schema, default_specification=DRAFT202012))
            )

    registry = Registry().with_resources(schema_resources)

    # Map document types to their schema $ids
    # URL format: .../UBL-Invoice-2 → Invoice
    doc_type_to_schema_id = {}
    for schema_id in schemas_by_id:
        last_segment = schema_id.rsplit("/", 1)[-1]
        if last_segment.startswith("UBL-"):
            doc_name = last_segment[4:].rsplit("-", 1)[0]  # UBL-Invoice-2 → Invoice
            doc_type_to_schema_id[doc_name] = schema_id

    # Load the examples index for document type lookup
    index_path = examples_dir / "index.json"
    if not index_path.exists():
        print("  No index.json found in examples directory")
        return False
    with open(index_path, encoding="utf-8") as f:
        index_data = json.load(f)
    examples_meta = index_data.get("examples", {})

    # Validate each example
    total = 0
    passed = 0
    failed = 0
    skipped = 0

    for example_file in sorted(examples_dir.glob("*.json")):
        if example_file.name == "index.json":
            continue

        with open(example_file, encoding="utf-8") as f:
            instance = json.load(f)

        # Determine document type from the index
        meta = examples_meta.get(example_file.name, {})
        doc_type = meta.get("documentType", "")

        if not doc_type or doc_type not in doc_type_to_schema_id:
            print(f"  SKIP: {example_file.name} (no matching schema for '{doc_type}')")
            skipped += 1
            continue

        schema_id = doc_type_to_schema_id[doc_type]
        schema = schemas_by_id[schema_id]

        total += 1
        try:
            validator = jsonschema.Draft202012Validator(schema, registry=registry)
            errors = list(validator.iter_errors(instance))
            if errors:
                print(f"  FAIL: {example_file.name} ({len(errors)} error(s))")
                for err in errors[:3]:
                    path = " → ".join(str(p) for p in err.absolute_path) or "(root)"
                    print(f"        {path}: {err.message[:120]}")
                if len(errors) > 3:
                    print(f"        ... and {len(errors) - 3} more")
                failed += 1
            else:
                print(f"  OK:   {example_file.name}")
                passed += 1
        except Exception as e:
            print(f"  ERR:  {example_file.name}: {e}")
            failed += 1

    print(f"\nValidation: {passed} passed, {failed} failed, {skipped} skipped (of {total + skipped} total)")
    return failed == 0


def main():
    parser = argparse.ArgumentParser(
        description="Convert UBL XML examples to JSON instances"
    )
    parser.add_argument(
        "--xml-dir",
        type=Path,
        default=DEFAULT_XML_DIR,
        help="Directory containing XML example files (default: xml/UBL-2.5)",
    )
    parser.add_argument(
        "--schemas-dir",
        type=Path,
        default=SCHEMAS_DIR,
        help="Directory containing generated JSON schemas (default: json/schemas)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=EXAMPLES_DIR,
        help="Output directory for JSON examples (default: json/examples)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate output against schemas (requires jsonschema, referencing)",
    )
    args = parser.parse_args()

    if not args.xml_dir.is_dir():
        print(f"Error: XML directory not found: {args.xml_dir}")
        sys.exit(1)

    if not args.schemas_dir.is_dir():
        print(f"Error: Schemas directory not found: {args.schemas_dir}")
        sys.exit(1)

    # Build type map from semantic model
    print("Building type map from semantic model...")
    type_map = build_type_map()
    print(f"  Resolved {len(type_map)} basic component → UDT type mappings")

    # Build deprecated element set (DocBook Section 5.2)
    deprecated = build_deprecated_set()
    dep_count = sum(len(v) for v in deprecated.values())
    print(f"  Loaded {dep_count} deprecated elements across {len(deprecated)} parent types")

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Get available document schemas
    maindoc_schemas = {
        p.stem.replace("-2.5", "").removeprefix("UBL-"): p
        for p in (args.schemas_dir / "maindoc").glob("*.json")
    }
    print(f"  Found {len(maindoc_schemas)} document schemas")

    # Hand-crafted examples that should not be overwritten by conversion.
    # These contain manually authored JWS content per DocBook Section 12.3.
    HAND_CRAFTED = {
        "UBL-Invoice-2.0-Enveloped",
        "UBL-Invoice-2.0-Detached",
    }

    # Convert each XML file
    xml_files = sorted(args.xml_dir.glob("*.xml"))
    print(f"\nConverting {len(xml_files)} XML files...")

    converted = 0
    skipped = 0
    errors = 0
    index_entries = OrderedDict()

    for xml_path in xml_files:
        if xml_path.stem in HAND_CRAFTED:
            # Preserve hand-crafted example; still include in index
            out_name = xml_path.stem + ".json"
            out_path = args.output_dir / out_name
            if out_path.exists():
                try:
                    doc_type, _ = convert_xml_to_json(xml_path, type_map, deprecated)
                    index_entries[out_name] = {
                        "documentType": doc_type,
                        "sourceXML": xml_path.name,
                        "schemaRef": f"../schemas/maindoc/UBL-{doc_type}-2.5.json",
                    }
                except Exception:
                    pass
                print(f"  KEEP:  {xml_path.name} (hand-crafted)")
                skipped += 1
                continue
        try:
            doc_type, json_obj = convert_xml_to_json(xml_path, type_map, deprecated)
        except Exception as e:
            print(f"  ERROR: {xml_path.name}: {e}")
            errors += 1
            continue

        if doc_type not in maindoc_schemas:
            print(f"  SKIP:  {xml_path.name} (no schema for '{doc_type}')")
            skipped += 1
            continue

        # Write JSON
        out_name = xml_path.stem + ".json"
        out_path = args.output_dir / out_name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(json_obj, f, indent=2, ensure_ascii=False)
            f.write("\n")

        # Track metadata for the index
        index_entries[out_name] = {
            "documentType": doc_type,
            "sourceXML": xml_path.name,
            "schemaRef": f"../schemas/maindoc/UBL-{doc_type}-2.5.json",
        }

        print(f"  OK:    {xml_path.name} → {out_name} ({doc_type})")
        converted += 1

    # Write index file with metadata for all examples
    index_path = args.output_dir / "index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(
            {"description": "UBL 2.5 JSON example instances", "examples": index_entries},
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")
    print(f"  Wrote {index_path}")

    print(f"\nConverted: {converted}, Skipped: {skipped}, Errors: {errors}")

    # Validate if requested
    if args.validate:
        print("\nValidating examples against schemas...")
        success = validate_examples(args.schemas_dir, args.output_dir)
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
