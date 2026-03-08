# Creating Pluggable Tiozins

Every component you write for Tiozin is a Tiozin: an Input that reads from your database, a Transform that applies your business logic, an Output that writes to your system, a Runner that manages your execution engine. This guide shows how to build each one, using a SQLite family as the running example. Data flows through the pipeline as SQL strings.

## How Tiozin finds your plugins

Plugin discovery uses Python's `entry_points` mechanism. See [Creating a Provider Family](families.md) for the full registration walkthrough.

Once your package is installed, Tiozin makes your Tiozins available by class name. Users reference them using the `kind` field in any job YAML or Python definition. The framework resolves the class at runtime without any manual wiring.

## Eager and lazy execution

Any step can do its work immediately or defer it to the runner.

An **eager** step executes inside its own method and returns the result directly. An input that reads a file, a transform that calls an external API, an output that writes to a database inline: all are eager. The step does its work, returns its value (or `None`), and the pipeline moves on.

A **lazy** step returns a plan object instead. The runner collects all plan objects at the end of the job and decides how to execute them: sequentially, in parallel, as a batch, or whatever the engine handles best.

The Output and Runner pair is where this distinction matters most. `write()` can return `None` (eager) or a typed plan object (lazy). The runner's `run()` receives the list of plan objects and executes them.

Here is an example of eager execution. The step may write directly inside `write()` using the active connection and return `None`. The runner has nothing to do for that output:

```python
class MyDuckdbOutput(Output[DuckDBPyRelation]):
    def write(self, data: DuckDBPyRelation) -> None:
        self.duckdb.execute(f"COPY ({data.query}) TO '{self.path}' (FORMAT PARQUET)")
```

A Spark output is a good example of lazy execution. `write()` builds a `DataFrameWriter` and returns it without calling `.save()`. The runner collects all writers and triggers them, which is when Spark actually executes the job:

```python
class MySparkOutput(Output[DataFrame]):
    def write(self, data: DataFrame) -> DataFrameWriter:
        return data.write.format("parquet").mode("overwrite").option("path", self.path)
```

You choose the pattern by what your `write()` returns and what your `run()` knows how to handle.

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

This is where your business logic lives. Call external APIs, apply ML models, run SQL, compute aggregations. As long as you accept what the previous step returned and return something the next step can use, the framework does not care what happens in between. That is the point: Tiozin handles the structure, you handle the logic.

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

## Implementing a Registry

Extend the appropriate registry class and implement `get()` and `register()`.

```python
from tiozin import SecretRegistry
from tiozin.exceptions import TiozinNotFoundError


class SQLiteSecretRegistry(SecretRegistry):
    def __init__(self, table: str = "secrets", **options) -> None:
        super().__init__(**options)
        self.table = table

    def get(self, identifier: str, version: str | None = None) -> str:
        conn = self.context.runner.session
        row = conn.execute(
            f"SELECT value FROM {self.table} WHERE key = ?", (identifier,)
        ).fetchone()
        if not row:
            raise TiozinNotFoundError(identifier)
        return row[0]

    def register(self, identifier: str, value: str) -> None:
        conn = self.context.runner.session
        conn.execute(
            f"INSERT OR REPLACE INTO {self.table} (key, value) VALUES (?, ?)",
            (identifier, value),
        )
```

The `try_get()` method is provided by the base class. It catches `TiozinNotFoundError` and returns `None`.

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

## Using @tioproxy

Proxies let you add shared methods to every step in your family without repeating code in each class.

See [Tio Proxy](../concepts/proxies.md) for how the proxy chain is built across the class hierarchy.

## Stateless steps, stateful runner

The most important rule in the family model is about who can hold state.

The Runner is stateful by design. It owns connections, sessions, and any resource that has a lifecycle. `setup()` creates them. `teardown()` releases them. Everything in between can use them safely through `self.context.runner.session`.

Inputs, Transforms, and Outputs must be stateless. They receive all runtime dependencies through `self.context`. They must not open connections in `__init__`, store sessions as instance attributes, maintain mutable state between calls, or use module-level singletons.

The reason is practical. The framework may instantiate steps multiple times, reuse them across executions, or run them in parallel. A step that holds a connection will fail unpredictably under these conditions. A step that gets its connection from the context will always work, regardless of how the framework chooses to run it.

Configuration parameters set in `__init__` are fine. Storing `self.table = table` is not state, it is configuration. What you must not store is anything that is alive: connections, file handles, sessions, loggers created at runtime.

```python
# Fine: table name is configuration, not state
class SQLiteOutput(Output[str]):
    def __init__(self, table: str, **options) -> None:
        super().__init__(**options)
        self.table = table  # ok

    def write(self, data: str) -> SQLiteWriteSpec:
        conn = self.context.runner.session  # correct: get the connection from context
        ...


# Wrong: connection opened and held in __init__
class SQLiteOutput(Output[str]):
    def __init__(self, table: str, path: str, **options) -> None:
        super().__init__(**options)
        self.table = table
        self._conn = sqlite3.connect(path)  # wrong: the runner has not started yet, and
                                            # live objects like connections cannot be
                                            # serialized by engines such as Spark
```

| Role | Can hold state | Where the session comes from |
|---|---|---|
| Runner | yes | creates and owns it in `setup()` |
| Input | no | `self.context.runner.session` |
| Transform | no | `self.context.runner.session` |
| Output | no | `self.context.runner.session` |
| Registry | yes, with care | its own implementation |
