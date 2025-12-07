from abc import ABC
import logging


class Resource(ABC):
    """
    Base class for all resources in Tio, providing common attributes and logging.

    A Resource represents any managed entity in Tio, such as Jobs, Inputs, Transforms,
    Outputs, or Runners. It provides a consistent interface for naming, describing, and
    logging activities related to the resource.

    Attributes:
        kind: The class name of the resource, used to identify the type.
        name: The name of the resource. Defaults to the class name if not provided.
        description: An optional textual description of the resource.
        logger: A logger instance scoped to the resource name.

    Example:
        ```python
        class MyResource(Resource):
            pass

        resource = MyResource(name="example", description="A demo resource")
        print(resource)       # "example"
        print(resource.kind)  # "MyResource"
        resource.logger.info("Resource initialized")
        ```
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
