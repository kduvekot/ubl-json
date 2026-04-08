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
    ("render_inline_text", test_render_inline_text),
    ("render_inline_bold_italic", test_render_inline_bold_italic),
    ("render_inline_hyperlink", test_render_inline_hyperlink),
    ("render_inline_special_chars", test_render_inline_special_chars),
    ("render_inline_apostrophe_in_url", test_render_inline_apostrophe_in_url),
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
