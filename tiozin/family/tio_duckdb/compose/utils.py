from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

from duckdb import DuckDBPyRelation


def fetchall_as_pydict(relation: DuckDBPyRelation) -> list[dict[str, Any]]:
    """
    Materialize a DuckDB relation into a list of dictionaries.

    Each row is converted into a ``dict`` mapping column names to values,
    using the relation's result schema. This eagerly executes the relation.

    If the relation does not produce a result set (e.g. DDL or DML statements
    such as ``CREATE``, ``INSERT``, or ``COPY``), an empty list is returned.
    """
    is_dml_or_ddl = not relation or not relation.description

    if is_dml_or_ddl:
        return []

    columns = [col[0] for col in relation.description]
    dataset = relation.fetchall()
    return [dict(zip(columns, row, strict=True)) for row in dataset]


def sql_literal(value: Any) -> str:
    """
    Converts a Python value to a DuckDB SQL literal.

    Supports booleans, strings, numbers, None, bytes, date/time types,
    lists, tuples, dicts (as DuckDB structs), and falls back to ``repr()``
    for anything else.

    Examples::

        >>> sql_literal(True)
        'true'
        >>> sql_literal("hello")
        "'hello'"
        >>> sql_literal(None)
        'NULL'
        >>> sql_literal([1, 2, 3])
        '[1, 2, 3]'
        >>> sql_literal({"a": 1, "b": "x"})
        "{'a': 1, 'b': 'x'}"
    """
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    if isinstance(value, bytes):
        return f"'\\x{value.hex()}'::BLOB"
    if isinstance(value, datetime):
        return f"'{value.isoformat()}'::TIMESTAMP"
    if isinstance(value, date):
        return f"'{value.isoformat()}'::DATE"
    if isinstance(value, time):
        return f"'{value.isoformat()}'::TIME"
    if isinstance(value, timedelta):
        return f"INTERVAL '{int(value.total_seconds())}' SECOND"
    if isinstance(value, (list, tuple)):
        items = ", ".join(sql_literal(v) for v in value)
        return f"[{items}]"
    if isinstance(value, dict):
        entries = ", ".join(f"'{k}': {sql_literal(v)}" for k, v in value.items())
        return f"{{{entries}}}"
    return repr(value)
