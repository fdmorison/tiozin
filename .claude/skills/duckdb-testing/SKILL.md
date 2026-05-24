---
name: duckdb-testing
description: DuckDB testing patterns. Use when writing or reviewing tests that involve DuckDB code.
user-invocable: false
---

# DuckDB Testing

## Comparing results

Call `.fetchall()` to get a list of Python tuples, then compare with `==`.

```python
actual = relation.fetchall()
expected = [("amet", 1), ("lorem", 3)]
assert actual == expected
```

## Ordering

DuckDB does not guarantee row order without `ORDER BY`. Follow @rules/testing.md#11-ordering.

## Inline input data

Use `VALUES` with `.set_alias()`, then register before passing to the transform.

```python
input_rel = duckdb_session.sql("""
    SELECT * FROM (VALUES
        ('lorem ipsum dolor'),
        ('lorem lorem dolor')
    ) AS t(value)
""").set_alias("input")

duckdb_session.register("input", input_rel)
```

## DuckDBPyConnection fixture

Use the `duckdb_session` fixture from `tests/conftest.py`. Never instantiate a connection inside a test.

```python
# ✔ Correct
def test_transform_should_count_words(duckdb_session: DuckDBPyConnection) -> None: ...

# ❌ Incorrect
def test_transform_should_count_words() -> None:
    conn = duckdb.connect()
```
