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

The `tio_kernel` family ships NoOp implementations for optional registries: `SettingRegistry`, `SecretRegistry`, `SchemaRegistry`, `LineageRegistry`, `MetricRegistry`, and `TransactionRegistry`. They return `None` or discard events. They work fine for local development and testing.

`JobRegistry` is covered by `FileJobRegistry` and `SettingRegistry` is covered by `FileSettingRegistry`. Both are production-ready implementations that load YAML or JSON manifests from any location [fsspec](https://filesystem-spec.readthedocs.io/en/latest/) supports: local paths, object storage (`s3://`, `gs://`, `az://`), or remote protocols (`http://`, `https://`, `ftp://`, `sftp://`).

`FileJobRegistry` is the registry used when you run `tiozin run path/to/job.yaml`. Pass a URL instead of a path and it will fetch the manifest over HTTP or FTP instead:

```yaml
registries:
  job:
    kind: tio_kernel:FileJobRegistry
    location: https://example.com/jobs
```

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

Once implemented, register your registry as a Tiozin via Python `entry_points`. See [Creating Pluggable Tiozins](../extending/tiozins.md).
