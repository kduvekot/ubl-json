# CLAUDE.md

## GitHub CLI

Always use `--repo kduvekot/ubl-json` when calling `gh` commands. The git remote uses a local proxy, so `gh` cannot auto-detect the repository.

Example:
```bash
gh run list --repo kduvekot/ubl-json --branch main
gh run view 12345 --repo kduvekot/ubl-json
```
