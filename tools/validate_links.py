#!/usr/bin/env python3
"""Validate that links in the spec HTML resolve correctly.

Checks two categories:
  1. Relative links — must resolve to files in the pages directory.
  2. External URLs — HTTP HEAD request to verify they're reachable.

Schema identifier URLs (docs.oasis-open.org/ubl/2/json/schemas/) are
skipped — they are identifiers, not meant to resolve to a web page.

Usage:
    python tools/validate_links.py <pages-dir> [--subdir <preview-slug>]

Prints warnings for broken links but never fails the build.
"""

import argparse
import ipaddress
import re
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path

# URLs to skip: schema identifiers (not meant to resolve) and sites
# that block CI/cloud requests (verified manually to be reachable).
SKIP_PATTERNS = [
    "docs.oasis-open.org/ubl/2/json/schemas/",
    "unece.org/",
]

TIMEOUT = 10  # seconds per request
MAX_GET_BYTES = 8192  # only read this many bytes on GET fallback


def _is_private_url(url: str) -> bool:
    """Return True if *url* targets a private, loopback, or link-local address.

    Resolves the hostname to IP addresses and rejects any that fall within
    non-public ranges.  This prevents SSRF attacks against cloud metadata
    endpoints (169.254.x.x), localhost, and RFC 1918 networks.
    """
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return True  # no host → reject

        # Reject well-known cloud metadata hostnames regardless of DNS
        _BLOCKED_HOSTS = {
            "metadata.google.internal",
            "metadata.internal",
        }
        if hostname.lower() in _BLOCKED_HOSTS:
            return True

        # Resolve and check every address the hostname points to
        for info in socket.getaddrinfo(hostname, parsed.port or 80,
                                       proto=socket.IPPROTO_TCP):
            addr = info[4][0]
            ip = ipaddress.ip_address(addr)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return True
    except (socket.gaierror, ValueError):
        return True  # unresolvable → skip rather than risk connecting

    return False


def find_links(html_path: Path) -> tuple[list[str], list[str]]:
    """Extract links from an HTML file.

    Returns (relative_links, external_urls).
    """
    content = html_path.read_text(encoding="utf-8")
    relative: list[str] = []
    external: list[str] = []

    for match in re.finditer(r'(?:href|src)="([^"]*)"', content):
        url = match.group(1)

        # Skip fragments, data URIs, and unresolved XML entities
        if url.startswith(("#", "data:", "mailto:")) or "&" in url:
            continue

        if url.startswith(("http://", "https://")):
            # Skip schema identifiers
            if any(pat in url for pat in SKIP_PATTERNS):
                continue
            external.append(url)
        else:
            # Strip fragment from relative link
            url = url.split("#")[0]
            if url:
                relative.append(url)

    return relative, external


def check_relative(base: Path, links: list[str]) -> list[str]:
    """Return broken relative links."""
    broken = []
    seen = set()
    for link in links:
        if link in seen:
            continue
        seen.add(link)
        if not (base / link).exists():
            broken.append(link)
    return broken


def check_external(urls: list[str]) -> list[tuple[str, str]]:
    """Return list of (url, reason) for unreachable external URLs.

    Skips URLs that resolve to private/loopback/link-local addresses to
    prevent SSRF.  Falls back from HEAD to a size-limited GET when servers
    reject HEAD requests.
    """
    broken = []
    seen = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)

        # SSRF protection: reject URLs targeting internal networks
        if _is_private_url(url):
            broken.append((url, "blocked (private/internal address)"))
            continue

        try:
            req = urllib.request.Request(url, method="HEAD",
                                        headers={"User-Agent": "UBL-LinkCheck/1.0"})
            resp = urllib.request.urlopen(req, timeout=TIMEOUT)
            if resp.status >= 400:
                broken.append((url, f"HTTP {resp.status}"))
        except urllib.error.HTTPError:
            # Some servers reject HEAD — try GET with a size limit
            try:
                req = urllib.request.Request(url, method="GET",
                                            headers={"User-Agent": "UBL-LinkCheck/1.0"})
                resp = urllib.request.urlopen(req, timeout=TIMEOUT)
                resp.read(MAX_GET_BYTES)  # read limited bytes then discard
                if resp.status >= 400:
                    broken.append((url, f"HTTP {resp.status}"))
            except Exception as e2:
                broken.append((url, str(e2)))
        except Exception as e:
            broken.append((url, str(e)))
    return broken


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pages_dir", type=Path, help="Root of the gh-pages directory")
    parser.add_argument("--subdir", help="Preview subdirectory to validate")
    args = parser.parse_args()

    base = args.pages_dir / args.subdir if args.subdir else args.pages_dir
    index = base / "index.html"
    if not index.exists():
        print(f"ERROR: {index} not found", file=sys.stderr)
        sys.exit(2)

    relative, external = find_links(index)

    # Check relative links
    broken_rel = check_relative(base, relative)
    if broken_rel:
        print(f"::warning::Link validation: {len(broken_rel)} broken relative link(s)")
        for link in sorted(broken_rel):
            print(f"  BROKEN (relative): {link}")

    # Check external URLs
    broken_ext = check_external(external)
    if broken_ext:
        print(f"::warning::Link validation: {len(broken_ext)} unreachable external URL(s)")
        for url, reason in sorted(broken_ext):
            print(f"  BROKEN (external): {url} — {reason}")

    if not broken_rel and not broken_ext:
        n_rel = len(set(relative))
        n_ext = len(set(external))
        print(f"OK: {n_rel} relative + {n_ext} external links all valid")


if __name__ == "__main__":
    main()
