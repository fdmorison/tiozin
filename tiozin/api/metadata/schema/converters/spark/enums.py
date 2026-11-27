from enum import StrEnum


class SparkTimeType(StrEnum):
    """
    Spark type a time property is written as. An option of the Spark writer,
    neither an Open Data Contract Standard type nor a Tiozin convention, and
    never written to a schema.

    No single Spark type reads a time from every source, so pick the one the
    source supports.

    - time: time(3) in millis, time(6) otherwise, Spark 4.1 and later.
    - timestamp_ntz: a timestamp without timezone, the default.
    - long: the time as a number.
    - string: the time as text.

    Examples:

        ```python
        schema.to_spark(time_type=SparkTimeType.TIME)
        schema.to_spark(time_type="time")
        ```
    """

    TIME = "time"
    TIMESTAMP_NTZ = "timestamp_ntz"
    LONG = "long"
    STRING = "string"
