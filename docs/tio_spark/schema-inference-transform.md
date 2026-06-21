# SparkSchemaInferenceTransform

Infers the schema of fields that hold JSON strings, then converts each one from `STRING` to the matching Spark type such as a struct or an array. Fields that are not listed pass through untouched.

```yaml
transforms:
  - kind: SparkSchemaInferenceTransform
    name: parse_payload
    json_fields: payload
```

Given a `payload` field of JSON strings such as `{"name": "John", "age": 30}`, the transform infers and applies the schema:

```text
payload STRING  →  payload STRUCT<age BIGINT, name STRING>
```

## Parameters

| Property | Required | Default | Description |
|---|---|---|---|
| `json_fields` | No | `[]` | Field name or list of field names holding JSON strings to infer |
| `sampling_ratio` | No | `0.10` | Fraction of rows used to infer the schema |
| `unnest_fields` | No | `[]` | Fields to expand into top-level columns after inference |
| `timezone` | No | `UTC` | Source timezone for naive values in `auto_timestamp_fields` |
| `timestamp_format` | No | inferred | Pattern or list of patterns used to parse timestamps in `auto_timestamp_fields` |
| `auto_timestamp_fields` | No | `[]` | Fields to convert to UTC timestamps, auto-detecting each value at runtime: timezone-aware strings keep their embedded zone, naive strings are read in `timezone`, and numeric strings or integers are read as compact dates (`yyyyMMdd` or `yyyyMMddHHmmss`) |
| `**options` | No | see below | [Spark JSON reader options](https://spark.apache.org/docs/latest/sql-data-sources-json.html) that override the reader defaults |

When `json_fields` is empty, the transform returns the input unchanged.

## json_fields

`json_fields` accepts a single field name or a list. List each field that holds JSON, and the transform infers and converts every one of them independently.

```yaml
transforms:
  - kind: SparkSchemaInferenceTransform
    name: parse_records
    json_fields:
      - user
      - address
```

```text
user STRING     →  user STRUCT<age BIGINT, name STRING>
address STRING  →  address STRUCT<city STRING, street STRING>
```

## unnest_fields

By default each inferred field becomes a single struct column. List a field under `unnest_fields` to expand its struct into top-level columns and drop the original field. Only the fields listed are expanded; every other field passes through as a struct.

```yaml
transforms:
  - kind: SparkSchemaInferenceTransform
    name: parse_user
    json_fields: value
    unnest_fields:
      - value
```

A `value` field holding `{"name": "John", "age": 30}` expands into two columns:

```text
value STRING  →  age BIGINT, name STRING
```

When two or more fields are unnested and their inner fields share the same name, the resulting DataFrame contains duplicate column names. The transform does not detect or resolve this. In that case, leave the field out of `unnest_fields` and handle the expansion in a later transform step.

## sampling_ratio

To infer a schema, the transform reads a sample of the rows rather than the whole dataset. `sampling_ratio` sets the fraction of rows used and defaults to `0.10`, which is 10 percent. Lower the ratio on large datasets to reduce inference cost.

```yaml
transforms:
  - kind: SparkSchemaInferenceTransform
    name: parse_payload
    json_fields: payload
    sampling_ratio: 0.01
```

If the sample produces no fields, for example when the ratio is too small to capture any row, the transform retries the inference using the full dataset. The conversion still succeeds.

## auto_timestamp_fields

`auto_timestamp_fields` converts the listed fields to UTC timestamps after schema inference. Each value is inspected at runtime: a timezone-aware string keeps its embedded timezone, a timezone-naive string is read in `timezone` and converted to UTC, and a numeric string or integer is treated as a compact date (`yyyyMMdd` or `yyyyMMddHHmmss`). Use dot notation to reach a nested field.

```yaml
transforms:
  - kind: SparkSchemaInferenceTransform
    name: parse_payload
    json_fields: payload
    auto_timestamp_fields:
      - payload.created_at
      - payload.updated_at
```

`timezone` sets the source zone for naive values and defaults to `UTC`. `timestamp_format` accepts a [Java SimpleDateFormat](https://docs.oracle.com/javase/8/docs/api/java/text/SimpleDateFormat.html) pattern such as `dd/MM/yyyy HH:mm:ss`, or a list of patterns. When a list is provided, the JSON reader uses the first pattern and `auto_timestamp_fields` tries each pattern in order before falling back to the built-in defaults. When `timestamp_format` is omitted, Spark infers the format and the transform does not pass a format to the reader.

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

Any key that is not a named parameter is forwarded to the [Spark JSON reader](https://spark.apache.org/docs/latest/sql-data-sources-json.html), overriding the defaults above or adding new options. The example below switches to permissive parsing and reads numeric primitives as strings:

```yaml
transforms:
  - kind: SparkSchemaInferenceTransform
    name: parse_payload
    json_fields: payload
    mode: PERMISSIVE
    primitivesAsString: true
    allowUnquotedFieldNames: true
```

The same call expressed programmatically:

```python
SparkSchemaInferenceTransform(
    name="parse_payload",
    json_fields="payload",
    mode="PERMISSIVE",
    primitivesAsString=True,
    allowUnquotedFieldNames=True,
)
```

## Related

- Reshape the inferred columns with [SparkSqlTransform](sql-transform.md).
- Review how results flow between steps in the [tio_spark overview](index.md).
- Build a transform of your own in [Creating Pluggable Tiozins](../extending/tiozins.md).
