# Configuration

Tiozin reads configuration from environment variables. All settings have sensible defaults and work out of the box.

---

## Environment files

Tiozin loads `.env` files automatically from these locations, in order:

1. `/etc/tiozin/.env` — system-wide
2. `~/.env` — user home directory
3. `~/.config/tiozin/.env` — user config directory
4. `/config/.env` — container mount
5. `/tiozin/.env` — container mount
6. `.env` in the current directory and all parent directories

Later files take precedence over earlier ones. This means a project-level `.env` overrides system defaults.

---

## Logging

| Variable | Default | Description |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `TIO_LOG_DATE_FORMAT` | `iso` | Timestamp format in log output |
| `TIO_LOG_JSON` | `false` | Emit logs as JSON (for log aggregation systems like Datadog or CloudWatch) |
| `TIO_LOG_JSON_ENSURE_ASCII` | `false` | Force ASCII encoding in JSON logs |
| `TIO_LOG_SHOW_LOCALS` | `false` | Include local variables in exception tracebacks |

---

## Using environment variables in jobs

Access environment variables inside job YAML using the `ENV` namespace:

```yaml
runner:
  kind: SparkRunner
  log_level: "{{ ENV.LOG_LEVEL }}"
```

If the variable is not set, Tiozin raises an error at render time. Use `| default()` to make it optional:

```yaml
log_level: "{{ ENV.LOG_LEVEL | default('INFO') }}"
```

See [Templates Reference](templates.md) for more details on templating.
