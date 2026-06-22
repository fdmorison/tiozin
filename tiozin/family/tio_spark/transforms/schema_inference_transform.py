from humps.main import camelize
from pyspark.sql import DataFrame
from pyspark.sql import functions as sf
from pyspark.sql.types import StructType

from tiozin.utils import as_list, default

from .. import SparkTransform
from .. import functions as tio

FULL_SAMPLING_RATIO = 1.0

DEFAULT_READER_OPTIONS = dict(
    mode="FAILFAST",
    primitivesAsString=False,
    allowComments=True,
    allowSingleQuotes=True,
    allowNumericLeadingZeros=True,
)


class SparkSchemaInferenceTransform(SparkTransform):
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
            Field or list of fields containing JSON strings to infer schemas from.

        sampling_ratio:
            Fraction of rows used for schema inference. Defaults to ``0.10``.

        unnest_fields:
            Field or list of fields to expand into top-level columns after schema inference.

        timezone:
            Default timezone used when parsing timestamp values without a timezone
            indicator. This setting is applied to ``auto_timestamp_fields`` and passed
            to Spark readers that support timezone-aware parsing (such as JSON).
            Defaults to ``UTC``.

        timestamp_format:
            Pattern or list of patterns used to parse timestamps
            (e.g., ``"dd/MM/yyyy HH:mm:ss"``). Accepts Java SimpleDateFormat patterns.
            Only the first pattern is passed to the JSON reader and ``timestamp_fields``.
            When omitted, Spark infers the format.

        date_format:
            Pattern or list of patterns used to parse date values
            (e.g., ``"dd/MM/yyyy"``). Accepts Java SimpleDateFormat patterns.
            Only the first pattern is passed to ``date_fields``. When omitted, Spark
            infers the format.

        auto_timestamp_fields:
            Field or list of fields to convert to UTC timestamps. Each value is inspected
            at runtime: timezone-aware strings use the embedded timezone; timezone-naive
            strings are assumed to be in ``timezone`` and converted to UTC; numeric values
            and numeric strings are interpreted as compact dates (``yyyyMMdd`` or
            ``yyyyMMddHHmmss``). When ``timestamp_format`` or ``date_format`` are
            provided, all patterns from both are combined (deduplicated, preserving order)
            and tried in sequence. Applied after JSON schema inference. Use dot notation
            for nested fields.

        timestamp_fields:
            Field or list of fields to convert to timestamps using the Spark
            ``to_timestamp`` function. When ``timestamp_format`` is provided, it is used
            to parse the field; otherwise Spark infers the format. Fields that do not
            exist in the DataFrame are silently ignored. Applied after JSON schema
            inference. Use dot notation for nested fields.

        date_fields:
            Field or list of fields to convert to dates using the Spark ``to_date``
            function. When ``date_format`` is provided, it is used to parse the field;
            otherwise Spark infers the format. Fields that do not exist in the DataFrame
            are silently ignored. Applied after JSON schema inference. Use dot notation
            for nested fields.

    Examples:

        ```python
        SparkSchemaInferenceTransform(
            name="infer schema",
            json_fields=["payload", "metadata"],
            auto_timestamp_fields=["payload.created_at", "payload.updated_at"]
        )
        ```

        ```yaml
        transforms:
        - kind: SparkSchemaInferenceTransform
            name: infer schema
            json_fields: ["payload", "metadata"]
            auto_timestamp_fields: ["payload.created_at", "payload.updated_at"]
        ```

        ```yaml
        transforms:
        - kind: SparkSchemaInferenceTransform
            name: infer schema
            json_fields: ["payload", "metadata"]
            mode: PERMISSIVE
            # Spark Reader extra fields
            primitivesAsString: true
            allowUnquotedFieldNames: true
        ```
    """

    def __init__(
        self,
        json_fields: list[str] = None,
        sampling_ratio: float = None,
        unnest_fields: list[str] = None,
        timezone: str = None,
        timestamp_format: str | list[str] = None,
        auto_timestamp_fields: list[str] = None,
        timestamp_fields: list[str] = None,
        date_fields: list[str] = None,
        date_format: str | list[str] = None,
        **options,
    ) -> None:
        super().__init__(**options)
        # Plugin parameters
        self.json_fields = as_list(json_fields, [])
        self.sampling_ratio = default(sampling_ratio, 0.10)
        self.unnest_fields = as_list(unnest_fields, [])
        self.timezone = timezone or "UTC"
        self.timestamp_format = as_list(timestamp_format)
        self.timestamp_fields = as_list(timestamp_fields, [])
        self.auto_timestamp_fields = as_list(auto_timestamp_fields, [])
        self.date_fields = as_list(date_fields, [])
        self.date_format = as_list(date_format)
        # Reader parameters
        self.reader_options = {
            k: v
            for k, v in {
                **DEFAULT_READER_OPTIONS,
                **camelize(self.options),
                "timeZone": self.timezone,
                "samplingRatio": self.sampling_ratio,
                "timestampFormat": self.timestamp_format[0] if self.timestamp_format else None,
            }.items()
            if v is not None
        }

    def transform(self, data: DataFrame) -> DataFrame:
        source_df = data
        result_df = data

        for field in self.json_fields:
            inferred_schema = self.infer_json_schema(source_df, field)
            result_df = result_df.withColumn(
                field, sf.from_json(field, inferred_schema, self.reader_options)
            )

        result_df = self.enforce_datetime(result_df)

        if self.unnest_fields:
            result_df = self.unnest_json_fields(result_df)

        return result_df

    def infer_json_schema(self, data: DataFrame, field: str) -> StructType:
        json_rdd = data.select(field).rdd.map(lambda row: row[0])
        sample_df = self.spark.read.options(**self.reader_options).json(json_rdd)

        if not sample_df.schema.fields:
            options = {
                **self.reader_options,
                "samplingRatio": FULL_SAMPLING_RATIO,
            }
            sample_df = self.spark.read.options(**options).json(json_rdd)

        self.info(f"Inferred schema for '{field}'")
        sample_df.printSchema()
        return sample_df.schema

    def unnest_json_fields(self, data: DataFrame) -> DataFrame:
        fields = [f"{field}.*" if field in self.unnest_fields else field for field in data.columns]
        return data.select(*fields)

    def enforce_datetime(self, data: DataFrame) -> DataFrame:
        first_timestamp_format = self.timestamp_format[0] if self.timestamp_format else None
        first_date_format = self.date_format[0] if self.date_format else None
        auto_formats = list(set(self.timestamp_format or []) | set(self.date_format or []))

        for field in self.auto_timestamp_fields:
            data = tio.with_field(
                data,
                field,
                tio.to_auto_timestamp(field, format=auto_formats, timezone=self.timezone),
            )

        for field in self.timestamp_fields:
            if tio.get_field(data, field) is not None:
                data = tio.with_field(
                    data,
                    field,
                    sf.to_timestamp(field, first_timestamp_format),
                )

        for field in self.date_fields:
            if tio.get_field(data, field) is not None:
                data = tio.with_field(
                    data,
                    field,
                    sf.to_date(field, first_date_format),
                )

        return data
