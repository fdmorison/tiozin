from abc import ABC
import logging


class Resource(ABC):
    """
    Base class for all Tiozin resources.

    Provides common interface for Jobs, Inputs, Transforms, Outputs, and Runners.

    Attributes:
        kind: Resource class name.
        name: Resource name (defaults to class name).
        description: Optional description.
        logger: Logger scoped to resource name.

    Example:
        class MyResource(Resource):
            pass

        resource = MyResource(name="example", description="Demo resource")
        resource.logger.info("Resource initialized")
    """

    def __init__(self, name: str = None, description: str = None) -> None:
        self.kind = type(self).__name__
        self.name = name or self.kind
        self.description = description
        self.logger = logging.getLogger(self.name)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'"{self.name}"'
