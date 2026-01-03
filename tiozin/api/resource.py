from typing import Any, Self, Unpack

from uuid_utils import uuid7

from tiozin import config, logs

from .typehint import LogKwargs


class Resource:
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
        logger: Pre-configured logger instance scoped to this resource's name.
        uri: Unique resource identifier.
        instance_uri: Unique resource instance identifier".
    """

    def __init__(
        self,
        name: str = None,
        description: str = None,
        **options,
    ) -> None:
        self.id = str(uuid7())
        self.kind = type(self).__name__
        self.name = name or self.kind
        self.description = description
        self.options = options
        self.logger = logs.get_logger(self.name)

    @property
    def uri(self) -> str:
        scheme = config.app_name
        authority = config.app_name
        path = f"{self.kind}/{self.name}" if self.kind != self.name else f"{self.kind}"
        return f"{scheme}://{authority}/{path}"

    @property
    def instance_uri(self) -> str:
        return f"{self.uri}/{self.id}"

    def setup(self) -> None:
        """
        Optional initialization hook.

        Called when the resource enters its execution context.
        Override if the resource requires setup logic such as establishing
        connections, initializing sessions, or allocating resources.
        """
        return None

    def teardown(self) -> None:
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

    def debug(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.error(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.critical(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.critical(msg, *args, **kwargs)

    def __enter__(self) -> Self:
        """
        Enters the resource execution context and triggers setup.
        """
        self.setup()
        return self

    def __exit__(self, clazz, error, trace) -> None:
        """
        Exits the resource execution context and triggers teardown.
        """
        self.teardown()

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
