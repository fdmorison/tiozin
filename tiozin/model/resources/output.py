from abc import abstractmethod
from typing import Generic, Optional, TypeVar, Unpack

from ..context import Context
from ..plugable import Plugable
from ..resource import Resource
from ..typehint import Taxonomy

TData = TypeVar("TData")
TWriter = TypeVar("TWriter")


class Output(Plugable, Resource, Generic[TData, TWriter]):
    """
    Output components write transformed data to external destinations.

    Outputs support multiple destinations like databases, data warehouses,
    files, and streaming platforms. Providers implement write() for their target.

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
        **kwargs: Unpack[Taxonomy],
    ) -> None:
        super().__init__(name, description, **kwargs)

    @abstractmethod
    def write(self, context: Context, data: TData) -> TWriter:
        """
        Write data to destination. Providers must implement.

        Returns a writer object that the Runner will use to complete the operation.
        """

    def execute(self, context: Context, data: TData) -> TWriter:
        """Template method that delegates to write()."""
        return self.write(context, data)
