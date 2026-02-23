# Creating a Provider Family

A provider family is an independent Python package that adds new execution backends to Tiozin. Families are discovered automatically via Python `entry_points`.

---

## Package naming

Provider packages must be prefixed with `tio_` or `tia_`:

- `tio_mongo`
- `tia_cassandra`
- `tio_john`

The prefix is how the framework identifies and groups your Tiozins. Pick whichever prefix fits your style — both work identically.

---

## Project structure

```
tio_mongo/
├── pyproject.toml
├── tio_mongo/
│   ├── __init__.py          ← public API
│   ├── runners/
│   │   └── mongo_runner.py
│   ├── inputs/
│   │   └── mongo_input.py
│   ├── outputs/
│   │   └── mongo_output.py
│   └── transforms/
│       └── mongo_transform.py
```

---

## Registering via entry_points

In `pyproject.toml`, declare your family under the `tiozin.family` group:

```toml
[project.entry-points."tiozin.family"]
tio_mongo = "tio_mongo"
```

The key is the family name (your package name). The value is the Python import path of your package's `__init__.py`.

Tiozin discovers all installed families at startup by scanning packages registered under `tiozin.family`. Discovery relies exclusively on `entry_points` — no manual registration is needed.

---

## Public API

Export all public Tiozins from your package's `__init__.py`:

```python
# tio_mongo/__init__.py
from .runners.mongo_runner import MongoRunner as MongoRunner
from .inputs.mongo_input import MongoInput as MongoInput
from .outputs.mongo_output import MongoOutput as MongoOutput
```

Only symbols exported from `__init__.py` are part of your public API. Internal modules may change without notice.

---

## What to include

A family typically provides:

- One or more **Runners** (required — defines the execution engine)
- One or more **Inputs** (reads from the technology)
- One or more **Outputs** (writes to the technology)
- Optionally **Transforms** (technology-specific transformations)
- Optionally **Registries** (metadata services backed by the technology)

You do not need to implement all roles. Provide only what makes sense for your technology.

---

## Installing a family

Because families are independent packages, users install them separately:

```bash
pip install tio_mongo
```

Once installed, all Tiozins from your family are immediately available in job YAML files using their class name as the `kind`.

---

## What's next?

See [Creating Pluggable Tiozins](tiozins.md) for how to implement each role — Runner, Input, Transform, Output, and Registry.
