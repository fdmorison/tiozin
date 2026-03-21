# Accessing Registries in Plugins

Every plugin (Input, Transform, Output) runs inside a job execution. During that execution, Tiozin makes all configured registries available through `self.context.registries`. This gives your plugin direct access to secrets, schemas, transactions, and the other infrastructure services your job depends on, without passing anything through the constructor.

## The basics

Inside any plugin method (`read`, `transform`, `write`), access a registry like this:

```python
from tiozin import Input


class MyInput(Input[list]):
    def read(self) -> list:
        secret = self.context.registries.secret.get("db/password")
        return fetch_data(password=secret)
```

`self.context` is the active execution context for the current step. `self.context.registries` is a `Registries` bundle that holds all seven registry instances configured in `tiozin.yaml`.

## All available registries

| Attribute | Registry type | What it provides |
|---|---|---|
| `registries.setting` | `SettingRegistry` | Configuration values |
| `registries.secret` | `SecretRegistry` | Credentials and secrets |
| `registries.schema` | `SchemaRegistry` | Data schemas |
| `registries.job` | `JobRegistry` | Job manifests |
| `registries.metric` | `MetricRegistry` | Execution metrics |
| `registries.lineage` | `LineageRegistry` | Lineage events |

Each attribute holds the instance configured in `tiozin.yaml` for that registry type. If no implementation is configured, the attribute holds the default no-op for that type.

## Common patterns

### Secret registry

The secret registry is the most common use case. Use it to fetch credentials that your plugin needs at runtime, keeping secrets out of job YAML and plugin code entirely.

```python
from tiozin import Input


class PostgresInput(Input[list]):
    def __init__(self, query: str, **options) -> None:
        super().__init__(**options)
        self.query = query

    def read(self) -> list:
        password = self.context.registries.secret.get("postgres/app_user")
        conn = connect(host="db.internal", password=password)
        return conn.execute(self.query).fetchall()
```

The secret identifier (`"postgres/app_user"`) is resolved at runtime by whatever backend is configured: HashiCorp Vault, AWS Secrets Manager, or any custom `SecretRegistry` implementation. The plugin does not know or care which backend is in use.

### Schema registry

Use the schema registry when your plugin needs to validate or apply a schema at read or write time.

```python
from typing import Any
from tiozin import Input


class AvroInput(Input[bytes]):
    def __init__(self, topic: str, **options) -> None:
        super().__init__(**options)
        self.topic = topic

    def read(self) -> bytes:
        schema = self.context.registries.schema.get(self.topic)
        raw = consume_message(self.topic)
        return deserialize(raw, schema=schema)
```

The schema is fetched by topic name from the configured schema registry backend (Confluent Schema Registry, a file-based registry, or any other implementation). The plugin stays decoupled from the schema storage technology.

## Why this works

When a job runs, `TiozinApp` passes the full `Registries` bundle into the job's `Context`. Every child step context inherits the same registries from the job context. No constructor injection is needed at any level.

Your plugin stays stateless. Configuration lives in `__init__` parameters. Infrastructure access happens through `self.context.registries` at call time. This is the Tiozin model: steps are stateless, infrastructure is contextual.

See [Creating Pluggable Tiozins](tiozins.md) for how to build Input, Transform, and Output plugins. See [Settings Reference](../settings.md) for how to configure each registry in `tiozin.yaml`.
