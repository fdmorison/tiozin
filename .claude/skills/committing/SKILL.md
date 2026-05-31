---
name: committing
description: Commits uncommitted changes using conventional commits, grouped by topic in dependency order. Use when the user has uncommitted changes to stage and commit.
user-invocable: true
---

## Rules

- Commit message format: `type: description`
  - `description` is lowercase, no trailing period, max 50 characters
  - No scope: omitting here saves characters
  - Wording does not need to describe the overall PR intent; describe only the changes in this commit
- Stage files by name, never with `git add -A` or `git add .`
- Never skip git hooks (`--no-verify`, `--no-gpg-sign`) unless the user explicitly requests it
- Never commit files that likely contain secrets (`.env`, `credentials.json`, etc.)
- Never use `git reset --hard`; use `git reset --soft` only
- If a pre-commit hook fails, the commit did not happen: fix the issue, re-stage, and commit again; never amend in this scenario

## Workflow

1. If the user asked to exclude any files, stash them before committing.
2. Analyze all uncommitted changes and group them by topic or independent unit of change.
3. Order the groups from least to most dependent: simpler, self-contained changes first; changes that depend on earlier ones last.
4. Commit each group separately, in that order.
