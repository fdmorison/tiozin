# SparkDeduplicateTransform

Removes duplicate rows from a Spark `DataFrame`, keeping one row per key.

By default, the transform keeps an arbitrary row for each key. Use `order_by` to control which row is kept: `last` keeps the row with the highest ordering values, while `first` keeps the row with the lowest.

```yaml
transforms:
  - kind: SparkDeduplicateTransform
    name: unique_customers
    keys: customer_id
```

Given the following input, duplicate rows with the same `customer_id` are reduced to one:

```text
Input                 Output
customer_id | name    customer_id | name
1           | Alice   1           | Alice
1           | Alice   2           | Bob
2           | Bob
```

Without `order_by`, the selected row is arbitrary and may vary between runs if duplicates differ in other fields. When the exact row matters, use `order_by` to define the selection criteria.

## Parameters

| Property | Required | Default | Description |
|---|---|---|---|
| `keys` | No | All fields | Field or list of fields used to identify duplicates. |
| `order_by` | No | — | Field or list of fields used to sort rows within each key group, in ascending order. |
| `keep` | No | `last` | Selects the first or last row after sorting. Requires `order_by`. |

Properties shared by all transforms are documented in [Inputs, Transforms & Outputs](../concepts/steps.md#transform).

## `keys`

Accepts a single field or a list of fields. When multiple fields are specified, rows belong to the same group only when all key fields match.

```yaml
transforms:
  - kind: SparkDeduplicateTransform
    name: unique_addresses
    keys: [customer_id, address_type]
```

For example, customers can have multiple address types, but only one row is retained for each combination of `customer_id` and `address_type`.

```text
Input                              Output
customer_id | address_type | street customer_id | address_type | street
1           | home         | Lorem  1           | home         | Lorem
1           | home         | Lorem  1           | work         | Ipsum
1           | work         | Ipsum
```

When `keys` is omitted, all fields are used to identify duplicates, except those specified in `order_by`. Without `order_by`, only exact duplicate rows are removed.

```yaml
transforms:
  - kind: SparkDeduplicateTransform
    name: unique_rows
```

```text
Input                     Output
customer_id | name        customer_id | name
1           | Alice       1           | Alice
1           | Alice       1           | Alicia
1           | Alicia
```

## `order_by`

Use `order_by` to select which row survives deduplication. The fields are sorted in ascending order, and `keep` determines which end of the sorted group is retained.

For example, to keep the latest version of each customer:

```yaml
transforms:
  - kind: SparkDeduplicateTransform
    name: latest_customers
    keys: customer_id
    order_by: version
```

Because `keep` defaults to `last`, the row with the highest version is retained.

```text
Input                              Output
customer_id | name   | version    customer_id | name   | version
1           | Alice  | 1           1           | Alicia | 3
1           | Alicia | 3           2           | Bob    | 1
1           | Ally   | 2
2           | Bob    | 1
```

### Multiple ordering fields

When `order_by` contains multiple fields, they are evaluated in sequence. Each subsequent field breaks ties on the preceding fields.

For example, to select the highest version and, among rows with the same version, the latest ingestion:

```yaml
transforms:
  - kind: SparkDeduplicateTransform
    name: latest_customers
    keys: customer_id
    order_by: [version, ingested_at]
```

```text
Input                                      Output
customer_id | name   | version | ingested_at customer_id | name   | version | ingested_at
1           | Alice  | 2       | 10          1           | Alicia | 2       | 30
1           | Alicia | 2       | 30
1           | Ally   | 2       | 20
1           | Ali    | 1       | 99
```

If rows have identical values across all `order_by` fields, the transform keeps an arbitrary row among them. Add further ordering fields when deterministic selection is required.

### Null values

Null values never take priority over non-null values. When rows are compared on an ordering field, a non-null value wins over a null, regardless of whether `keep` is `first` or `last`.

For example, the row with `version = 2` is retained over the row with a null version:

```text
Input                         Output
customer_id | name   | version customer_id | name   | version
1           | Alice  | null    1           | Alicia | 2
1           | Alicia | 2
```

### Deduplication without `keys`

When `keys` is omitted and `order_by` is specified, the ordering fields are excluded from duplicate identification. Rows that match on all other fields belong to the same group, and `keep` determines which ordering value survives.

For example, the transform below retains the highest version for each distinct combination of `customer_id` and `name`:

```yaml
transforms:
  - kind: SparkDeduplicateTransform
    name: latest_rows
    order_by: version
```

```text
Input                              Output
customer_id | name   | version    customer_id | name   | version
1           | Alice  | 1           1           | Alice  | 3
1           | Alice  | 3           1           | Alicia | 2
1           | Alicia | 2
```

## `keep`

Controls which row is retained after sorting:

- `last` keeps the row with the highest ordering values. This is the default.
- `first` keeps the row with the lowest ordering values.

The following example keeps the earliest version of each customer:

```yaml
transforms:
  - kind: SparkDeduplicateTransform
    name: first_customers
    keys: customer_id
    order_by: version
    keep: first
```

```text
Input                              Output
customer_id | name   | version    customer_id | name   | version
1           | Alice  | 1           1           | Alice  | 1
1           | Alicia | 3           2           | Bob    | 1
1           | Ally   | 2
2           | Bob    | 1
```

## Validation

The transform raises `TiozinInputError` if:

- `keep` is not `first` or `last`.
- `keep` is specified without `order_by`.

## Using It From Python

The transform can also be instantiated directly in Python:

```python
SparkDeduplicateTransform(
    name="latest_customers",
    keys="customer_id",
    order_by=["version", "ingested_at"],
    keep="last",
)
```

## Related

- [SparkSqlTransform](sql-transform.md) — filter or reshape rows using SQL.
- [tio_spark overview](index.md) — understand how data flows between steps.
- [Creating Pluggable Tiozins](../extending/tiozins.md) — implement custom transforms.
