# Creating a Provider Family

A provider family is an independent Python package that adds new execution backends to Tiozin. Families are discovered automatically via Python `entry_points`.

**A family is a package, not a plugin.** One entry_point registration makes the entire package available, and every class you choose to expose becomes a Tiozin. This is different from frameworks like Airflow, where each plugin class is registered individually. Register the family once and expose as many Tiozins as you need from a single package.

## Package naming

Provider packages must be prefixed with `tio_` or `tia_`:

- `tio_mongo`
- `tia_cassandra`
- `tio_john`

The prefix is how the framework identifies and groups your Tiozins. Pick whichever prefix fits your style. Both work identically.

## Project structure

```
tio_dilbert/
├── pyproject.toml
├── tio_dilbert/
│   ├── __init__.py     ← public API
│   ├── runners/
│   ├── inputs/
│   ├── outputs/
│   ├── transforms/
│   ├── registries/
│   ├── proxies/        ← optional: cross-cutting behavior
│   └── compose/        ← optional: assembly helpers, utilities
```

Add `proxies` and `compose` when you need shared behavior across all steps in your family or internal utilities that do not belong in the public API. See [Creating Pluggable Tiozins](tiozins.md) for how `@tioproxy` works.

## Registering via entry_points

In `pyproject.toml`, declare your family under the `tiozin.family` group:

```toml
[project.entry-points."tiozin.family"]
tio_dilbert = "tio_dilbert"
```

The key is the family name (your package name). The value is the Python import path of your package's `__init__.py`, which defines the family's public API.

This single declaration is the entire registration contract. Tiozin discovers all installed families at startup by scanning packages registered under `tiozin.family`, imports each one, and makes all their exported Tiozins available by class name. No additional registration calls, decorators, or configuration files are needed.

## Public API

The family's public API is defined by its `__init__.py`. Export every Tiozin you want users to access:

```python
# tio_dilbert/__init__.py
from .runners.dilbert_runner import DilbertRunner as DilbertRunner
from .inputs.dilbert_input import DilbertInput as DilbertInput
from .outputs.dilbert_output import DilbertOutput as DilbertOutput
```

Only symbols exported from `__init__.py` are part of the family's public API. Internal modules may change without notice.

## What to include

A family typically provides:

- One or more **Runners** (defines the execution engine)
- One or more **Inputs** (reads from the technology)
- One or more **Outputs** (writes to the technology)
- Optionally **Transforms** (technology-specific transformations)
- Optionally **Registries** (metadata services backed by the technology)

You do not need to implement all roles. Provide only what makes sense for your technology.

## Installing and using a family

Families are independent packages. Users install Tiozin and any families they need together:

```bash
pip install tiozin tio_dilbert
```

The first-party families `tio_spark` and `tio_duckdb` can also be installed as extras, which is a convenience alias for the same packages:

```bash
pip install tiozin[tio_spark]
pip install tiozin[tio_duckdb]
```

`tio_kernel` is the exception: it ships with Tiozin and requires no separate installation. The next section explains what it provides.

Once installed, all Tiozins from your family are immediately available in job YAML files using their class name as the `kind`:

```yaml
runner:
  kind: DilbertRunner

inputs:
  - kind: DilbertInput

outputs:
  - kind: DilbertOutput
```

### Declaring a Tiozin by class name

The short class name works as long as it is unique across all installed families. If two families export a class with the same name, qualify it with the family name:

```yaml
# Short name: works when unique across installed families
kind: DilbertInput

# Family-qualified: always unambiguous
kind: tio_dilbert:DilbertInput

# Full Python path: the last resort
kind: tio_dilbert.inputs.dilbert_input.DilbertInput
```

Use the short name by default. Switch to the family-qualified form if you get a `PluginConflictError` at startup.

## tio_kernel: the built-in family

`tio_kernel` is a special built-in provider family that ships with Tiozin. It is always present and cannot be disabled or replaced.

Its purpose is to guarantee that the system is always complete and executable, even when no additional families are installed.

### Functional defaults

`tio_kernel` ships production-ready implementations for common infrastructure needs:

| Plugin | Description |
|---|---|
| `FileJobRegistry` | Loads and stores job manifests from the filesystem (local paths or object storage via fsspec). Supports YAML and JSON |
| `FileSettingRegistry` | Loads framework configuration from any path or URI supported by fsspec |
| `EnvSecretRegistry` | Reads secrets from environment variables |
| `OpenLineageRegistry` | Sends run events to any OpenLineage-compatible backend (Marquez, OpenMetadata) via HTTP |

### No-op defaults

`tio_kernel` ships explicit no-op implementations for all execution plugin types and optional registries:

| Plugin | Description |
|---|---|
| `NoOpRunner` | Accepts any plan and returns `None`. No execution |
| `NoOpInput` | Returns `None`. No reads |
| `NoOpTransform` | Passes data through unchanged |
| `NoOpOutput` | Accepts data and discards it |
| `NoOpSecretRegistry` | Always returns `None`. No secret lookups |
| `NoOpSettingRegistry` | Always returns `None`. No settings |
| `NoOpSchemaRegistry` | Always returns `None`. No schema resolution |
| `NoOpLineageRegistry` | Discards all lineage events |
| `NoOpMetricRegistry` | Discards all metrics |
| `NoOpTransactionRegistry` | Discards all transactions |

These no-ops allow Tiozin to boot, validate configurations, and run dry-runs without any real execution backend.

### No-ops are not for production execution

The no-op execution plugins listed above are not intended for production workloads. For real execution, install a provider family such as `tio_spark` or `tio_duckdb`.

Other `tio_kernel` plugins are production-ready. `FileJobRegistry`, for example, reads job manifests from local paths or any object storage bucket on AWS, GCP, or Azure.

### Architectural boundary

Any plugin added to `tio_kernel` must justify why a default is necessary for system completeness. If a plugin can live in a specialized provider without affecting bootstrapping, validation, or demonstrability, it does not belong in `tio_kernel`.

## What's next?

See [Creating Pluggable Tiozins](tiozins.md) for how to implement each role: Runner, Input, Transform, Output, and Registry.
