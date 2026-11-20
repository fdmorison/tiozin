# Tech Stack

## Core

- Python
- Pydantic
- structlog
- Pendulum
- Jinja2 (`StrictUndefined`)
- ruamel-yaml

## Job Definitions

- YAML-based
- Flat and human-readable

## Filesystems and Protocols

Any filesystem or protocol supported by `fsspec`.

## Engines

The reference families, maintained in their own repositories, target:
- Spark (`tio_spark`): https://github.com/fdmorison/tio_spark
- DuckDB (`tio_duckdb`): https://github.com/fdmorison/tio_duckdb

Other families may target technologies such as:
- Flink
- Trino
- Apache Beam
- Redshift
- BigQuery
- Postgres
- Kafka
