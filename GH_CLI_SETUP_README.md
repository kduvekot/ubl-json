# GitHub CLI Auto-Installation for Claude Code

This package enables automatic installation of the GitHub CLI (`gh`) in Claude Code on the Web sessions, with automatic version checking and secure checksum verification.

## Features

- **Automatic Installation**: Installs `gh` CLI on session start
- **Version Control**: Pin specific versions or use AUTO mode for latest
- **Security**: BLOCKING SHA256 checksum verification
- **Update Notifications**: Alerts when newer versions are available
- **Environment Variables**: Update versions without git commits

## Installation

### 1. Copy Files to Your Repository

Copy the `.claude` directory to your repository root:

```bash
cp -r .claude /path/to/your/repo/
```

Your repository structure should look like:
```
your-repo/
├── .claude/
│   ├── settings.json
│   └── scripts/
│       └── install-gh-with-version-check.sh
└── ... your other files
```

### 2. Configure GitHub Token

In Claude Code on the Web, you need to configure your GitHub token as an environment variable:

1. Open your Claude Code session
2. Go to Settings (gear icon) → Environment Variables
3. Add a new variable:
   - **Name**: `GITHUB_TOKEN`
   - **Value**: Your GitHub Personal Access Token (fine-grained)

**Token Requirements:**
- Repository access to your target repository
- Permissions needed:
  - **Pull requests**: Read and write (for creating/merging PRs)
  - **Issues**: Read and write (for creating/commenting on issues)
  - **Contents**: Read (for viewing repository content)
  - **Metadata**: Read (automatically included)

Create a token at: https://github.com/settings/tokens?type=beta

### 3. Configure Version (Optional)

You can control which version of `gh` CLI to install:

**Option A: Auto-update to latest (recommended)**
Add environment variable:
- **Name**: `GH_SETUP_VERSION`
- **Value**: `AUTO`

**Option B: Pin specific version**
Add environment variable:
- **Name**: `GH_SETUP_VERSION`
- **Value**: `2.86.0` (or your preferred version)

If not set, defaults to version `2.83.2`.

### 4. Customize Usage Instructions (Optional)

If your repository uses the gh CLI with specific parameters (like `--repo`), you may want to add usage instructions to `.claude/CLAUDE.md`:

```markdown
## GitHub CLI Usage

You can use the gh CLI in this repo. For PR and issue commands, use the --repo parameter:

```bash
gh pr create --repo owner/repo-name
gh issue list --repo owner/repo-name
```

For repo view commands, use the positional argument:
```bash
gh repo view owner/repo-name
```

For API commands, include the repo in the endpoint path:
```bash
gh api repos/owner/repo-name/pulls
```
```

Replace `owner/repo-name` with your actual repository path.

## How It Works

### SessionStart Hook

The `.claude/settings.json` file configures a SessionStart hook that runs on:
- Initial session startup
- Session resume

This hook executes the installation script which:
1. Checks if `gh` is already installed
2. Verifies version matches configured version
3. Checks for available updates (non-blocking, cached for 24 hours)
4. Downloads and installs if needed
5. Verifies SHA256 checksum (BLOCKING - fails on mismatch)

### Version Checking

The script performs a quick API check (~0.3 seconds) to see if newer versions are available. This check is:
- **Non-blocking**: Won't delay your session if API is slow
- **Cached**: Only checks once per 24 hours
- **Visible**: Shows update notification in hook output

### Hook Output

When the hook runs, you'll see concise status messages:

**If update available:**
```
⚠️  Update available: v2.83.2 → v2.86.0 - Set GH_SETUP_VERSION=2.86.0
✓ GitHub CLI v2.83.2 ready
```

**If up-to-date:**
```
✓ GitHub CLI v2.83.2 ready
```

Detailed logs go to stderr for troubleshooting if needed.

## Configuration Options

### Environment Variables

