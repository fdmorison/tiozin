from __future__ import annotations

from dataclasses import dataclass, field

from duckdb import DuckDBPyConnection, DuckDBPyRelation

from ..utils import sql_literal


@dataclass
class ReadSpec:
    """
    Spec for a DuckDB ``read_<format>()`` table function call.

    Renders a ``DuckDBPyRelation`` via :meth:`to_relation`. Does not resolve aliases or apply
    Tiozin-specific transformations — use ``ReadBuilder`` for that.

    Examples::

        >>> ReadSpec("csv", ["/data/file.csv"], {"header": True}).to_relation(conn)
        <DuckDBPyRelation>

        >>> ReadSpec("text", ["/data/file.txt"], columns=["content AS value"]).to_relation(conn)
        <DuckDBPyRelation>
    """

    format: str
    path: list[str]
    options: dict[str, object] = field(default_factory=dict)
    columns: list[str] = field(default_factory=lambda: ["*"])

    def to_relation(self, conn: DuckDBPyConnection) -> DuckDBPyRelation:
        projection = ", ".join(self.columns)
        reader = f"read_{self.format}"
        if self.options:
            params = ", ".join(f"{k}={sql_literal(v)}" for k, v in self.options.items())
            return conn.sql(f"SELECT {projection} FROM {reader}({self.path}, {params})")
        return conn.sql(f"SELECT {projection} FROM {reader}({self.path})")
