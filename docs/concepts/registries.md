# Registries

A Registry is a metadata service that a job can use to look up or register information at execution time.

## What registries do

Registries are not step components. They start before the first job runs and stop when the app shuts down. During that time, jobs can use them to retrieve settings, secrets, schemas, and other metadata needed for execution.

The framework defines seven registry contracts:

| Registry | Purpose |
|---|---|
| `JobRegistry` | Looks up job definitions by name |
| `SettingRegistry` | Retrieves runtime configuration values |
| `SecretRegistry` | Retrieves secrets (passwords, tokens, API keys) |
| `SchemaRegistry` | Retrieves schema definitions for validation |
| `LineageRegistry` | Registers data lineage events |
| `MetricRegistry` | Registers execution metrics |
| `TransactionRegistry` | Registers execution transactions |

## Built-in registries

The `tio_kernel` family ships several production-ready implementations:

| Plugin | Registry | Description |
|---|---|---|
| `FileJobRegistry` | `JobRegistry` | Loads job manifests from any fsspec-supported location |
| `FileSettingRegistry` | `SettingRegistry` | Loads framework configuration from any fsspec-supported location |
| `EnvSecretRegistry` | `SecretRegistry` | Reads secrets from environment variables |
| `FileSchemaRegistry` | `SchemaRegistry` | Loads schema files from any fsspec-supported location |
| `OpenLineageRegistry` | `LineageRegistry` | Sends run events to any OpenLineage-compatible backend via HTTP |

NoOp versions are provided for registries that are not configured: `NoOpSchemaRegistry`, `NoOpMetricRegistry`, and `NoOpTransactionRegistry`. They return `None` or discard events. Use them in local development and testing when you do not need that registry.

`FileJobRegistry` is the registry used when you run `tiozin run path/to/job.yaml`. Set `location` to a folder, S3 prefix, or HTTP base URL and jobs are loaded by name relative to it:

```yaml
registries:
  job:
    kind: tio_kernel:FileJobRegistry
    location: s3://my-bucket/jobs
```

```bash
tiozin run my_pipeline.yaml  # loads s3://my-bucket/jobs/my_pipeline.yaml
```

Absolute paths and URIs passed directly to `tiozin run` are used as-is, regardless of `location`.

## Registry API

All registries share the same three methods:

| Method | Description |
|---|---|
| `get(identifier, version=None)` | Retrieve metadata by ID. Raises `TiozinNotFoundError` if not found |
| `register(identifier, value)` | Store metadata under an identifier |
| `try_get(identifier, version=None)` | Retrieve metadata or return `None` if not found |

## Implementing a custom registry

Extend the appropriate abstract class and implement `get()` and `register()`:

```python
from tiozin import SecretRegistry

class VaultSecretRegistry(SecretRegistry):
    def get(self, identifier: str, version: str | None = None):
        return vault_client.read_secret(identifier)

    def register(self, identifier: str, value) -> None:
        vault_client.write_secret(identifier, value)
```

`try_get()` is provided by the base class. It returns `None` instead of raising when the item is not found.

Once implemented, register your registry as a Tiozin via Python `entry_points`. See [Working with Registries](../extending/registry.md).
