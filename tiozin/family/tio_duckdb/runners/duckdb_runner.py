from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
from duckdb import DuckDBPyConnection, DuckDBPyRelation

from tiozin import Context, Runner
from tiozin.exceptions import NotInitializedError, TiozinUnexpectedError
from tiozin.utils import as_list, trim

from ..assembly.utils import fetchall_as_pydict
from ..typehints import DuckdbPlan

DuckdbOutput = dict[str, list[dict[str, Any]]]


class DuckdbRunner(Runner[DuckdbPlan, DuckDBPyConnection, DuckdbOutput]):
    """
    Executes Tiozin pipelines using DuckDB.

    This runner manages a DuckDB connection and executes plans produced by inputs, transforms, and
    outputs. Plans can be DuckDBPyRelation instances or SQL strings.

    Results are collected as Python dicts, suitable for single-node, in-memory workloads. For
    details about DuckDB configuration, refer to the official documentation at:

    https://duckdb.org/docs/configuration/overview

    Attributes:
        database:
            Path to the DuckDB database file, ``:default:`` or ``:memory:`` for an in-memory
            database. Defaults to ``:memory:<job_name>``.

        read_only:
            When True, opens the main and attached databases in read-only mode.
            Defaults to False.

        attach:
            Dictionary mapping database names to their file paths.
            Each entry is attached during setup time.

        extensions:
            List of DuckDB extension names to install and load during
            setup (e.g. httpfs, spatial, iceberg).

        **options:
            DuckDB configuration options passed directly to ``duckdb.connect(config=...)``.

    Examples:

        ```python
        DuckdbRunner(
            database="path/to/main.duckdb",
            attach={"analytics": "/data/analytics.duckdb"},
            extensions=["httpfs", "spatial"],
            threads=4,
        )
        ```

        ```yaml
        runner:
          kind: DuckdbRunner
          database: path/to/main.duckdb
          attach:
            analytics: /data/analytics.duckdb
          extensions:
            - httpfs
            - spatial
          threads: 4
        ```
    """

    def __init__(
        self,
        database: str | Path = None,
        read_only: bool = False,
        attach: str | Path | dict[str, str | Path] = None,
        extensions: list[str] = None,
        **options,
    ) -> None:
        super().__init__(**options)
        self.database = trim(database)
        self.read_only = read_only
        self.attach = attach or {}
        self.extensions = as_list(extensions, [])
        self._conn: DuckDBPyConnection = None

    @property
    def session(self) -> DuckDBPyConnection:
        """Active DuckDB connection. Raises ``NotInitializedError`` if called before ``setup``."""
        NotInitializedError.raise_if(
            self._conn is None,
            message="DuckDB connection not initialized for {tiozin}",
            tiozin=self,
        )
        return self._conn

    def setup(self, context: Context) -> None:
        """Opens the DuckDB connection, loads extensions, and attaches external databases."""
        if self._conn:
            return

        # Initialize main database
        self._conn = duckdb.connect(
            self.database or f":memory:{context.job.name}",
            read_only=self.read_only,
            config=self.options,
        )

        # Install and load extensions
        for ext in self.extensions:
            self._conn.install_extension(ext)
            self._conn.load_extension(ext)
            self.info(f"🧩 Extension '{ext}' loaded")

        # Attach additional databases
        for alias, path in self.attach.items():
            ro_flag = "(READ_ONLY)" if self.read_only else ""
            self._conn.execute(f"ATTACH '{path}' AS {alias} {ro_flag}")
            self.info(f"🔗 External database '{path}' attached as '{alias}'")

        self.info("🐤 DuckDB connection is ready!")

    def run(
        self,
        context: Context,
        execution_plan: DuckdbPlan,
        params: list | dict[str, Any] = None,
        alias: str = None,
        **options,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Executes one or more plans and returns their results as Python dicts.

        Each plan is either a ``DuckDBPyRelation`` (materialized in place) or a SQL
        string (executed against the active connection). Results are keyed by alias.

        Returns::

            {
                "step_alias": [
                    {"col_a": 1, "col_b": "x"},
                    {"col_a": 2, "col_b": "y"},
                ],
            }
        """
        results = {}
        params = params or options
        alias = alias or context.name

        for i, plan in enumerate(as_list(execution_plan)):
            plan_alias = alias if not i else f"{alias}_{i}"
            match plan:
                case None | "":
                    self.warning("Skipping the plan because it is empty or already executed.")

                case DuckDBPyRelation() as relation:
                    self.info(f"Running Duckdb Relation Action {relation.alias}")
                    results[relation.alias] = fetchall_as_pydict(relation)

                case str() as query:
                    self.info("Running DuckDB SQL Action")
                    relation = self.session.sql(query, params=params, alias=plan_alias)
                    if relation:
                        results[relation.alias] = fetchall_as_pydict(relation)

                case _:
                    raise TiozinUnexpectedError(f"Unsupported DuckDB plan: {type(plan)}")

        return results

    def teardown(self, _: Context) -> None:
        """Closes the DuckDB connection and releases resources."""
        if not self._conn:
            return
        self._conn.close()
        self._conn = None
        self.info("DuckDB connection closed")
