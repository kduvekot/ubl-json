#!/usr/bin/env python3
"""Build GitHub Pages content for UBL JSON Schema project.

This script manages the gh-pages directory structure:

    /index.html              ← spec document with banner (main branch)
    /json/schemas/           ← JSON schemas (main branch, matches spec links)
    /branches.json           ← metadata for active branch previews
    /branches/index.html     ← human-readable branch index
    /<short-sha>/            ← branch preview directory
        index.html           ← spec document with branch preview banner
        json/schemas/        ← generated schemas (relative links from spec work)

Usage:
    # Deploy main branch (spec + schemas)
    python build_pages.py deploy-main \\
        --pages-dir ./gh-pages \\
        --spec-html UBL-2.5-JSON-Syntax-Binding.html \\
        --schemas-dir json/schemas

    # Deploy branch preview (spec + schemas)
    python build_pages.py deploy-branch \\
        --pages-dir ./gh-pages \\
        --spec-html UBL-2.5-JSON-Syntax-Binding.html \\
        --schemas-dir json/schemas \\
        --branch feature/my-branch \\
        --sha abc1234def \\
        --pr 42 \\
        --run-id 12345678 \\
        --repo owner/repo

    # Clean up branch preview
    python build_pages.py cleanup-branch \\
        --pages-dir ./gh-pages \\
        --branch feature/my-branch
"""

import argparse
import html
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


BRANCHES_JSON = "branches.json"
REPO_URL_TEMPLATE = "https://github.com/{repo}"
PAGES_URL_TEMPLATE = "https://{owner}.github.io/{repo_name}"


def load_branches(pages_dir: Path) -> dict:
    """Load branches.json or return empty structure."""
    path = pages_dir / BRANCHES_JSON
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"branches": {}}


def save_branches(pages_dir: Path, data: dict):
    """Write branches.json."""
    path = pages_dir / BRANCHES_JSON
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def generate_banner_html(branches_data: dict, repo: str) -> str:
    """Generate the banner HTML to inject at the top of the spec page."""
    branch_count = len(branches_data.get("branches", {}))
    badge = f' <span style="background:#e0a800;color:#000;padding:1px 8px;border-radius:10px;font-size:0.8em;">{branch_count}</span>' if branch_count > 0 else ""

    return f"""<!-- UBL JSON Pages Banner -->
<div id="ubl-pages-banner" style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;padding:12px 24px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:14px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;position:sticky;top:0;z-index:9999;box-shadow:0 2px 8px rgba(0,0,0,0.3);">
  <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
    <strong style="font-size:16px;">UBL 2.5 JSON</strong>
    <a href="json/schemas/common/" style="color:#6ec6ff;text-decoration:none;">Common Schemas</a>
    <a href="json/schemas/maindoc/" style="color:#6ec6ff;text-decoration:none;">Document Schemas</a>
    <a href="branches/index.html" style="color:#6ec6ff;text-decoration:none;">Active Branches{badge}</a>
  </div>
  <div style="display:flex;align-items:center;gap:12px;">
    <a href="https://github.com/{html.escape(repo)}" style="color:#aaa;text-decoration:none;font-size:12px;">GitHub</a>
  </div>
</div>
<!-- End UBL JSON Pages Banner -->
"""


