from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

from ..exceptions import SchemaError

if TYPE_CHECKING:
    from ..model import Schema

T = TypeVar("T")


class SchemaConverter(ABC, Generic[T]):
    """
    Converts schemas to and from one external format.

    Built-in converters load on first use. Other packages add their own with
    `register`.

    Attributes:
        format: Name of the format, as given to `Schema.from_format` and
            `Schema.to_format`.

    Examples:

        Another package adds a format by implementing dump and load, then
        registering the converter:

        ```python
        class CsvHeaderConverter(SchemaConverter[str]):
            format = "csv-header"

            def dump(self, schema: Schema, **options) -> str:
                return ",".join(property.name for property in schema.properties or [])

            def load(self, schema: str, **options) -> Schema:
                return Schema(properties=[{"name": name} for name in schema.split(",")])

        SchemaConverter.register(CsvHeaderConverter())

        Schema.from_format("csv-header", "id,email").to_format("csv-header")
        # "id,email"
        ```
    """

    format: ClassVar[str]

    _registry: ClassVar[dict[str, SchemaConverter]] = {}

    @abstractmethod
    def dump(self, schema: Schema, **options) -> T:
        """
        Converts the schema to this format.

        Options are settings specific to this format. Each converter declares
        the options it supports and ignores the others.
        """
        pass

    @abstractmethod
    def load(self, schema: T | str, **options) -> Schema:
        """
        Converts a schema in this format to a Schema. The schema can also be a
        string holding the document of this format, such as Avro JSON.

        Options are settings specific to this format. Each converter declares
        the options it supports and ignores the others.
        """
        pass

    @classmethod
    def register(cls, converter: SchemaConverter) -> None:
        """
        Makes a converter available to `Schema.from_format` and
        `Schema.to_format`, under its format. A converter registered under a
        built-in format replaces the built-in one.

        Examples:

            ```python
            SchemaConverter.register(CsvHeaderConverter())
            ```
        """
        cls._registry[converter.format] = converter

    @classmethod
    def for_format(cls, format: str) -> SchemaConverter:
        """
        The converter for the given format.

        Raises SchemaError if no converter exists for the format.

        Examples:

            ```python
            converter = SchemaConverter.for_format("csv-header")
            converter.dump(schema)
            # "id,email"
            ```
        """
        if format not in cls._registry:
            cls.register(cls.builtin(format))

        return cls._registry[format]

    @staticmethod
    def builtin(format: str) -> SchemaConverter:
        """
        A new built-in converter for the given format.

        Raises SchemaError if the format is not built in.

        Examples:

            ```python
            SchemaConverter.builtin("avro")
            # AvroSchemaConverter()
            ```
        """
        match format:
            case "spark":
                from .spark import SparkSchemaConverter

                return SparkSchemaConverter()
            case "avro":
                from .avro import AvroSchemaConverter

                return AvroSchemaConverter()
            case _:
                raise SchemaError(f"Unsupported schema format `{format}`")
