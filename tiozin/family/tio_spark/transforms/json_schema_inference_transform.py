from humps.main import camelize
from pyspark.sql import DataFrame
from pyspark.sql import functions as sf
from pyspark.sql.types import StructType

from tiozin.utils import as_list, default

from .. import SparkTransform

FULL_SAMPLING_RATIO = 1.0

DEFAULT_READER_OPTIONS = dict(
    mode="FAILFAST",
    timeZone="UTC",
    primitivesAsString=False,
    allowComments=True,
    allowSingleQuotes=True,
    allowNumericLeadingZeros=True,
    dateFormat="yyyy-MM-dd",
    timestampFormat="yyyy-MM-dd'T'HH:mm:ss[.SSS][XXX]",
    samplingRatio=0.10,
)


class SparkJsonSchemaInferenceTransform(SparkTransform):
    """
    Infers schemas from JSON string columns.

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
        json_columns:
            Column name or list of column names containing JSON strings whose
            schemas should be inferred.

        sampling_ratio:
            Fraction of rows used to infer the schema. Defaults to ``0.10``.

        flatten:
            When ``True``, expands inferred fields into top-level columns.
            Defaults to ``False``.

        dateFormat:
            Pattern used to parse date strings. Accepts Java ``SimpleDateFormat``
            patterns. Defaults to ``yyyy-MM-dd``.

        timestampFormat:
            Pattern used to parse timestamp strings. Accepts Java
            ``SimpleDateFormat`` patterns. Defaults to
            ``yyyy-MM-dd'T'HH:mm:ss[.SSS][XXX]``.

    Examples:

        ```python
        SparkJsonSchemaInferenceTransform(
            name="infer schema",
            json_columns=["payload", "metadata"],
            flatten=True,
        )
        ```

        ```python
        SparkJsonSchemaInferenceTransform(
            name="infer schema",
            json_columns="payload",
            mode="PERMISSIVE",
            primitivesAsString=True,
            allowUnquotedFieldNames=True,
        )
        ```

        ```yaml
        transforms:
        - kind: SparkJsonSchemaInferenceTransform
            name: infer schema
            json_columns:
            - payload
            - metadata
            flatten: true
        ```

        ```yaml
        transforms:
        - kind: SparkJsonSchemaInferenceTransform
            name: infer schema
            json_columns: payload
            mode: PERMISSIVE
            primitivesAsString: true
            allowUnquotedFieldNames: true
        ```
    """

    def __init__(
        self,
        json_columns: list[str] = None,
        flatten: bool = False,
        **options,
    ) -> None:
        super().__init__(**options)
        # Plugin parameters
        self.json_columns = as_list(json_columns, [])
        self.flatten = flatten
        # Datasource parameters
        self.options = default(
            camelize(self.options),
            DEFAULT_READER_OPTIONS,
        )
        self.sampling_ratio = self.options["samplingRatio"]
        self.date_format = self.options["dateFormat"]
        self.timestamp_format = self.options["timestampFormat"]

    def transform(self, data: DataFrame) -> DataFrame:
        source_df = data
        inferred_df = data

        for column in self.json_columns:
            inferred_schema = self.infer_json_schema(source_df, column)
            inferred_df = inferred_df.withColumn(
                column, sf.from_json(column, inferred_schema, self.options)
            )

        if self.flatten:
            inferred_df = self.flatten_json_columns(inferred_df)

        return inferred_df

    def infer_json_schema(self, data: DataFrame, column: str) -> StructType:
        json_rdd = data.select(column).rdd.map(lambda row: row[0])
        sample_df = self.spark.read.options(**self.options).json(json_rdd)

        if not sample_df.schema.fields:
            options = {
                **self.options,
                "samplingRatio": FULL_SAMPLING_RATIO,
            }
            sample_df = self.spark.read.options(**options).json(json_rdd)

        self.info(f"Inferred schema for '{column}'")
        sample_df.printSchema()
        return sample_df.schema

    def flatten_json_columns(self, data: DataFrame) -> DataFrame:
        columns = [
            f"{column}.*" if column in self.json_columns else column for column in data.columns
        ]
        return data.select(*columns)
