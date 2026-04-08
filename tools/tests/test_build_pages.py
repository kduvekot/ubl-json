#!/usr/bin/env python3
"""Tests for build_pages.py — captures output for before/after comparison."""

import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

# Ensure the tools package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tools.build_pages import (
    preview_slug,
    load_branches,
    save_branches,
    generate_banner_html,
    generate_branch_banner_html,
    inject_banner,
    generate_directory_index,
    generate_branches_index,
    generate_branch_preview_page,
    generate_schema_listing,
)


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


class TestContext:
    """Sets up a realistic temp directory structure for testing."""

    def __init__(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="bp_test_"))
        self.pages_dir = self.tmpdir / "gh-pages"
        self.pages_dir.mkdir()

        # Create a minimal spec HTML file
        self.spec_html = self.tmpdir / "spec.html"
        self.spec_html.write_text(
            '<!DOCTYPE html><html><head><meta charset="UTF-8"></head>'
            "<body><h1>UBL 2.5 JSON Syntax Binding</h1></body></html>\n",
            encoding="utf-8",
        )

        # Create schemas directory with some dummy files
        self.schemas_dir = self.tmpdir / "schemas"
        (self.schemas_dir / "common").mkdir(parents=True)
        (self.schemas_dir / "maindoc").mkdir(parents=True)
        (self.schemas_dir / "common" / "UDT-2.5.json").write_text('{"test": true}\n')
        (self.schemas_dir / "maindoc" / "UBL-Invoice-2.5.json").write_text(
            '{"invoice": true}\n'
        )

        # Create examples directory
        self.examples_dir = self.tmpdir / "examples"
        self.examples_dir.mkdir()
        (self.examples_dir / "sample.json").write_text('{"example": true}\n')

    def cleanup(self):
        shutil.rmtree(self.tmpdir)


# ── Unit tests ────────────────────────────────────────────────────────────

def test_preview_slug():
    results = {}
    # Claude branch with session code
    results["claude_branch"] = preview_slug("claude/my-feature-zWMqu", "abc1234def5678")
    # Regular branch
    results["regular_branch"] = preview_slug("feature/my-branch", "abc1234def5678")
    # Claude branch without valid code
    results["claude_no_code"] = preview_slug("claude/short", "abc1234def5678")
    # Edge case: exact 5-char suffix
    results["claude_exact"] = preview_slug("claude/x-AbCdE", "1234567890abcdef")
    return results


def test_load_save_branches():
    ctx = TestContext()
    try:
        # Load from empty (no file yet)
        data = load_branches(ctx.pages_dir)
        assert data == {"branches": {}}, f"Expected empty branches, got {data}"

        # Save and reload
        data["branches"]["test/branch"] = {
            "sha": "abc1234",
            "slug": "abc12",
            "updated": "2025-01-01T00:00:00+00:00",
        }
        save_branches(ctx.pages_dir, data)

        reloaded = load_branches(ctx.pages_dir)
        assert reloaded == data, f"Round-trip failed: {reloaded} != {data}"

        # Return the saved JSON content for comparison
        return (ctx.pages_dir / "branches.json").read_text(encoding="utf-8")
    finally:
        ctx.cleanup()


def test_generate_banner_html():
    results = {}
    # Empty branches
    results["empty"] = generate_banner_html({"branches": {}}, "owner/repo")
    # With branches
    results["with_branches"] = generate_banner_html(
        {"branches": {"a": {}, "b": {}, "c": {}}}, "owner/repo"
    )
    # Repo with special chars
    results["special_repo"] = generate_banner_html(
        {"branches": {}}, "owner/<script>alert(1)</script>"
    )
    return results


def test_generate_branch_banner_html():
    results = {}
    results["basic"] = generate_branch_banner_html(
        "feature/test", "abc1234def", "owner/repo"
    )
    results["with_pr"] = generate_branch_banner_html(
        "feature/test", "abc1234def", "owner/repo", pr_num=42
    )
    results["with_all"] = generate_branch_banner_html(
        "feature/test", "abc1234def", "owner/repo", pr_num=42, run_id="12345"
    )
    results["xss_branch"] = generate_branch_banner_html(
        '<img onerror="alert(1)">', "abc1234def", "owner/repo"
    )
    return results


def test_inject_banner():
    ctx = TestContext()
    try:
        results = {}
        # First injection
        banner = generate_banner_html({"branches": {}}, "owner/repo")
        inject_banner(ctx.spec_html, banner)
        results["first_inject"] = ctx.spec_html.read_text(encoding="utf-8")

        # Re-injection (should replace, not duplicate)
        banner2 = generate_banner_html(
            {"branches": {"a": {}}}, "owner/repo"
        )
        inject_banner(ctx.spec_html, banner2)
        results["re_inject"] = ctx.spec_html.read_text(encoding="utf-8")

        # Count banners — should be exactly 1
        content = results["re_inject"]
        banner_count = content.count("<!-- UBL JSON Pages Banner -->")
        results["banner_count_after_reinject"] = banner_count
        assert banner_count == 1, f"Expected 1 banner, found {banner_count}"

        return results
    finally:
        ctx.cleanup()


def test_generate_directory_index():
    ctx = TestContext()
    try:
        generate_directory_index(ctx.schemas_dir / "common", "Common Schemas")
        content = (ctx.schemas_dir / "common" / "index.html").read_text(encoding="utf-8")
        return content
    finally:
        ctx.cleanup()


