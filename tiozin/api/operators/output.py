from abc import abstractmethod
from typing import Generic, Optional, TypeVar, Unpack

from .. import Context, Operator, OperatorKwargs, Plugable

TData = TypeVar("TData")
TWriter = TypeVar("TWriter")


class Output(Plugable, Operator, Generic[TData, TWriter]):
    """
    Output operators write transformed data to external destinations.

    Outputs support multiple destinations like databases, data warehouses,
    files, and streaming platforms. Providers implement write() for their target.

    Attributes:
        options: All extra initialization parameters of the operator flow into
            this attribute. Use it to pass provider-specific configurations like
            Spark write options (e.g., mode="overwrite", partitionBy=["date"]).

    Examples of outputs:
        - BigQueryOutput: Write to Google BigQuery tables
        - ParquetOutput: Save data as Parquet files
        - RedshiftOutput: Load data into Amazon Redshift
        - ElasticsearchOutput: Index data in Elasticsearch
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        **options: Unpack[OperatorKwargs],
    ) -> None:
        super().__init__(name, description, **options)

    @abstractmethod
    def write(self, context: Context, data: TData) -> TWriter:
        """
        Write data to destination. Providers must implement.

        Returns a writer object that the Runner will use to complete the operation.
        """

    def execute(self, context: Context, data: TData) -> TWriter:
        """Template method that delegates to write()."""
        return self.write(context, data)
