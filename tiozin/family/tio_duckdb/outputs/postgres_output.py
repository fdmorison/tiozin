from __future__ import annotations

from typing import get_args

from duckdb import DuckDBPyRelation

from tiozin.api.metadata.lineage.model import Lineage, LineageDataset
from tiozin.exceptions import RequiredArgumentError, TiozinInputError
from tiozin.utils import as_list, randstr, trim_lower, trim_upper

from .. import DuckdbOutput, env
from ..typehints import DuckdbPlan, DuckdbPostgresWriteMode

EXTENSION = "postgres"
DEFAULT_MODE = "APPEND"


class DuckdbPostgresOutput(DuckdbOutput):
    """
    Materializes a DuckDB relation into a PostgreSQL table.

    Supports append, truncate, overwrite, and merge write modes, automatic schema evolution, and
    optional pre/post SQL execution. Intended for pipelines that require controlled writes into
    PostgreSQL tables.

    For extension-specific behavior and limitations, see:
    https://duckdb.org/docs/extensions/postgres

    Args:
        host:
            PostgreSQL server hostname or IP address. Defaults to "localhost".
        port:
            PostgreSQL server port. Defaults to 5432.
        database:
            Target PostgreSQL database name. Defaults to "postgres".
        user:
            Username used for authentication. Defaults to "postgres".
        password:
            Password used for authentication. Defaults to "".
        schema:
            Target schema in PostgreSQL. Defaults to "public".
        table:
            Target table name in PostgreSQL.

        mode:
            Write strategy applied to the target table. Supported values are "append", "truncate",
            "overwrite", and "merge". Defaults to "append".

            - append: Ensures the table exists and inserts incoming rows.
            - truncate: Ensures the table exists, clears existing data, then inserts incoming rows.
            - overwrite: Recreates the table structure on each run and loads the new dataset.
            - merge: Performs an upsert using a staging table and a PostgreSQL MERGE statement.
              Requires `primary_key`.

        primary_key:
            Column or columns used as the primary key when the table is created.
            Required when `mode="merge"`.

        merge_key:
            Conflict key used during `merge` operations. When not provided, `primary_key` is used.

        pre_pgsql:
            SQL statement(s) executed on PostgreSQL before the write strategy
            runs. Use this to prepare dependencies that could block the write
            (for example, dropping views or disabling triggers).

        post_pgsql:
            SQL statement(s) executed on PostgreSQL after the write completes.
            Common uses include creating indexes, granting permissions,
            or recreating views.

        **options:
            Additional keyword arguments forwarded to the DuckDB Postgres extension.

    Examples:
        Basic append:

            >>> DuckdbPostgresOutput(
            ...     mode="append",
            ...     table="events",
            ... )

        Merge using a business key:

            >>> DuckdbPostgresOutput(
            ...     mode="merge",
            ...     table="events",
            ...     merge_key=["external_id"],
            ... )

        Overwrite with primary key definition:

            >>> DuckdbPostgresOutput(
            ...     mode="overwrite",
            ...     table="events",
            ...     primary_key="id",
            ... )

        Complete YAML configuration:

        ```yaml
        outputs:
          - kind: DuckdbPostgresOutput
            name: write_to_postgres
            description: Loads the customer dataset into the PostgreSQL table public.customers.
            # Write strategy
            mode: merge
            primary_key: id
            # Target table
            schema: public
            database: tiozin
            table: customers
            # Connection
            host: localhost
            port: 5432
            user: tiozin
            password: "{{ ENV.PGPASSWORD | default('tiozin') }}"
            # Pre-write SQL (runs before the write strategy)
            pre_pgsql:
              - DROP VIEW IF EXISTS public.vw_customers_summary
            # Post-write SQL (runs after the write strategy)
            post_pgsql:
              - GRANT ALL ON public.customers TO tiozin
              - CREATE INDEX IF NOT EXISTS idx_customers_email ON public.customers(email)
        ```
    """

    def __init__(
        self,
        table: str = None,
        host: str = None,
        database: str = None,
        user: str = None,
        password: str = None,
        port: int = None,
        schema: str = None,
        mode: DuckdbPostgresWriteMode = None,
        primary_key: str | list[str] = None,
        merge_key: str | list[str] = None,
        pre_pgsql: str | list[str] = None,
        post_pgsql: str | list[str] = None,
        **options,
    ) -> None:
        super().__init__(**options)
        RequiredArgumentError.raise_if_missing(
            table=table,
        )
        TiozinInputError.raise_if_not_in(
            trim_lower(mode),
            get_args(DuckdbPostgresWriteMode),
            allow_none=True,
        )
        self.table = table
        self.host = host or env.PGHOST
        self.database = database or env.PGDATABASE
        self.user = user or env.PGUSER
        self.password = password or env.PGPASSWORD
        self.port = port or env.PGPORT
        self.schema = schema or env.PGSCHEMA
        self.mode = trim_upper(mode) or DEFAULT_MODE
        self.primary_key = as_list(primary_key, [])
        self.merge_key = as_list(merge_key, self.primary_key)
        self.pre_pgsql = as_list(pre_pgsql, [])
        self.post_pgsql = as_list(post_pgsql, [])
        self._token = randstr()

    @property
    def _database(self) -> str:
        return f"_pg_{self.slug}"

    @property
    def _secret(self) -> str:
        return f"{self._database}_secret"

    @property
    def _pg_table(self) -> str:
        return f"{self.schema}.{self.table}"

    @property
    def _pg_staging(self) -> str:
        return f"{self.schema}._{self.table}_temp_{self._token}"

    @property
    def _pg_probe(self) -> str:
        return f"{self.schema}._{self.table}_probe_{self._token}"

    @property
    def _table(self) -> str:
        return f"{self._database}.{self._pg_table}"

    @property
    def _staging(self) -> str:
        return f"{self._database}.{self._pg_staging}"

    @property
    def _probe(self) -> str:
        return f"{self._database}.{self._pg_probe}"

    def lineage(self) -> Lineage:
        return Lineage(
            inputs=[],
            outputs=[
                LineageDataset.from_postgres(
                    self.host, self.port, self.database, self.schema, self.table
                )
            ],
        )

    def setup(self, data: DuckDBPyRelation) -> None:
        self.duckdb.execute(
            f"""
            INSTALL {EXTENSION};LOAD {EXTENSION};
            CREATE SECRET IF NOT EXISTS {self._secret} (
                TYPE POSTGRES,
                HOST '{self.host}',
                PORT {self.port},
                DATABASE '{self.database}',
                USER '{self.user}',
                PASSWORD '{self.password}'
            );
            ATTACH '' AS {self._database}
            (TYPE POSTGRES, SECRET {self._secret}, SCHEMA '{self.schema}')
            """
        )

    def write(self, data: DuckDBPyRelation) -> DuckdbPlan:
        self.info(f"Writing to Postgres table `{self.schema}.{self.table}`")
        strategy = {
            "APPEND": self._write_append,
            "TRUNCATE": self._write_truncate,
            "OVERWRITE": self._write_overwrite,
            "MERGE": self._write_merge,
        }
        return self.scriptfy(
            self.create_table_as_select(self._table, data),
            self._create_primary_key(),
            self._evolve_schema(data),
            self._postgres_execute(self.pre_pgsql),
            strategy[self.mode](data),
            self._postgres_execute(self.post_pgsql),
        )

    def _write_append(self, source: DuckDBPyRelation) -> list[str]:
        return [
            self.insert_into(self._table, source),
        ]

    def _write_truncate(self, source: DuckDBPyRelation) -> list[str]:
        return [
            self.truncate(self._table),
            self.insert_into(self._table, source),
        ]

    def _write_overwrite(self, source: DuckDBPyRelation) -> list[str]:
        return [
            self._postgres_execute(f"""
                CREATE TABLE {self._pg_staging} (LIKE {self._pg_table}
                INCLUDING ALL EXCLUDING INDEXES);
                DROP TABLE {self._pg_table};
                ALTER TABLE {self._pg_staging} RENAME TO {self.table};
            """),
            self._create_primary_key(),
            self.insert_into(self._table, source),
        ]

    def _write_merge(self, source: DuckDBPyRelation) -> list[str]:
        RequiredArgumentError.raise_if_missing(
            merge_key=self.merge_key,
        )

        schema = list(source.columns)
        fields = [c for c in schema if c not in self.merge_key]

        on_clause = " AND ".join(f"target.{k}=source.{k}" for k in self.merge_key)
        update_set = ", ".join(f"{c}=COALESCE(source.{c},target.{c})" for c in fields)
        insert_cols = ", ".join(schema)
        insert_vals = ", ".join(f"source.{c}" for c in schema)

        return [
            self.create_table_as_select(self._table, source),
            self._create_primary_key(),
            self.create_table_as_select(self._staging, source, with_data=True),
            f"""
                MERGE INTO {self._table} AS target
                USING {self._staging} AS source
                ON {on_clause}
                WHEN MATCHED THEN
                    UPDATE SET {update_set}
                WHEN NOT MATCHED THEN
                    INSERT ({insert_cols})
                    VALUES ({insert_vals})
            """,
            f"DROP TABLE {self._staging}",
        ]

    def _postgres_execute(self, *statements: str) -> str:
        return f"""
        CALL postgres_execute('{self._database}',$$
            DO $do$
            BEGIN
                {self.scriptfy(statements)}
                DROP TABLE IF EXISTS {self._pg_staging};
                DROP TABLE IF EXISTS {self._pg_probe};
            EXCEPTION WHEN OTHERS THEN
                DROP TABLE IF EXISTS {self._pg_staging};
                DROP TABLE IF EXISTS {self._pg_probe};
                RAISE;
            END
            $do$;
        $$)
        """

    def _create_primary_key(self) -> list[str]:
        if not self.primary_key:
            return ""

        pk = ",".join(f'"{c}"' for c in self.primary_key)
        return self._postgres_execute(
            f"""
            IF NOT EXISTS (
                SELECT 1
                    FROM information_schema.table_constraints
                WHERE table_schema    = '{self.schema}'
                    AND table_name      = '{self.table}'
                    AND constraint_type = 'PRIMARY KEY'
            ) THEN
                ALTER TABLE {self._pg_table} ADD PRIMARY KEY ({pk});
            END IF;
            """
        )

    def _evolve_schema(self, source: DuckDBPyRelation) -> list[str]:
        probe_name = self._pg_probe.split(".")[-1]
        return [
            self.create_table_as_select(self._probe, source),
            self._postgres_execute(f"""
                DECLARE field RECORD;
                BEGIN
                    FOR field IN
                        SELECT
                            a.attname                                       AS name
                          , pg_catalog.format_type(a.atttypid, a.atttypmod) AS type
                         FROM pg_attribute a
                         JOIN pg_class     c ON c.oid = a.attrelid
                         JOIN pg_namespace n ON n.oid = c.relnamespace
                        WHERE n.nspname = '{self.schema}'
                          AND c.relname = '{probe_name}'
                          AND a.attnum > 0
                          AND NOT a.attisdropped
                    LOOP
                        EXECUTE FORMAT(
                            'ALTER TABLE {self._pg_table} ADD COLUMN IF NOT EXISTS %I %s',
                            field.name,
                            field.type
                        );
                    END LOOP;
                    DROP TABLE IF EXISTS {self._pg_probe};
                EXCEPTION WHEN OTHERS THEN
                    DROP TABLE IF EXISTS {self._pg_probe};
                    RAISE;
                END
            """),
            "CALL pg_clear_cache()",
        ]
