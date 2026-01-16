from typing import Any

from tiozin import config
from tiozin.utils import helpers

from .loggable import Loggable


class Resource(Loggable):
    """
    Base class for all Tiozin resources.

    A Resource is a named, identifiable unit in the system. It provides
    logging, lifecycle hooks, and a unique execution identity, serving as
    the foundation for Jobs, Inputs, Transforms, Outputs, Runners,
    and Registries.

    Attributes:
        id: Unique identifier for this resource instance.
        kind: The resource's Python type, used for runtime inspection and plugin discovery.
        name: Human-readable name for logging and debugging.
        description: Optional description of the resource's purpose.
        options: Extra provider-specific configuration options.
        uri: Unique resource identifier.
        instance_uri: Unique resource instance identifier.
    """

    def __init__(
        self,
        name: str = None,
        description: str = None,
        **options,
    ) -> None:
        self.id = helpers.generate_id()
        self.kind = type(self).__name__
        self.name = name or self.kind
        self.description = description
        self.options = options

    @property
    def uri(self) -> str:
        scheme = config.app_name
        authority = config.app_name
        path = f"{self.kind}/{self.name}" if self.kind != self.name else f"{self.kind}"
        return f"{scheme}://{authority}/{path}"

    @property
    def instance_uri(self) -> str:
        return f"{self.uri}/{self.id}"

    def setup(self, *args, **kwargs) -> None:
        """
        Optional initialization hook.

        Called when the resource enters its execution context.
        Override if the resource requires setup logic such as establishing
        connections, initializing sessions, or allocating resources.
        """
        return None

    def teardown(self, *args, **kwargs) -> None:
        """
        Optional cleanup hook.

        Called when the resource exits its execution context.
        Override if the resource requires cleanup logic such as closing
        connections, releasing resources, or performing final operations.
        """
        return None

    def to_dict(self) -> dict[str, Any]:
        """
        Returns a shallow dictionary representation of the resource state.
        """
        return vars(self).copy()

    def __str__(self) -> str:
        """Returns a simple string representation of the resource."""
        return self.name

    def __repr__(self) -> str:
        """Returns a concise string representation of the resource."""
        return f"{self.name}"

    def __hash__(self) -> int:
        """
        Hashes the resource using its unique execution identifier.
        """
        return hash(self.id)

    def __eq__(self, other: Any) -> bool:
        """
        Compares resources by execution identity.
        """
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id
