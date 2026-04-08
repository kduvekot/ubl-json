#!/usr/bin/env python3
"""Tests for validate_links.py — captures output for before/after comparison."""

import json
import shutil
import socket
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import urllib.error

# Ensure the tools package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tools.validate_links import find_links, check_relative, check_external, _is_private_url


class TestContext:
    """Sets up a temp directory with HTML and files for testing."""

    def __init__(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="vl_test_"))
        self.pages_dir = self.tmpdir / "pages"
        self.pages_dir.mkdir()

    def write_html(self, filename, content):
        path = self.pages_dir / filename
        path.write_text(content, encoding="utf-8")
        return path

    def write_file(self, relpath, content="dummy"):
        path = self.pages_dir / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def cleanup(self):
        shutil.rmtree(self.tmpdir)


# ── find_links tests ─────────────────────────────────────────────────────

def test_find_links_basic():
    """Basic link extraction: relative and external."""
    ctx = TestContext()
    try:
        html_path = ctx.write_html("index.html", """
<!DOCTYPE html>
<html><head></head><body>
<a href="json/schemas/common/">Common Schemas</a>
<a href="https://github.com/owner/repo">GitHub</a>
<a href="https://example.com/page">Example</a>
<a href="other.html">Other</a>
</body></html>
""")
        relative, external = find_links(html_path)
        return {"relative": sorted(relative), "external": sorted(external)}
    finally:
        ctx.cleanup()


def test_find_links_skips():
    """Should skip fragments, data URIs, mailto, unresolved entities, and schema identifiers."""
    ctx = TestContext()
    try:
        html_path = ctx.write_html("index.html", """
<a href="#section1">Fragment</a>
<a href="data:text/html,hello">Data URI</a>
<a href="mailto:test@example.com">Email</a>
<a href="https://docs.oasis-open.org/ubl/2/json/schemas/UBL-Invoice-2">Schema ID</a>
<a href="page.html?foo=1&amp;bar=2">Entity in URL</a>
<a href="https://unece.org/some-page">UNECE</a>
<a href="https://real-site.com/page">Real</a>
""")
        relative, external = find_links(html_path)
        return {"relative": sorted(relative), "external": sorted(external)}
    finally:
        ctx.cleanup()


def test_find_links_fragment_strip():
    """Relative links should have fragments stripped."""
    ctx = TestContext()
    try:
        html_path = ctx.write_html("index.html", """
<a href="page.html#anchor">Link</a>
<a href="dir/file.json#/defs/Foo">JSON pointer</a>
""")
        relative, external = find_links(html_path)
        return {"relative": sorted(relative), "external": sorted(external)}
    finally:
        ctx.cleanup()


def test_find_links_src_attribute():
    """Should also extract src= attributes (images, scripts)."""
    ctx = TestContext()
    try:
        html_path = ctx.write_html("index.html", """
<img src="images/logo.png">
<script src="https://cdn.example.com/lib.js"></script>
""")
        relative, external = find_links(html_path)
        return {"relative": sorted(relative), "external": sorted(external)}
    finally:
        ctx.cleanup()


# ── check_relative tests ─────────────────────────────────────────────────

def test_check_relative_all_exist():
    """All relative links resolve — no broken links."""
    ctx = TestContext()
    try:
        ctx.write_file("page.html")
        ctx.write_file("json/schemas/common/UDT.json")
        links = ["page.html", "json/schemas/common/UDT.json"]
        broken = check_relative(ctx.pages_dir, links)
        return {"broken": broken}
    finally:
        ctx.cleanup()


def test_check_relative_some_missing():
    """Some links don't resolve."""
    ctx = TestContext()
    try:
        ctx.write_file("exists.html")
        links = ["exists.html", "missing.html", "also/missing.json"]
        broken = check_relative(ctx.pages_dir, links)
        return {"broken": sorted(broken)}
    finally:
        ctx.cleanup()


