from abc import abstractmethod
from typing import Generic, TypeVar

from tiozin.api import Plugable, Resource
from tiozin.exceptions import NotFoundError
from tiozin.utils import helpers

TMetadata = TypeVar("TMetadata")


class Registry(Plugable, Resource, Generic[TMetadata]):
    """
    Base class for metadata registries.

    Stores and retrieves metadata for resources, configurations, or entities.
    Subclasses define storage and retrieval implementation.
    """

    def __init__(self, **options) -> None:
        super().__init__(**options)
        self.registry_kind = helpers.detect_base_kind(self, Registry)
        self.ready = False

    def setup(self, **kwargs) -> None:
        return None

    def teardown(self, **kwargs) -> None:
        return None

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

    def safe_get(self, identifier: str) -> TMetadata | None:
        """Retrieve metadata or return None if not found."""
        try:
            return self.get(identifier)
        except NotFoundError:
            return None
