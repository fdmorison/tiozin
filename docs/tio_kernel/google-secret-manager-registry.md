# GoogleSecretManagerRegistry

Reads and writes secrets backed by [Google Cloud Secret Manager](https://cloud.google.com/secret-manager/docs).

```yaml
registries:
  secret:
    kind: tio_kernel:GoogleSecretManagerRegistry
    project_id: my-gcp-project
```

Each secret identifier maps directly to a secret name inside the configured project. The retrieved value is wrapped in a `Secret` object that masks itself in logs and reprs, keeping credentials out of output even when injected into connection strings or other values.

## Parameters

| Property | Required | Description | Default |
|---|---|---|---|
| `project_id` | yes | Google Cloud project that holds the secrets. The registry raises `RequiredArgumentError` when it is missing. | |
| `location` | no | API endpoint override (for example, `http://localhost:6174` for an emulator). When unset, the client uses the default Google endpoint. | |

Credentials are resolved through [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials), so the same resolution order applies as for any other Google Cloud client: an attached service account, a `gcloud` login, or `GOOGLE_APPLICATION_CREDENTIALS`.

## How It Works

When a job or plugin calls `secret.get("DB_PASSWORD")`, the registry accesses `projects/{project_id}/secrets/DB_PASSWORD/versions/latest` and returns a `Secret`. If the secret does not exist, it raises `SecretNotFoundError`.

```python
from tiozin import Input


class PostgresInput(Input[list]):
    def read(self) -> list:
        password = self.context.registries.secret.get("DB_PASSWORD")
        conn = connect(host="db.internal", password=password)
        return conn.execute(self.query).fetchall()
```

Registering a secret creates it with automatic replication when it does not exist yet, then adds a new version holding the value. Previous versions are kept, and every lookup reads the latest one.

Secrets injected into job YAML via `{{ SECRET.name }}` go through the same registry. The masked repr ensures they do not appear in logs:

```yaml
runner:
  kind: SparkRunner
  url: jdbc:postgresql://host:5432/db?password={{ SECRET.DB_PASSWORD }}
  # logged as: jdbc:postgresql://host:5432/db?password=***
```

## Pointing At An Emulator

Setting `location` sends every call to that endpoint instead of the Google API, which is what a local Secret Manager emulator needs:

```yaml
registries:
  secret:
    kind: tio_kernel:GoogleSecretManagerRegistry
    project_id: my-gcp-project
    location: http://localhost:6174
```

## Setup

Install the tio_kernel extra:

```bash
pip install tiozin[tio_kernel]
```

To install the Secret Manager client without the rest of the tio_kernel backends, use the `gcp` extra:

```bash
pip install tiozin[gcp]
```

## When To Use It

Use `GoogleSecretManagerRegistry` when secrets live in Google Cloud Secret Manager and the runtime can obtain Application Default Credentials: workloads on GKE, Cloud Run, Compute Engine, or Dataproc with an attached service account, or local development against an emulator.

For secrets stored in environment variables, use [EnvSecretRegistry](env-secret-registry.md). For secrets in AWS Parameter Store, use [AwsParameterStoreSecretRegistry](aws-parameter-store-secret-registry.md). For other vaults or secret managers, implement a custom `SecretRegistry`. See [Creating Pluggable Tiozins](../extending/tiozins.md).

## Related

- [How to Use Secrets in Jobs](../how-to/secrets.md)
- [EnvSecretRegistry](env-secret-registry.md)
- [AwsParameterStoreSecretRegistry](aws-parameter-store-secret-registry.md)
- [Working with Registries](../extending/registry.md)
