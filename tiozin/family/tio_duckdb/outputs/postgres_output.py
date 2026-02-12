from __future__ import annotations

from duckdb import DuckDBPyRelation

from tiozin.api import Context
from tiozin.exceptions import RequiredArgumentError
from tiozin.utils import as_list, bind_self_tokens, trim, trim_upper

from .. import DuckdbOutput
from ..typehints import DuckdbPlan, DuckdbPostgresWriteMode

EXTENTION = "postgres"


class DuckdbPostgresOutput(DuckdbOutput):
    """
    Writes a DuckDB relation to a PostgreSQL table using DuckDB's postgres extension.

    This output writes DuckDBPyRelation data to a PostgreSQL database using
    DuckDB's native postgres extension, which provides high-performance data
    transfer between DuckDB and PostgreSQL.

    For advanced options, refer to DuckDB documentation at:

    https://duckdb.org/docs/extensions/postgres

    Attributes:
        host:
            PostgreSQL server hostname or IP address.

        port:
            PostgreSQL server port. Defaults to 5432.

        database:
            Name of the PostgreSQL database.

        user:
            PostgreSQL username for authentication.

        password:
            PostgreSQL password for authentication.

        schema:
            Target schema in PostgreSQL. Defaults to ``"public"``.

        table:
            Target table name in PostgreSQL.

        mode:
            Write mode: ``"append"`` or ``"overwrite"``.

        pre_pgsql:
            SQL statement or list of statements to execute before writing.
            Supports ``@self`` token to reference the target table.

        post_pgsql:
            SQL statement or list of statements to execute after writing.
            Useful for GRANTs, index creation, or other post-write operations.
            Supports ``@self`` token to reference the target table.

        **options:
            Additional options passed to the postgres extension.

    Examples:

        ```python
        DuckdbPostgresOutput(
            host="localhost",
            port=5432,
            database="analytics",
            user="etl_user",
            password="secret",
            schema="public",
            table="events",
            mode="append",
        )
        ```

        ```yaml
        outputs:
          - type: DuckdbPostgresOutput
            host: localhost
            port: 5432
            database: analytics
            user: etl_user
            password: ${POSTGRES_PASSWORD}
            schema: public
            table: events
            mode: append
        ```
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        schema: str = None,
        table: str = None,
        mode: DuckdbPostgresWriteMode = None,
        pre_pgsql: str | list[str] = None,
        post_pgsql: str | list[str] = None,
        **options,
    ) -> None:
        super().__init__(**options)
        RequiredArgumentError.raise_if_missing(
            host=host,
            database=database,
            user=user,
            password=password,
            table=table,
        )
        self.host = trim(host) or "localhost"
        self.port = port or 5432
        self.user = trim(user)
        self.password = trim(password)
        self.database = trim(database)
        self.schema = trim(schema) or "public"
        self.table = trim(table)
        self.mode = trim_upper(mode) or "APPEND"
        self.pre_pgsql = as_list(pre_pgsql, [])
        self.post_pgsql = as_list(post_pgsql, [])

    @property
    def _pg_db(self) -> str:
        return f"_pg_{self.name}"

    @property
    def _pg_secret(self) -> str:
        return f"{self._pg_db}_secret"

    @property
    def _pg_table(self) -> str:
        return f"{self._pg_db}.{self.schema}.{self.table}"

    def _when(self, cond: bool, *sql: str) -> str:
        return ";\n".join(sql) if cond else ""

    def _pg_format(self, statements: list[str], alias: str) -> list[str]:
        return [
            f"FROM postgres_execute('{self._pg_db}',$${bind_self_tokens(sql, [alias])}$$);"
            for sql in statements
        ]

    def setup(self, _: Context, data: DuckDBPyRelation) -> None:
        self.duckdb.install_extension(EXTENTION)
        self.duckdb.load_extension(EXTENTION)
        self.duckdb.execute(
            f"""
            CREATE SECRET IF NOT EXISTS {self._pg_secret} (
                TYPE POSTGRES,
                HOST '{self.host}',
                PORT {self.port},
                DATABASE '{self.database}',
                USER '{self.user}',
                PASSWORD '{self.password}'
            )
            """
        )
        self.duckdb.execute(
            f"ATTACH '' AS {self._pg_db} "
            f"(TYPE POSTGRES, SECRET {self._pg_secret}, SCHEMA '{self.schema}')"
        )

    def write(self, _: Context, data: DuckDBPyRelation) -> DuckdbPlan:
        """
        Writes the relation to PostgreSQL using DuckDB's postgres extension.

        Installs and loads the postgres extension, attaches to the PostgreSQL
        database, and inserts the data into the target table.

        When ``mode`` is ``overwrite``, the target table is truncated before
        inserting new data. When ``mode`` is ``"append"``, data is inserted
        without modifying existing rows.

        If the target table does not exist, it is created automatically.

        Returns a SQL string to be executed lazily by the runner.
        """
        self.info(f"Writing to Postgres table `{self.schema}.{self.table}`")

        pre_pgsql = self._pg_format(self.pre_pgsql, data.alias)
        post_pgsql = self._pg_format(self.post_pgsql, data.alias)

        drop_table_when_overwrite = self._when(
            self.mode == "OVERWRITE",
            f"DROP TABLE IF EXISTS {self._pg_table}",
        )

        clear_table_when_truncate = self._when(
            self.mode == "TRUNCATE",
            f"TRUNCATE TABLE {self._pg_table}",
        )

        execution_plan = [
            # Built-in preparation phase
            drop_table_when_overwrite,
            f"CREATE TABLE IF NOT EXISTS {self._pg_table} AS SELECT * FROM {data.alias} LIMIT 0",
            clear_table_when_truncate,
            # User pre-write hooks for Postgres
            *pre_pgsql,
            # Actual Output phase
            f"INSERT INTO {self._pg_table} SELECT * FROM {data.alias}",
            # User post-write hooks for Postgres
            *post_pgsql,
        ]
        return ";\n".join(sql for sql in execution_plan if sql)
