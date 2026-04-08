#!/usr/bin/env python3
"""Tests for generate_json_schemas.py — captures output for before/after comparison.

Runs the full schema generation pipeline against the real GC files and
captures checksums + content of all generated schema files. This ensures
that refactoring changes don't alter the output.
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

from tools.generate_json_schemas import (
    parse_gc_file,
    build_registry,
    generate_unqualified_data_types,
    generate_qualified_data_types,
    generate_common_basic_components,
    generate_common_aggregate_components,
    generate_common_extension_components,
    generate_signature_schemas,
    generate_document_schemas,
    generate_catalog,
    SCHEMA_BASE,
    FILE_VERSION_SUFFIX,
    _LIBRARY_MODELS,
)


BASE_DIR = Path(__file__).resolve().parent.parent.parent
GC_DIR = BASE_DIR / "gc"


def hash_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def collect_tree(root):
    """Return a sorted dict of {relative_path: sha256} for all files under root."""
    tree = {}
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            full = Path(dirpath) / fn
            rel = full.relative_to(root)
            tree[str(rel)] = hash_file(full)
    return dict(sorted(tree.items()))


def load_all_json(root):
    """Return a dict of {relative_path: parsed_json} for all .json files."""
    result = {}
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".json"):
                full = Path(dirpath) / fn
                rel = str(full.relative_to(root))
                with open(full, encoding="utf-8") as f:
                    result[rel] = json.load(f)
    return dict(sorted(result.items()))


# ── Unit tests for parse/build ───────────────────────────────────────────

def test_parse_gc_file():
    """Parse the main GC file and verify row count and structure."""
    gc_path = GC_DIR / "UBL-Entities-2.5.gc"
    if not gc_path.exists():
        return {"skipped": True, "reason": "GC file not found"}
    rows = parse_gc_file(gc_path)
    # Check basic structure
    sample = rows[0] if rows else {}
    has_model = "ModelName" in sample
    has_component = "ComponentType" in sample
    return {
        "row_count": len(rows),
        "has_model_name": has_model,
        "has_component_type": has_component,
        "sample_keys": sorted(sample.keys()),
    }


def test_build_registry():
    """Build registry and verify model/ABIE counts."""
    gc_path = GC_DIR / "UBL-Entities-2.5.gc"
    if not gc_path.exists():
        return {"skipped": True, "reason": "GC file not found"}
    rows = parse_gc_file(gc_path)
    registry = build_registry(rows)
    model_names = sorted(registry["models"].keys())
    abie_counts = {
        name: len(data["abies"])
        for name, data in registry["models"].items()
    }
    total_abies = sum(abie_counts.values())
    return {
        "model_count": len(model_names),
        "total_abies": total_abies,
        "model_names": model_names,
    }


def test_constants():
    """Verify key constants haven't changed."""
    return {
        "SCHEMA_BASE": SCHEMA_BASE,
        "FILE_VERSION_SUFFIX": FILE_VERSION_SUFFIX,
        "LIBRARY_MODELS": sorted(_LIBRARY_MODELS),
    }


# ── Schema generation tests ──────────────────────────────────────────────

def _build_full_registry():
    """Parse all GC files and build the combined registry."""
    main_rows = parse_gc_file(GC_DIR / "UBL-Entities-2.5.gc")
    sig_rows = parse_gc_file(GC_DIR / "UBL-Signature-Entities-2.5.gc")
    ext_rows = parse_gc_file(GC_DIR / "UBL-Extension-Entities-2.5.gc")
    all_rows = main_rows + sig_rows + ext_rows
    registry = build_registry(all_rows)
    return registry, all_rows


def test_generate_unqualified_data_types():
    """Generate UDT schema and verify structure."""
    tmpdir = Path(tempfile.mkdtemp(prefix="gs_test_"))
    try:
        generate_unqualified_data_types(tmpdir)
        out_file = tmpdir / f"UnqualifiedDataTypes{FILE_VERSION_SUFFIX}.json"
        assert out_file.exists(), f"Output file not created: {out_file}"
        with open(out_file, encoding="utf-8") as f:
            schema = json.load(f)
        defs = schema.get("$defs", {})
        return {
            "file_hash": hash_file(out_file),
            "schema_id": schema.get("$id"),
            "def_count": len(defs),
            "def_names": sorted(defs.keys()),
        }
    finally:
        shutil.rmtree(tmpdir)


