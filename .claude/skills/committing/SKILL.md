---
name: committing
description: Commits uncommitted changes by grouping related changes into focused commits and applying the repository commit conventions.
user-invocable: true
allowed-tools:
  - Bash(git checkout *)
  - Bash(git switch *)
  - Bash(git status *)
  - Bash(git diff *)
  - Bash(git grep *)
  - Bash(git log *)
  - Bash(git add *)
  - Bash(git commit *)
  - Bash(make format)
---

## Rules

- Keep commits focused and atomic:
  - Each commit should represent a single topic or unit of work.
  - Do not mix unrelated changes.
  - Split independent changes into separate commits whenever practical.
  - A reviewer should be able to understand the implementation incrementally by reading the history from first to last.
- Stage files by name. Never use `git add .` or `git add -A`.
- Never use `git reset --hard`.
- Never commit directly to `main`. Always create a feature branch first.
- Never skip git hooks (`--no-verify`) unless explicitly requested.
- Never commit files that may contain secrets (`.env`, `credentials.json`, etc.).
- Never commit absolute paths, local paths, secrets, or PII to any file.
- Only fake secrets and fake PII are allowed in test fixtures, stubs and tests.
- If a pre-commit hook fails, the commit did not happen. Fix the issue, re-stage affected files, and create a new commit.

## Policies

- Commit message format:
  ```text
  <type>: <description>

  <body>

  Co-Authored-By: Claude <model> <noreply@anthropic.com>
  ```
- `type` must be one of the commit types defined in `.github/workflows/pr-checks.yaml`.
- `description` is lowercase, imperative, and has no trailing period.
- Do not use scopes in commit messages on feature branches. This rule does not apply to PR titles.
- The commit title (`<type>(<scope>): <description>`) is at most 50 characters.
- Describe only the changes in the commit, not the overall PR intent.
- The body is optional. When present:
  - Leave a blank line between the title and body.
  - Wrap lines at 72 characters.
  - Explain why the change was made when the reason is not obvious.
- Order commits using progressive disclosure patterns:
  - Commit independent changes before dependent changes.
  - Commit simpler changes before more complex changes.
  - Each commit should build naturally on the commits that precede it.

## Workflow

1. Run `make format`.
2. Review all remaining uncommitted changes.
3. Create the required commits.
