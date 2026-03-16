# LinearJob

Runs a pipeline sequentially: inputs produce data, transforms process it in order, and outputs persist the result. This is the default job type and covers most ETL workloads.

```yaml
kind: LinearJob
name: my_job
```

## How data flows

Data moves in a single direction. Each stage consumes the result of the previous one.

### Simple pipeline

```text
┌───────┐    ┌─────────────┐    ┌─────────────┐    ┌────────┐
│ Input │───►│ Transform 1 │───►│ Transform 2 │───►│ Output │
└───────┘    └─────────────┘    └─────────────┘    └────────┘
```

### Multiple inputs

When multiple inputs are present, each regular transform processes each dataset independently. To combine them into a single stream, use a `CoTransform` as the first transform. A `CoTransform` receives all datasets as arguments at once:

```text
┌─────────┐    ┌──────────────────┐
│ Input 1 │───►│                  │
└─────────┘    │   CoTransform    │    ┌─────────────┐    ┌────────┐
┌─────────┐    │ (join, union...) │───►│ Transform 2 │───►│ Output │
│ Input 2 │───►│                  │    └─────────────┘    └────────┘
└─────────┘    │                  │
┌─────────┐    │                  │
│ Input N │───►│                  │
└─────────┘    └──────────────────┘
```

SQL-based transforms in families like `tio_spark` and `tio_duckdb` are `CoTransform` implementations — they can reference all upstream inputs by name in the query.

### Multiple outputs

All outputs receive the same final dataset:

```text
                                ┌──────────┐
                                │ Output 1 │
                            ───►└──────────┘
┌───────┐    ┌─────────────┐    ┌──────────┐
│ Input │───►│ Transform 1 │───►│ Output 2 │
└───────┘    └─────────────┘    └──────────┘
                            ───►┌──────────┐
                                │ Output N │
                                └──────────┘
```

### Multiple inputs and multiple outputs

All inputs are combined by the `CoTransform`, and the final dataset is then written to all outputs:

```text
┌─────────┐    ┌──────────────────┐                     ┌──────────┐
│ Input 1 │───►│                  │                     │ Output 1 │
└─────────┘    │   CoTransform    │                 ───►└──────────┘
┌─────────┐    │ (join, union...) │    ┌───────────┐    ┌──────────┐
│ Input 2 │───►│                  │───►│ Transform │───►│ Output 2 │
└─────────┘    │                  │    └───────────┘    └──────────┘
┌─────────┐    │                  │                 ───►┌──────────┐
│ Input N │───►│                  │                     │ Output N │
└─────────┘    └──────────────────┘                     └──────────┘
```

## Design intent

`LinearJob` intentionally avoids modeling arbitrary DAGs. Its goal is a clear, easy-to-reason-about execution model that fits most ETL workloads. For pipelines that require branching or complex dependency graphs, use a dedicated orchestrator and model each branch as a separate Tiozin job.
