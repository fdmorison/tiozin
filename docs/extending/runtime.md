# Implementing ETL Tiozins

Build Runner, Input, Transform, and Output plugins using a SQLite family as the running example. Data flows through the pipeline as SQL strings.

## Implementing a Runner

The Runner is the only component that can hold state. It creates the connection during `setup`, executes the plan during `run`, and releases everything during `teardown`.

Start by defining the contract between your outputs and your runner. A `SQLiteWriteSpec` tells the runner exactly what needs to be written, without writing it yet.

```python
from dataclasses import dataclass
import sqlite3

from tiozin import Runner


@dataclass
class SQLiteWriteSpec:
    sql: str


class SQLiteRunner(Runner[list[SQLiteWriteSpec], sqlite3.Connection, None]):
    def __init__(self, path: str = "example.db", **options) -> None:
        super().__init__(**options)
        self.path = path
        self._conn: sqlite3.Connection | None = None

    @property
    def session(self) -> sqlite3.Connection:
        return self._conn

    def setup(self) -> None:
        self._conn = sqlite3.connect(self.path, isolation_level=None)
        self.info(f"Connected to SQLite at {self.path}")

    def run(self, plan: list[SQLiteWriteSpec | None]) -> None:
        specs = [s for s in plan if s is not None]
        cursor = self._conn.cursor()
        try:
            cursor.execute("BEGIN")
            for spec in specs:
                cursor.execute(spec.sql)
            cursor.execute("COMMIT")
        except Exception:
            cursor.execute("ROLLBACK")
            raise

    def teardown(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
            self.info("SQLite connection closed")
```

`run()` receives a list of `SQLiteWriteSpec` objects, one per output. It executes each SQL statement inside a single transaction. If any statement fails, everything is rolled back. The outputs have no idea and do not need to care.

In YAML:

```yaml
runner:
  kind: SQLiteRunner
  path: example.db
```

## Implementing an Input

An Input reads data from a source and passes it to the next step. Extend `Input` and implement `read()`.

```python
from tiozin import Input


class SQLiteInput(Input[str]):
    def __init__(self, query: str, **options) -> None:
        super().__init__(**options)
        self.query = query

    def read(self) -> str:
        return self.query
```

The session comes from `self.context.runner.session`. Never open a connection in `__init__` or `read()`. The runner owns the connection lifecycle.

In YAML:

```yaml
inputs:
  - kind: SQLiteInput
    name: orders_source
    description: High-value open orders created since the start of the month.
    query: |
      WITH orders(id, status, total) AS (
          VALUES (1, 'open', 200), (2, 'open', 50), (3, 'closed', 300)
      )
      SELECT *
      FROM orders
      WHERE status = 'open'
        AND total > 100
```

The `kind` is your class name exactly. The `name` is a required unique identifier within the job. The `description` is optional but useful for anyone reading the YAML later. Any parameter you define in `__init__`, like `query`, becomes a YAML field automatically.

## Implementing a Transform

A Transform receives input from the previous step, applies business logic, and returns the result. Extend `Transform` and implement `transform()`.

```python
from tiozin import Transform


class TaxTransform(Transform[str]):
    def __init__(self, tax_rate: float = 0.1, **options) -> None:
        super().__init__(**options)
        self.tax_rate = tax_rate

    def transform(self, data: str) -> str:
        return f"""
        SELECT *,
               total * (1 + {self.tax_rate}) AS total_with_tax
        FROM ({data}) base
        """
```

This is where your business logic lives. Call external APIs, apply ML models, run SQL, compute aggregations. As long as you accept what the previous step returned and return something the next step can use, the framework does not care what happens in between.

In YAML:

```yaml
transforms:
  - kind: TaxTransform
    name: apply_tax
    description: Applies tax rate to total column.
    tax_rate: 0.15
```

For operations that need to combine multiple inputs, extend `CoTransform` instead.

## Implementing an Output

An Output writes data to a destination. Extend `Output` and implement `write()`.

### The simplest output

Write immediately and return `None`. The runner receives nothing and skips it. Simple and direct.

```python
from tiozin import Output


class SQLiteOutput(Output[str]):
    def __init__(self, table: str, **options) -> None:
        super().__init__(**options)
        self.table = table

    def write(self, data: str) -> None:
        conn = self.context.runner.session
        conn.execute(f"CREATE TABLE IF NOT EXISTS {self.table} AS {data}")
```

In YAML:

```yaml
outputs:
  - kind: SQLiteOutput
    name: orders_sink
    description: Writes enriched orders to SQLite.
    table: processed_orders
```

### Lazy output

Return a `SQLiteWriteSpec` from `write()` instead of writing immediately. The runner collects all specs and executes them inside a single transaction.

