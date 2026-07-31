# Batches

Learn what batches are, how they identify work, how they progress through their lifecycle, and how they carry metadata between executions.

Batches exist only for jobs whose backlog policy supports them. See [Jobs](jobs.md#backlog-policy) for the available backlog policies.

Reading time: about 5 minutes.

## What is a Batch?

A batch represents the data a job processes for a single nominal time.

A batch is identified by its **resource** and **nominal time**. The resource is defined by the job (`org`, `region`, `domain`, `subdomain`, `layer`, `product`, and `model`), while the nominal time identifies the processing window.

A batch is **not** an execution. It keeps the same identity regardless of how many times it is retried or replayed.

## Processing Window

Every batch covers a processing window, bounded by `nominal_start_time` and `nominal_end_time`.

Tiozin does not filter data by the window. It records the bounds on the batch, and the plugin reads them to decide what to fetch from the source.

For incremental jobs, the first batch typically covers the entire history, because `nominal_start_time` defaults to the Unix epoch:

```yaml
nominal_start_time: 1970-01-01T00:00:00Z
nominal_end_time: 2026-01-16T00:00:00Z
```

Subsequent batches continue from the previous window:

```yaml
nominal_start_time: 2026-01-16T00:00:00Z
nominal_end_time: 2026-01-17T00:00:00Z
```

Both bounds are truncated to the job's cadence, so a daily job always starts and ends on day boundaries, a minutely job on minute boundaries, and so on.

## Backlog

The backlog is the collection of batches awaiting processing for a resource. It holds every batch in `PENDING`, `RUNNING`, or `FAILED`:

- `PENDING` batches are waiting for their first attempt.
- `FAILED` batches remain eligible for retry until they exceed the retry limit or are quarantined.
- `RUNNING` batches are included because an interrupted execution may terminate before the batch can be transitioned to `FAILED`, so the batch is recovered and retried.

`SUCCEEDED`, `QUARANTINED`, and `CANCELED` batches are never in the backlog. A quarantined or canceled batch returns to it only through a replay.

Incremental jobs consume pending batches from the backlog and create new ones as processing advances. See [How to Work with Incremental Backlogs](../how-to/batches.md).

## Lifecycle

A batch is registered as `PENDING` and moves through the following states:

| Status | Meaning |
| --- | --- |
| `PENDING` | Queued and awaiting the start of processing |
| `RUNNING` | Actively being processed |
| `FAILED` | Processing failed, retried until the retry limit is exhausted |
| `SUCCEEDED` | Processing completed successfully |
| `QUARANTINED` | Definitively failed or isolated, excluded from the backlog until replayed |
| `CANCELED` | Abandoned by manual action, whether queued or in progress |

The transitions between them are:

- `PENDING → RUNNING → SUCCEEDED` is the happy path.
- A failure sends the batch to `FAILED`, and a later run retries it through `RUNNING`. Once the batch exhausts the retry limit of its registry, the run escalates it to `QUARANTINED` instead of retrying again.
- An operator can cancel a `PENDING` or `RUNNING` batch, and quarantine a `PENDING`, `RUNNING`, or `FAILED` one, through the `tiozin batch` commands.
- Any status can be replayed back to `PENDING`, which restarts the retry count at zero.

## Batch Members

### Identity

Identifies the data product the batch belongs to and the slice of data it represents. All fields are immutable after registration except `nominal_end_time`, which may expand as Tiozin uses the elastic processing window approach.

| Member | Type | Description |
| --- | --- | --- |
| `id` | `str` | UUIDv7 identifier. Immutable. |
| `org`, `region`, `domain`, `subdomain`, `layer`, `product`, `model` | `str` | Resource the batch belongs to. Immutable. |
| `nominal_time` | `NominalTime` | UTC nominal processing time, truncated to the job cadence. Together with the resource, uniquely identifies the batch. Immutable. |
| `nominal_start_time` | `NominalTime` | UTC start of the processing window. Immutable. |
| `nominal_end_time` | `NominalTime` | UTC end of the processing window. |
| `qualified_natural_key` | `str` | The resource and the nominal time joined with dots, as in `acme.latam.sales.b2b.gold.orders.fact_orders.2026-01-16T00:00:00Z`. |

### Transactional

How the batch moves through its lifecycle. The framework calls these methods during execution, and the `tiozin batch` commands call them from the command line. Every transition merges the extra keyword arguments into `attributes`.

| Member | Type | Description |
| --- | --- | --- |
| `status` | `BatchStatus` | Where the batch stands in its lifecycle. |
| `attempts` | `int` | Number of execution attempts since registration or replay. |
| `retries` | `int` | Convenience property equivalent to `max(0, attempts - 1)`. |
| `register()` | `Batch` | Registers the batch in the batch registry. |
| `begin(**attributes)` | `Batch` | Moves the batch to `RUNNING` and increments `attempts`. |
| `commit(**attributes)` | `Batch` | Moves the batch to `SUCCEEDED`. |
| `rollback(error=None, **attributes)` | `Batch` | Moves the batch to `FAILED`, discarding the attribute and bookmark changes made during the attempt. Records `error` under the `__error` attribute when given. |
| `cancel(**attributes)` | `Batch` | Moves the batch to `CANCELED`, so it leaves the backlog. |
| `quarantine(error=None, **attributes)` | `Batch` | Moves the batch to `QUARANTINED`, excluding it from the backlog until it is replayed. Records `error` under the `__error` attribute when given. |
| `replay(**attributes)` | `Batch` | Moves the batch back to `PENDING`, resetting `attempts` when the batch is in a terminal status. |

### Attributes and Bookmarks

Two open key-value maps, both addressable with dotted keys. Attributes carry information across the pipeline layers of one execution. Bookmarks carry reading progress into the next batch of the same job. A failed execution rolls both back to the values the batch started with.

Bookmarks come in two kinds. A managed bookmark is a lower and an upper bound over an ordered column of the source, and Tiozin freezes the upper bound on the first read, so a retry or a replay covers the same slice. A simple bookmark is a plain value the plugin stores and interprets on its own, with no window and no replay guarantee.

| Member | Type | Description |
| --- | --- | --- |
| `attributes` | `dict` | Free-form values set by the job or by an operator. Read and written directly, as in `batch.attributes["source.file"]`. |
| `bookmarks` | `dict` | Progress markers. Managed ones are stored under `__tio_managed/` and are better reached through the methods below. |
| `get_managed_bookmark(key, fallback=None)` | `Any` | Returns the managed bookmark identified by `key`, or `fallback` when absent. |
| `set_managed_bookmark(key, next_value)` | `Any` | Updates the managed bookmark identified by `key`. See [How to Work with Incremental Backlogs](../how-to/batches.md#2-reading-new-data). |
| `get_managed_bookmark_window(key)` | `tuple[Any \| None, Any \| None]` | Returns the `(lower, upper)` managed bookmark window for `key`. |
| `next_bookmarks()` | `dict` | Returns the bookmarks that will be propagated to the next batch. |
| `get_bookmark(key, fallback=None)` | `Any` | Returns the simple bookmark identified by `key`, or `fallback` when absent. |
| `set_bookmark(key, next_value)` | `Any` | Stores the simple bookmark identified by `key`. See [How to Work with Incremental Backlogs](../how-to/batches.md#3-simple-bookmarks). |

### Other

| Member | Type | Description |
| --- | --- | --- |
| `framework` | `str` | `{name}/{version}` of the framework that created the batch. Immutable. |
| `created_at` | `TechnicalTime` | UTC timestamp when the batch was registered. Immutable. |
| `updated_at` | `TechnicalTime` | UTC timestamp of the last update. |

## Related

- [Jobs](jobs.md)
- [How to Work with Incremental Backlogs](../how-to/batches.md)
- [IcebergBatchRegistry](../tio_kernel/iceberg-batch-registry.md)