All configuration is done via Claude Code environment variables:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `GH_SETUP_VERSION` | Version to install | `2.83.2` | `2.86.0` or `AUTO` |
| `GH_CHECK_UPDATES` | Check for updates | `true` | `false` to disable |
| `GH_VERSION_CHECK_CACHE_HOURS` | Update check frequency | `24` | `48` for 2 days |
| `GITHUB_TOKEN` | GitHub authentication | *(required)* | `ghp_...` or `github_pat_...` |

### Script Configuration

Advanced users can modify `.claude/scripts/install-gh-with-version-check.sh`:

- Line 20: Change default version fallback
- Line 44: Toggle update checking
- Line 45: Adjust API timeout
- Line 46: Change cache duration

## Updating gh CLI Version

### Method 1: Environment Variable (No git commits needed)

1. Go to Claude Code Settings → Environment Variables
2. Update `GH_SETUP_VERSION` to new version (e.g., `2.86.0`)
3. Start a new Claude Code session
4. The new version will be installed automatically

### Method 2: AUTO Mode (Always latest)

1. Set `GH_SETUP_VERSION=AUTO` in environment variables
2. Each session will automatically use the latest release
3. Update notifications won't show (since you're always on latest)

## Security

This installation method provides several security improvements over third-party installers:

### ✓ Secure Download
- HTTPS only (enforced via `--proto '=https'`)
- TLS 1.2+ required
- Direct from official GitHub releases

### ✓ Checksum Verification
- Downloads official SHA256 checksums
- **BLOCKING** verification (installation aborts on mismatch)
- Protects against corrupted downloads and MITM attacks

### ✓ Transparent & Auditable
- All code visible in your repository
- No external dependencies (except curl, tar, sha256sum)
- Full audit trail in logs

### ✓ Version Control
- Pin specific versions for reproducibility
- Test updates before rolling out
- No surprise changes

## Troubleshooting

### gh CLI not found

Check if the hook ran successfully:
1. Look for hook output at session start
2. Verify `CLAUDE_CODE_REMOTE=true` (should be automatic in CCW)
3. Check `~/.local/bin` is in PATH

### Update notification not showing

- Notifications only show if installed version differs from latest
- Check is cached for 24 hours (won't show every session)
- Set `GH_CHECK_UPDATES=false` to disable checks entirely

### Checksum verification failed

This is a **security critical** error. Possible causes:
1. Corrupted download - retry in new session
2. Network issues - check connectivity
3. **Security incident** - verify release on GitHub

Never bypass checksum verification.

### Permission denied errors

Token may lack required permissions. Verify your token has:
- Repository access configured
- Pull requests: Read and write
- Issues: Read and write
- Contents: Read

### Rate limiting

GitHub API has rate limits:
- **Without token**: 60 requests/hour
- **With token**: 5000 requests/hour

The update check uses 1 API call per 24 hours (cached).

## Customization for Your Repository

### Adapting the gh CLI Usage

This setup is optimized for repositories using a local git proxy (common in Claude Code on the Web). If your repository doesn't use a proxy, you can:

1. Remove the `--repo` parameter instructions from your documentation
2. Use standard `gh` commands directly
3. Keep the installation setup as-is (works everywhere)

### Hook Timeout

The default timeout is 90 seconds. For slower connections:

1. Edit `.claude/settings.json`
2. Change `"timeout": 90` to a higher value (e.g., 120)

### Disable Update Checking

To skip version checks entirely:

1. Add environment variable: `GH_CHECK_UPDATES=false`
2. Or modify script line 44: `CHECK_FOR_UPDATES="false"`

## Version History

- **v1.0**: Initial release with AUTO mode, version checking, and security features
- Based on tweakers-smileys repository gh-setup implementation

## Credits

This setup was developed as a secure alternative to `gh-setup-hooks` with:
- BLOCKING checksum verification
- Version pinning and AUTO mode
- Update notifications
- Full transparency and auditability

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review detailed logs (stderr output during hook execution)
3. Verify environment variables are set correctly
4. Test with a clean session (clear cache if needed)

## License

This setup is provided as-is. The GitHub CLI itself is licensed under MIT by GitHub, Inc.
