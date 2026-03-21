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
| `location` | Base URL of the OpenLineage backend | required |
| `timeout` | HTTP request timeout in seconds | `10` |

## How it works

You do not call lineage methods directly. The framework emits events automatically at each job lifecycle transition:

| State | When |
|---|---|
| `START` | After `setup()`, before `submit()` |
| `COMPLETE` | After `submit()` returns successfully |
| `FAIL` | When `submit()` raises an exception |

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
    "namespace": "acme.us-east.finance.orders.gold",
    "name": "orders-etl"
  },
  "inputs": [
    {
      "namespace": "acme.us-east.finance.orders.gold",
      "name": "raw.orders"
    }
  ],
  "outputs": [
    {
      "namespace": "acme.us-east.finance.orders.gold",
      "name": "orders"
    }
  ],
  "producer": "tiozin"
}
```

The `namespace` is built from the job's `org`, `region`, `domain`, `subdomain`, and `layer` fields joined by `.`. The `name` is the job slug.

## Inputs and outputs

`inputs` and `outputs` are empty by default. Pass dataset names when calling `register()` directly:

```python
self.context.registries.lineage.register(
    event.run_id,
    RunEvent.from_context(
        self.context,
        RunState.COMPLETE,
        inputs=["finance.raw_orders"],
        outputs=["finance.orders"],
    ),
)
```

For the automatic lifecycle events emitted by `JobProxy`, `inputs` and `outputs` are always empty. Dataset-level lineage requires explicit calls.

## Using with Marquez

Point `location` at the Marquez API and run the UI at port `3000`:

```yaml
registries:
  lineage:
    kind: tio_kernel:OpenLineageRegistry
    location: "http://{{ ENV.MARQUEZ_HOST | default('localhost') }}:5000"
    # → http://localhost:5000
```
