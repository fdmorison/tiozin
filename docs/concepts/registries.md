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
| `BatchRegistry` | Registers batch executions |

## Built-in registries

The `tio_kernel` family ships several production-ready implementations:

| Plugin | Registry | Description |
|---|---|---|
| `FileJobRegistry` | `JobRegistry` | Loads job manifests from any fsspec-supported location |
| `FileSettingRegistry` | `SettingRegistry` | Loads framework configuration from any fsspec-supported location |
| `EnvSecretRegistry` | `SecretRegistry` | Reads secrets from environment variables |
| `FileSchemaRegistry` | `SchemaRegistry` | Loads schema files from any fsspec-supported location |
| `OpenLineageRegistry` | `LineageRegistry` | Sends run events to any OpenLineage-compatible backend via HTTP |

NoOp versions are available for every registry type: `NoOpLineageRegistry`, `NoOpSchemaRegistry`, `NoOpMetricRegistry`, `NoOpSecretRegistry`, `NoOpSettingRegistry`, and `NoOpBatchRegistry`. They do nothing or return safe fallback values. Use them in local development and testing when no real backend is needed.

`FileJobRegistry` is the registry used by `tiozin run path/to/job.yaml`. Set `location` to a folder, S3 prefix, or HTTP base URL and jobs are loaded by name relative to it:

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

Each registry type defines its own read and write methods. The signatures differ because each registry serves a different purpose:

| Registry | Read method | Write method |
|---|---|---|
| `JobRegistry` | `get(identifier)` | `register(identifier, value)` |
| `SettingRegistry` | `get()` | (none) |
| `SecretRegistry` | `get(identifier)` | `register(identifier, value)` |
| `SchemaRegistry` | `get(subject, version=None)` | `register(subject, value)` |
| `LineageRegistry` | (none) | `emit(event)` |
| `MetricRegistry` | inherited from base | inherited from base |
| `BatchRegistry` | inherited from base | inherited from base |

All registries that have a `get()` method raise when the item is not found and `failfast=True`. When `failfast=False` (the default), `get()` returns `None` instead.

## Implementing a custom registry

Extend the appropriate abstract class and implement `get()` and `register()`:

```python
from tiozin import SecretRegistry

class VaultSecretRegistry(SecretRegistry):
    def get(self, identifier: str):
        return vault_client.read_secret(identifier)

    def register(self, identifier: str, value) -> None:
        vault_client.write_secret(identifier, value)
```

Once implemented, register the registry as a Tiozin via Python `entry_points`. See [Working with Registries](../extending/registry.md).
