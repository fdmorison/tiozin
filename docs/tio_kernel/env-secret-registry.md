# EnvSecretRegistry

Reads secrets from environment variables.

```yaml
registries:
  secret:
    kind: tio_kernel:EnvSecretRegistry
```

This is the default secret registry. Each secret identifier maps directly to an environment variable name (case-sensitive). The retrieved value is wrapped in a `Secret` object that masks itself in logs and reprs, keeping credentials out of output even when injected into connection strings or other values.

## Parameters

| Property | Description | Default |
|---|---|---|
| `location` | Unused for this registry, defaults to the Tiozin URI | |

## How it works

When a job or plugin calls `secret.get("DB_PASSWORD")`, the registry reads `os.environ["DB_PASSWORD"]` and returns a `Secret`. If the variable is not set, it raises `SecretNotFoundError`.

```python
from tiozin import Input


class PostgresInput(Input[list]):
    def read(self) -> list:
        password = self.context.registries.secret.get("DB_PASSWORD")
        conn = connect(host="db.internal", password=password)
        return conn.execute(self.query).fetchall()
```

Secrets injected into job YAML via `{{ SECRET.name }}` go through the same registry. The masked repr ensures they do not appear in logs:

```yaml
runner:
  kind: SparkRunner
  url: jdbc:postgresql://host:5432/db?password={{ SECRET.DB_PASSWORD }}
  # logged as: jdbc:postgresql://host:5432/db?password=***
```

## When to use it

Use `EnvSecretRegistry` when secrets are injected as environment variables at runtime: container deployments, Kubernetes secrets mounted as env vars, CI/CD pipelines, or local development with a `.env` file.

For secrets stored in a vault or secret manager (HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager), implement a custom `SecretRegistry`. See [Creating Pluggable Tiozins](../extending/tiozins.md).
