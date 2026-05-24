---
name: spark-testing
description: Spark testing patterns. Use when writing or reviewing tests that involve PySpark code.
user-invocable: false
---

# Spark Testing

## Comparing DataFrames

Never use `==`. Use `assertDataFrameEqual` from `pyspark.testing`:

```python
from pyspark.testing import assertDataFrameEqual

assertDataFrameEqual(actual, expected)
```

When data comparison is not needed, use `assertSchemaEqual` instead:

```python
from pyspark.testing import assertSchemaEqual

assertSchemaEqual(actual.schema, expected.schema)
```

## Ordering

`assertDataFrameEqual` ignores row order by default. Follow @rules/testing.md#11-ordering.

When order is not part of the contract, use the default behavior.
When order is part of the contract, pass `checkRowOrder=True` — never sort `actual`.

## Inline expected DataFrames

Always declare the schema explicitly — inferred schemas produce unexpected types across environments.

```python
# ✔ Correct
expected = spark.createDataFrame(
    [("lorem", 3), ("ipsum", 1)],
    schema="`word` STRING, `count` BIGINT",
)
assertDataFrameEqual(actual, expected)

# ❌ Incorrect — schema inferred
expected = spark.createDataFrame([("lorem", 3)])
```

## SparkSession fixture

Use the `spark` fixture from `tests/conftest.py`. Never instantiate `SparkSession` inside a test.

```python
# ✔ Correct
def test_word_count_should_return_counts(spark: SparkSession) -> None: ...

# ❌ Incorrect
def test_word_count_should_return_counts() -> None:
    spark = SparkSession.builder.getOrCreate()
```

## Scoping assertions

Select only the columns under test before asserting.

```python
actual = result.select("word", "count")
expected = spark.createDataFrame(
    [("lorem", 3), ("ipsum", 1)],
    schema="`word` STRING, `count` BIGINT",
)
assertDataFrameEqual(actual, expected)
```
