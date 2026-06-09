from __future__ import annotations

from collections.abc import Callable

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as sf
from pyspark.sql.types import ArrayType, StructField, StructType

FIELD_DELIMITER = "."
FIELD_PLACEHOLDER = "\x00"
FIELD_ESCAPED_DELIMITER = "\\."


def split_field(field: str) -> list[str]:
    """
    Splits a dotted field path into its components.

    A literal dot can be escaped with a backslash to keep it as part of a
    single component instead of triggering a split.

    Args:
        field:
            Dotted field path. Use a backslash before the dot to keep it as
            a literal character within a component.

    Returns:
        List of field path components.

    Example:
        ```python
        split_field("address.city")
        # -> ["address", "city"]

        split_field("created\\.at")
        # -> ["created.at"]
        ```
    """
    escaped = field.replace(FIELD_ESCAPED_DELIMITER, FIELD_PLACEHOLDER)
    parts = escaped.split(FIELD_DELIMITER)
    return [part.replace(FIELD_PLACEHOLDER, FIELD_DELIMITER) for part in parts]


def join_field(fields: list[str]) -> str:
    """
    Joins field path components into a dotted path.

    Any literal dot inside a component is escaped with a backslash, so the
    result round-trips back through `split_field`.

    Args:
        fields:
            Field path components to join.

    Returns:
        The dotted field path.

    Example:
        ```python
        join_field(["address", "city"])
        # -> "address.city"

        join_field(["created.at"])
        # -> "created\\.at"
        ```
    """
    escaped = [field.replace(FIELD_DELIMITER, FIELD_ESCAPED_DELIMITER) for field in fields]
    return FIELD_DELIMITER.join(escaped)


def get_field(df: DataFrame, field: str) -> StructField | None:
    """
    Resolves a field in a DataFrame schema, including nested fields.

    Walks the schema following the dotted path, descending into structs and
    into the element type of arrays of structs.

    Args:
        df:
            The DataFrame whose schema is inspected.
        field:
            Dotted field path. Use a backslash before the dot to keep it as
            a literal character within a component.

    Returns:
        The resolved StructField, or None if the path does not exist.

    Example:
        ```python
        get_field(df, "address.city")
        # -> StructField('city', StringType(), True)

        get_field(df, "missing.path")
        # -> None
        ```
    """
    fields = df.schema.fields

    for name in split_field(field):
        child = next((f for f in fields if f.name == name), None)
        if not child:
            return None
        dtype = child.dataType
        match dtype:
            case StructType():
                fields = dtype.fields
            case ArrayType(elementType=StructType()):
                fields = dtype.elementType.fields
            case _:
                fields = []

    return child


def with_field(
    df: DataFrame,
    field: str,
    fn_or_column: Callable[..., Column] | Column,
    **kwargs,
) -> DataFrame:
    """
    Applies a Spark function or expression to a field, including nested fields.

    Spark's `withColumn` cannot target a nested field: it treats the dotted
    string as a top-level column name. This rebuilds the enclosing struct with
    `Column.withField` so the value is applied to the actual nested field.

    The `fn_or_column` argument is either a Column expression used as is, or a
    callable that receives the field name as its first argument. Extra keyword
    arguments are forwarded to the callable.

    Args:
        df:
            The DataFrame to transform.
        field:
            Dotted field path. Use a backslash before the dot to keep it as
            a literal character within a component.
        fn_or_column:
            A Column expression, or a Spark function applied to the field name.
        **kwargs:
            Extra keyword arguments forwarded when `fn_or_column` is a callable.

    Returns:
        A new DataFrame with the value applied to the field.

    Example:
        ```python
        with_field(df, "created_at", sf.to_timestamp)
        # applies to_timestamp to the top-level created_at column

        with_field(df, "event.created_at", sf.to_timestamp, format="yyyy-MM-dd")
        # applies to_timestamp with a format to the nested event.created_at field

        with_field(df, "amount", sf.col("amount").cast("decimal(10,2)"))
        # applies a prebuilt Column expression to the amount field
        ```
    """
    root, *nested = split_field(field)

    if isinstance(fn_or_column, Column):
        column = fn_or_column
    else:
        column = fn_or_column(field, **kwargs)

    if not nested:
        return df.withColumn(root, column)

    path = FIELD_DELIMITER.join(nested)
    return df.withColumn(root, sf.col(root).withField(path, column))