def test_generate_branches_index():
    ctx = TestContext()
    try:
        # Save some branches first
        data = {
            "branches": {
                "feature/one": {
                    "sha": "aaa1111bbb2222",
                    "slug": "aaa11",
                    "updated": "2025-06-01T10:00:00+00:00",
                    "pr": 10,
                    "run_id": "99999",
                },
                "claude/test-xYzAb": {
                    "sha": "ccc3333ddd4444",
                    "slug": "xYzAb",
                    "updated": "2025-06-02T12:00:00+00:00",
                    "pr": None,
                    "run_id": None,
                },
            }
        }
        save_branches(ctx.pages_dir, data)
        generate_branches_index(ctx.pages_dir, "owner/repo")
        content = (ctx.pages_dir / "branches" / "index.html").read_text(encoding="utf-8")
        return content
    finally:
        ctx.cleanup()


def test_generate_schema_listing():
    ctx = TestContext()
    try:
        result = generate_schema_listing(ctx.schemas_dir)
        return result
    finally:
        ctx.cleanup()


def test_deploy_main_e2e():
    """End-to-end test of deploy-main command."""
    ctx = TestContext()
    try:
        # Simulate argparse namespace
        class Args:
            pages_dir = str(ctx.pages_dir)
            spec_html = str(ctx.spec_html)
            schemas_dir = str(ctx.schemas_dir)
            examples_dir = str(ctx.examples_dir)
            repo = "owner/repo"

        from tools.build_pages import cmd_deploy_main

        cmd_deploy_main(Args())
        tree = collect_tree(ctx.pages_dir)
        contents = {}
        for rel_path in tree:
            full = ctx.pages_dir / rel_path
            contents[rel_path] = full.read_text(encoding="utf-8")
        return {"tree": tree, "contents": contents}
    finally:
        ctx.cleanup()


def test_deploy_branch_e2e():
    """End-to-end test of deploy-branch command."""
    ctx = TestContext()
    try:
        class Args:
            pages_dir = str(ctx.pages_dir)
            spec_html = str(ctx.spec_html)
            schemas_dir = str(ctx.schemas_dir)
            examples_dir = str(ctx.examples_dir)
            branch = "claude/my-feature-zWMqu"
            sha = "abc1234def5678901234567890abcdef12345678"
            repo = "owner/repo"
            pr = "42"
            run_id = "9876543"

        from tools.build_pages import cmd_deploy_branch

        cmd_deploy_branch(Args())
        tree = collect_tree(ctx.pages_dir)
        contents = {}
        for rel_path in tree:
            full = ctx.pages_dir / rel_path
            contents[rel_path] = full.read_text(encoding="utf-8")
        return {"tree": tree, "contents": contents}
    finally:
        ctx.cleanup()


def test_cleanup_branch_e2e():
    """End-to-end test of cleanup-branch after deploy-branch."""
    ctx = TestContext()
    try:
        # First deploy a branch
        class DeployArgs:
            pages_dir = str(ctx.pages_dir)
            spec_html = str(ctx.spec_html)
            schemas_dir = str(ctx.schemas_dir)
            examples_dir = str(ctx.examples_dir)
            branch = "feature/test"
            sha = "deadbeef12345678"
            repo = "owner/repo"
            pr = None
            run_id = None

        from tools.build_pages import cmd_deploy_branch, cmd_cleanup_branch

        cmd_deploy_branch(DeployArgs())
        tree_before = collect_tree(ctx.pages_dir)

        # Now clean up
        class CleanupArgs:
            pages_dir = str(ctx.pages_dir)
            branch = "feature/test"
            repo = "owner/repo"

        cmd_cleanup_branch(CleanupArgs())
        tree_after = collect_tree(ctx.pages_dir)

        contents_after = {}
        for rel_path in tree_after:
            full = ctx.pages_dir / rel_path
            contents_after[rel_path] = full.read_text(encoding="utf-8")

        return {
            "tree_before": tree_before,
            "tree_after": tree_after,
            "contents_after": contents_after,
        }
    finally:
        ctx.cleanup()


# ── Runner ────────────────────────────────────────────────────────────────

ALL_TESTS = [
    ("preview_slug", test_preview_slug),
    ("load_save_branches", test_load_save_branches),
    ("generate_banner_html", test_generate_banner_html),
    ("generate_branch_banner_html", test_generate_branch_banner_html),
    ("inject_banner", test_inject_banner),
    ("generate_directory_index", test_generate_directory_index),
    ("generate_branches_index", test_generate_branches_index),
    ("generate_schema_listing", test_generate_schema_listing),
    ("deploy_main_e2e", test_deploy_main_e2e),
    ("deploy_branch_e2e", test_deploy_branch_e2e),
    ("cleanup_branch_e2e", test_cleanup_branch_e2e),
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
            # For nested dicts, show which sub-keys changed
            if isinstance(before[key], dict) and isinstance(after[key], dict):
                for sk in sorted(set(before[key].keys()) | set(after[key].keys())):
                    bv = before[key].get(sk)
                    av = after[key].get(sk)
                    if bv != av:
                        diffs.append(f"    sub-key '{sk}' differs")

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
        print("Running build_pages tests...")
        _, failed = run_all(snapshot)
        sys.exit(failed)
