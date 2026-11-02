"""
PySpark DataFrame and Column functions.

Functions that operate directly on PySpark ``DataFrame`` and ``Column``
objects.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as sf
from pyspark.sql.types import ArrayType, StructField, StructType

from tiozin.exceptions import TiozinInputError
from tiozin.utils import as_list

from .utils import join_field, split_field

FIELD_DELIMITER = "."
DATE_DELIMITERS = "_-./"
TIMEZONE_OFFSET_PATTERN = (
    r"("
    r"Z|UTC"
    r"|[+-]\d\d:\d\d"
    r"|([\./:]\d{2}|\.\d+|\d{3,})\s?[+-]\d{2}(?::?\d{2})?"  # +HH, +HHMM, +HH:MM
    r"|\s?[A-Za-z]{2,5}([+-]\d{1,2}(:?\d{2})?)?"  # any abbrev: UTC, GMT+8, PST, BRT, AEST
    r"|\s?[A-Za-z]+/[A-Za-z_]+(/[A-Za-z_]+)?"  # IANA zone: America/Sao_Paulo
    r")$"
)
TIMESTAMP_FORMATS = [
    *[f"yyyy{d}MM{d}dd[['T'][' ']HH:mm[:ss][.SSSSSS][' ']][XXX][x][O][z]" for d in DATE_DELIMITERS],
    *[f"dd{d}MM{d}yyyy[['T'][' ']HH:mm[:ss][.SSSSSS][' ']][XXX][x][O][z]" for d in DATE_DELIMITERS],
    "yyyyMMdd[XXX][x][O][z]",
    "yyyyMMddHHmmss[XXX][x][O][z]",
    "dd MMM yyyy HH:mm:ss[ ][XXX][x][O][z]",
]
EPOCH_PATTERN = r"^\d+$"

PARTITION_EXPR = re.compile(r"(?:(?P<transform>\w+)\()?(?P<arguments>[^()]+)\)?")


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


def list_fields(
    df: DataFrame | StructType,
    leaves_only: bool = False,
    stop_at_arrays: bool = False,
) -> dict[str, str]:
    """
    Lists all fields in a DataFrame schema with their DDL types, including nested fields.

    Walks the schema depth-first, descending into structs and into the element
    type of arrays of structs. Nested fields are named by their dotted path.

    Args:
        df:
            The DataFrame or schema to inspect.
        leaves_only:
            Whether to omit the fields that have children. Defaults to False.
        stop_at_arrays:
            Whether to list arrays without descending into their elements.
            Defaults to False.

    Returns:
        The field names mapped to their DDL types, sorted by name.

    Example:
        ```python
        list_fields(df)
        # -> {
        #     "address": "struct<city:string>",
        #     "address.city": "string",
        #     "id": "bigint",
        #     "items": "array<struct<sku:string>>",
        #     "items.sku": "string",
        # }

        list_fields(df, leaves_only=True)
        # -> {"address.city": "string", "id": "bigint", "items.sku": "string"}

        list_fields(df, stop_at_arrays=True)
        # -> {
        #     "address": "struct<city:string>",
        #     "address.city": "string",
        #     "id": "bigint",
        #     "items": "array<struct<sku:string>>",
        # }

        list_fields(df, leaves_only=True, stop_at_arrays=True)
        # -> {"address.city": "string", "id": "bigint", "items": "array<struct<sku:string>>"}
        ```
    """

    def walk(schema: StructType, path: list[str]):
        for field in schema.fields:
            field_path = [*path, field.name]
            field_name = join_field(field_path)
            field_type = field.dataType
            if isinstance(field_type, ArrayType) and not stop_at_arrays:
                field_type = field_type.elementType
            is_leaf = not isinstance(field_type, StructType)
            if is_leaf or not leaves_only:
                yield field_name, field.dataType.simpleString()
            if not is_leaf:
                yield from walk(field_type, field_path)

    schema = df if isinstance(df, StructType) else df.schema
    return dict(sorted(walk(schema, [])))


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


def to_partition_column(expr: str | Column) -> Column:
    """
    Converts a partition expression into a column for `DataFrameWriterV2.partitionedBy()`.

    An expression is either a column name or a call to a function from
    `pyspark.sql.functions`. Call arguments are passed to the function.

    Args:
        expr:
            The partition expression. A `Column` is returned as is.

    Returns:
        The column or transform to partition by.

    Raises:
        TiozinInputError: If the expression cannot be parsed or names an unknown function.

    Example:
        ```python
        to_partition_column("created_at")
        # -> col("created_at")

        to_partition_column("days(created_at)")
        # -> days("created_at")

        to_partition_column("bucket(16, customer_id)")
        # -> bucket(16, col("customer_id"))
        ```
    """
    if isinstance(expr, Column):
        return expr

    match = PARTITION_EXPR.fullmatch(expr.strip())
    TiozinInputError.raise_if(
        match is None,
        f"Invalid partition expression: '{expr}'",
    )

    transform = match["transform"] or "col"
    arguments = match["arguments"] or ""

    function = getattr(sf, transform, None)
    TiozinInputError.raise_if(
        function is None,
        f"Unknown partition transform: '{transform}'",
    )

    args = tuple(arg.strip() for arg in arguments.split(","))

    if function == sf.bucket:
        num_buckets, col = args
        return function(int(num_buckets), sf.col(col))

    return function(*args)


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


def to_auto_timestamp(
    field: str | Column,
    format: str | list[str] = None,
    timezone: str = None,
) -> Column:
    """
    Converts a column to a UTC timestamp by trying a broad set of built-in formats.

    No ``format`` parameter is needed for most common timestamp shapes.
    Custom formats are tried first; built-in formats always follow as a fallback,
    so specifying a format extends the search without removing coverage.
    Values that match no format produce ``null``.

    Rules:
        - Timezone-aware values use the timezone present in the value.
        - Timezone-naive values assume the ``timezone`` parameter.
        - Numeric values and numeric strings are interpreted as compact dates, not epoch.

    Built-in formats (tried after any custom ``format``):
        ISO / delimited (``_``, ``-``, ``.``, ``/``):
            ``yyyy-MM-dd``, ``yyyy/MM/dd``, ``yyyy_MM_dd``, ``yyyy.MM.dd``
            Each accepts an optional ``T`` or space separator, ``HH:mm[:ss][.SSSSSS]``,
            and any timezone indicator.

        European / delimited (``_``, ``-``, ``.``, ``/``):
            ``dd-MM-yyyy``, ``dd/MM/yyyy``, ``dd_MM_yyyy``, ``dd.MM.yyyy``
            Each accepts an optional time component and timezone indicator.

        Compact:
            ``yyyyMMdd``, ``yyyyMMddHHmmss``, each with optional timezone.

        RFC 2822:
            ``dd MMM yyyy HH:mm:ss`` with optional timezone
            (e.g., ``15 Jan 2024 10:30:00 UTC``).

    Args:
        field:
            Column name or Column to convert.
        format:
            Optional format or list of formats tried before the built-in defaults.
        timezone:
            Source timezone for values without a timezone indicator.
            Defaults to ``UTC``.

    Returns:
        A UTC timestamp column. Values that match no format are ``null``.

    Examples:
        "2024-01-15T10:30:00Z"      -> 2024-01-15T10:30:00Z
        "2024-01-15T10:30:00-03:00" -> 2024-01-15T13:30:00Z
        "2024-01-15T10:30:00 BRT"   -> 2024-01-15T13:30:00Z
        "2024-01-15T10:30:00"       -> 2024-01-15T10:30:00Z
        "20240115103000"            -> 2024-01-15T10:30:00Z
        20240115103000              -> 2024-01-15T10:30:00Z

        timezone="America/Sao_Paulo":
        "2024-01-15T10:30:00"       -> 2024-01-15T13:30:00Z

        format="dd/MM/yyyy HH:mm:ss":
        "15/01/2024 10:30:00"       -> 2024-01-15T10:30:00Z
    """
    field = sf.col(field) if isinstance(field, str) else field
    field = field.cast("STRING")
    timezone = sf.lit(timezone or "UTC")
    formats = as_list(format, []) + TIMESTAMP_FORMATS

    parse_ntz = sf.coalesce(
        *[sf.to_utc_timestamp(sf.try_to_timestamp(field, sf.lit(fmt)), timezone) for fmt in formats]
    )
    parse_wtz = sf.coalesce(*[sf.try_to_timestamp(field, sf.lit(fmt)) for fmt in formats])

    return sf.when(
        has_timezone(field),
        parse_wtz,
    ).otherwise(
        parse_ntz,
    )
