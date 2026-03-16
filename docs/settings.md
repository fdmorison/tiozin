# Settings Reference

Tiozin configuration has two independent layers:

- **`tiozin.yaml`**: declares which registries to use and where to find them
- **Environment variables**: control logging, hostname, and registry defaults that have no `tiozin.yaml` equivalent

Both layers work independently. You can use only environment variables, only a YAML file, or combine them. Values in `tiozin.yaml` override the environment variable defaults for the same field.

## The basics

Create a `tiozin.yaml` in your project root:

```yaml
registries:
  job:
    kind: FileJobRegistry
    location: examples/jobs
```

That is enough to get started. Run any job in that directory:

```bash
tiozin run examples/jobs/dummy.yaml
```

Every other registry defaults to a no-op implementation.

## How Tiozin finds tiozin.yaml

If you do not specify a location explicitly, Tiozin searches for `tiozin.yaml` in this order:

1. Current working directory (`tiozin.yaml`)
2. `~/tiozin.yaml`
3. `~/.config/tiozin/tiozin.yaml`
4. `/etc/tiozin/tiozin.yaml`
5. `/tiozin/tiozin.yaml`
6. `/config/tiozin.yaml`
7. `/tiozin.yaml`

The first file found wins. If none is found, Tiozin starts with built-in defaults (all registries are no-ops).

## Specifying the location explicitly

Three ways to point Tiozin at a specific file, in order of precedence:

**From the CLI:**

```bash
tiozin run examples/jobs/dummy.yaml --settings-file tiozin.example.yaml
```

**From Python:**

```python
from tiozin import TiozinApp

app = TiozinApp(settings_file="tiozin.example.yaml")
app.run("examples/jobs/dummy.yaml")
```

**From an environment variable:**

```bash
TIO_SETTING_REGISTRY_LOCATION=tiozin.example.yaml tiozin run examples/jobs/dummy.yaml
```

## Registry configuration

`tiozin.yaml` has a single top-level key: `registries`. Under it, you configure seven registries. See `tiozin.example.yaml` at the project root for a fully annotated example.

Every registry accepts the same set of fields:

```yaml
registries:
  job:
    kind: FileJobRegistry
    name: my-job-registry
    description: Local job registry for development
    location: examples/jobs
    timeout: 30
    readonly: false
    cache: false
```

### Registry fields

| Field | Default | Description |
|---|---|---|
| `kind` | see defaults table below | Plugin class name |
| `name` | `null` | Optional label for this registry instance |
| `description` | `null` | Optional description |
| `location` | `null` | Path or URL to the registry backend |
| `timeout` | `null` | Request timeout in seconds |
| `readonly` | `null` | When `true`, the registry rejects write operations |
| `cache` | `null` | When `true`, retrieved metadata is cached in memory |

### Default kinds

| Registry | Default kind |
|---|---|
| `settings` | `tio_kernel:FileSettingRegistry` |
| `job` | `tio_kernel:FileJobRegistry` |
| `schema` | `tio_kernel:NoOpSchemaRegistry` |
| `secret` | `tio_kernel:NoOpSecretRegistry` |
| `transaction` | `tio_kernel:NoOpTransactionRegistry` |
| `lineage` | `tio_kernel:NoOpLineageRegistry` |
| `metric` | `tio_kernel:NoOpMetricRegistry` |

Tiozin resolves plugin kinds by class name, looking up the class across all installed families. If two families define a class with the same name, qualify it with the family prefix: `tio_kernel:FileJobRegistry`.

## Templates in registry configuration

Any string field in a registry block accepts Jinja templates. Tiozin resolves them at startup, before the registry initializes.

```yaml
registries:
  transaction:
    kind: NoOpTransactionRegistry
    location: "postgresql://postgres:{{ ENV.PGPASSWORD | default('postgres') }}@localhost:5432/tiozin"

  lineage:
    kind: NoOpLineageRegistry
    location: "s3://my-bucket/lineage/{{ DAY.flat_date }}/"
    # → s3://my-bucket/lineage/2026-03-15/
```

Registry templates run at startup, before any job executes. Job variables (`name`, `org`, `domain`, `nominal_time`, and all other context fields) are not available here. Only two variables are injected:

| Variable | Description |
|---|---|
| `ENV.<NAME>` | Value of environment variable `NAME` |
| `DAY`, `D`, `day`, `d` | Current date and time at startup, as a `TemplateDate` |

`TemplateDate` exposes the same shorthands as in job templates (`ds`, `ts`, `flat_date`, `flat_year`, `deep_date`, etc.). See [templates.md](templates.md) for the full reference.

Use `| default(...)` for optional environment variables to avoid startup errors when the variable is not set.

Rendered values persist for the registry's entire lifetime. Tiozin restores the original template strings on shutdown.

## Settings delegation

A `tiozin.yaml` can delegate to another settings source by declaring `registries.settings`. Tiozin follows the chain until it reaches a file with no `settings` key.

```yaml
# tiozin.yaml
registries:
  settings:
    kind: FileSettingRegistry
    location: shared/tiozin.yaml

  job:
    kind: FileJobRegistry
    location: examples/jobs
```

