from typing import TYPE_CHECKING

import wrapt
from pyspark.sql import DataFrame

from tiozin.utils.runtime import tio_alias

if TYPE_CHECKING:
    from ...typehints import SparkEtlStep, SparkPlan


class SparkStepProxy(wrapt.ObjectProxy):
    """
    Spark-specific proxy for ETL steps.

    This proxy layers Spark execution semantics on top of generic ETL steps, allowing them to
    participate in SQL-first pipelines without leaking Spark-specific concerns into step
    implementations.

    The proxy is responsible for mediating how step results are exposed to the Spark execution
    environment.
    """

    def __repr__(self) -> str:
        return repr(self.__wrapped__)

    def read(self) -> DataFrame:
        """
        Executes the input step and exposes its result as a Spark temporary view.

        The resulting DataFrame is registered under the step name, making
        it available for downstream SQL-based steps.
        """
        step: SparkEtlStep = self.__wrapped__
        df: DataFrame = step.read()
        return self._register_view(df)

    def transform(self, *data: DataFrame) -> DataFrame:
        """
        Executes the transform step and exposes its result as a Spark temporary view.

        Registering the result allows subsequent steps to reference the
        transformation by name in SQL queries.
        """
        step: SparkEtlStep = self.__wrapped__
        df: DataFrame = step.transform(*data)
        return self._register_view(df)

    def write(self, data: DataFrame) -> "SparkPlan":
        """
        Executes the output step.

        Write steps that return a DataFrame are registered as views.
        Non-DataFrame results (e.g. DataFrameWriter) are passed through
        unchanged, as they represent terminal actions.
        """
        step: SparkEtlStep = self.__wrapped__
        df_or_writer: SparkPlan = step.write(data)
        return self._register_view(df_or_writer)

    def _register_view(self, df: DataFrame) -> DataFrame:
        """
        Registers a DataFrame as a Spark temporary view using the step name.
        """
        if not isinstance(df, DataFrame):
            return df

        step: SparkEtlStep = self.__wrapped__
        view_name = step.name

        df.createOrReplaceTempView(view_name)
        df = df.alias(view_name)
        tio_alias(df, view_name)
        return df
