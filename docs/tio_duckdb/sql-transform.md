# DuckdbSqlTransform

Runs a DQL SQL query on the active DuckDB connection and passes the resulting relation to the next step. Only queries that return a relation are supported: SELECT statements, CTEs (`WITH ... SELECT ...`), and similar DQL constructs. DDL (`CREATE`, `DROP`) and DML (`INSERT`, `UPDATE`, `DELETE`) do not return a relation and will raise an error. Use outputs for write operations.

```yaml
transforms:
  - kind: DuckdbSqlTransform
    name: filtered
    query: SELECT * FROM customers WHERE status = 'active'
```

## Parameters

| Property | Description | Default |
|---|---|---|
| `query` | DQL SQL query. Supports step references, `@data` aliases, and `$param` named parameters | |
| `args` | Named parameter values for the query | |

## Referencing upstream steps

Because the framework registers every step result as a named view, any input or prior transform is referenceable by its slug directly in SQL:

```yaml
inputs:
  - kind: DuckdbFileInput
    name: customers
    path: data/customers.csv

  - kind: DuckdbFileInput
    name: orders
    path: data/orders.csv

transforms:
  - kind: DuckdbSqlTransform
    name: enriched
    query: |-
      SELECT c.name, o.total
      FROM customers c
      JOIN orders o ON c.id = o.customer_id
```

## The @data alias

`@data` is a shorthand that resolves to the slug of the upstream step at query time. Use it to write a generic transform without hardcoding the upstream step name.

```yaml
transforms:
  - kind: DuckdbSqlTransform
    name: enriched
    query: |-
      SELECT c.name, o.total
      FROM customers c
      JOIN orders o ON c.id = o.customer_id

  - kind: DuckdbSqlTransform
    name: high_value
    query: SELECT * FROM @data WHERE total > 100
    # @data resolves to enriched, the previous step
```

When a transform receives multiple upstream relations, aliases are assigned positionally:

| Token | Resolves to |
|---|---|
| `@data` or `@data0` | first upstream relation |
| `@data1` | second upstream relation |
| `@data2` | third upstream relation |

```yaml
inputs:
  - kind: DuckdbFileInput
    name: customers
    path: data/customers.csv

  - kind: DuckdbFileInput
    name: orders
    path: data/orders.csv

transforms:
  - kind: DuckdbSqlTransform
    name: joined
    query: |-
      SELECT c.name, o.total
      FROM @data c
      JOIN @data1 o ON c.id = o.customer_id
```

## Named parameters

Named parameters are a DuckDB feature. Use `$param_name` in the query and supply the values under `args`. See the [DuckDB parameterized queries reference](https://duckdb.org/docs/clients/python/dbapi#parameterized-queries) for details.

```yaml
transforms:
  - kind: DuckdbSqlTransform
    name: filtered
    query: SELECT * FROM @data WHERE total > $min_total AND status = $status
    args:
      min_total: 500
      status: active
```
