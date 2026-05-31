# Settings Guide

`tiozin.yaml` is the framework configuration file. It is separate from your job files.

Job files define what to do: which plugins to run, with what inputs and outputs. `tiozin.yaml` defines how the framework is wired: which registry services to use, where to find them, and how to reach them.

This separation is intentional. Service URLs, endpoints, and credentials belong in one place. If a registry URL changes, you update `tiozin.yaml` once. You do not touch any job file.

Framework configuration has two independent layers:

- `tiozin.yaml`: declares which registries to use and where to find them
- Environment variables: control logging, hostname, and registry defaults

Both layers work independently. Values in `tiozin.yaml` override the matching environment variable for the same field. See [YAML reference](reference.md) and [environment variable reference](env.md) for lookup tables.

## The simplest setup

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

Registries you do not declare fall back to their defaults. See [Default kinds](reference.md#default-kinds) for the full list.

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
export TIO_SETTING_REGISTRY_LOCATION=tiozin.example.yaml
tiozin run examples/jobs/dummy.yaml
```

## Registries

`tiozin.yaml` has a `registries` key where you configure up to seven registries. Each registry connects the framework to a backend service: job definitions, schemas, and secrets.

Every registry block uses the same set of fields:

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

See [Registry fields](reference.md#registry-fields) for a description of each field and [Default kinds](reference.md#default-kinds) for what Tiozin uses when you omit a registry.

Tiozin resolves plugin kinds by class name, looking up the class across all installed families. If two families define a class with the same name, qualify it with the family prefix: `tio_kernel:FileJobRegistry`.

The `transaction` and `metric` registries are declared in the framework as reserved slots. They accept configuration but are not yet backed by functional implementations.

## Runtime defaults

`runtime_defaults` declares fallback arguments for specific plugin kinds. When a job loads a plugin matching a declared `kind`, any fields not explicitly set in the job definition are filled from the defaults here.

```yaml
runtime_defaults:

  - kind: LocalRunner
    log_level: info

  - kind: SqlTransform
    dialect: ansi

  - kind: CsvInput
    encoding: utf-8
    schema_subject: auto

  - kind: ParquetOutput
    compression: snappy
    mode: append
```

Job arguments always win. Defaults fill in missing or `null` fields only, including inside nested mappings.

## Templates in configuration

Both `registries` and `runtime_defaults` string fields accept Jinja2 templates, but with different variable scopes.

### Registry fields

```yaml
registries:
  lineage:
    kind: OpenLineageRegistry
    location: "http://{{ ENV.MARQUEZ_HOST | default('localhost') }}:5000"
    # → http://marquez:5000
```

Tiozin resolves these templates at setup time. Only two variables are available:

| Variable | Description |
|---|---|
| `ENV.<NAME>` | Value of environment variable `NAME` |
| `DAY` | Current date and time at setup, as a [TemplateDate](../templates.md) |

Rendered values remain in effect for the registry's entire lifetime. Tiozin restores the original template strings on teardown.

### Runtime defaults fields

```yaml
runtime_defaults:
  - kind: CsvInput
    encoding: "{{ ENV.FILE_ENCODING | default('utf-8') }}"
    # → utf-8
```

| Variable | Description |
|---|---|
| `ENV.<NAME>` | Value of environment variable `NAME` |
| `SECRET.<NAME>` | Value of secret `NAME` from the secret registry |
| `DAY` | Current date and time, as a [TemplateDate](../templates.md) |
| `org`, `domain`, `product`, … | Job context fields |

## Settings delegation

A `tiozin.yaml` can hand off its configuration to another settings file by declaring a `setting` registry under `registries`. Tiozin boots that registry and reads its configuration instead. If that file also declares a `registries.setting`, the process repeats. The chain stops at the first file that has no `setting` key.

```yaml
# tiozin.yaml
registries:
  setting:
    kind: FileSettingRegistry
    location: shared/tiozin.yaml
```

```yaml
# shared/tiozin.yaml: no setting key, delegation stops here
registries:
  job:
    kind: AcmeJobRegistry
    location: https://acme.example.com/jobs
```

The registries from the final file in the chain take effect. Tiozin detects cycles: if the same location appears twice in the chain, it raises an error.
