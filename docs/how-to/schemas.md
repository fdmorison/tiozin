# How to Use Schemas in Jobs

This guide covers storing schemas in a registry and attaching them to the steps of a job. The schema attached to a step is available to plugin code and is included in the step's lineage event.

The starting point is the built-in file-backed registry and the shape of a schema file. Tiozin adopts the [Open Data Contract Standard (ODCS) v3.2.0](https://bitol-io.github.io/open-data-contract-standard/v3.2.0/schema/) schema object as its canonical schema format. After that come the `schema_subject` field on a step, the `auto` subject derived from the job taxonomy, version pinning, and reading the resolved schema from plugin code. The sections that follow cover working with a `Schema` in Python: converting it to Spark or Avro, building it in code, and evolving it with the schema observed in the data.

Reading time: about 8 minutes.

[Registries](../concepts/registries.md) covers what a registry is, how `failfast` behaves, and how one is declared in `tiozin.yaml`. This guide assumes it.

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

```text
examples/schemas/
  acme.latam.ecommerce.sales.raw.storefront.orders.yaml
  acme.latam.ecommerce.sales.raw.storefront.customers.yaml
```

Each file holds a schema object, not a full data contract. The abstraction here is a schema registry, not a contract registry.

A schema file describes the fields of a dataset following the [ODCS schema object spec](https://bitol-io.github.io/open-data-contract-standard/v3.2.0/schema/):

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

Keys that are not part of the ODCS schema object are rejected when the file loads, so a misspelled key fails instead of being silently ignored. Extra metadata belongs in `customProperties`.

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

If the subject is not found and `failfast` is `false` (the default), execution continues without a schema. With `failfast: true`, the registry raises `SchemaNotFoundError` and the step fails.

## Use "auto" to keep subjects consistent across your platform

The `"auto"` subject resolves to the default subject template:

```text
{{org}}.{{region}}.{{domain}}.{{subdomain}}.{{layer}}.{{product}}.{{model}}
```

For a job with `org=acme`, `region=latam`, `domain=ecommerce`, `subdomain=sales`, `layer=raw`, `product=storefront`, `model=customers`, `"auto"` resolves to:

```text
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

Use `auto` when your schema subjects follow the same taxonomy as the job.

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
from pyspark.sql import DataFrame

from tiozin import Schema, Transform


class SelectSchemaColumns(Transform[DataFrame]):
    def transform(self, data: DataFrame) -> DataFrame:
        schema: Schema | None = self.context.output_schema
        if schema is None:
            return data
        return data.select([field.name for field in schema.properties])
```

You can also look up any schema directly from the registry using an explicit subject:

```python
schema = self.context.registries.schema.get("acme.latam.ecommerce.sales.raw.storefront.customers")
```

Or using `"auto"` to resolve from the active job context:

```python
schema = self.context.registries.schema.get("auto")
```

## Convert a Schema to Spark or Avro

A `Schema` converts to the [Apache Spark](https://spark.apache.org/docs/latest/) and [Apache Avro](https://avro.apache.org/docs/) schema formats and back. Every conversion works with the JSON form of the format. `to_spark()` and `to_avro()` return a dict, and `from_spark()` and `from_avro()` accept a dict or a JSON string:

```python
from pyspark.sql.types import StructType

from tiozin import Schema

spark_schema = StructType.fromJson(schema.to_spark())
avro_schema = schema.to_avro()

observed = Schema.from_spark(data.schema.jsonValue())
```

`to_spark()` returns a dict, not a `StructType`. Pass the dict to `StructType.fromJson()` when Spark needs the type itself.

Attributes that the target format cannot express travel inside the converted document, so converting that document back to a `Schema` restores them. Spark keeps schema-level attributes, such as the name, under a `metadata` key that `StructType.fromJson()` drops.

The target Spark version only changes how the `time` logical type is mapped. `to_spark()` targets the installed PySpark version, or Spark 3.5 when PySpark is not installed.

Spark has a native time type from Spark 4.1 on. On 4.1 and later, a `time` property becomes `time(6)` for microseconds (`micros`, the default unit) or `time(3)` for milliseconds (`millis`).

On older Spark versions, a `time` property becomes `timestamp_ntz` on `1970-01-01`, the same way Spark reads a SQL `TIME` column over [JDBC](https://spark.apache.org/docs/latest/sql-data-sources-jdbc.html). The field metadata keeps the `time` logical type, so `Schema.from_spark()` reads it back as a time.

Spark times stop at microseconds. A time in nanoseconds (`nanos`) gets the finest precision Spark has: `time(6)` on 4.1 and later, or `timestamp_ntz` before 4.1. The field metadata keeps the `nanos` unit, so `Schema.from_spark()` restores it. Tiozin also logs a warning that Spark truncates the values when it reads the data.

To target a specific Spark version, pass the `version` argument. The version must start with major.minor, so `4.1`, `v4.1`, and `4.1rc1` all work, while `4` or `abc` raises `SchemaError`:

```python
schema.to_spark(version="4.1")
```

Each shortcut also has a generic equivalent. `to_format()` and `from_format()` take the format name, `"spark"` or `"avro"`, as their first argument, followed by the same arguments as the shortcut. Any other format name raises `SchemaError`:

```python
schema.to_format("avro")["type"]
# → 'record'

Schema.from_format("avro", '{"type": "record", "name": "users", "fields": []}')
```

## Build a Schema in Code

Each builder method adds one property and returns the schema, so the calls chain. A dotted path such as `address.city` adds a nested property, and its parent must already exist:

```python
from tiozin import Schema

schema = (
    Schema(name="customers")
    .integer("id", required=True, primaryKey=True)
    .string("email", classification="pii")
    .object("address")
    .string("address.city")
    .array("tags", of="string")
)

list(schema.flatten())
# → ['id', 'email', 'address', 'address.city', 'tags']

schema["address.city"].logicalType
# → 'string'
```

Keyword arguments set ODCS attributes on the new property, such as `required` or `description`. The builders are `string`, `integer`, `number`, `boolean`, `date`, `timestamp`, `time`, `object`, `array`, and `map`. `add()` accepts any logical type as its second argument, and `remove()` drops the property at a path.

A few operations reshape the whole schema. `normalize_field_names()` renames every property to snake case by default, or to another case such as `"camel"`. `sort()` orders properties by name at every level, and `show()` prints the schema as colored YAML:

```python
schema = Schema(name="users").string("First Name").object("Home Address")
schema.string("Home Address.Zip Code")

list(schema.normalize_field_names().flatten())
# → ['first_name', 'home_address', 'home_address.zip_code']
```

Every operation in this section changes the schema in place and returns it. Call `clone()` first to keep the original.

## Evolve a Schema and Copy Its Documentation

`evolve()` merges an observed schema, such as one converted from the data, into a contract schema while keeping backward compatibility:

```python
contract = Schema(name="users").integer("id", required=True, primaryKey=True)
observed = Schema(name="users").integer("id").string("email", unique=True)

contract.evolve(observed)
print(contract.to_yaml())
```

```yaml
name: users
properties:
- name: id
  logicalType: integer
  required: true
  primaryKey: true
- name: email
  logicalType: string
  required: false
```

The same rules apply at every level of nesting, and names are case sensitive:

- A property in both schemas keeps the contract definition.
- A property only in the observed schema is added as optional, without key, uniqueness, or partitioning constraints.
- A property only in the contract is kept.

`document_from()` goes the other way. It copies documentation from the contract into the observed schema, without touching structure or types:

```python
contract = Schema(name="users", description="App users").integer("id", description="User id")
observed = Schema(name="users").integer("id").string("email")

observed.document_from(contract)
print(observed.to_yaml())
```

```yaml
name: users
description: App users
properties:
- name: id
  logicalType: integer
  description: User id
- name: email
  logicalType: string
```

Where the contract has documentation, it replaces the documentation of the observed schema, both on the schema itself and on every property with the same name. Documentation covers `description`, `businessName`, `tags`, `synonyms`, `authoritativeDefinitions`, `classification`, `examples`, and `criticalDataElement`.

## Show the schema at retrieval time

Set `show_schema: true` to print the resolved schema after every successful lookup:

```yaml
registries:
  schema:
    kind: tio_kernel:FileSchemaRegistry
    location: examples/schemas
    show_schema: true
```

The registry logs one line naming the schema and counting its properties. If the schema has no `name`, the line uses the subject instead:

```bash
2026-04-07T03:17:01.850593Z [info] [FileSchemaRegistry] 📄 `load_customers` received schema `customers` with 6 properties
```

Right after that line, the schema is printed to the terminal as colored YAML. It does not go through the logger:

```yaml
name: customers
physicalType: table
physicalName: customers
description: Raw customer master data ingested from source system.
properties:
- name: id
  logicalType: integer
  physicalType: integer
  description: Unique customer identifier
  required: true
  primaryKey: true
  primaryKeyPosition: 1
- name: name
  logicalType: string
  physicalType: varchar
  description: Full name of the customer
  required: true
# ...
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

| Property | Description | Example output |
|---|---|---|
| `kind` | Plugin class name | `tio_kernel:FileSchemaRegistry` |
| `location` | Root path or URI where schema files are stored | |
| `subject_template` | Jinja template used to resolve the subject when `"auto"` is used | `{{org}}.{{region}}.{{domain}}.{{subdomain}}.{{layer}}.{{product}}.{{model}}` |
| `default_version` | Schema version used when `schema_version` is not set on the step | `latest` |
| `show_schema` | Print the resolved schema after each successful lookup | `false` |
| `timeout` | Request timeout in seconds (for remote locations) | `3` |
| `readonly` | Reject write operations | `false` |
| `cache` | Cache retrieved schemas in memory | `false` |
| `failfast` | When `true`, raises when the schema is not found; when `false`, returns `None` | `false` |
| `name` | Display name for this registry instance | |
| `description` | Human-readable description | |
