# Quick Start Guide

## 3-Step Setup

### 1. Copy Files
```bash
# Copy the .claude directory to your repository root
cp -r .claude /path/to/your/repo/
```

### 2. Set Environment Variables

In Claude Code Settings → Environment Variables, add:

| Variable | Value | Required |
|----------|-------|----------|
| `GITHUB_TOKEN` | Your GitHub token | **Yes** |
| `GH_SETUP_VERSION` | `AUTO` (or specific version like `2.86.0`) | Optional |

### 3. Start Session

That's it! On your next Claude Code session, gh CLI will be installed automatically.

## What You'll See

```
⚠️  Update available: v2.83.2 → v2.86.0 - Set GH_SETUP_VERSION=2.86.0
✓ GitHub CLI v2.83.2 ready
```

## Common Commands

```bash
# Create a PR
gh pr create --repo owner/repo-name --title "My PR"

# List issues
gh issue list --repo owner/repo-name

# View repository
gh repo view owner/repo-name
```

Replace `owner/repo-name` with your actual repository (e.g., `microsoft/vscode`).

## Need Help?

See the full [README.md](README.md) for detailed documentation, troubleshooting, and customization options.

## Token Setup

Create a GitHub fine-grained personal access token at:
https://github.com/settings/tokens?type=beta

**Required permissions:**
- Pull requests: Read and write
- Issues: Read and write
- Contents: Read

Grant access to your repository and copy the token to `GITHUB_TOKEN` environment variable.
