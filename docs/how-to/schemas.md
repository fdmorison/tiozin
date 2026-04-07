# How to Use Schemas in Jobs

Attach a schema to any step to make it available to your plugin code and include it in lineage events.

Tiozin adopts the [Open Data Contract Standard (ODCS)](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/schema/) schema as its canonical schema format.

## The basics

Tiozin ships `FileSchemaRegistry` as the built-in implementation, which uses a filesystem directory as the registry backend. Other implementations can be created for other backends (Confluent Schema Registry, AWS Glue, a REST API), as long as they extend `SchemaRegistry` and belong to a registered Tiozin Family.

Configure it in `tiozin.yaml` by pointing `location` at a folder of YAML schema files:

```yaml
registries:
  schema:
    kind: tio_kernel:FileSchemaRegistry
    location: examples/schemas
```

Each file in that folder is a schema. The filename (without `.yaml`) is its subject:

```
examples/schemas/
  acme.latam.ecommerce.sales.raw.storefront.orders.yaml
  acme.latam.ecommerce.sales.raw.storefront.customers.yaml
```

Each file holds a schema object, not a full data contract. The abstraction here is a schema registry, not a contract registry.

A schema file describes the fields of a dataset following the [ODCS schema object spec](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/schema/):

```yaml
name: customers
physicalName: customers
physicalType: table
description: Raw customer master data.

properties:
  - name: id
    logicalType: integer
    physicalType: integer
    required: true
    primaryKey: true

  - name: email
    logicalType: string
    physicalType: varchar
    required: true
```

## Attach a schema to a step

`schema_subject` identifies the schema of the data produced by the step. Add it to any Input, Transform, or Output in your job YAML:

```yaml
inputs:
  - kind: DuckdbFileInput
    name: load_customers
    path: examples/data/ecommerce/customers.csv
    format: csv
    schema_subject: acme.latam.ecommerce.sales.raw.storefront.customers
```

When the step runs, the framework fetches the schema from the registry and makes it available as `context.output_schema`. It is also included in the lineage event, so the dataset fields appear in any OpenLineage-compatible backend such as Marquez. See [How to Configure OpenLineage](openlineage.md).

If the subject is not found, execution continues without a schema. The step does not fail.

## Use "auto" to keep subjects consistent across your platform

The `"auto"` subject resolves to the default subject template:

```
{{org}}.{{region}}.{{domain}}.{{subdomain}}.{{layer}}.{{product}}.{{model}}
```

For a job with `org=acme`, `region=latam`, `domain=ecommerce`, `subdomain=sales`, `layer=raw`, `product=storefront`, `model=customers`, `"auto"` resolves to:

```
acme.latam.ecommerce.sales.raw.storefront.customers
```

The `"auto"` subject may be used in Inputs, Transforms, and Outputs:

```yaml
inputs:
  - kind: DuckdbFileInput
    name: load_customers
    path: examples/data/ecommerce/customers.csv
    format: csv
    schema_subject: auto

transforms:
  - kind: DuckdbSqlTransform
    name: add_metadata
    query: "SELECT * FROM @data"
    schema_subject: auto

outputs:
  - kind: DuckdbFileOutput
    name: save_customers
    path: .output/lake/customers
    format: parquet
    schema_subject: auto
```

This is the recommended approach when your schema subjects follow the same taxonomy as the job.

## Pin a specific version

Set `schema_version` on the step to request a specific version:

```yaml
inputs:
  - kind: DuckdbFileInput
    name: load_customers
    schema_subject: auto
    schema_version: "2"
```

When omitted, the registry uses the `default_version` (default: `latest`). `FileSchemaRegistry` ignores the version field since each file contains a single schema. Other backends (Confluent Schema Registry, for example) use it to select the right version.

## Customize the subject template and default version

If your project uses a different subject naming convention or version default, configure them in `tiozin.yaml`:

```yaml
registries:
  schema:
    kind: tio_kernel:FileSchemaRegistry
    location: examples/schemas
    subject_template: "{{domain}}.{{layer}}.{{product}}.{{model}}"
    default_version: "2"
```

With that template, `"auto"` resolves to `ecommerce.raw.storefront.customers` instead. Any Jinja variable available in job templates (`org`, `region`, `domain`, `subdomain`, `layer`, `product`, `model`) works here.

You can also use a custom template directly on a step instead of `"auto"`:

```yaml
inputs:
  - kind: DuckdbFileInput
    name: load_customers
    schema_subject: "{{domain}}.{{product}}.{{model}}"
```

The subject is rendered using the active job context before the registry lookup.

## Access the schema in plugin code

When a step has `schema_subject`, the resolved schema is available as `self.context.output_schema` during `read()`, `transform()`, or `write()`:

```python
from tiozin import Output, Schema


class SparkParquetOutput(Output[DataFrame]):
    def write(self, data: DataFrame) -> None:
        schema: Schema | None = self.context.output_schema
        if schema is not None:
            spark_schema = schema.export("spark")
            data = data.select([col for col in spark_schema.fieldNames()])
        data.write.parquet(self.path)
```

You can also look up any schema directly from the registry using an explicit subject:

```python
schema = self.context.registries.schema.get("acme.latam.ecommerce.sales.raw.storefront.customers")
```

Or using `"auto"` to resolve from the active job context:

```python
schema = self.context.registries.schema.get("auto")
```

## Show the schema at retrieval time

Set `show_schema: true` to print the resolved schema to the logs after every successful lookup:

```yaml
registries:
  schema:
    kind: tio_kernel:FileSchemaRegistry
    location: examples/schemas
    show_schema: true
```

```bash
2026-04-07T03:17:01.850593Z [info] [FileSchemaRegistry] Schema `tiozin.eu.ecommerce.sales.raw.storefront.customers`:
name: customers
physicalType: table
description: Raw customer master data ingested from source system.
physicalName: customers
properties:
- name: id
  physicalType: integer
  description: Unique customer identifier
  primaryKey: true
  primaryKeyPosition: 1
  logicalType: integer
  required: true
- name: name
  physicalType: varchar
  description: Full name of the customer
  logicalType: string
  required: true
```

Useful during development to confirm which schema is being picked up.

## Remote schema files

`FileSchemaRegistry` supports any location that `fsspec` can read:

```yaml
registries:
  schema:
    kind: tio_kernel:FileSchemaRegistry
    location: s3://my-bucket/schemas
```

```yaml
registries:
  schema:
    kind: tio_kernel:FileSchemaRegistry
    location: https://schemas.internal.company.com/tiozin
```

Supported protocols: `s3://`, `gs://`, `az://`, `http://`, `https://`, `ftp://`, `sftp://`, and local paths.

## All parameters

| Property | Default | Description |
|---|---|---|
| `kind` | | `tio_kernel:FileSchemaRegistry` |
| `location` | | Root path or URI where schema files are stored |
| `subject_template` | `{{org}}.{{region}}.{{domain}}.{{subdomain}}.{{layer}}.{{product}}.{{model}}` | Jinja template used to resolve the subject when `"auto"` is used |
| `default_version` | `latest` | Schema version used when `schema_version` is not set on the step |
| `show_schema` | `false` | Log the resolved schema after each successful lookup |
| `timeout` | `3` | Request timeout in seconds (for remote locations) |
| `readonly` | `false` | Reject write operations |
| `cache` | `false` | Cache retrieved schemas in memory |
| `name` | | Display name for this registry instance |
| `description` | | Human-readable description |
