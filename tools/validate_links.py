#!/usr/bin/env python3
"""Validate that relative links in the spec HTML resolve to files on disk.

Scans the spec HTML (index.html) in a pages directory for <a href="...">
links and verifies that relative URLs point to existing files. Absolute
URLs (http/https) and fragment-only links (#...) are skipped.

Usage:
    python tools/validate_links.py <pages-dir> [--subdir <preview-slug>]

Prints warnings for broken links but never fails the build.
"""

import argparse
import re
import sys
from pathlib import Path


def find_relative_links(html_path: Path) -> list[str]:
    """Extract relative href/src URLs from an HTML file."""
    content = html_path.read_text(encoding="utf-8")
    urls: list[str] = []
    for match in re.finditer(r'(?:href|src)="([^"]*)"', content):
        url = match.group(1)
        # Skip absolute URLs, fragments, data URIs, and template entities
        if (url.startswith(("http://", "https://", "#", "data:", "mailto:"))
                or "&" in url):  # unresolved XML entities like &this-loc;
            continue
        # Strip fragment
        url = url.split("#")[0]
        if url:
            urls.append(url)
    return urls


def validate(pages_dir: Path, subdir: str | None = None) -> list[str]:
    """Return list of broken relative links."""
    if subdir:
        base = pages_dir / subdir
    else:
        base = pages_dir

    index = base / "index.html"
    if not index.exists():
        print(f"ERROR: {index} not found", file=sys.stderr)
        sys.exit(2)

    links = find_relative_links(index)
    broken = []
    seen = set()

    for link in links:
        if link in seen:
            continue
        seen.add(link)
        target = base / link
        if not target.exists():
            broken.append(link)

    return broken


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pages_dir", type=Path, help="Root of the gh-pages directory")
    parser.add_argument("--subdir", help="Preview subdirectory to validate (e.g. slug)")
    args = parser.parse_args()

    broken = validate(args.pages_dir, args.subdir)

    if broken:
        print(f"::warning::Link validation: {len(broken)} broken relative link(s)")
        for link in sorted(broken):
            print(f"  BROKEN: {link}")
    else:
        print(f"OK: all relative links resolve")


if __name__ == "__main__":
    main()
