# Settings Reference

Tiozin configuration has two independent layers:

- `tiozin.yaml`: declares which registries to use and where to find them
- Environment variables: control logging, hostname, and registry defaults

Both layers work independently. Values in `tiozin.yaml` override the matching environment variable for the same field.

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

Registries you do not declare fall back to their defaults (see [Default kinds](#default-kinds)).

## How Tiozin finds tiozin.yaml

If you do not specify a location explicitly, Tiozin searches for `tiozin.yaml` in this order:

1. Current working directory (`tiozin.yaml`)
2. `~/tiozin.yaml`
3. `~/.config/tiozin/tiozin.yaml`
4. `/etc/tiozin/tiozin.yaml`
5. `/tiozin/tiozin.yaml`
6. `/config/tiozin.yaml`
7. `/tiozin.yaml`

The first file found wins. If none is found, Tiozin starts with built-in defaults.

## Specifying the location explicitly

Three ways to point Tiozin at a specific file, in order of precedence:

**From the CLI:**

```bash
tiozin run examples/jobs/dummy.yaml --settings-path tiozin.example.yaml
```

**From Python:**

```python
from tiozin import TiozinApp

app = TiozinApp(settings_path="tiozin.example.yaml")
app.run("examples/jobs/dummy.yaml")
```

**From an environment variable:**

```bash
TIO_SETTING_REGISTRY_LOCATION=tiozin.example.yaml tiozin run examples/jobs/dummy.yaml
```

## Validating jobs without running them

`tiozin validate` checks one or more job manifests for errors without executing them.

```bash
tiozin validate examples/jobs/dummy.yaml
```

Validate multiple jobs in one call:

```bash
tiozin validate examples/jobs/ingest.yaml examples/jobs/transform.yaml
```

Use `--settings-path` to point at a specific settings file:

```bash
tiozin validate examples/jobs/dummy.yaml --settings-path tiozin.staging.yaml
```

Exit codes:

| Code | Meaning |
|---|---|
| `0` | All jobs are valid |
| `1` | Unexpected error (bug or provider error) |
| `2` | Validation error (invalid manifest, missing fields, unknown job identifier) |

`tiozin validate` runs the full settings and registry stack but stops before building or submitting the job. Use it in CI/CD pipelines to catch manifest errors early.

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
    failfast: false
```

### Registry fields

| Field | Description | Default |
|---|---|---|
| `kind` | Plugin class name | see [Default kinds](#default-kinds) |
| `name` | Optional label for this registry instance | `null` |
| `description` | Optional description | `null` |
| `location` | Path or URL to the registry backend | `null` |
| `timeout` | Request timeout in seconds | `3` |
| `readonly` | When `true`, the registry rejects write operations | `false` |
| `cache` | When `true`, retrieved metadata is cached in memory | `false` |
| `failfast` | When `true`, raises an error when metadata is not found; when `false`, returns `null` | `false` |

### Default kinds

| Registry | Default kind |
|---|---|
| `setting` | `tio_kernel:FileSettingRegistry` |
| `job` | `tio_kernel:FileJobRegistry` |
| `schema` | `tio_kernel:FileSchemaRegistry` |
| `secret` | `tio_kernel:EnvSecretRegistry` |
| `transaction` | `tio_kernel:NoOpTransactionRegistry` |
| `lineage` | `tio_kernel:NoOpLineageRegistry` |
| `metric` | `tio_kernel:NoOpMetricRegistry` |

Tiozin resolves plugin kinds by class name, looking up the class across all installed families. If two families define a class with the same name, qualify it with the family prefix: `tio_kernel:FileJobRegistry`.

## Templates in registry configuration

Any string field in a registry block accepts Jinja templates. Tiozin resolves them at setup time, before the registry starts accepting requests.

```yaml
registries:
  transaction:
    kind: NoOpTransactionRegistry
    location: "postgresql://postgres:{{ ENV.PGPASSWORD | default('postgres') }}@localhost:5432/tiozin"

  lineage:
    kind: OpenLineageRegistry
    location: "http://{{ ENV.MARQUEZ_HOST | default('localhost') }}:5000"
    # → http://marquez:5000
```

Only two variables are available during registry setup:

| Variable | Description |
|---|---|
| `ENV.<NAME>` | Value of environment variable `NAME` |
| `DAY` | Current date and time at setup, as a [TemplateDate](templates.md) |

All [TemplateDate](templates.md) shorthands (`ds`, `ts`, `flat_date`, `flat_year`, `deep_date`, etc.) are also injected directly, so `{{ ds }}` works the same as `{{ DAY.ds }}`.

Use `| default(...)` for optional environment variables to avoid errors when the variable is not set.

Rendered values remain in effect for the registry's entire lifetime. Tiozin restores the original template strings on teardown.

Job variables (`name`, `org`, `domain`, `nominal_time`, and other context fields) are not available here. `SECRET` is also not available: registries are set up before the secret registry is initialized, so secrets cannot be used to configure other registries.

## Settings delegation

A `tiozin.yaml` can hand off its configuration to another settings file by declaring a `setting` registry under `registries`. Tiozin boots that registry and reads its configuration instead. If that file also declares a `registries.setting`, the process repeats. The chain stops at the first file that has no `setting` key.

```yaml
# tiozin.yaml
registries:
  setting:
    kind: FileSettingRegistry
    location: shared/tiozin.yaml

  job:
    kind: FileJobRegistry
    location: examples/jobs
```

```yaml
# shared/tiozin.yaml: no setting key, delegation stops here
registries:
  schema:
    kind: NoOpSchemaRegistry
    location: http://schema-registry:8081
```

The registries from the final file in the chain take effect. Tiozin detects cycles: if the same location appears twice in the chain, it raises an error.

## Environment-only settings

These settings have no `tiozin.yaml` equivalent. They can only be set via environment variables or `.env` files.

### General

| Variable | Description | Default |
|---|---|---|
| `HOSTNAME` | Application hostname, used as pod name in Kubernetes | system hostname |

### Logging

| Variable | Description | Default |
|---|---|---|
| `LOG_LEVEL` | Log level | `INFO` |
| `TIO_LOG_DATE_FORMAT` | Timestamp format in log output | `iso` |
| `TIO_LOG_JSON` | Emit logs as JSON for log aggregation systems | `false` |
| `TIO_LOG_JSON_ENSURE_ASCII` | Force ASCII encoding in JSON logs | `false` |
| `TIO_LOG_SHOW_LOCALS` | Include local variables in exception tracebacks | `false` |
| `TIO_LOG_REDACT_MIN_LENGTH` | Minimum secret length to qualify for redaction in logs | `3` |

Accepted values for `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

### Job

| Variable | Description | Default |
|---|---|---|
| `TIO_JOB_NAMESPACE_TEMPLATE` | Jinja template used to derive `namespace` when not set on the job | `{{org}}.{{region}}.{{domain}}.{{subdomain}}` |

Available template variables for `TIO_JOB_NAMESPACE_TEMPLATE`: `org`, `region`, `domain`, `subdomain`, `layer`, `product`, `model`.

## Registry environment variables

Every registry field has a matching environment variable. These act as defaults: a value in `tiozin.yaml` always overrides the environment variable for the same field.

### Settings registry

| Variable | Description | Default |
|---|---|---|
| `TIO_SETTING_REGISTRY_KIND` | Plugin class name | `tio_kernel:FileSettingRegistry` |
| `TIO_SETTING_REGISTRY_LOCATION` | Path or URL to the registry backend | `null` |
| `TIO_SETTING_REGISTRY_TIMEOUT` | Request timeout in seconds | `null` |
| `TIO_SETTING_REGISTRY_READONLY` | Reject write operations when set | `null` |
| `TIO_SETTING_REGISTRY_CACHE` | Cache retrieved metadata in memory when set | `null` |
| `TIO_SETTING_REGISTRY_FAILFAST` | Raise on missing metadata when set | `null` |

### Job registry

| Variable | Description | Default |
|---|---|---|
| `TIO_JOB_REGISTRY_KIND` | Plugin class name | `tio_kernel:FileJobRegistry` |
| `TIO_JOB_REGISTRY_LOCATION` | Path or URL to the registry backend | `null` |
| `TIO_JOB_REGISTRY_TIMEOUT` | Request timeout in seconds | `null` |
| `TIO_JOB_REGISTRY_READONLY` | Reject write operations when set | `null` |
| `TIO_JOB_REGISTRY_CACHE` | Cache retrieved metadata in memory when set | `null` |
| `TIO_JOB_REGISTRY_FAILFAST` | Raise on missing metadata when set | `null` |

### Schema registry

| Variable | Description | Default |
|---|---|---|
| `TIO_SCHEMA_REGISTRY_KIND` | Plugin class name | `tio_kernel:FileSchemaRegistry` |
| `TIO_SCHEMA_REGISTRY_LOCATION` | Path or URL to the registry backend | `null` |
| `TIO_SCHEMA_REGISTRY_TIMEOUT` | Request timeout in seconds | `null` |
| `TIO_SCHEMA_REGISTRY_READONLY` | Reject write operations when set | `null` |
| `TIO_SCHEMA_REGISTRY_CACHE` | Cache retrieved metadata in memory when set | `null` |
| `TIO_SCHEMA_REGISTRY_FAILFAST` | Raise on missing metadata when set | `null` |
| `TIO_SCHEMA_REGISTRY_SHOW_SCHEMA` | Log schemas after retrieval | `false` |
| `TIO_SCHEMA_REGISTRY_SUBJECT_TEMPLATE` | Jinja template used to derive the schema subject | `{{org}}.{{region}}.{{domain}}.{{subdomain}}.{{layer}}.{{product}}.{{model}}` |
| `TIO_SCHEMA_REGISTRY_DEFAULT_VERSION` | Schema version used when not specified | `latest` |

### Secret registry

| Variable | Description | Default |
|---|---|---|
| `TIO_SECRET_REGISTRY_KIND` | Plugin class name | `tio_kernel:EnvSecretRegistry` |
| `TIO_SECRET_REGISTRY_LOCATION` | Path or URL to the registry backend | `null` |
| `TIO_SECRET_REGISTRY_TIMEOUT` | Request timeout in seconds | `null` |
| `TIO_SECRET_REGISTRY_READONLY` | Reject write operations when set | `null` |
| `TIO_SECRET_REGISTRY_CACHE` | Cache retrieved metadata in memory when set | `null` |
| `TIO_SECRET_REGISTRY_FAILFAST` | Raise on missing metadata when set | `null` |

### Transaction registry

| Variable | Description | Default |
|---|---|---|
| `TIO_TRANSACTION_REGISTRY_KIND` | Plugin class name | `tio_kernel:NoOpTransactionRegistry` |
| `TIO_TRANSACTION_REGISTRY_LOCATION` | Path or URL to the registry backend | `null` |
| `TIO_TRANSACTION_REGISTRY_TIMEOUT` | Request timeout in seconds | `null` |
| `TIO_TRANSACTION_REGISTRY_READONLY` | Reject write operations when set | `null` |
| `TIO_TRANSACTION_REGISTRY_CACHE` | Cache retrieved metadata in memory when set | `null` |
| `TIO_TRANSACTION_REGISTRY_FAILFAST` | Raise on missing metadata when set | `null` |

### Lineage registry

| Variable | Description | Default |
|---|---|---|
| `TIO_LINEAGE_REGISTRY_KIND` | Plugin class name | `tio_kernel:NoOpLineageRegistry` |
| `TIO_LINEAGE_REGISTRY_LOCATION` | Path or URL to the registry backend | `null` |
| `TIO_LINEAGE_REGISTRY_TIMEOUT` | Request timeout in seconds | `null` |
| `TIO_LINEAGE_REGISTRY_READONLY` | Reject write operations when set | `null` |
| `TIO_LINEAGE_REGISTRY_CACHE` | Cache retrieved metadata in memory when set | `null` |
| `TIO_LINEAGE_REGISTRY_FAILFAST` | Raise on missing metadata when set | `null` |
| `TIO_LINEAGE_REGISTRY_EMIT_LEVEL` | Granularity of lineage events emitted | `JOB` |

Accepted values for `TIO_LINEAGE_REGISTRY_EMIT_LEVEL`: `JOB`, `STEP`, `ALL`.

### Metric registry

| Variable | Description | Default |
|---|---|---|
| `TIO_METRIC_REGISTRY_KIND` | Plugin class name | `tio_kernel:NoOpMetricRegistry` |
| `TIO_METRIC_REGISTRY_LOCATION` | Path or URL to the registry backend | `null` |
| `TIO_METRIC_REGISTRY_TIMEOUT` | Request timeout in seconds | `null` |
| `TIO_METRIC_REGISTRY_READONLY` | Reject write operations when set | `null` |
| `TIO_METRIC_REGISTRY_CACHE` | Cache retrieved metadata in memory when set | `null` |
| `TIO_METRIC_REGISTRY_FAILFAST` | Raise on missing metadata when set | `null` |

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
