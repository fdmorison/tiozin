from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, Self, TypeVar

if TYPE_CHECKING:
    from ..model import Schema

T = TypeVar("T")


class SchemaConverter(ABC, Generic[T]):
    @abstractmethod
    def export(self, schema: Schema) -> T:
        pass

    @abstractmethod
    def import_(self, schema: T) -> Schema:
        pass

    @classmethod
    def for_format(cls, format: str) -> Self:
        match format:
            case "spark":
                from .spark import SparkSchemaConverter

                return SparkSchemaConverter()
            case "odcs":
                from .odcs import OdcsSchemaConverter

                return OdcsSchemaConverter()
            case _:
                raise ValueError(f"Unsupported export format: {format}")