```python
from tiozin import Output


class SQLiteOutput(Output[str]):
    def __init__(self, table: str, **options) -> None:
        super().__init__(**options)
        self.table = table

    def write(self, data: str) -> SQLiteWriteSpec:
        sql = f"CREATE TABLE IF NOT EXISTS {self.table} AS {data}"
        return SQLiteWriteSpec(sql=sql)
```

`write()` does not execute anything. The runner executes all SQL statements within a single transaction.

In YAML:

```yaml
outputs:
  - kind: SQLiteOutput
    name: orders_sink
    table: processed_orders

  - kind: SQLiteOutput
    name: summary_sink
    table: daily_summaries
```

## Putting it all together

Here is the complete job YAML for the SQLite ETL built throughout this guide. It wires the runner, input, transform, and output into a single `LinearJob`:

```yaml
kind: LinearJob
name: sqlite_orders_etl
description: |
  Reads high-value open orders, applies tax, and writes the result to SQLite.

runner:
  kind: SQLiteRunner
  path: example.db

inputs:
  - kind: SQLiteInput
    name: orders_source
    description: High-value open orders created since the start of the month.
    query: |
      WITH orders(id, status, total) AS (
          VALUES (1, 'open', 200), (2, 'open', 50), (3, 'closed', 300)
      )
      SELECT *
      FROM orders
      WHERE status = 'open'
        AND total > 100

transforms:
  - kind: TaxTransform
    name: apply_tax
    description: Applies tax rate to total column.
    tax_rate: 0.15

outputs:
  - kind: SQLiteOutput
    name: orders_sink
    description: Writes enriched orders to SQLite.
    table: processed_orders
```

Save it as `sqlite_orders_etl.yaml` and run it:

```bash
tiozin run sqlite_orders_etl.yaml
```

For `tiozin run` to resolve `SQLiteRunner`, `SQLiteInput`, `TaxTransform`, and `SQLiteOutput` by name, your package must declare a `tiozin.family` entry point. If you packaged your SQLite components as `tio_sqlite`, add this to your `pyproject.toml`:

```toml
[project.entry-points."tiozin.family"]
tio_sqlite = "tio_sqlite"
```

Install your package (e.g. `uv sync`, `poetry install`) and the classes become available to the framework. See [Creating a Provider Family](families.md) for the full walkthrough, including how to structure the package and what the family module must export.

## Appendix

### Lineage

Tiozin automatically reports lineage at each job execution, making your plugins visible in a lineage graph.

To enable this, see [Lineage](lineage.md) for details on configuring the job namespace and overriding `external_datasets()` in your plugins.

### Stateless steps, stateful runner

The Runner is the only component expected to hold stateful resources like connections and sessions. It creates them in `setup()`, exposes them via the `session` property, and releases them in `teardown()`.

Inputs, Transforms, and Outputs should be stateless. They must not open or store connections. Tiozin may copy step objects internally, and distributed engines like Spark may serialize them and send them to workers. Live objects like connections do not survive either operation.

Access the session from context inside the method call, not during initialization:

```python
# correct: use the session as a local variable
def write(self, data: str) -> SQLiteWriteSpec:
    conn = self.context.runner.session
    ...

# wrong: opening and storing a connection as instance state
def write(self, data: str) -> SQLiteWriteSpec:
    self._conn = sqlite3.connect(self.path)  # do not store live objects
    ...
```

Storing configuration in `__init__` is fine. `self.table = table` is a parameter, not state.

### Eager and lazy execution

Steps either execute immediately or defer execution to the runner.

- **Eager**: the step does the work and returns the result
- **Lazy**: the step returns a plan; the runner executes it later

Use eager when the work is simple or must run inline. Use lazy when execution should be controlled by the runner (e.g. batching, parallelism, engine optimization).

```python
# eager: executes the SQL and returns a materialized result
def transform(self, data: DuckDBPyRelation) -> Any:
    return self.duckdb.execute("SELECT * FROM orders").fetchdf()

# lazy: returns a relation; DuckDB executes it when the next step consumes it
def transform(self, data: DuckDBPyRelation) -> DuckDBPyRelation:
    return self.duckdb.sql("SELECT * FROM orders")
```

This matters most for **Outputs**. If `write()` returns `None`, the output is eager and the runner has nothing to collect. If it returns a plan object, the runner collects it and executes everything in `run()`. A Spark runner, for example, collects all `DataFrameWriter` objects from every output and triggers them together. That is when Spark actually executes the job.

```python
# eager: calls a Spark action directly; return None signals the runner has nothing to collect
def write(self, data: DataFrame) -> None:
    data.write.format("parquet").mode("overwrite").option("path", self.path).save()
    return None

# lazy: returns the writer, runner collects all writers and triggers them together
def write(self, data: DataFrame) -> DataFrameWriter:
    return data.write.format("parquet").mode("overwrite").option("path", self.path)
```

Some families expose convenience properties like `self.duckdb` or `self.spark`. These are shortcuts to `self.context.runner.session` and give direct access to the active execution session.
