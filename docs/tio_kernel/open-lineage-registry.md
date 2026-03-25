# OpenLineageRegistry

Sends run events to any [OpenLineage](https://openlineage.io/)-compatible backend (Marquez, OpenMetadata, and others) via `POST /api/v1/lineage`.

```yaml
registries:
  lineage:
    kind: tio_kernel:OpenLineageRegistry
    location: http://localhost:5000
```

## Parameters

| Property | Description | Default |
|---|---|---|
| `location` | Base URL of the OpenLineage backend | none |
| `timeout` | HTTP request timeout in seconds | `3` |
| `verify` | Verify TLS certificates | `true` |
| `api_key` | Bearer token for API key authentication | none |
| `readonly` | Reject write operations | `false` |
| `cache` | Cache retrieved metadata in memory | `false` |
| `name` | Display name for this registry instance | class name |
| `description` | Human-readable description | none |

## How it works

You do not call lineage methods directly. The framework emits events automatically at each job lifecycle transition:

| State | When |
|---|---|
| `START` | After `job.setup()` and `runner.setup()`, before `submit()` |
| `COMPLETE` | After `submit()` returns successfully |
| `FAIL` | When an exception occurs during execution |

## Event structure

Each event follows the OpenLineage `RunEvent` spec:

```json
{
  "eventType": "COMPLETE",
  "eventTime": "2026-03-21T19:00:00+00:00",
  "run": {
    "runId": "job_abc123"
  },
  "job": {
    "namespace": "acme.latam.ecommerce.checkout",
    "name": "orders_etl"
  },
  "inputs": [
    {
      "namespace": "s3://my-bucket",
      "name": "raw/orders"
    }
  ],
  "outputs": [
    {
      "namespace": "file",
      "name": ".output/lake/orders"
    }
  ],
  "producer": "tiozin"
}
```

The job `namespace` comes from the job's `namespace` field. When not set explicitly, it is derived from `TIO_JOB_NAMESPACE_TEMPLATE` (default: `org.region.domain.subdomain`). The `name` is the job slug.

Inputs and outputs in the event are the physical datasets reported by each step. File plugins report the actual paths. Postgres plugins report the target table. Steps that do not override `lineage()` fall back to a logical dataset derived from the step's taxonomy fields.


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

Any extra field in the manifest is forwarded as a keyword argument to `OpenLineageClient`. This lets you configure transports beyond the default HTTP setup.

The example below uses Kafka. The `transport` field is passed directly as `transport=` to `OpenLineageClient`:

```yaml
registries:
  lineage:
    kind: tio_kernel:OpenLineageRegistry
    transport:
      type: kafka
      topicName: openlineage.events
      messageKey: some-value
      properties:
        bootstrap.servers: localhost:9092,another.host:9092
        acks: all
        retries: 3
        key.serializer: org.apache.kafka.common.serialization.StringSerializer
        value.serializer: org.apache.kafka.common.serialization.StringSerializer
```

For the full list of transport types and their options, see the [OpenLineage client configuration reference](https://openlineage.io/docs/client/python/#transport).

## Using with Marquez

Point `location` at the Marquez API and run the UI at port `3000`:

```yaml
registries:
  lineage:
    kind: tio_kernel:OpenLineageRegistry
    location: "http://{{ ENV.MARQUEZ_HOST | default('localhost') }}:5000"
    # → http://localhost:5000
```