```yaml
# shared/tiozin.yaml (no settings key, delegation stops here)
registries:
  schema:
    kind: NoOpSchemaRegistry
    location: http://schema-registry:8081
```

Registries from the final file in the chain take effect. A declared `settings` entry must have a `location`. Declaring one without a location raises an error at startup. Tiozin also detects cycles: if the same location appears twice in the chain, it raises an error.

## Environment-only settings

These settings have no `tiozin.yaml` equivalent. They can only be set via environment variables or `.env` files.

### General

| Variable | Default | Description |
|---|---|---|
| `HOSTNAME` | system hostname | Application hostname, used as pod name in Kubernetes |

### Logging

| Variable | Default | Description |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `TIO_LOG_DATE_FORMAT` | `iso` | Timestamp format in log output |
| `TIO_LOG_JSON` | `false` | Emit logs as JSON for log aggregation systems |
| `TIO_LOG_JSON_ENSURE_ASCII` | `false` | Force ASCII encoding in JSON logs |
| `TIO_LOG_SHOW_LOCALS` | `false` | Include local variables in exception tracebacks |

## Registry environment variables

Every registry field has a matching environment variable. These act as defaults: a value in `tiozin.yaml` always overrides the environment variable for the same field.

### Settings registry

| Variable | Default |
|---|---|
| `TIO_SETTING_REGISTRY_KIND` | `tio_kernel:FileSettingRegistry` |
| `TIO_SETTING_REGISTRY_LOCATION` | `null` |
| `TIO_SETTING_REGISTRY_TIMEOUT` | `null` |
| `TIO_SETTING_REGISTRY_READONLY` | `null` |
| `TIO_SETTING_REGISTRY_CACHE` | `null` |

### Job registry

| Variable | Default |
|---|---|
| `TIO_JOB_REGISTRY_KIND` | `tio_kernel:FileJobRegistry` |
| `TIO_JOB_REGISTRY_LOCATION` | `null` |
| `TIO_JOB_REGISTRY_TIMEOUT` | `null` |
| `TIO_JOB_REGISTRY_READONLY` | `null` |
| `TIO_JOB_REGISTRY_CACHE` | `null` |

### Schema registry

| Variable | Default |
|---|---|
| `TIO_SCHEMA_REGISTRY_KIND` | `tio_kernel:NoOpSchemaRegistry` |
| `TIO_SCHEMA_REGISTRY_LOCATION` | `null` |
| `TIO_SCHEMA_REGISTRY_TIMEOUT` | `null` |
| `TIO_SCHEMA_REGISTRY_READONLY` | `null` |
| `TIO_SCHEMA_REGISTRY_CACHE` | `null` |

### Secret registry

| Variable | Default |
|---|---|
| `TIO_SECRET_REGISTRY_KIND` | `tio_kernel:NoOpSecretRegistry` |
| `TIO_SECRET_REGISTRY_LOCATION` | `null` |
| `TIO_SECRET_REGISTRY_TIMEOUT` | `null` |
| `TIO_SECRET_REGISTRY_READONLY` | `null` |
| `TIO_SECRET_REGISTRY_CACHE` | `null` |

### Transaction registry

| Variable | Default |
|---|---|
| `TIO_TRANSACTION_REGISTRY_KIND` | `tio_kernel:NoOpTransactionRegistry` |
| `TIO_TRANSACTION_REGISTRY_LOCATION` | `null` |
| `TIO_TRANSACTION_REGISTRY_TIMEOUT` | `null` |
| `TIO_TRANSACTION_REGISTRY_READONLY` | `null` |
| `TIO_TRANSACTION_REGISTRY_CACHE` | `null` |

### Lineage registry

| Variable | Default |
|---|---|
| `TIO_LINEAGE_REGISTRY_KIND` | `tio_kernel:NoOpLineageRegistry` |
| `TIO_LINEAGE_REGISTRY_LOCATION` | `null` |
| `TIO_LINEAGE_REGISTRY_TIMEOUT` | `null` |
| `TIO_LINEAGE_REGISTRY_READONLY` | `null` |
| `TIO_LINEAGE_REGISTRY_CACHE` | `null` |

### Metric registry

| Variable | Default |
|---|---|
| `TIO_METRIC_REGISTRY_KIND` | `tio_kernel:NoOpMetricRegistry` |
| `TIO_METRIC_REGISTRY_LOCATION` | `null` |
| `TIO_METRIC_REGISTRY_TIMEOUT` | `null` |
| `TIO_METRIC_REGISTRY_READONLY` | `null` |
| `TIO_METRIC_REGISTRY_CACHE` | `null` |

## .env files

Tiozin loads `.env` files automatically from these locations, in order:

1. `/etc/tiozin/.env` (system-wide)
2. `~/.env`
3. `~/.config/tiozin/.env`
4. `/config/.env`
5. `/tiozin/.env`
6. `.env` in the current directory and all parent directories

Later files take precedence over earlier ones. A project `.env` overrides system defaults. Variables set directly in the shell always take precedence over `.env` files.

Copy `.env.example` from the project root to get started:

```bash
cp .env.example .env
```
