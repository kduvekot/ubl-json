#!/usr/bin/env python3
"""Tests for convert_to_docbook.py — captures output for before/after comparison.

Runs the full docx-to-DocBook conversion against the real source .docx
and compares the XML output byte-for-byte with the baseline.
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

# Ensure the tools package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tools.convert_to_docbook import (
    xml_escape,
    slugify,
    render_inline,
    convert,
    _url_base,
    _build_entities,
    _emit_preamble,
    _emit_articleinfo,
    _is_definition_para,
    _get_list_tag,
    _render_list_items,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DOCX_PATH = BASE_DIR / "source" / "UBL_2.5_JSON_Syntax_Binding_version_1.0_WD01.docx"
EXISTING_XML = BASE_DIR / "UBL-json.xml"


def hash_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ── Unit tests for xml_escape ─────────────────────────────────────────────

def test_xml_escape_basic():
    """Standard XML special characters should be escaped."""
    return {
        "ampersand": xml_escape("A & B"),
        "lt": xml_escape("a < b"),
        "gt": xml_escape("a > b"),
        "quot": xml_escape('say "hello"'),
        "combined": xml_escape('x < y & "z"'),
    }


def test_xml_escape_apostrophe():
    """Apostrophes should be escaped for use in XML attributes."""
    result = xml_escape("it's a test")
    has_apos = "&apos;" in result or "'" not in result or "&#39;" in result
    return {
        "input": "it's a test",
        "output": result,
        "apostrophe_safe": has_apos,
    }


def test_xml_escape_none():
    """None input should return empty string."""
    return {"result": xml_escape(None)}


def test_xml_escape_clean():
    """Text with no special characters should pass through unchanged."""
    return {"result": xml_escape("hello world 123")}


def test_xml_escape_entity_value():
    """Entity values with special chars should be fully escaped.

    This tests the context used at line 669 of convert_to_docbook.py:
    <!ENTITY name "value"> — value must have & < > " ' escaped.
    """
    # Simulates a real-world title with an apostrophe
    test_cases = {
        "plain": xml_escape("Working Draft 01"),
        "with_apostrophe": xml_escape("Editor's Draft"),
        "with_quotes": xml_escape('The "UBL" Standard'),
        "with_amp": xml_escape("JSON & XML"),
        "with_angle": xml_escape("value < 10 > 0"),
    }
    return test_cases


# ── Unit tests for slugify ────────────────────────────────────────────────

def test_slugify():
    """Slugify should produce uppercase, hyphenated slugs."""
    return {
        "basic": slugify("Hello World"),
        "special_chars": slugify("Section 1.2: Overview"),
        "underscores": slugify("some_thing_here"),
        "spaces_and_hyphens": slugify("A - B  C"),
    }


# ── Unit tests for render_inline ──────────────────────────────────────────

def test_url_base():
    """_url_base should strip filename and annotations from URLs."""
    return {
        "simple": _url_base("https://example.com/path/file.html"),
        "with_annotation": _url_base("https://example.com/path/file.html (Authoritative)"),
        "no_path": _url_base("https://example.com"),
    }


def test_build_entities():
    """_build_entities should produce the correct entity dict from metadata."""
    meta = {
        "title": "UBL 2.5 JSON Syntax Binding Version 1.0",
        "status": "Working Draft 01",
        "date": "01 January 2025",
        "this_version_urls": ["https://docs.oasis-open.org/ubl/csd01-UBL-2.5-JSON-1.0/file.html"],
        "latest_version_urls": ["https://docs.oasis-open.org/ubl/UBL-2.5-JSON-1.0/file.html"],
        "technical_committee": "OASIS UBL TC",
        "abstract": "This document defines...",
    }
    entities = _build_entities(meta)
    return {
        "name": entities["name"],
        "version": entities["version"],
        "spec-version": entities["spec-version"],
        "stage": entities["stage"],
        "has_this_loc": bool(entities["this-loc"]),
        "has_latest_loc": bool(entities["latest-loc"]),
    }


def test_emit_preamble():
    """_emit_preamble should produce valid XML declaration with entities."""
    entities = {"name": "UBL", "version": "2.5"}
    lines = _emit_preamble(entities)
    joined = "\n".join(lines)
    return {
        "has_xml_decl": "<?xml" in joined,
        "has_doctype": "<!DOCTYPE" in joined,
        "has_entity": '<!ENTITY name "UBL">' in joined,
        "line_count": len(lines),
    }


def test_emit_articleinfo():
    """_emit_articleinfo should produce the <articleinfo> block."""
    meta = {
        "title": "Test Title",
        "status": "Draft",
        "date": "2025-01-01",
        "editors": [{"name": "John Doe", "email": "john@example.com", "org": "ACME"}],
        "technical_committee": "Test TC",
        "abstract": "A test abstract.",
    }
    lines = _emit_articleinfo(meta)
    joined = "\n".join(lines)
    return {
        "has_article_open": "<article " in joined,
        "has_articleinfo": "<articleinfo>" in joined,
        "has_articleinfo_close": "</articleinfo>" in joined,
        "has_editor": "<editor>" in joined,
        "has_abstract": "<abstract>" in joined,
        "line_count": len(lines),
    }


def test_is_definition_para():
    """_is_definition_para should detect TERM<tab>Definition patterns."""
    yes = {"inline": [{"type": "text", "text": "Term", "bold": True}], "raw_text": "Term\tDefinition"}
    no_tab = {"inline": [{"type": "text", "text": "Term", "bold": True}], "raw_text": "Term Definition"}
    no_bold = {"inline": [{"type": "text", "text": "Term", "bold": False}], "raw_text": "Term\tDefinition"}
    empty = {"inline": [], "raw_text": ""}
    return {
        "with_tab_and_bold": _is_definition_para(yes),
        "without_tab": _is_definition_para(no_tab),
        "without_bold": _is_definition_para(no_bold),
        "empty": _is_definition_para(empty),
    }


def test_get_list_tag():
    """_get_list_tag should return correct list type based on numbering format."""
    nmap = {("1", "0"): "decimal", ("2", "0"): "bullet", ("3", "0"): "lowerRoman"}
    return {
        "decimal": _get_list_tag("1", 0, nmap),
        "bullet": _get_list_tag("2", 0, nmap),
        "roman": _get_list_tag("3", 0, nmap),
        "unknown": _get_list_tag("99", 0, nmap),
    }


def test_render_list_items():
    """_render_list_items should produce proper nested list XML."""
    nmap = {("1", "0"): "bullet"}
    items = [
        {"numId": "1", "ilvl": 0, "inline": [{"type": "text", "text": "Item 1", "bold": False, "italic": False}]},
        {"numId": "1", "ilvl": 0, "inline": [{"type": "text", "text": "Item 2", "bold": False, "italic": False}]},
    ]
    lines = _render_list_items(items, 2, nmap)
    return {"lines": lines, "line_count": len(lines)}


def test_render_inline_text():
    """Plain text rendering."""
    items = [{"type": "text", "text": "hello world", "bold": False, "italic": False}]
    return {"result": render_inline(items)}


def test_render_inline_bold_italic():
    """Bold and italic rendering."""
    items = [
        {"type": "text", "text": "bold", "bold": True, "italic": False},
        {"type": "text", "text": " and ", "bold": False, "italic": False},
        {"type": "text", "text": "italic", "bold": False, "italic": True},
        {"type": "text", "text": " and ", "bold": False, "italic": False},
        {"type": "text", "text": "both", "bold": True, "italic": True},
    ]
    return {"result": render_inline(items)}


def test_render_inline_hyperlink():
    """Hyperlink rendering with special characters in URL."""
    items = [
        {"type": "hyperlink", "url": "https://example.com/page?a=1&b=2", "text": "Click here"},
    ]
    return {"result": render_inline(items)}


def test_render_inline_special_chars():
    """Text with XML special characters should be escaped."""
    items = [
        {"type": "text", "text": "x < y & z > w", "bold": False, "italic": False},
    ]
    return {"result": render_inline(items)}


def test_render_inline_apostrophe_in_url():
    """Apostrophe in a hyperlink URL should be safe in the attribute."""
    items = [
        {"type": "hyperlink", "url": "https://example.com/it's", "text": "link"},
    ]
    result = render_inline(items)
    # The URL goes into url="...", so apostrophes must be safe
    return {"result": result}


# ── Appendix numbering test ──────────────────────────────────────────────

def test_appendix_titles_no_duplicate_numbers():
    """Appendix section titles must not contain hardcoded number prefixes.

    The docx source has numbers baked into headings (e.g. "C.1 Common schemas")
    but DocBook XSLT auto-generates them, so the converter must strip them.
    This test guards against regression.
    """
    if not DOCX_PATH.exists():
        return {"skipped": True, "reason": f"Source .docx not found: {DOCX_PATH}"}

    import re

    tmpdir = Path(tempfile.mkdtemp(prefix="ctd_test_"))
    try:
        output_path = tmpdir / "UBL-json.xml"
        convert(str(DOCX_PATH), str(output_path))
        content = output_path.read_text(encoding="utf-8")

        # Find all <title> elements inside <appendix> blocks
        in_appendix = False
        numbered_titles = []
        prefix_re = re.compile(r'^[A-Z]\.\d+(?:\.\d+)*\s')

        for line_no, line in enumerate(content.splitlines(), 1):
            if '<appendix ' in line:
                in_appendix = True
            elif '</appendix>' in line:
                in_appendix = False
            elif in_appendix and '<title>' in line:
                # Extract title text between <title> and </title>
                m = re.search(r'<title>(.*?)</title>', line)
                if m:
                    title_text = m.group(1)
                    if prefix_re.match(title_text):
                        numbered_titles.append(
                            {"line": line_no, "title": title_text}
                        )

        assert not numbered_titles, (
            f"Found {len(numbered_titles)} appendix <title> elements with "
            f"hardcoded number prefixes (would cause duplicate numbering in "
            f"HTML): {numbered_titles[:5]}"
        )

        return {"checked": True, "duplicate_titles_found": 0}
    finally:
        shutil.rmtree(tmpdir)


# ── Full conversion test ──────────────────────────────────────────────────

def test_full_conversion():
    """Run full docx → DocBook conversion and capture output hash."""
    if not DOCX_PATH.exists():
        return {"skipped": True, "reason": f"Source .docx not found: {DOCX_PATH}"}

    tmpdir = Path(tempfile.mkdtemp(prefix="ctd_test_"))
    try:
        output_path = tmpdir / "UBL-json.xml"
        convert(str(DOCX_PATH), str(output_path))

        assert output_path.exists(), "Output XML was not created"
        content = output_path.read_text(encoding="utf-8")

        return {
            "output_hash": hash_file(output_path),
            "output_size": len(content),
            "has_xml_decl": content.startswith("<?xml"),
            "has_doctype": "<!DOCTYPE" in content,
            "has_article": "<article " in content,
            "line_count": content.count("\n"),
        }
    finally:
        shutil.rmtree(tmpdir)


def test_conversion_matches_baseline():
    """The conversion output should match the existing UBL-json.xml baseline."""
    if not DOCX_PATH.exists():
        return {"skipped": True, "reason": f"Source .docx not found: {DOCX_PATH}"}
    if not EXISTING_XML.exists():
        return {"skipped": True, "reason": f"Baseline XML not found: {EXISTING_XML}"}

    tmpdir = Path(tempfile.mkdtemp(prefix="ctd_test_"))
    try:
        output_path = tmpdir / "UBL-json.xml"
        convert(str(DOCX_PATH), str(output_path))

        new_content = output_path.read_text(encoding="utf-8")
        baseline_content = EXISTING_XML.read_text(encoding="utf-8")

        matches = new_content == baseline_content

        # If different, find first differing line for diagnostics
        first_diff = None
        if not matches:
            new_lines = new_content.splitlines()
            base_lines = baseline_content.splitlines()
            for i, (nl, bl) in enumerate(zip(new_lines, base_lines)):
                if nl != bl:
                    first_diff = {
                        "line": i + 1,
                        "baseline": bl[:120],
                        "new": nl[:120],
                    }
                    break
            if first_diff is None and len(new_lines) != len(base_lines):
                first_diff = {
                    "line": min(len(new_lines), len(base_lines)) + 1,
                    "baseline_lines": len(base_lines),
                    "new_lines": len(new_lines),
                }

        return {
            "matches_baseline": matches,
            "first_diff": first_diff,
            "baseline_hash": hash_file(EXISTING_XML),
            "new_hash": hash_file(output_path),
        }
    finally:
        shutil.rmtree(tmpdir)


# ── Runner ────────────────────────────────────────────────────────────────

ALL_TESTS = [
    ("xml_escape_basic", test_xml_escape_basic),
    ("xml_escape_apostrophe", test_xml_escape_apostrophe),
    ("xml_escape_none", test_xml_escape_none),
    ("xml_escape_clean", test_xml_escape_clean),
    ("xml_escape_entity_value", test_xml_escape_entity_value),
    ("slugify", test_slugify),
    ("url_base", test_url_base),
    ("build_entities", test_build_entities),
    ("emit_preamble", test_emit_preamble),
    ("emit_articleinfo", test_emit_articleinfo),
    ("is_definition_para", test_is_definition_para),
    ("get_list_tag", test_get_list_tag),
    ("render_list_items", test_render_list_items),
    ("render_inline_text", test_render_inline_text),
    ("render_inline_bold_italic", test_render_inline_bold_italic),
    ("render_inline_hyperlink", test_render_inline_hyperlink),
    ("render_inline_special_chars", test_render_inline_special_chars),
    ("render_inline_apostrophe_in_url", test_render_inline_apostrophe_in_url),
    ("appendix_titles_no_duplicate_numbers", test_appendix_titles_no_duplicate_numbers),
    ("full_conversion", test_full_conversion),
    ("conversion_matches_baseline", test_conversion_matches_baseline),
]


def run_all(snapshot_path=None):
    results = {}
    passed = 0
    failed = 0

    for name, fn in ALL_TESTS:
        try:
            result = fn()
            results[name] = result
            passed += 1
            print(f"  PASS: {name}")
        except Exception as e:
            failed += 1
            results[name] = f"ERROR: {e}"
            print(f"  FAIL: {name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{passed} passed, {failed} failed")

    if snapshot_path:
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, sort_keys=True, default=str)
        print(f"Snapshot written to {snapshot_path}")

    return results, failed


def compare_snapshots(before_path, after_path):
    """Compare two snapshot files and report differences."""
    with open(before_path, encoding="utf-8") as f:
        before = json.load(f)
    with open(after_path, encoding="utf-8") as f:
        after = json.load(f)

    diffs = []
    all_keys = sorted(set(before.keys()) | set(after.keys()))

    for key in all_keys:
        if key not in before:
            diffs.append(f"  NEW test: {key}")
        elif key not in after:
            diffs.append(f"  REMOVED test: {key}")
        elif before[key] != after[key]:
            diffs.append(f"  CHANGED: {key}")
            if isinstance(before[key], dict) and isinstance(after[key], dict):
                for sk in sorted(set(before[key].keys()) | set(after[key].keys())):
                    bv = before[key].get(sk)
                    av = after[key].get(sk)
                    if bv != av:
                        diffs.append(f"    sub-key '{sk}': {repr(bv)[:100]} -> {repr(av)[:100]}")

    if not diffs:
        print("No differences — output is identical.")
    else:
        print(f"{len(diffs)} difference(s) found:")
        for d in diffs:
            print(d)

    return diffs


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "compare":
        compare_snapshots(sys.argv[2], sys.argv[3])
    else:
        snapshot = sys.argv[1] if len(sys.argv) > 1 else None
        print("Running convert_to_docbook tests...")
        _, failed = run_all(snapshot)
        sys.exit(failed)
