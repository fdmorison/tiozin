# DuckdbPostgresOutput

Writes a DuckDB relation into a PostgreSQL table. Uses the DuckDB Postgres extension to handle the transfer directly. Supports four write modes, automatic schema evolution, and SQL hooks that run before and after each write.

A complete working example is in [`examples/jobs/duckdb/postgres/postgres_output.yaml`](../../examples/jobs/duckdb/postgres/postgres_output.yaml).

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    name: save_customers
    table: customers
```

Connection defaults are read from standard PostgreSQL environment variables (`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGSCHEMA`). Properties set in the job always take priority.

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    name: save_customers
    table: customers
    host: my-postgres-host
    port: 5432
    database: analytics
    user: etl_user
    password: "{{ ENV.PGPASSWORD }}"
```

## Parameters

| Property | Description | Default |
|---|---|---|
| `table` | Target table name in PostgreSQL | |
| `host` | PostgreSQL server hostname | `$PGHOST` (`localhost`) |
| `port` | PostgreSQL server port | `$PGPORT` (`5432`) |
| `database` | PostgreSQL database name | `$PGDATABASE` (`postgres`) |
| `user` | PostgreSQL username | `$PGUSER` (`postgres`) |
| `password` | PostgreSQL password | `$PGPASSWORD` |
| `schema` | Target schema | `$PGSCHEMA` (`public`) |
| `mode` | Write mode: `append`, `truncate`, `overwrite`, or `merge` | `append` |
| `primary_key` | Column name or list for the primary key, required for `merge` mode | |
| `merge_key` | Conflict key for `merge`, defaults to `primary_key` when not set | `primary_key` |
| `pre_pgsql` | SQL statement or list to run on PostgreSQL before the write | |
| `post_pgsql` | SQL statement or list to run on PostgreSQL after the write | |
| `**options` | Additional keyword arguments passed to the DuckDB Postgres extension | |

## Write modes

All modes create the target table automatically if it does not exist yet.

### Append

Inserts incoming rows into the table. Does not deduplicate: running twice on the same data produces twice as many rows.

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    table: events
    mode: append
```

### Truncate

Clears the table before each write, then inserts incoming rows. Every run replaces the table content with the current batch. The table structure is preserved.

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    table: events
    mode: truncate
```

### Overwrite

Recreates the table on every run. The new table structure matches the current batch exactly. Check constraints, column defaults, and outbound foreign keys are preserved. The primary key is re-added automatically if `primary_key` is set. Other indexes are not preserved: recreate them via `post_pgsql`.

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    table: events
    mode: overwrite
    primary_key: id
    post_pgsql:
      - CREATE INDEX IF NOT EXISTS idx_events_date ON public.events(date)
```

### Merge

Upserts rows by key. Existing rows are updated; new rows are inserted. Incoming `NULL` values do not overwrite existing non-null values. Requires `primary_key`.

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    table: customers
    mode: merge
    primary_key: id
```

Use `merge_key` when the conflict key differs from the primary key:

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    table: customers
    mode: merge
    primary_key: id
    merge_key: external_id
```

## Schema evolution

All modes detect new columns automatically. When the incoming batch has a column the target table does not, that column is added to the table before the write runs. Existing rows get `NULL` for the new column.

## Hooks

`pre_pgsql` runs SQL on PostgreSQL before the write strategy executes, but after schema evolution has already run. `post_pgsql` runs after the write completes. Both accept a single statement or a list.

Common uses: drop dependent views before an overwrite, grant permissions and recreate views after a write.

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    table: events
    mode: overwrite
    primary_key: id
    pre_pgsql:
      - DROP VIEW IF EXISTS public.vw_events_summary
    post_pgsql:
      - CREATE INDEX IF NOT EXISTS idx_events_date ON public.events(date)
      - GRANT SELECT ON public.events TO reporter
      - CREATE VIEW public.vw_events_summary AS SELECT date, count(*) FROM public.events GROUP BY date
```