def test_generate_qualified_data_types():
    """Generate QDT schema and verify structure."""
    _, all_rows = _build_full_registry()
    tmpdir = Path(tempfile.mkdtemp(prefix="gs_test_"))
    try:
        generate_qualified_data_types(tmpdir, all_rows)
        out_file = tmpdir / f"QualifiedDataTypes{FILE_VERSION_SUFFIX}.json"
        with open(out_file, encoding="utf-8") as f:
            schema = json.load(f)
        defs = schema.get("$defs", {})
        return {
            "file_hash": hash_file(out_file),
            "schema_id": schema.get("$id"),
            "def_count": len(defs),
        }
    finally:
        shutil.rmtree(tmpdir)


def test_generate_cbc():
    """Generate CBC schema and verify structure."""
    registry, _ = _build_full_registry()
    tmpdir = Path(tempfile.mkdtemp(prefix="gs_test_"))
    try:
        generate_common_basic_components(tmpdir, registry)
        out_file = tmpdir / f"CommonBasicComponents{FILE_VERSION_SUFFIX}.json"
        with open(out_file, encoding="utf-8") as f:
            schema = json.load(f)
        defs = schema.get("$defs", {})
        return {
            "file_hash": hash_file(out_file),
            "schema_id": schema.get("$id"),
            "def_count": len(defs),
        }
    finally:
        shutil.rmtree(tmpdir)


def test_generate_cac():
    """Generate CAC schema and verify structure."""
    registry, _ = _build_full_registry()
    tmpdir = Path(tempfile.mkdtemp(prefix="gs_test_"))
    try:
        generate_common_aggregate_components(tmpdir, registry)
        out_file = tmpdir / f"CommonAggregateComponents{FILE_VERSION_SUFFIX}.json"
        with open(out_file, encoding="utf-8") as f:
            schema = json.load(f)
        defs = schema.get("$defs", {})
        return {
            "file_hash": hash_file(out_file),
            "schema_id": schema.get("$id"),
            "def_count": len(defs),
        }
    finally:
        shutil.rmtree(tmpdir)


def test_generate_extension_components():
    """Generate extension components schema and verify structure."""
    registry, _ = _build_full_registry()
    tmpdir = Path(tempfile.mkdtemp(prefix="gs_test_"))
    try:
        generate_common_extension_components(tmpdir, registry)
        out_file = tmpdir / f"CommonExtensionComponents{FILE_VERSION_SUFFIX}.json"
        with open(out_file, encoding="utf-8") as f:
            schema = json.load(f)
        defs = schema.get("$defs", {})
        return {
            "file_hash": hash_file(out_file),
            "schema_id": schema.get("$id"),
            "def_count": len(defs),
            "def_names": sorted(defs.keys()),
        }
    finally:
        shutil.rmtree(tmpdir)


def test_generate_signature_schemas():
    """Generate signature schemas and verify structure."""
    registry, _ = _build_full_registry()
    tmpdir = Path(tempfile.mkdtemp(prefix="gs_test_"))
    try:
        generate_signature_schemas(tmpdir, registry)
        results = {}
        for name in ["SignatureBasicComponents", "SignatureAggregateComponents"]:
            out_file = tmpdir / f"{name}{FILE_VERSION_SUFFIX}.json"
            with open(out_file, encoding="utf-8") as f:
                schema = json.load(f)
            defs = schema.get("$defs", {})
            results[name] = {
                "file_hash": hash_file(out_file),
                "schema_id": schema.get("$id"),
                "def_count": len(defs),
            }
        return results
    finally:
        shutil.rmtree(tmpdir)


def test_generate_document_schemas():
    """Generate document schemas and verify count."""
    registry, _ = _build_full_registry()
    tmpdir = Path(tempfile.mkdtemp(prefix="gs_test_"))
    try:
        generate_document_schemas(tmpdir, registry)
        files = sorted(tmpdir.glob("*.json"))
        file_hashes = {f.name: hash_file(f) for f in files}
        return {
            "file_count": len(files),
            "file_hashes": file_hashes,
        }
    finally:
        shutil.rmtree(tmpdir)


