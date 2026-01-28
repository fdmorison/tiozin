import wrapt
from pyspark.sql import DataFrame

from tiozin import Context, EtlStep

from .typehints import SparkPlan


class SparkStepProxy(wrapt.ObjectProxy):
    """
    Proxy that adds Spark-specific, provider-level cross-cutting behavior to EtlSteps.

    Automatically registers DataFrames created by `read` and `transform` as temporary views named
    after the step and aliases the DataFrame with the step name. Views are created once and reused
    on subsequent calls.

    Notes:
        - Assumes that the step name is a valid Spark identifier.
        - Idempotent: if the view already exists, it is reused silently by design.
    """

    def read(self, context: Context) -> DataFrame:
        step: EtlStep = self.__wrapped__
        df: DataFrame = step.read(context)
        return self._create_view_if_not_exists(df)

    def transform(self, context: Context, *data: DataFrame) -> DataFrame:
        step: EtlStep = self.__wrapped__
        df: DataFrame = step.transform(context, *data)
        return self._create_view_if_not_exists(df)

    def write(self, context: Context, data: DataFrame) -> SparkPlan:
        step: EtlStep = self.__wrapped__
        df_or_writer: SparkPlan = step.write(context, data)
        return df_or_writer

    def _create_view_if_not_exists(self, df: DataFrame) -> DataFrame:
        if df is None:
            return df
        step: EtlStep = self.__wrapped__
        df.createOrReplaceTempView(step.name)
        return df.alias(step.name)

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
