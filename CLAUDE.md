# Claude Instructions — Tiozin

## Before anything else

Read `agents.md` before taking any action in this project.
It defines the domain model, public API boundaries, and agent responsibilities.

---

## Agents

| Concern       | Spec file                  |
|---------------|----------------------------|
| Tests         | `agents/test-agent.md`     |
| Test rules    | `agents/test-rules.md`     |
| Documentation | `agents/docs-agent.md`     |
| PR format     | `.github/pull_request_template.md` |

---

## Commands

Use Makefile commands. Never invoke tools directly.

| Purpose          | Command            |
|------------------|--------------------|
| Run tests        | `make test`        |
| Format code      | `make format`      |
| Lint check       | `make check`       |
| Install deps     | `make install`     |
| Install dev deps | `make install-dev` |
| Build package    | `make build`       |

---

## Code Style

- Never define functions outside of classes. Use `@staticmethod` on the relevant class instead.
- Never use `# noqa` to suppress linter errors. Fix the code instead.
- Use single backticks in docstrings. Never use RST double backticks.

---

## Test Conventions

Beyond `agents/test-rules.md`:

- Condition suffix must be `_when_`, never `_for_`.
- Never write `# Arrange / Act`. Use only `# Arrange` or `# Act` separately.
- `actual` and `expected` tuples must always be multiline, never on a single line.

---

## Behavior

- Never overwrite a file the user has manually edited. User edits are authoritative.
- Do exactly what was asked. No extra fixtures, helpers, or abstractions.
