"""
PySpark DataFrame and Column functions.

Functions that operate directly on PySpark ``DataFrame`` and ``Column``
objects.
"""

from __future__ import annotations

from collections.abc import Callable

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as sf
from pyspark.sql.types import ArrayType, StructField, StructType

from .utils import join_field, split_field

FIELD_DELIMITER = "."
TIMEZONE_OFFSET_PATTERN = (
    r"("
    r"Z|UTC"
    r"|[+-]\d\d:\d\d"
    r"|([\./:]\d{2}|\.\d+|\d{3,})\s?[+-]\d{2}(?::?\d{2})?"  # +HH, +HHMM, +HH:MM
    r"|\s?[A-Za-z]{2,5}([+-]\d{1,2}(:?\d{2})?)?"  # any abbrev: UTC, GMT+8, PST, BRT, AEST
    r"|\s?[A-Za-z]+/[A-Za-z_]+(/[A-Za-z_]+)?"  # IANA zone: America/Sao_Paulo
    r")$"
)
EPOCH_PATTERN = r"^\d+$"


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

    path = join_field(nested)
    return df.withColumn(root, sf.col(root).withField(path, column))


def has_timezone(field: str | Column) -> Column:
    """
    Detects whether a timestamp-like string ends with a timezone indicator.

    Assumes the field holds timestamp strings; it is not a validator for free-form text.
    Detection is lexical (anchored at the end), not a check that the timezone is real.

    Detects:
        - `Z`
        - Numeric offset (`+HH`, `+HHMM`, `+HH:MM`), only when following a time component,
          so a trailing year (e.g. `-2024` in `01-01-2024`) is not mistaken for an offset.
        - 2-5 letter abbreviation, optional offset (`UTC`, `PST`, `AEST`, `GMT+8`).
        - IANA zone id, two or three segments (`America/Sao_Paulo`).

    Args:
        field:
            Column name or Column holding timestamp-like strings.

    Returns:
        A boolean Column, `True` when a timezone indicator is found at the end.

    Examples:
        "2024-01-15T10:30:00Z"                   -> True
        "2024/01/15T10:30:00Z"                   -> True
        "15/01/2024T10:30:00Z"                   -> True
        "2024-01-15T10:30:00 Z"                  -> True
        "2024-01-15T10:30:00 UTC"                -> True
        "2024-01-15T10:30:00-04:00"              -> True
        "2024-01-15T10:30:00+04:00"              -> True
        "2024-01-15T10:30:00 GMT+8"              -> True
        "2024-01-15T10:30:00 America/Sao_Paulo"  -> True
        "2024-01-15T10:30:00"                    -> False
        "20240115103000Z"                        -> True
        "20240115103000"                         -> False
        "2024-01-01Z"                            -> True
        "2024/01/01Z"                            -> True
        "01/01/2024Z"                            -> True
        "2024-01-01"                             -> False
    """
    field = sf.col(field) if isinstance(field, str) else field
    return field.rlike(TIMEZONE_OFFSET_PATTERN)


def to_auto_timestamp(field: str, timezone: str = None, format: str = None) -> Column:
    """
    Converts a column to a UTC timestamp.

    Useful for ingestion scenarios where timestamp formats are inconsistent.

    Rules:
        - Timezone-aware values use the timezone present in the value.
        - Timezone-naive values assume the ``timezone`` parameter.
        - Numeric values and numeric strings are interpreted as Unix epoch seconds.

    Args:
        field:
            Column name to convert.
        timezone:
            Source timezone for values without a timezone indicator.
            Defaults to ``UTC``.
        format:
            Optional datetime format. Disables epoch detection.

    Returns:
        A UTC timestamp column.

    Examples:
        "2024-01-15T10:30:00Z"      -> 2024-01-15T10:30:00Z
        "2024-01-15T10:30:00-03:00" -> 2024-01-15T13:30:00Z
        "2024-01-15T10:30:00"       -> 2024-01-15T10:30:00Z
        "1705314600"                -> 2024-01-15T10:30:00Z
        1705314600                  -> 2024-01-15T10:30:00Z

        timezone="America/Sao_Paulo":
        "2024-01-15T10:30:00"       -> 2024-01-15T13:30:00Z

        format="dd/MM/yyyy HH:mm:ss":
        "15/01/2024 10:30:00"       -> 2024-01-15T10:30:00Z
    """
    field = sf.upper(sf.col(field).cast("STRING"))
    timezone = timezone or "UTC"
    fmt = sf.lit(format) if format else None

    expr = sf.when(
        field.rlike(TIMEZONE_OFFSET_PATTERN),
        sf.to_timestamp_ltz(field, fmt),
    )

    if not format:
        expr = expr.when(
            field.rlike(EPOCH_PATTERN),
            sf.timestamp_seconds(field.cast("LONG")),
        )

    return expr.otherwise(
        sf.to_utc_timestamp(
            sf.to_timestamp_ntz(field, fmt),
            timezone,
        ),
    )
