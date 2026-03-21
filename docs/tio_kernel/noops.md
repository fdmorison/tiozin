# NoOp Components

`tio_kernel` ships a NoOp implementation for every plugin type. NoOp components do nothing: they log lifecycle events, return `None`, and discard any data written to them. Use them in tests, dry-runs, and configuration validation. They are not intended for production workloads.

## NoOpRunner

A runner that does nothing. Logs each lifecycle step and returns an empty list from `run()`.

```yaml
runner:
  kind: tio_kernel:NoOpRunner
```

### Parameters

| Property | Description | Default |
|---|---|---|
| `verbose` | Log lifecycle events | `true` |
| `force_error` | Raise a `RuntimeError` on `run()`, useful for testing error handling | `false` |

## NoOpInput

An input that does nothing and returns `None`.

```yaml
inputs:
  - kind: tio_kernel:NoOpInput
    name: placeholder
```

### Parameters

| Property | Description | Default |
|---|---|---|
| `verbose` | Log lifecycle events | `true` |
| `force_error` | Raise a `RuntimeError` on `read()` | `false` |

## NoOpTransform

A transform that does nothing and returns `None`.

```yaml
transforms:
  - kind: tio_kernel:NoOpTransform
    name: placeholder
```

### Parameters

| Property | Description | Default |
|---|---|---|
| `verbose` | Log lifecycle events | `true` |
| `force_error` | Raise a `RuntimeError` on `transform()` | `false` |

## NoOpOutput

An output that does nothing and returns `None`.

```yaml
outputs:
  - kind: tio_kernel:NoOpOutput
    name: placeholder
```

### Parameters

| Property | Description | Default |
|---|---|---|
| `verbose` | Log lifecycle events | `true` |
| `force_error` | Raise a `RuntimeError` on `write()` | `false` |

## NoOp registries

NoOp registries do nothing. Use them when the real registry is not available.

| Kind | Contract |
|---|---|
| `tio_kernel:NoOpSettingRegistry` | `SettingRegistry` |
| `tio_kernel:NoOpSecretRegistry` | `SecretRegistry` |
| `tio_kernel:NoOpSchemaRegistry` | `SchemaRegistry` |
| `tio_kernel:NoOpLineageRegistry` | `LineageRegistry` |
| `tio_kernel:NoOpMetricRegistry` | `MetricRegistry` |
| `tio_kernel:NoOpTransactionRegistry` | `TransactionRegistry` |

```yaml
registries:
  secret:
    kind: tio_kernel:NoOpSecretRegistry
  lineage:
    kind: tio_kernel:NoOpLineageRegistry
```