def test_generate_catalog():
    """Generate catalog and verify structure."""
    registry, _ = _build_full_registry()
    tmpdir = Path(tempfile.mkdtemp(prefix="gs_test_"))
    try:
        generate_catalog(tmpdir, registry)
        cat_file = tmpdir / "catalog.json"
        with open(cat_file, encoding="utf-8") as f:
            catalog = json.load(f)
        return {
            "file_hash": hash_file(cat_file),
            "entry_count": len(catalog),
        }
    finally:
        shutil.rmtree(tmpdir)


def test_full_pipeline():
    """Run the full pipeline and capture checksums of all output files.

    This is the golden test: any change that alters schema output will
    show up as a hash difference here.
    """
    registry, all_rows = _build_full_registry()
    tmpdir = Path(tempfile.mkdtemp(prefix="gs_test_"))
    output_dir = tmpdir / "schemas"
    try:
        generate_unqualified_data_types(output_dir / "common")
        generate_qualified_data_types(output_dir / "common", all_rows)
        generate_common_basic_components(output_dir / "common", registry)
        generate_common_aggregate_components(output_dir / "common", registry)
        generate_common_extension_components(output_dir / "common", registry)
        generate_signature_schemas(output_dir / "common", registry)
        generate_document_schemas(output_dir / "maindoc", registry)
        generate_catalog(output_dir, registry)

        tree = collect_tree(output_dir)
        return {
            "file_count": len(tree),
            "tree": tree,
        }
    finally:
        shutil.rmtree(tmpdir)


# ── Encoding verification test ────────────────────────────────────────────

def test_output_files_are_utf8():
    """Verify all generated files are valid UTF-8 with no BOM."""
    registry, all_rows = _build_full_registry()
    tmpdir = Path(tempfile.mkdtemp(prefix="gs_test_"))
    output_dir = tmpdir / "schemas"
    try:
        generate_unqualified_data_types(output_dir / "common")
        generate_qualified_data_types(output_dir / "common", all_rows)
        generate_common_basic_components(output_dir / "common", registry)
        generate_common_aggregate_components(output_dir / "common", registry)
        generate_common_extension_components(output_dir / "common", registry)
        generate_signature_schemas(output_dir / "common", registry)
        generate_document_schemas(output_dir / "maindoc", registry)
        generate_catalog(output_dir, registry)

        issues = []
        for dirpath, _, filenames in os.walk(output_dir):
            for fn in filenames:
                full = Path(dirpath) / fn
                raw = full.read_bytes()
                # Check for BOM
                if raw.startswith(b"\xef\xbb\xbf"):
                    issues.append(f"{fn}: has UTF-8 BOM")
                # Check valid UTF-8
                try:
                    raw.decode("utf-8")
                except UnicodeDecodeError as e:
                    issues.append(f"{fn}: invalid UTF-8: {e}")
                # Check ends with newline
                if not raw.endswith(b"\n"):
                    issues.append(f"{fn}: missing trailing newline")

        return {"issues": issues, "all_valid": len(issues) == 0}
    finally:
        shutil.rmtree(tmpdir)


# ── Runner ────────────────────────────────────────────────────────────────

ALL_TESTS = [
    ("constants", test_constants),
    ("parse_gc_file", test_parse_gc_file),
    ("build_registry", test_build_registry),
    ("generate_udt", test_generate_unqualified_data_types),
    ("generate_qdt", test_generate_qualified_data_types),
    ("generate_cbc", test_generate_cbc),
    ("generate_cac", test_generate_cac),
    ("generate_ext", test_generate_extension_components),
    ("generate_sig", test_generate_signature_schemas),
    ("generate_docs", test_generate_document_schemas),
    ("generate_catalog", test_generate_catalog),
    ("full_pipeline", test_full_pipeline),
    ("output_utf8", test_output_files_are_utf8),
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
                        if isinstance(bv, dict) and isinstance(av, dict):
                            # One more level for nested dicts (e.g., tree hashes)
                            for ssk in sorted(set(bv.keys()) | set(av.keys())):
                                if bv.get(ssk) != av.get(ssk):
                                    diffs.append(f"    {sk}.{ssk} differs")
                        else:
                            diffs.append(f"    sub-key '{sk}': {repr(bv)[:80]} -> {repr(av)[:80]}")

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
        print("Running generate_json_schemas tests...")
        _, failed = run_all(snapshot)
        sys.exit(failed)
