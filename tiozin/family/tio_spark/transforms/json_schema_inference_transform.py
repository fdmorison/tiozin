from humps.main import camelize
from pyspark.sql import DataFrame
from pyspark.sql import functions as sf
from pyspark.sql.types import StructType

from tiozin.utils import as_list, default

from .. import SparkTransform
from ..utils import with_field

FULL_SAMPLING_RATIO = 1.0

DEFAULT_READER_OPTIONS = dict(
    mode="FAILFAST",
    timeZone="UTC",
    primitivesAsString=False,
    allowComments=True,
    allowSingleQuotes=True,
    allowNumericLeadingZeros=True,
    samplingRatio=0.10,
)


class SparkJsonSchemaInferenceTransform(SparkTransform):
    """
    Infers schemas from JSON string fields.

    To infer the schema, the transform samples a portion of the data. By default,
    10% of the rows are used. For large datasets, a smaller sampling ratio may
    reduce inference cost. If no schema can be inferred from the sample, the
    transform automatically retries using all rows.

    The transform uses the following JSON reader defaults:

    - Fails fast when invalid JSON is found.
    - Uses UTC for date and time parsing.
    - Accepts JSON comments.
    - Accepts single quotes.
    - Accepts numeric values with leading zeros.

    Additional reader options can be provided and override the defaults. For all supported JSON
    reader options, refer to:

    https://spark.apache.org/docs/latest/sql-data-sources-json.html

    Attributes:
        json_fields:
            Field name or list of field names containing JSON strings whose
            schemas should be inferred.

        sampling_ratio:
            Fraction of rows used to infer the schema. Defaults to ``0.10``.

        flatten:
            When ``True``, expands inferred fields into top-level fields.
            Defaults to ``False``.

        timezone:
            Timezone of the source data. Used to convert naive timestamps in
            ``timestamp_without_timezone_fields`` to UTC. Defaults to ``UTC``.

        timestamp_with_timezone_fields:
            Field or list of fields containing timestamp strings with an embedded
            timezone offset (for example, ``"2024-01-15T10:30:00-03:00"``). The
            offset in the string is respected. Nested fields are supported using
            dot notation.

        timestamp_without_timezone_fields:
            Field or list of fields containing naive timestamp strings without a
            timezone offset (for example, ``"2024-01-15T10:30:00"``). The strings
            are interpreted as being in ``timezone`` and converted to UTC. Nested
            fields are supported using dot notation.

        timestamp_format:
            Pattern used to parse timestamp strings. Accepts Java ``SimpleDateFormat`` patterns.
            When omitted, Spark infers the format from the data.

    Examples:

        ```python
        SparkJsonSchemaInferenceTransform(
            name="infer schema",
            json_fields=["payload", "metadata"],
            flatten=True,
        )
        ```

        ```python
        SparkJsonSchemaInferenceTransform(
            name="infer schema",
            json_fields="payload",
            mode="PERMISSIVE",
            primitivesAsString=True,
            allowUnquotedFieldNames=True,
        )
        ```

        ```yaml
        transforms:
        - kind: SparkJsonSchemaInferenceTransform
            name: infer schema
            json_fields:
            - payload
            - metadata
            flatten: true
        ```

        ```yaml
        transforms:
        - kind: SparkJsonSchemaInferenceTransform
            name: infer schema
            json_fields: payload
            mode: PERMISSIVE
            primitivesAsString: true
            allowUnquotedFieldNames: true
        ```
    """

    def __init__(
        self,
        json_fields: list[str] = None,
        timestamp_with_timezone_fields: list[str] = None,
        timestamp_without_timezone_fields: list[str] = None,
        flatten: bool = False,
        **options,
    ) -> None:
        super().__init__(**options)
        # Plugin parameters
        self.json_fields = as_list(json_fields, [])
        self.timestamp_with_timezone_fields = as_list(timestamp_with_timezone_fields, [])
        self.timestamp_without_timezone_fields = as_list(timestamp_without_timezone_fields, [])
        self.flatten = flatten
        # Datasource parameters
        self.options = default(
            camelize(self.options),
            DEFAULT_READER_OPTIONS,
        )
        self.sampling_ratio = self.options.get("samplingRatio")
        self.timezone = self.options.get("timeZone")
        self.timestamp_format = self.options.get("timestampFormat")

    def transform(self, data: DataFrame) -> DataFrame:
        source_df = data
        result_df = data

        for field in self.json_fields:
            inferred_schema = self.infer_json_schema(source_df, field)
            result_df = result_df.withColumn(
                field, sf.from_json(field, inferred_schema, self.options)
            )

        result_df = self.enforce_datetime(result_df)

        if self.flatten:
            result_df = self.flatten_json_fields(result_df)

        return result_df

    def infer_json_schema(self, data: DataFrame, field: str) -> StructType:
        json_rdd = data.select(field).rdd.map(lambda row: row[0])
        sample_df = self.spark.read.options(**self.options).json(json_rdd)

        if not sample_df.schema.fields:
            options = {
                **self.options,
                "samplingRatio": FULL_SAMPLING_RATIO,
            }
            sample_df = self.spark.read.options(**options).json(json_rdd)

        self.info(f"Inferred schema for '{field}'")
        sample_df.printSchema()
        return sample_df.schema

    def flatten_json_fields(self, data: DataFrame) -> DataFrame:
        fields = [f"{field}.*" if field in self.json_fields else field for field in data.columns]
        return data.select(*fields)

    def enforce_datetime(self, data: DataFrame) -> DataFrame:
        timestamp_format = sf.lit(self.timestamp_format) if self.timestamp_format else None

        for field in self.timestamp_with_timezone_fields:
            data = with_field(data, field, sf.to_timestamp_ltz(field, timestamp_format))

        for field in self.timestamp_without_timezone_fields:
            ts = sf.to_timestamp_ntz(field, timestamp_format)
            data = with_field(data, field, sf.to_utc_timestamp(ts, self.timezone))

        return data
