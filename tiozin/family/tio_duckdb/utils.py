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
