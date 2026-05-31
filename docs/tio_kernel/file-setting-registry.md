# FileSettingRegistry

Loads framework settings from a `tiozin.yaml` file.

```yaml
registries:
  setting:
    kind: tio_kernel:FileSettingRegistry
    location: config/tiozin.yaml
```

## Parameters

| Property | Description | Default |
|---|---|---|
| `location` | Path or URI of the settings file, discovered automatically if not set | |
| `**options` | fsspec storage options | |

## Automatic discovery

When `location` is not set, Tiozin searches for a `tiozin.yaml` in the following order:

| Priority | Path |
|---|---|
| 1 | `tiozin.yaml` (current working directory) |
| 2 | `~/tiozin.yaml` |
| 3 | `~/.config/tiozin/tiozin.yaml` |
| 4 | `/etc/tiozin/tiozin.yaml` |
| 5 | `/tiozin/tiozin.yaml` |
| 6 | `/config/tiozin.yaml` |
| 7 | `/tiozin.yaml` |

If no file is found at any of these paths, built-in defaults are used and the pipeline runs without a settings file.

## Delegating to another registry

A `tiozin.yaml` can hand off settings resolution to a different `SettingRegistry` by setting `registries.setting` to a non-null value:

```yaml
# tiozin.yaml
registries:
  setting:
    kind: tio_kernel:FileSettingRegistry
    location: s3://my-bucket/config/tiozin.yaml
```

This keeps a minimal local file that points to a shared remote configuration.
