# Dependencies

A reference for contributors and platform engineers. After reading, you will know what each library does, why it was chosen, and how much disk space each install group costs including transitive dependencies. Use it to evaluate the cost of adding or removing a dependency, or to decide which extras belong in a given Docker image or cluster environment.

5 min read. Sizes are approximate and exclude package versions, which drift.

## How Dependencies Are Grouped

Tiozin has a core set and three optional extras, one per provider family.

The core installs with `pip install tiozin` and carries everything the framework needs to parse jobs, render templates, and run the compose engine. It does not include any execution engine.

`tio_kernel` is always installed as a family. The `tiozin[tio_kernel]` extra installs only the external libraries required by tio_kernel plugins that depend on them (state and secret backends). `tio_duckdb` and `tio_spark` follow the same pattern for their execution engines.

| Install | Adds | Approximate footprint |
|---------|------|-----------------------|
| `pip install tiozin` | Core framework | ~15 MB |
| `pip install tiozin[tio_kernel]` | External libs for state and secret backends | ~230 MB |
| `pip install tiozin[tio_duckdb]` | DuckDB engine | ~56 MB |
| `pip install tiozin[tio_spark]` | Spark engine | ~350 MB |

## Core Dependencies

These install with every Tiozin and total roughly 15 MB. None of them is an execution engine.

| Library | Approximate size | Role |
|---------|------------------|------|
| [pydantic](https://docs.pydantic.dev/) | ~3 MB | Foundation for modeling, serializing, and deserializing the entire Tiozin metadata model |
| [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | ~0.5 MB | Foundation for the metadata model with environment variable resolution, complementing pydantic in the same goal |
| [fsspec](https://filesystem-spec.readthedocs.io/) | ~3 MB | Foundation for reading and writing files from almost anywhere just by specifying a path: local disk, S3, GCS, Azure, or SFTP, as long as credentials are in place |
| [pendulum](https://pendulum.eustace.io/docs/) | ~1 MB | Foundation for all date and time logic across the framework: template date functions, lineage timestamps, and state tracking |
| [jinja2](https://jinja.palletsprojects.com/) | ~1 MB | Foundation for the Tiozin template system, which allows job definitions to reference environment variables, dates, and secrets inline |
| [ruamel.yaml](https://yaml.dev/doc/ruamel.yaml/) | ~1 MB | Foundation for the declarative approach: all YAML job definitions go through ruamel. Chosen over PyYAML because it preserves comments and supports YAML 1.2 |
| [wrapt](https://wrapt.readthedocs.io/) | ~0.6 MB | Foundation for the proxy system that intercepts and enriches every plugin call, enabling lineage, metrics, logging, and state tracking without touching plugin code |
| [openlineage-python](https://openlineage.io/docs/client/python) | ~0.6 MB | Foundation for lineage tracking: provides the standard data models (datasets, run events, facets) that Tiozin emits to any OpenLineage-compatible backend |
| [structlog](https://www.structlog.org/) | ~0.5 MB | Foundation for pipeline execution logging. Every execution event goes through structlog, which formats and routes log output |
| [typer](https://typer.tiangolo.com/) | ~0.2 MB | Foundation for the `tiozin` CLI command and every subcommand it exposes |
| [uuid-utils](https://github.com/aminalaee/uuid-utils) | ~0.8 MB | Utility for generating run and state identifiers for Tiozin |
| [environs](https://github.com/sloria/environs) | < 0.1 MB | Foundation for simple environment variables that do not need to be part of a serializable Pydantic model |
| [single-source](https://github.com/rabbit72/single-source) | < 0.1 MB | Foundation for Tiozin version tracking, so it never falls out of sync with the installed package |
| [python-slugify](https://github.com/un33k/python-slugify) | < 0.1 MB | Utility for creating normalized, filesystem-safe and database-safe slugs for naming ETL steps (Inputs, Transforms, Outputs) and jobs |
| [pyhumps](https://humps.readthedocs.io/) | < 0.1 MB | Utility for converting camelCase field names from external schemas to snake_case during schema inference |

## Optional Family Dependencies

### Tio Kernel

`pip install tiozin[tio_kernel]` installs the external libraries required by tio_kernel plugins, roughly 230 MB including all transitive dependencies.

| Library | Approximate size | Role |
|---------|------------------|------|
| [pyiceberg](https://py.iceberg.apache.org/) | ~3.5 MB direct, ~170 MB with transitives | Reads and writes state in [Apache Iceberg](https://iceberg.apache.org/docs/latest/) tables. Installed with the `pyarrow` extra, which pulls [PyArrow](https://arrow.apache.org/docs/python/) (~143 MB) and [zstandard](https://github.com/indygreg/python-zstandard) (~23 MB) |
| [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) | ~1 MB direct, ~25 MB with transitives | Backs the AWS Parameter Store secret registry. Most of the weight is `botocore` (~23 MB) |
| [google-cloud-secret-manager](https://cloud.google.com/secret-manager/docs/reference/libraries) | ~1 MB direct, ~35 MB with transitives | Backs the [GCP Secret Manager](https://cloud.google.com/secret-manager/docs) registry. Pulls `grpc` (~16 MB) and the Google API/auth/protobuf stack |

The dominant cost is `pyarrow` (~143 MB), pulled transitively by `pyiceberg[pyarrow]`. If `pyarrow` is already present in the environment (e.g. the image already has `tio_spark` installed), that cost is not duplicated.

### Tio DuckDB

`pip install tiozin[tio_duckdb]` adds the embedded analytical engine, roughly 56 MB.

| Library | Approximate size | Role |
|---------|------------------|------|
| [duckdb](https://duckdb.org/docs/) | ~56 MB | The DuckDB execution engine, an in-process analytical database |

### Tio Spark

`pip install tiozin[tio_spark]` adds the Spark engine, roughly 350 MB.

| Library | Approximate size | Role |
|---------|------------------|------|
| [pyspark](https://spark.apache.org/docs/latest/api/python/) | ~340 MB | The [Apache Spark](https://spark.apache.org/docs/latest/) execution engine |
| [databricks-sdk](https://databricks-sdk-py.readthedocs.io/) | ~11 MB | Present only because of runtime imports in `datacontract-cli` |

## Related

- [Contributing](CONTRIBUTING.md)
- [Family Model: Tios and Tiozins](concepts/family.md)
- [Settings Guide](settings/index.md)
