from abc import abstractmethod
from typing import Generic, TypeVar

from tiozin.api import Tiozin
from tiozin.exceptions import TiozinNotFoundError

TMetadata = TypeVar("TMetadata")


class Registry(Tiozin, Generic[TMetadata]):
    """
    Base class for metadata registries.

    Stores and retrieves metadata for resources, configurations, or entities.
    Subclasses define storage and retrieval implementation.
    """

    def __init__(self, **options) -> None:
        super().__init__(**options)
        self.ready = False

    @abstractmethod
    def get(self, identifier: str, version: str | None = None) -> TMetadata:
        """
        Retrieve metadata by identifier.

        Raises:
            NotFoundException: When metadata was not found.
        """

    @abstractmethod
    def register(self, identifier: str, value: TMetadata) -> None:
        """Register metadata in the registry."""

    def try_get(self, identifier: str, version: str | None = None) -> TMetadata | None:
        """Retrieve metadata or return None if not found."""
        try:
            return self.get(identifier, version)
        except TiozinNotFoundError:
            return None