def test_check_relative_deduplication():
    """Duplicate links should only be checked once."""
    ctx = TestContext()
    try:
        links = ["missing.html", "missing.html", "missing.html"]
        broken = check_relative(ctx.pages_dir, links)
        return {"broken": broken, "count": len(broken)}
    finally:
        ctx.cleanup()


# ── check_external tests (mocked) ────────────────────────────────────────

def test_check_external_all_ok():
    """All external URLs return 200."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    with patch("tools.validate_links._is_private_url", return_value=False), \
         patch("tools.validate_links.urllib.request.urlopen", return_value=mock_resp):
        broken = check_external(["https://example.com", "https://other.com"])
    return {"broken": broken}


def test_check_external_head_fails_get_succeeds():
    """HEAD returns 405, GET fallback succeeds."""
    call_count = [0]

    def mock_urlopen(req, timeout=None):
        call_count[0] += 1
        if req.get_method() == "HEAD":
            raise urllib.error.HTTPError(
                req.full_url, 405, "Method Not Allowed", {}, None
            )
        resp = MagicMock()
        resp.status = 200
        return resp

    with patch("tools.validate_links._is_private_url", return_value=False), \
         patch("tools.validate_links.urllib.request.urlopen", side_effect=mock_urlopen):
        broken = check_external(["https://head-reject.com"])
    return {"broken": broken, "calls": call_count[0]}


def test_check_external_both_fail():
    """Both HEAD and GET fail."""
    def mock_urlopen(req, timeout=None):
        raise urllib.error.URLError("Connection refused")

    with patch("tools.validate_links._is_private_url", return_value=False), \
         patch("tools.validate_links.urllib.request.urlopen", side_effect=mock_urlopen):
        broken = check_external(["https://down.com"])
    return {"broken": [(u, r) for u, r in broken]}


def test_check_external_deduplication():
    """Duplicate URLs should only be checked once."""
    call_count = [0]

    def mock_urlopen(req, timeout=None):
        call_count[0] += 1
        resp = MagicMock()
        resp.status = 200
        return resp

    with patch("tools.validate_links._is_private_url", return_value=False), \
         patch("tools.validate_links.urllib.request.urlopen", side_effect=mock_urlopen):
        broken = check_external([
            "https://example.com",
            "https://example.com",
            "https://example.com",
        ])
    return {"broken": broken, "calls": call_count[0]}


# ── SSRF protection tests ────────────────────────────────────────────────

def test_is_private_url_ip_literals():
    """_is_private_url should detect private IP addresses in URLs."""
    # Map of URL -> whether getaddrinfo should be called (IP literals resolve directly)
    test_cases = {
        "http://127.0.0.1:8080/admin": True,
        "http://[::1]/secret": True,
        "http://10.0.0.1/internal": True,
        "http://172.16.0.1/internal": True,
        "http://192.168.1.1/router": True,
        "http://169.254.169.254/latest/meta-data/": True,
    }
    results = {}
    for url, expected in test_cases.items():
        # Mock getaddrinfo to return the IP from the URL itself
        from urllib.parse import urlparse
        parsed = urlparse(url)
        hostname = parsed.hostname
        port = parsed.port or 80

        def make_mock_gai(h, p):
            def mock_gai(host, port_arg, proto=None):
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (h, p))]
            return mock_gai

        with patch("tools.validate_links.socket.getaddrinfo", side_effect=make_mock_gai(hostname, port)):
            result = _is_private_url(url)
        results[url] = {"is_private": result, "expected": expected}
    return results


def test_is_private_url_blocked_hosts():
    """_is_private_url should block well-known metadata hostnames."""
    results = {}
    for url in [
        "http://metadata.google.internal/",
        "http://metadata.internal/something",
    ]:
        results[url] = _is_private_url(url)
    return results


def test_check_external_private_ips():
    """URLs pointing to private/internal IPs should be blocked."""
    private_urls = [
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/",
        "http://127.0.0.1:8080/admin",
        "http://[::1]/secret",
        "http://10.0.0.1/internal",
        "http://172.16.0.1/internal",
        "http://192.168.1.1/router",
    ]

    # Mock urlopen so we can see which URLs were attempted
    attempted = []

    def mock_urlopen(req, timeout=None):
        attempted.append(req.full_url)
        resp = MagicMock()
        resp.status = 200
        return resp

    # _is_private_url returns True for all these → urlopen should never be called
    with patch("tools.validate_links._is_private_url", return_value=True), \
         patch("tools.validate_links.urllib.request.urlopen", side_effect=mock_urlopen):
        broken = check_external(private_urls)

    return {
        "attempted_count": len(attempted),
        "attempted": attempted,
        "broken": [(u, r) for u, r in broken],
        "all_blocked": len(attempted) == 0,
    }


def test_check_external_public_urls_allowed():
    """Public URLs should still be checked normally."""
    public_urls = [
        "https://github.com/owner/repo",
        "https://www.oasis-open.org/committees/ubl/",
    ]

    mock_resp = MagicMock()
    mock_resp.status = 200
    with patch("tools.validate_links._is_private_url", return_value=False), \
         patch("tools.validate_links.urllib.request.urlopen", return_value=mock_resp):
        broken = check_external(public_urls)
    return {"broken": broken}


# ── main() integration test ──────────────────────────────────────────────

def test_main_integration():
    """End-to-end test of main() with mocked external checks."""
    ctx = TestContext()
    try:
        ctx.write_html("index.html", """
