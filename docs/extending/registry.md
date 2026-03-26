# Working with Registries

Registries are a type of Tiozin. Tiozin discovers them by class name via Python `entry_points`, just like Inputs, Transforms, and Outputs. Unlike step components, registries start before the first job runs and stop when the app shuts down.

## Implementing a Registry

Extend the appropriate registry class and implement `get()` and `register()`.

```python
import boto3
from tiozin import SecretRegistry


class AWSSecretRegistry(SecretRegistry):
    def __init__(self, region: str = None, location: str = None, **options) -> None:
        super().__init__(location=location, **options)
        self._client = boto3.client("secretsmanager", region_name=region, endpoint_url=location)

    def get(self, identifier: str, version: str = None) -> str:
        try:
            return self._client.get_secret_value(SecretId=identifier)["SecretString"]
        except self._client.exceptions.ResourceNotFoundException:
            return None

    def register(self, identifier: str, value: str) -> None:
        self._client.put_secret_value(SecretId=identifier, SecretString=value)
```

Tiozin raises `SecretNotFoundError` automatically if `get()` returns `None`.

Once implemented, register your registry as a Tiozin via Python `entry_points`. See [Creating a Provider Family](families.md).

## Accessing Registries from Plugins

Every plugin (Input, Transform, Output) runs inside a job execution. During that execution, Tiozin makes all configured registries available through `self.context.registries`. This gives your plugin direct access to secrets, schemas, transactions, and the other infrastructure services your job depends on, without passing anything through the constructor.

### The basics

Inside any plugin method (`read`, `transform`, `write`), access a registry like this:

```python
from tiozin import Input


class MyInput(Input[list]):
    def read(self) -> list:
        secret = self.context.registries.secret.get("db/password")
        return fetch_data(password=secret)
```

`self.context` is the active execution context for the current step. `self.context.registries` is a `Registries` bundle that holds all seven registry instances configured in `tiozin.yaml`.

### All available registries

| Attribute | Registry type | What it provides |
|---|---|---|
| `registries.setting` | `SettingRegistry` | Configuration values |
| `registries.secret` | `SecretRegistry` | Credentials and secrets |
| `registries.schema` | `SchemaRegistry` | Data schemas |
| `registries.job` | `JobRegistry` | Job manifests |
| `registries.metric` | `MetricRegistry` | Execution metrics |
| `registries.lineage` | `LineageRegistry` | Lineage events |

Each attribute holds the instance configured in `tiozin.yaml` for that registry type. If no implementation is configured, the attribute holds the default no-op for that type.

### Common patterns

#### Secret registry

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

#### Schema registry

Use the schema registry when your plugin needs to validate or apply a schema at read or write time.

```python
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

### Configuring registries in tiozin.yaml

Once your registry is implemented and registered as a Tiozin, configure it in `tiozin.yaml` so the framework picks it up at startup:

```yaml
registries:
  secret:
    kind: AWSSecretRegistry
    region: us-east-1
```

See [Settings Reference](../settings.md) for the full list of registry slots and configuration options.
