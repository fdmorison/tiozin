from abc import abstractmethod
from typing import Generic, Optional, TypeVar

from .context import Context
from .plugable import Plugable
from .resource import Resource

TData = TypeVar("TData")


class Input(Plugable, Resource, Generic[TData]):
    """
    Input components read data from external sources into Tiozin pipelines.

    Inputs support multiple sources like databases, files, APIs, streams,
    and cloud storage. They can optionally include schema metadata for
    validation and type enforcement.

    Schema attributes:
        - schema: Data schema definition (JSON, Avro, etc)
        - schema_subject: Subject name in schema registry
        - schema_version: Specific schema version to use

    Examples of inputs:
        - S3Input: Read files from Amazon S3
        - PostgresInput: Query data from PostgreSQL
        - KafkaInput: Consume messages from Kafka topics
        - HttpApiInput: Fetch data from REST APIs
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        schema: Optional[str] = None,
        schema_subject: Optional[str] = None,
        schema_version: Optional[str] = None,
        **options,
    ) -> None:
        super().__init__(name, description, **options)
        self.schema = schema
        self.schema_subject = schema_subject
        self.schema_version = schema_version

    @abstractmethod
    def read(self, context: Context) -> TData:
        """Read data from source. Providers must implement."""

    def execute(self, context: Context) -> TData:
        """Template method that delegates to read()."""
        return self.read(context)
