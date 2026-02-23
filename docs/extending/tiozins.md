# Creating Pluggable Tiozins

Every component you write for Tiozin is a Tiozin: an Input that reads from your database, a Transform that applies your business logic, an Output that writes to your system, a Runner that manages your execution engine. This guide shows how to build each one, using a MongoDB family as the running example. Data flows through the pipeline as `pandas.DataFrame`.

---

## How Tiozin finds your plugins

Tiozin discovers plugins through Python's standard `entry_points` mechanism. You declare your package once in `pyproject.toml`, and from that point forward Tiozin loads your plugins automatically at startup. No registration calls, no decorators, no configuration files.

```toml
[project.entry-points."tiozin.family"]
tio_sqlite = "tio_sqlite"
```

The key is your package name. The value is the Python import path to your package. When Tiozin starts, it scans all installed packages registered under `tiozin.family`, imports each one, and makes their Tiozins available by class name.

That is the entire discovery contract. Once your package is installed, users reference your Tiozins by class name using the `kind` field in any job YAML.

---

## Eager and lazy execution

Before implementing Output and Runner, you need to understand how execution flows.

When a job runs, Tiozin calls each step in sequence: inputs read, transforms modify, outputs write. But "write" does not always mean "execute immediately."

An eager output writes immediately inside `write()` and returns `None`. The runner receives nothing and skips it.

A lazy output returns a typed plan object describing what to write. The runner collects all plans from all outputs and decides how to execute them: sequentially, in parallel, as a batch, or any other strategy that makes sense for the underlying engine.

Lazy execution is what makes the runner genuinely useful. Spark returns `DataFrameWriter` objects. DuckDB returns SQL strings. The runner executes each one in the right way. You can do the same in your own family.

You choose the pattern by what your `write()` returns and what your `run()` knows how to handle.

---

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
        self._conn = sqlite3.connect(self.path)
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

---

## Implementing an Input

An Input reads data from a source and passes it to the next step. Extend `Input` and implement `read()`.

```python
import sqlite3

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
      SELECT *
      FROM orders
      WHERE status = 'open'
        AND total > 100
```

The `kind` is your class name exactly. The `name` is a required unique identifier within the job. The `description` is optional but useful for anyone reading the YAML later. Any parameter you define in `__init__`, like `query`, becomes a YAML field automatically.

---

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

Notice `self.context.nominal_time`. The execution context is always available and gives you the reference time, the run ID, Data Mesh fields, and more.

In YAML:

```yaml
transforms:
  - kind: TaxTransform
    name: apply_tax
    description: Applies tax rate to total column.
    tax_rate: 0.15
```

For operations that need to combine multiple inputs, extend `CoTransform` instead.

---

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
        cursor = self.context.runner.session.cursor()
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.table} AS {data}")
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

---

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
        cursor = self.context.runner.session.cursor()
        cursor.execute(f"SELECT value FROM {self.table} WHERE key = ?", (identifier,))
        row = cursor.fetchone()
        if not row:
            raise TiozinNotFoundError(identifier)
        return row[0]

    def register(self, identifier: str, value: str) -> None:
        cursor = self.context.runner.session.cursor()
        cursor.execute(f"INSERT OR REPLACE INTO {self.table} (key, value) VALUES (?, ?)", (identifier, value))
```

The `try_get()` method is provided by the base class. It catches `TiozinNotFoundError` and returns `None`.

---

## Using @tioproxy

Proxies let you add shared methods to every step in your family without repeating code in each class.

See [Tio Proxy](../concepts/proxies.md) for how the proxy chain is built across the class hierarchy.

---

## Stateless steps, stateful runner

The most important rule in the family model is about who can hold state.

The Runner is stateful by design. It owns connections, sessions, and any resource that has a lifecycle. `setup()` creates them. `teardown()` releases them. Everything in between can use them safely through `self.context.runner.session`.

Inputs, Transforms, and Outputs must be stateless. They receive all runtime dependencies through `self.context`. They must not open connections in `__init__`, store sessions as instance attributes, maintain mutable state between calls, or use module-level singletons.

The reason is practical. The framework may instantiate steps multiple times, reuse them across executions, or run them in parallel. A step that holds a connection will fail unpredictably under these conditions. A step that gets its connection from the context will always work, regardless of how the framework chooses to run it.

Configuration parameters set in `__init__` are fine. Storing `self.table = table` is not state, it is configuration. What you must not store is anything that is alive: connections, file handles, sessions, loggers created at runtime.

| Role | Can hold state | Where the session comes from |
|---|---|---|
| Runner | yes | creates and owns it in `setup()` |
| Input | no | `self.context.runner.session` |
| Transform | no | `self.context.runner.session` |
| Output | no | `self.context.runner.session` |
| Registry | yes, with care | its own implementation |
