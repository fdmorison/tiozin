# How to Configure OpenLineage

Send job lineage events to any [OpenLineage](https://openlineage.io/)-compatible backend: Marquez, OpenMetadata, or any service that accepts the OpenLineage HTTP API.

## The basics

Add `OpenLineageRegistry` to your `tiozin.yaml`:

```yaml
registries:
  lineage:
    kind: tio_kernel:OpenLineageRegistry
    location: http://localhost:5000
```

That is all you need. On every job run, Tiozin emits `START`, `COMPLETE`, and `FAIL` events automatically. You do not call any lineage methods in your code.

## What gets emitted

Each event follows the [OpenLineage RunEvent spec](https://openlineage.io/docs/spec/object-model/):

```json
{
  "eventType": "COMPLETE",
  "eventTime": "2026-03-21T19:00:00+00:00",
  "run": { "runId": "abc123" },
  "job": {
    "namespace": "acme.latam.ecommerce.checkout",
    "name": "orders_etl"
  },
  "inputs": [
    {
      "namespace": "s3://my-bucket",
      "name": "raw/orders",
      "facets": {
        "schema": {
          "fields": [
            {"name": "order_id", "type": "long"},
            {"name": "customer.id", "type": "long"}
          ]
        }
      }
    }
  ],
  "outputs": [
    {
      "namespace": "file",
      "name": ".output/lake/orders",
      "facets": {}
    }
  ]
}
```

The job `namespace` comes from the job's `namespace` field. When not set, it is derived from the job's taxonomy using `TIO_JOB_NAMESPACE_TEMPLATE` (default: `{{org}}.{{region}}.{{domain}}.{{subdomain}}`).

By default, each step reports a logical dataset derived from the job's taxonomy. Override `external_datasets()` to report the physical dataset the step actually touches (a table, a path, a topic).

When a dataset has a schema attached, it is included in the lineage event. Nested structs use dot notation (`customer.id`). Array elements use bracket notation (`items[].sku`).

## Emit level

By default, Tiozin emits one pair of events per job run (job-level lineage). You can switch to step-level or emit both.

| Value | What gets emitted |
|---|---|
| `JOB` | One START/COMPLETE/FAIL per job (default) |
| `STEP` | One START/COMPLETE/FAIL per step (Input, Transform, Output) |
| `ALL` | Both job-level and step-level events |

Set it in `tiozin.yaml`:

```yaml
registries:
  lineage:
    kind: tio_kernel:OpenLineageRegistry
    location: http://localhost:5000
    emit_level: ALL
```

Or via environment variable:

```bash
TIO_LINEAGE_REGISTRY_EMIT_LEVEL=ALL
```

Step-level events carry a `parent` facet pointing to the job run, so your lineage backend can group them correctly.

## Lineage is best-effort

Lineage errors never interrupt job execution. If the backend is unreachable or returns an error, Tiozin logs a warning and continues. You will not see a job failure because of a lineage issue.

## Marquez

Point `location` at the Marquez API and open the UI at port `3000`:

```yaml
registries:
  lineage:
    kind: tio_kernel:OpenLineageRegistry
    location: "http://{{ ENV.MARQUEZ_HOST | default('localhost') }}:5000"
```

## Authentication

Set `api_key` to send a `Bearer` token with every request:

```yaml
registries:
  lineage:
    kind: tio_kernel:OpenLineageRegistry
    location: http://openmetadata:4000
    api_key: "{{ ENV.OPENLINEAGE_API_KEY }}"
```

## Custom transport

Any extra field in the registry block is forwarded as a keyword argument to `OpenLineageClient`. Use this for non-HTTP transports.

Kafka example:

```yaml
registries:
  lineage:
    kind: tio_kernel:OpenLineageRegistry
    transport:
      type: kafka
      topicName: openlineage.events
      messageKey: some-value
      properties:
        bootstrap.servers: localhost:9092
        acks: all
        retries: 3
        key.serializer: org.apache.kafka.common.serialization.StringSerializer
        value.serializer: org.apache.kafka.common.serialization.StringSerializer
```

For the full list of transport options, see the [OpenLineage Python client reference](https://openlineage.io/docs/client/python/#transport).

## Job namespace

The job namespace places the job in your organization's lineage graph. By default it is `{{org}}.{{region}}.{{domain}}.{{subdomain}}`.

Override it on a specific job:

```yaml
kind: LinearJob
name: orders_etl
namespace: acme.latam.ecommerce.checkout
```

Change the global default with `TIO_JOB_NAMESPACE_TEMPLATE`:

```bash
TIO_JOB_NAMESPACE_TEMPLATE="{{org}}.{{domain}}"
```

The namespace is always logical: it represents where the job fits in your organization, not where the data lives.

## Dataset namespaces

Dataset namespaces point to the system where data physically lives. Follow the [OpenLineage naming spec](https://openlineage.io/docs/spec/naming/) for the correct format per backend:

| System | Namespace format |
|---|---|
| S3 | `s3://my-bucket` |
| GCS | `gs://my-bucket` |
| Postgres | `postgres://host:5432` |
| Kafka | `kafka://broker:9092` |
| BigQuery | `bigquery` |

Override `external_datasets()` on your Input or Output to report the physical dataset it touches:

```python
from tiozin import Output, Dataset, Datasets


class PostgresOutput(Output[str]):
    def __init__(self, table: str, **options) -> None:
        super().__init__(**options)
        self.table = table

    def write(self, data: str) -> None:
        ...

    def external_datasets(self) -> Datasets:
        return Datasets(
            outputs=[Dataset.postgres("host", 5432, "mydb", "public", self.table)],
        )
```

Steps that do not override `external_datasets()` fall back to a logical dataset derived from the job's taxonomy.

## All parameters

| Property | Default | Description |
|---|---|---|
| `kind` | | `tio_kernel:OpenLineageRegistry` |
| `location` | | Base URL of the OpenLineage backend |
| `emit_level` | `JOB` | Emission level: `JOB`, `STEP`, or `ALL` |
| `timeout` | `3` | HTTP request timeout in seconds |
| `verify` | `true` | Verify TLS certificates |
| `api_key` | | Bearer token for API key authentication |
| `readonly` | `false` | Reject write operations |
| `cache` | `false` | Cache retrieved metadata in memory |
| `name` | | Display name for this registry instance |
| `description` | | Human-readable description |
