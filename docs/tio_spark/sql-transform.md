# SparkSqlTransform

Runs a Spark SQL query against the registered temporary views and passes the resulting DataFrame to the next step. Any SQL query supported by Spark SQL works here.

```yaml
transforms:
  - kind: SparkSqlTransform
    name: filtered
    query: SELECT * FROM customers WHERE status = 'active'
```

## Parameters

| Property | Description | Default |
|---|---|---|
| `query` | Spark SQL query. Supports step references, `@data` aliases, and `:param` named parameters | |
| `args` | Named parameter values for the query, as a dict or a positional list | |

## Referencing upstream steps

Because the framework registers every step result as a named temporary view, any input or prior transform is referenceable by its slug directly in SQL:

```yaml
inputs:
  - kind: SparkFileInput
    name: customers
    path: data/customers

  - kind: SparkFileInput
    name: orders
    path: data/orders

transforms:
  - kind: SparkSqlTransform
    name: enriched
    query: |-
      SELECT c.name, o.total
      FROM customers c
      JOIN orders o ON c.id = o.customer_id
```

## The @data alias

`@data` is a shorthand that resolves to the slug of the upstream step at query time. Use it when you want to write a generic transform without hardcoding the upstream step name.

```yaml
transforms:
  - kind: SparkSqlTransform
    name: enriched
    query: |-
      SELECT c.name, o.total
      FROM customers c
      JOIN orders o ON c.id = o.customer_id

  - kind: SparkSqlTransform
    name: high_value
    query: SELECT * FROM @data WHERE total > 100
    # @data resolves to enriched, the previous step
```

When a transform receives multiple upstream DataFrames, the aliases map positionally to the inputs received by the `transform` method:

```python
def transform(self, data: DataFrame, *others: DataFrame) -> DataFrame:
    # @data / @data0  →  data       (first upstream step)
    # @data1          →  others[0]  (second upstream step)
    # @data2          →  others[1]  (third upstream step)
    ...
```

```yaml
inputs:
  - kind: SparkFileInput
    name: customers
    path: data/customers

  - kind: SparkFileInput
    name: orders
    path: data/orders

transforms:
  - kind: SparkSqlTransform
    name: joined
    # @data   →  customers (first input)
    # @data1  →  orders    (second input)
    query: |-
      SELECT c.name, o.total
      FROM @data c
      JOIN @data1 o ON c.id = o.customer_id
```

## Named parameters

Named parameters are a Spark SQL feature. Use `:param_name` in the query and supply the values under `args`. `args` accepts a dict of named values or a list of positional values. See the [Spark SQL parameterized queries reference](https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select.html) for details.

```yaml
transforms:
  - kind: SparkSqlTransform
    name: filtered
    query: SELECT * FROM @data WHERE total > :min_total AND status = :status
    args:
      min_total: 500
      status: active
```