def inject_banner(spec_html_path: Path, banner_html: str):
    """Inject the banner into the spec HTML after <body>."""
    with open(spec_html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove any existing banner
    import re
    content = re.sub(
        r"<!-- UBL JSON Pages Banner -->.*?<!-- End UBL JSON Pages Banner -->\n?",
        "",
        content,
        flags=re.DOTALL,
    )

    # Inject after <body...>
    body_match = re.search(r"(<body[^>]*>)", content, re.IGNORECASE)
    if body_match:
        insert_pos = body_match.end()
        content = content[:insert_pos] + "\n" + banner_html + content[insert_pos:]
    else:
        # Fallback: prepend
        content = banner_html + content

    with open(spec_html_path, "w", encoding="utf-8") as f:
        f.write(content)


def generate_branch_banner_html(
    branch_name: str,
    sha: str,
    repo: str,
    pr_num: int | None = None,
    run_id: str | None = None,
) -> str:
    """Generate the banner HTML for a branch preview page."""
    sha_short = sha[:7]
    commit_url = f"https://github.com/{html.escape(repo)}/commit/{sha}"
    pr_html = ""
    if pr_num:
        pr_url = f"https://github.com/{html.escape(repo)}/pull/{pr_num}"
        pr_html = f' &middot; <a href="{pr_url}" style="color:#fff;text-decoration:underline;">PR #{pr_num}</a>'
    artifact_html = ""
    if run_id:
        artifact_url = f"https://github.com/{html.escape(repo)}/actions/runs/{run_id}"
        artifact_html = f' &middot; <a href="{artifact_url}" style="color:#aaa;text-decoration:none;font-size:12px;">Artifacts</a>'

    return f"""<!-- UBL JSON Pages Banner -->
<div id="ubl-pages-banner" style="background:linear-gradient(135deg,#5c2d00,#8b4513);color:#fff;padding:12px 24px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:14px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;position:sticky;top:0;z-index:9999;box-shadow:0 2px 8px rgba(0,0,0,0.3);">
  <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
    <strong style="font-size:16px;">&#9888; Branch Preview</strong>
    <span style="color:#ffd799;">{html.escape(branch_name)}</span>
    <span style="color:#ccc;">@</span>
    <a href="{commit_url}" style="color:#6ec6ff;text-decoration:none;font-family:monospace;">{html.escape(sha_short)}</a>{pr_html}
  </div>
  <div style="display:flex;align-items:center;gap:12px;">
    <a href="json/schemas/common/" style="color:#6ec6ff;text-decoration:none;">Common Schemas</a>
    <a href="json/schemas/maindoc/" style="color:#6ec6ff;text-decoration:none;">Document Schemas</a>
    <a href="../branches/" style="color:#6ec6ff;text-decoration:none;">All Branches</a>
    <a href="../" style="color:#6ec6ff;text-decoration:none;">Main</a>{artifact_html}
  </div>
</div>
<!-- End UBL JSON Pages Banner -->
"""


def generate_schema_listing(schemas_dir: Path, path_prefix: str = "", url_prefix: str = "json/schemas/") -> str:
    """Generate HTML list of schemas from a directory."""
    common_dir = schemas_dir / "common"
    maindoc_dir = schemas_dir / "maindoc"

    lines = []

    if common_dir.is_dir():
        files = sorted(common_dir.glob("*.json"))
        if files:
            lines.append("<h3>Common Schemas</h3>")
            lines.append("<ul>")
            for f in files:
                name = f.stem
                url = f"{path_prefix}{url_prefix}common/{f.name}"
                lines.append(f'  <li><a href="{url}">{html.escape(name)}</a></li>')
            lines.append("</ul>")

    if maindoc_dir.is_dir():
        files = sorted(maindoc_dir.glob("*.json"))
        if files:
            lines.append(f"<h3>Document Schemas ({len(files)})</h3>")
            lines.append("<ul>")
            for f in files:
                name = f.stem
                url = f"{path_prefix}{url_prefix}maindoc/{f.name}"
                lines.append(f'  <li><a href="{url}">{html.escape(name)}</a></li>')
            lines.append("</ul>")

    return "\n".join(lines)


def generate_directory_index(dir_path: Path, title: str):
    """Generate a simple index.html for a directory listing its files."""
    entries = sorted(dir_path.iterdir())
    files = [e for e in entries if e.is_file() and e.name != "index.html"]
    dirs = [e for e in entries if e.is_dir()]

    items = []
    for d in dirs:
        items.append(f'  <li><a href="{d.name}/">{html.escape(d.name)}/</a></li>')
    for f in files:
        size = f.stat().st_size
        size_str = f"{size:,} bytes" if size < 10000 else f"{size / 1024:.1f} KB"
        items.append(f'  <li><a href="{f.name}">{html.escape(f.name)}</a> <span style="color:#888;font-size:0.9em;">({size_str})</span></li>')

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #333; }}
  a {{ color: #0366d6; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  ul {{ list-style: none; padding: 0; }}
  li {{ padding: 4px 0; }}
  li a {{ font-family: monospace; }}
</style>
</head>
<body>
<h1>{html.escape(title)}</h1>
<p><a href="../">&larr; Back</a></p>
<ul>
{"".join(items) if items else "  <li><em>No files</em></li>"}
</ul>
</body>
</html>
"""
    with open(dir_path / "index.html", "w", encoding="utf-8") as f:
        f.write(page_html)


def generate_branches_index(pages_dir: Path, repo: str):
    """Generate branches/index.html from branches.json."""
    branches_dir = pages_dir / "branches"
    branches_dir.mkdir(exist_ok=True)

    data = load_branches(pages_dir)
    branches = data.get("branches", {})

    owner, repo_name = repo.split("/", 1) if "/" in repo else ("", repo)
    pages_base = f"https://{owner}.github.io/{repo_name}" if owner else ""

    rows = []
    for branch_name, info in sorted(branches.items()):
        sha_short = info.get("sha", "")[:7]
        sha_full = info.get("sha", "")
        updated = info.get("updated", "")
        pr_num = info.get("pr")
        run_id = info.get("run_id")

        preview_url = f"../{sha_short}/"
        pr_link = f'<a href="https://github.com/{html.escape(repo)}/pull/{pr_num}">#{pr_num}</a>' if pr_num else "&mdash;"
        artifact_link = f'<a href="https://github.com/{html.escape(repo)}/actions/runs/{run_id}">Artifacts</a>' if run_id else "&mdash;"

        rows.append(f"""      <tr>
        <td><strong>{html.escape(branch_name)}</strong></td>
        <td><a href="{preview_url}"><code>{html.escape(sha_short)}</code></a></td>
        <td>{pr_link}</td>
        <td>{html.escape(updated[:16]) if updated else "&mdash;"}</td>
        <td><a href="{preview_url}">Preview</a></td>
        <td>{artifact_link}</td>
      </tr>""")

    no_branches = '<tr><td colspan="6" style="text-align:center;color:#888;padding:24px;">No active branch previews</td></tr>' if not rows else ""

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UBL 2.5 JSON &mdash; Active Branches</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1000px; margin: 40px auto; padding: 0 20px; color: #333; }}
  a {{ color: #0366d6; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
  th, td {{ border: 1px solid #ddd; padding: 10px 14px; text-align: left; }}
  th {{ background: #f6f8fa; font-weight: 600; }}
  tr:hover {{ background: #f9f9f9; }}
  code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
  .back {{ margin-bottom: 20px; }}
</style>
</head>
<body>
<p class="back"><a href="../">&larr; Back to Specification</a></p>
<h1>Active Branch Previews</h1>
<p>Each feature branch with an open pull request gets a preview deployment with generated JSON schemas.</p>

<table>
  <thead>
    <tr>
      <th>Branch</th>
      <th>Commit</th>
      <th>PR</th>
      <th>Updated</th>
      <th>Preview</th>
      <th>Artifacts</th>
    </tr>
  </thead>
  <tbody>
{chr(10).join(rows) if rows else no_branches}
  </tbody>
</table>

<p style="margin-top:24px;color:#888;font-size:0.85em;">
  This page is automatically updated by CI. Branch previews are removed when their pull request is closed.
</p>
</body>
</html>
"""
    with open(branches_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(page_html)


def generate_branch_preview_page(
    sha_dir: Path,
    branch_name: str,
    sha: str,
    repo: str,
    pr_num: int | None = None,
    run_id: str | None = None,
):
    """Generate the index.html for a branch preview directory (fallback when spec HTML unavailable)."""
    sha_short = sha[:7]
    schemas_path = sha_dir / "json" / "schemas"
    schema_listing = generate_schema_listing(schemas_path) if schemas_path.is_dir() else ""

    pr_link = f' &middot; <a href="https://github.com/{html.escape(repo)}/pull/{pr_num}">PR #{pr_num}</a>' if pr_num else ""
    artifact_link = f' &middot; <a href="https://github.com/{html.escape(repo)}/actions/runs/{run_id}">Download Artifacts</a>' if run_id else ""
    commit_link = f'<a href="https://github.com/{html.escape(repo)}/commit/{sha}"><code>{html.escape(sha_short)}</code></a>'

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UBL 2.5 JSON &mdash; Branch Preview: {html.escape(branch_name)}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #333; }}
  a {{ color: #0366d6; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  h1 {{ border-bottom: 2px solid #e1e4e8; padding-bottom: 8px; }}
  .meta {{ background: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 6px; padding: 16px; margin: 16px 0; font-size: 0.95em; }}
  .meta strong {{ color: #24292e; }}
  ul {{ list-style: none; padding: 0; }}
  li {{ padding: 3px 0; }}
  li a {{ font-family: monospace; }}
  h3 {{ margin-top: 24px; color: #24292e; }}
  .warning {{ background: #fff8c5; border: 1px solid #d4a72c; border-radius: 6px; padding: 12px 16px; margin: 16px 0; font-size: 0.9em; }}
</style>
</head>
<body>
<p><a href="../">&larr; Back to Specification</a> &middot; <a href="../branches/">All Branches</a></p>

<h1>Branch Preview: {html.escape(branch_name)}</h1>

<div class="warning">
  This is a <strong>preview</strong> of schemas generated from a feature branch. These are not yet merged into the main specification.
</div>

<div class="meta">
  <strong>Commit:</strong> {commit_link}{pr_link}{artifact_link}<br>
  <strong>Generated:</strong> {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
</div>

{schema_listing}

</body>
</html>
"""
    with open(sha_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(page_html)


def cmd_deploy_main(args):
    """Deploy main branch content to gh-pages root."""
    pages_dir = Path(args.pages_dir)
    pages_dir.mkdir(parents=True, exist_ok=True)

    # Ensure .nojekyll exists
    (pages_dir / ".nojekyll").touch()

    # Copy spec HTML as index.html
    if args.spec_html and os.path.isfile(args.spec_html):
        shutil.copy2(args.spec_html, pages_dir / "index.html")
        print(f"Copied spec HTML to {pages_dir / 'index.html'}")

    # Copy schemas to json/schemas/ (matches relative links in spec HTML)
    if args.schemas_dir and os.path.isdir(args.schemas_dir):
        dest = pages_dir / "json" / "schemas"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(args.schemas_dir, dest)
        print(f"Copied schemas to {dest}")

        # Generate directory index pages for schemas
        generate_directory_index(dest, "UBL 2.5 JSON Schemas")
        for subdir in dest.iterdir():
            if subdir.is_dir():
                generate_directory_index(subdir, f"UBL 2.5 JSON Schemas — {subdir.name}")

    # Inject banner into index.html
    index_html = pages_dir / "index.html"
    if index_html.exists():
        branches_data = load_branches(pages_dir)
        banner = generate_banner_html(branches_data, args.repo)
        inject_banner(index_html, banner)
        print("Injected navigation banner into index.html")

    # Rebuild branches index
    generate_branches_index(pages_dir, args.repo)
    print("Rebuilt branches index")


def cmd_deploy_branch(args):
    """Deploy branch preview to gh-pages."""
    pages_dir = Path(args.pages_dir)
    pages_dir.mkdir(parents=True, exist_ok=True)

    sha_short = args.sha[:7]
    branch_name = args.branch

    # Load current branches data
    data = load_branches(pages_dir)
    branches = data.setdefault("branches", {})

    # Clean up old deployment for this branch if SHA changed
    if branch_name in branches:
        old_sha = branches[branch_name].get("sha", "")[:7]
        if old_sha and old_sha != sha_short:
            old_dir = pages_dir / old_sha
            if old_dir.exists():
                shutil.rmtree(old_dir)
                print(f"Removed old deployment at {old_dir}")

    # Create new deployment directory
    sha_dir = pages_dir / sha_short
    sha_dir.mkdir(parents=True, exist_ok=True)

    pr_num = int(args.pr) if args.pr else None

    # Copy spec HTML as index.html (the main page for the preview)
    spec_html = getattr(args, "spec_html", None)
    if spec_html and os.path.isfile(spec_html):
        shutil.copy2(spec_html, sha_dir / "index.html")
        print(f"Copied spec HTML to {sha_dir / 'index.html'}")

        # Inject branch preview banner
        banner = generate_branch_banner_html(
            branch_name, args.sha, args.repo,
            pr_num=pr_num, run_id=args.run_id,
        )
        inject_banner(sha_dir / "index.html", banner)
        print("Injected branch preview banner into spec HTML")
    else:
        # Fallback: generate a simple preview page if spec HTML unavailable
        generate_branch_preview_page(
            sha_dir, branch_name, args.sha, args.repo,
            pr_num=pr_num, run_id=args.run_id,
        )
        print(f"Generated fallback preview page at {sha_dir / 'index.html'}")

    # Copy schemas to json/schemas/ (matches relative links in spec HTML)
    if args.schemas_dir and os.path.isdir(args.schemas_dir):
        dest = sha_dir / "json" / "schemas"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(args.schemas_dir, dest)
        print(f"Copied schemas to {dest}")

        # Generate directory index pages
        generate_directory_index(dest, f"Schemas — {branch_name}")
        for subdir in dest.iterdir():
            if subdir.is_dir():
                generate_directory_index(subdir, f"Schemas — {branch_name} — {subdir.name}")

    # Update branches.json
    branches[branch_name] = {
        "sha": args.sha,
        "updated": datetime.now(timezone.utc).isoformat(),
        "pr": pr_num,
        "run_id": args.run_id,
    }
    save_branches(pages_dir, data)
    print(f"Updated branches.json: {branch_name} → {sha_short}")

    # Rebuild branches index page
    generate_branches_index(pages_dir, args.repo)
    print("Rebuilt branches index")

    # Re-inject banner into main index.html (update branch count)
    index_html = pages_dir / "index.html"
    if index_html.exists():
        banner = generate_banner_html(data, args.repo)
        inject_banner(index_html, banner)
        print("Updated banner in index.html")


def cmd_cleanup_branch(args):
    """Remove a branch preview from gh-pages."""
    pages_dir = Path(args.pages_dir)
    branch_name = args.branch

    data = load_branches(pages_dir)
    branches = data.get("branches", {})

    if branch_name not in branches:
        print(f"Branch '{branch_name}' not found in branches.json, nothing to clean up")
        return

    # Remove deployment directory
    sha_short = branches[branch_name].get("sha", "")[:7]
    if sha_short:
        sha_dir = pages_dir / sha_short
        if sha_dir.exists():
            shutil.rmtree(sha_dir)
            print(f"Removed deployment directory {sha_dir}")

    # Remove from branches.json
    del branches[branch_name]
    save_branches(pages_dir, data)
    print(f"Removed '{branch_name}' from branches.json")

    # Rebuild branches index
    generate_branches_index(pages_dir, args.repo)
    print("Rebuilt branches index")

    # Re-inject banner into main index.html (update branch count)
    index_html = pages_dir / "index.html"
    if index_html.exists():
        banner = generate_banner_html(data, args.repo)
        inject_banner(index_html, banner)
        print("Updated banner in index.html")


def main():
    parser = argparse.ArgumentParser(description="Build GitHub Pages content for UBL JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # deploy-main
    p_main = subparsers.add_parser("deploy-main", help="Deploy main branch content")
    p_main.add_argument("--pages-dir", required=True, help="Path to gh-pages directory")
    p_main.add_argument("--spec-html", help="Path to generated spec HTML file")
    p_main.add_argument("--schemas-dir", help="Path to generated schemas directory")
    p_main.add_argument("--repo", required=True, help="GitHub repo (owner/name)")

    # deploy-branch
    p_branch = subparsers.add_parser("deploy-branch", help="Deploy branch preview")
    p_branch.add_argument("--pages-dir", required=True, help="Path to gh-pages directory")
    p_branch.add_argument("--spec-html", help="Path to generated spec HTML file")
    p_branch.add_argument("--schemas-dir", required=True, help="Path to generated schemas directory")
    p_branch.add_argument("--branch", required=True, help="Branch name")
    p_branch.add_argument("--sha", required=True, help="Full commit SHA")
    p_branch.add_argument("--repo", required=True, help="GitHub repo (owner/name)")
    p_branch.add_argument("--pr", help="Pull request number")
    p_branch.add_argument("--run-id", help="GitHub Actions run ID")

    # cleanup-branch
    p_cleanup = subparsers.add_parser("cleanup-branch", help="Remove branch preview")
    p_cleanup.add_argument("--pages-dir", required=True, help="Path to gh-pages directory")
    p_cleanup.add_argument("--branch", required=True, help="Branch name to clean up")
    p_cleanup.add_argument("--repo", required=True, help="GitHub repo (owner/name)")

    args = parser.parse_args()

    if args.command == "deploy-main":
        cmd_deploy_main(args)
    elif args.command == "deploy-branch":
        cmd_deploy_branch(args)
    elif args.command == "cleanup-branch":
        cmd_cleanup_branch(args)


if __name__ == "__main__":
    main()
