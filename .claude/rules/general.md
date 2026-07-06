# General

## 0. Agents

- Delegate all test-related work to the `tester` agent.
- Delegate all documentation-related work to the `technical-writer` agent.
- Delegate all PullRequest-related work to the `pr-writer` agent.

## 1. Skills

- Delegate all commit related work to the `committing` skill.

## 2. Never overwrite user edits

If the user has already made a change to a file, do not overwrite it. Confirm before acting
when the intent is ambiguous.

## 3. Do exactly what was requested

Do not add features, rename symbols, refactor, or clean up code beyond the scope of the
request. If something adjacent looks wrong, point it out — do not fix it silently.

## 4. Keep config mirrors in sync

The following files must always be kept in sync with each other:

- `tiozin/env.py` ↔ `tests/env.py`
- `tiozin/config.py` ↔ `tests/config.py`

## 5. Breaking changes are limited to public exports

A change is only a breaking change if it affects the public API surface. Internal
changes (including renames and removals) are not breaking. The public API surface
is defined by:

- `tiozin/__init__.py`
- `tiozin/api/__init__.py`
- `tiozin/utils/__init__.py`
- `tiozin/family/tio_duckdb/__init__.py`
- `tiozin/family/tio_kernel/__init__.py`
- `tiozin/family/tio_spark/__init__.py`

## 6. `Input`, `Transform`, and `Output` Tiozins must remain stateless

Plugin classes must not store mutable runtime state between executions. All state
belongs in the constructor and must derive solely from the parameters passed to it.
