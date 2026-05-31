# YAML Configuration Reference

See the [settings guide](index.md) for a full walkthrough.

## Registry Fields

Every registry in `tiozin.yaml` accepts the same set of fields.

| Field | Description | Default |
|---|---|---|
| `kind` | Plugin class name | see [Default kinds](#default-kinds) |
| `name` | Optional label for this registry instance | `null` |
| `description` | Optional description | `null` |
| `location` | Path or URL to the registry backend | `null` |
| `timeout` | Request timeout in seconds | `3` |
| `readonly` | When `true`, the registry rejects write operations | `false` |
| `cache` | When `true`, retrieved metadata is cached in memory | `false` |
| `failfast` | When `true`, raises an error when metadata is not found; when `false`, returns `null` | `true` |

## Default Kinds

Any registry omitted from `tiozin.yaml` uses these defaults.

| Registry | Default kind |
|---|---|
| `setting` | `tio_kernel:FileSettingRegistry` |
| `job` | `tio_kernel:FileJobRegistry` |
| `schema` | `tio_kernel:FileSchemaRegistry` |
| `secret` | `tio_kernel:EnvSecretRegistry` |
| `transaction` | `tio_kernel:NoOpTransactionRegistry` |
| `lineage` | `tio_kernel:NoOpLineageRegistry` |
| `metric` | `tio_kernel:NoOpMetricRegistry` |

## runtime_defaults Entries

`runtime_defaults` is a list. Each entry requires a `kind` field matching a plugin class name, followed by any number of plugin-specific arguments.

```yaml
runtime_defaults:
  - kind: CsvInput
    encoding: utf-8
    schema_subject: auto
```

All fields beyond `kind` are forwarded to the plugin as default arguments. Job-level arguments always take precedence.
