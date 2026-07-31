# IcebergBatchRegistry

The `IcebergBatchRegistry` persists batches in an [Apache Iceberg](https://iceberg.apache.org/) table, allowing batch metadata and execution history to survive across job runs.

The registry is built on top of [PyIceberg](https://py.iceberg.apache.org/), so it can use any catalog supported by PyIceberg. Besides the registry-specific settings documented here, any additional configuration properties are forwarded unchanged to the underlying catalog. Refer to the [PyIceberg catalog configuration](https://py.iceberg.apache.org/configuration/) for the complete list of supported catalog types and catalog-specific options.

By default, the registry creates a self-contained SQLite catalog under the configured `location`, making it suitable for local development without requiring any external services.

```yaml
registries:
  batch:
    kind: tio_kernel:IcebergBatchRegistry
    location: .checkpoints
```

## Parameters

| Property | Required | Default | Description |
| -------- | -------- | ------- | ----------- |
| `location` | yes | | Location of the Iceberg catalog. Its meaning depends on the selected catalog type. |
| `database` | no | `default` | Iceberg namespace containing the batch table. |
| `table` | no | `tiozin_batches` | Batch table name. |
| `catalog` | no | `tiozin` | Catalog name. |
| `catalog_type` | no | `sqlite` | Catalog implementation used by PyIceberg. |
| `retention_days` | no | `30` | Number of days of batch history to retain. |
| `retries` | no | `3` | Maximum number of retry attempts before a failed batch is quarantined. |
| Any other property | no | | Forwarded unchanged to the underlying PyIceberg catalog configuration. |

`retries` belongs to every batch registry, not only this one. Its default comes from `TIO_BATCH_REGISTRY_RETRIES`, which itself defaults to `3`. Once a batch exhausts them, the next failure moves it to `QUARANTINED` instead of `FAILED`, and the backlog stops retrying it.

## Location

The meaning of `location` depends on the selected catalog type. For local catalogs it usually refers to a directory, while for remote catalogs it typically represents the catalog uri.

| Catalog Type | Meaning of `location` |
|--------------|----------------------|
| `sqlite` | Local directory where the catalog database and Iceberg warehouse are stored. |
| `rest` | URI of the Iceberg REST catalog endpoint. |
| Other catalog types | Usually ignored. The catalog-specific configuration determines how the catalog is located. |

For local development, `location` is a directory:

```yaml
registries:
  batch:
    kind: tio_kernel:IcebergBatchRegistry
    location: .checkpoints
```

For REST catalogs, it becomes the catalog endpoint:

```yaml
registries:
  batch:
    kind: tio_kernel:IcebergBatchRegistry
    catalog_type: rest
    location: https://glue.us-east-1.amazonaws.com/iceberg
```

## Catalog Types

`catalog_type` selects the catalog implementation used by the registry.

All catalog types supported by PyIceberg can be used. The only exception is `sqlite`, which is a convenience alias provided by Tiozin for local development.

### sqlite (default)

`sqlite` is a convenience catalog that configures a local SQL catalog backed by SQLite. The registry automatically derives the catalog URI and warehouse location from `location`, so configuring a single directory is enough to create a fully functional local catalog.

```yaml
registries:
  batch:
    kind: tio_kernel:IcebergBatchRegistry
    location: .checkpoints
```

### rest

`rest` connects to an Iceberg REST catalog. In this mode, `location` becomes the catalog endpoint (`uri` in PyIceberg), while authentication, warehouse configuration, request signing, and other vendor-specific settings are supplied as additional catalog properties.

Examples of REST catalogs include AWS Glue and Databricks Unity Catalog.

### Other catalog types

Any other catalog implementation supported by PyIceberg can be used by setting `catalog_type` accordingly. The registry forwards both the selected catalog type and any additional configuration properties directly to PyIceberg without modification.

Refer to the [PyIceberg catalog configuration](https://py.iceberg.apache.org/configuration/) for the complete list of supported catalog implementations.

## Catalog Options

Most catalog-specific settings are intentionally not exposed as registry parameters.

Instead, any configuration property that is not recognized by `IcebergBatchRegistry` is forwarded directly to PyIceberg. This allows new catalog features to be used without requiring changes to the registry itself.

For example, the following configuration passes `warehouse`, `credential`, and every `rest.*` property directly to the configured catalog:

```yaml
registries:
  batch:
    kind: tio_kernel:IcebergBatchRegistry
    catalog_type: rest
    location: https://glue.us-east-1.amazonaws.com/iceberg

    warehouse: <account-id>:s3tablescatalog/<table-bucket-name>

    rest.sigv4-enabled: true
    rest.signing-name: glue
    rest.signing-region: us-east-1
```

Refer to the [PyIceberg catalog configuration](https://py.iceberg.apache.org/configuration/) for the catalog-specific properties supported by each implementation.

## What The Table Stores

Each batch is one row. The table is partitioned by the resource fields (`org`, `region`, `domain`, `subdomain`, `layer`, `product`, `model`), so jobs writing different resources do not contend for the same files, and it is sorted by `created_at`.

Alongside those fields, every row carries:

| Column | Description |
|--------|-------------|
| `id` | Unique batch identifier. |
| `nominal_time` | Logical time that, together with the resource fields, identifies the batch. |
| `nominal_start_time` | Start of the batch's processing window. |
| `nominal_end_time` | End of the batch's processing window. |
| `status` | Current lifecycle status of the batch. |
| `attempts` | Number of execution attempts since the batch started or was replayed. |
| `attributes` | JSON document of metadata scoped to a single execution. |
| `bookmarks` | JSON document of metadata carried across executions. |
| `framework` | Framework version that created the batch, as `{name}/{version}`. |
| `created_at` | When the batch was first registered. |
| `updated_at` | When the batch was last updated. |

## Attributes And Bookmarks

Both are stored as JSON documents, so their keys can vary freely from one batch to the next without requiring schema changes.

`attributes` propagate across pipeline layers within a single execution, and they are transactional: when the job fails, they roll back to the values recorded before the run.

`bookmarks` propagate across executions of the same job and carry into the next batch, which is what lets an incremental job resume where the previous one stopped.

For how batches use both during a run, see [How to Process Pending Work Incrementally](../how-to/batches.md).

## Retention

`retention_days` controls how long Iceberg snapshots are retained.

Older snapshots are automatically removed during registry cleanup. Increasing this value preserves a longer execution history at the cost of additional storage, while reducing it reclaims storage sooner. The default is **30 days**.

## Examples

### Local SQLite Catalog

Creates a self-contained local catalog that stores both the catalog metadata and the Iceberg warehouse under `location`.

```yaml
registries:
  batch:
    kind: tio_kernel:IcebergBatchRegistry
    location: .checkpoints
```

### AWS Glue

Connects to AWS Glue through its Iceberg REST endpoint.

```yaml
registries:
  batch:
    kind: tio_kernel:IcebergBatchRegistry
    catalog_type: rest
    location: https://glue.<region>.amazonaws.com/iceberg
    warehouse: <account-id>:s3tablescatalog/<table-bucket-name>
    rest.sigv4-enabled: true
    rest.signing-name: glue
    rest.signing-region: <region>
```

### Databricks Unity Catalog

Connects to Databricks Unity Catalog through its Iceberg REST endpoint.

```yaml
registries:
  batch:
    kind: tio_kernel:IcebergBatchRegistry
    catalog_type: rest
    location: https://<workspace-url>/api/2.1/unity-catalog/iceberg-rest
    warehouse: <uc-catalog-name>
    token: <databricks-pat-token>  # You can use some envvar, eg: {{ENV.PATH_TOKEN}}
```

## Setup

Install the Iceberg support:

```bash
pip install tiozin[tio_kernel]
```

Then enable the registry in `tiozin.yaml`:

```yaml
registries:
  batch:
    kind: tio_kernel:IcebergBatchRegistry
    location: .checkpoints
```

If no batch registry is configured, Tiozin uses `NoOpBatchRegistry`, which discards every registered batch.

## Related

- [How to Process Pending Work Incrementally](../how-to/batches.md)
- [NoOpBatchRegistry](noops.md)
- [Working with Registries](../extending/registry.md)
