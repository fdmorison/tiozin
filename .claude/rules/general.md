# General

## 1. Never overwrite user edits

If the user has already made a change to a file, do not overwrite it. Confirm before acting
when the intent is ambiguous.

## 2. Do exactly what was requested

Do not add features, rename symbols, refactor, or clean up code beyond the scope of the
request. If something adjacent looks wrong, point it out — do not fix it silently.

## 3. Keep config mirrors in sync

The following files must always be kept in sync with each other:

- `tiozin/env.py` ↔ `tests/env.py`
- `tiozin/config.py` ↔ `tests/config.py`

## 4. Breaking changes are limited to public exports

A change is only a breaking change if it affects the public API surface. Internal
changes (including renames and removals) are not breaking. The public API surface
is defined by:

- `tiozin/__init__.py`
- `tiozin/api/__init__.py`
- `tiozin/utils/__init__.py`
- `tiozin/family/tio_duckdb/__init__.py`
- `tiozin/family/tio_kernel/__init__.py`
- `tiozin/family/tio_spark/__init__.py`

## 5. `Input`, `Transform`, and `Output` Tiozins must remain stateless

Plugin classes must not store mutable runtime state between executions. All state
belongs in the constructor and must derive solely from the parameters passed to it.