<!DOCTYPE html>
<html><head></head><body>
<a href="exists.html">Good</a>
<a href="missing.html">Bad</a>
<a href="https://github.com/oasis-tcs/ubl">GitHub</a>
</body></html>
""")
        ctx.write_file("exists.html")

        # Capture stdout
        import io
        from contextlib import redirect_stdout

        mock_resp = MagicMock()
        mock_resp.status = 200

        with patch("tools.validate_links._is_private_url", return_value=False), \
             patch("tools.validate_links.urllib.request.urlopen", return_value=mock_resp), \
             patch("sys.argv", ["validate_links.py", str(ctx.pages_dir)]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                from tools.validate_links import main
                main()
            output = buf.getvalue()

        return {"output": output}
    finally:
        ctx.cleanup()


# ── Runner ────────────────────────────────────────────────────────────────

ALL_TESTS = [
    ("find_links_basic", test_find_links_basic),
    ("find_links_skips", test_find_links_skips),
    ("find_links_fragment_strip", test_find_links_fragment_strip),
    ("find_links_src_attribute", test_find_links_src_attribute),
    ("check_relative_all_exist", test_check_relative_all_exist),
    ("check_relative_some_missing", test_check_relative_some_missing),
    ("check_relative_deduplication", test_check_relative_deduplication),
    ("check_external_all_ok", test_check_external_all_ok),
    ("check_external_head_fails_get_succeeds", test_check_external_head_fails_get_succeeds),
    ("check_external_both_fail", test_check_external_both_fail),
    ("check_external_deduplication", test_check_external_deduplication),
    ("is_private_url_ip_literals", test_is_private_url_ip_literals),
    ("is_private_url_blocked_hosts", test_is_private_url_blocked_hosts),
    ("check_external_private_ips", test_check_external_private_ips),
    ("check_external_public_urls_allowed", test_check_external_public_urls_allowed),
    ("main_integration", test_main_integration),
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
            if isinstance(before[key], dict) and isinstance(after[key], dict):
                for sk in sorted(set(before[key].keys()) | set(after[key].keys())):
                    bv = before[key].get(sk)
                    av = after[key].get(sk)
                    if bv != av:
                        diffs.append(f"    sub-key '{sk}': {bv!r} -> {av!r}")

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
        print("Running validate_links tests...")
        _, failed = run_all(snapshot)
        sys.exit(failed)
