# SparkJsonSchemaInferenceTransform

Infers the schema of columns that hold JSON strings, then converts each one from `STRING` to the matching Spark type such as a struct or an array. Columns that are not listed pass through untouched.

```yaml
transforms:
  - kind: SparkJsonSchemaInferenceTransform
    name: parse_payload
    json_columns: payload
```

Given a `payload` column of JSON strings such as `{"name": "John", "age": 30}`, the transform infers and applies the schema:

```text
payload STRING  →  payload STRUCT<age BIGINT, name STRING>
```

## Parameters

| Property | Required | Default | Description |
|---|---|---|---|
| `json_columns` | No | `[]` | Column name or list of column names holding JSON strings to infer |
| `sampling_ratio` | No | `0.10` | Fraction of rows used to infer the schema |
| `flatten` | No | `false` | Expand inferred struct fields into top-level columns |
| `**options` | No | see below | [Spark JSON reader options](https://spark.apache.org/docs/latest/sql-data-sources-json.html) that override the reader defaults |

When `json_columns` is empty, the transform returns the input unchanged.

## json_columns

`json_columns` accepts a single column name or a list. List each column that holds JSON, and the transform infers and converts every one of them independently.

```yaml
transforms:
  - kind: SparkJsonSchemaInferenceTransform
    name: parse_records
    json_columns:
      - user
      - address
```

```text
user STRING     →  user STRUCT<age BIGINT, name STRING>
address STRING  →  address STRUCT<city STRING, street STRING>
```

## flatten

By default each inferred column becomes a single struct column. Set `flatten` to `true` to expand the struct fields into top-level columns and drop the original column.

```yaml
transforms:
  - kind: SparkJsonSchemaInferenceTransform
    name: parse_user
    json_columns: value
    flatten: true
```

A `value` column holding `{"name": "John", "age": 30}` expands into two columns:

```text
value STRING  →  age BIGINT, name STRING
```

When two or more JSON columns are flattened and their fields share the same name, the resulting DataFrame will contain duplicate column names. The transform does not detect or resolve this. In that case, set `flatten` to `false` and handle the expansion in a subsequent transform step.

## sampling_ratio

To infer a schema, the transform reads a sample of the rows rather than the whole dataset. `sampling_ratio` sets the fraction of rows used and defaults to `0.10`, which is 10 percent. Lower the ratio on large datasets to reduce inference cost.

```yaml
transforms:
  - kind: SparkJsonSchemaInferenceTransform
    name: parse_payload
    json_columns: payload
    sampling_ratio: 0.01
```

If the sample produces no fields, for example when the ratio is too small to capture any row, the transform retries the inference using the full dataset. The conversion still succeeds.

## Reader Defaults And Options

The transform reads JSON through the [Spark JSON data source](https://spark.apache.org/docs/latest/sql-data-sources-json.html) and applies these defaults:

| Option | Default | Effect |
|---|---|---|
| `mode` | `FAILFAST` | Raises an error on malformed JSON |
| `timeZone` | `UTC` | Parses dates and times in UTC |
| `primitivesAsString` | `false` | Keeps numbers and booleans as their native types |
| `allowComments` | `true` | Accepts JSON comments |
| `allowSingleQuotes` | `true` | Accepts single-quoted strings |
| `allowNumericLeadingZeros` | `true` | Accepts numbers with leading zeros |

Because `mode` defaults to `FAILFAST`, malformed JSON raises an error and stops the transform. Set `mode` to `PERMISSIVE` to keep parsing instead of failing.

Any key that is not `json_columns`, `sampling_ratio`, or `flatten` is forwarded to the [Spark JSON reader](https://spark.apache.org/docs/latest/sql-data-sources-json.html), overriding the defaults above or adding new options. The example below switches to permissive parsing and reads numeric primitives as strings:

```yaml
transforms:
  - kind: SparkJsonSchemaInferenceTransform
    name: parse_payload
    json_columns: payload
    mode: PERMISSIVE
    primitivesAsString: true
    allowUnquotedFieldNames: true
```

The same call expressed programmatically:

```python
SparkJsonSchemaInferenceTransform(
    name="parse_payload",
    json_columns="payload",
    mode="PERMISSIVE",
    primitivesAsString=True,
    allowUnquotedFieldNames=True,
)
```

## Related

- Reshape the inferred columns with [SparkSqlTransform](sql-transform.md).
- Review how results flow between steps in the [tio_spark overview](index.md).
- Build a transform of your own in [Creating Pluggable Tiozins](../extending/tiozins.md).
