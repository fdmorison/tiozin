from typing import Any

from duckdb import DuckDBPyRelation

from tiozin import Context
from tiozin.exceptions import InvalidInputError
from tiozin.utils import bind_self_tokens, trim

from .. import DuckdbCoTransform


class DuckdbSqlTransform(DuckdbCoTransform):
    """
    Transforms data by executing a SQL query on the active DuckDB connection.

    This transform is **DQL-only**: it is intended exclusively for SQL statements
    that produce a relational result (i.e. queries that return a
    ``DuckDBPyRelation``).

    The query can reference any relation previously registered as a view
    by upstream inputs or transforms, using the step name as the table
    identifier.

    Additionally, the ``@self`` token can be used to reference the current
    input data without knowing the upstream step name:

        - ``@self`` or ``@self0``: Primary input
        - ``@self1``, ``@self2``, ...: Additional inputs (for multi-input transforms)

    Since the DuckDB proxy already registers each step result as a named view,
    ``@self`` is resolved by replacing the token with the input relation's alias
    at query time — no temporary views are created or destroyed.

    ── Note on DDL and DML ──

    SQL statements that perform schema definition or data mutation
    (e.g. ``CREATE``, ``DROP``, ``INSERT``, ``UPDATE``, ``DELETE``, ``COPY``)
    are **not supported** by this transform.

    Such statements do not produce a relational result and therefore violate
    the contract of a Transform, which requires a relation to be returned for
    downstream steps.

    DDL statements should be modeled as Inputs, while DML statements should be
    handled by Outputs or by dedicated mutation-oriented transforms.

    For details about DuckDB SQL syntax, refer to the official documentation at:
    https://duckdb.org/docs/sql/introduction

    Attributes:
        query:
            SQL query to execute. Supports ``@self`` references and
            ``$param`` named parameters.

        args:
            Dictionary of named parameters to bind to the query.

        **options:
            Additional options.

    Examples:

        ```python
        DuckdbSqlTransform(
            query="SELECT *, amount * 1.1 AS taxed FROM @self WHERE status = $status",
            args={"status": "active"},
        )
        ```

        ```yaml
        transforms:
          - kind: DuckdbSqlTransform
            query: "SELECT *, amount * 1.1 AS taxed FROM @self WHERE status = $status"
            args:
              status: active
        ```
    """

    def __init__(
        self,
        query: str,
        args: dict[str, Any] = None,
        **options,
    ) -> None:
        super().__init__(**options)
        self.query = trim(query)
        self.args = args or {}

    def transform(
        self, context: Context, data: DuckDBPyRelation, *others: DuckDBPyRelation
    ) -> DuckDBPyRelation:
        query = bind_self_tokens(
            self.query,
            [data.alias, *(other.alias for other in others)],
        )

        relation = self.duckdb.sql(
            query,
            params=self.args,
        )

        InvalidInputError.raise_if(
            relation is None,
            "Only DQL statements can be handled by DuckdbSqlTransform. "
            "The provided SQL did not produce a relation.",
        )

        return relation
