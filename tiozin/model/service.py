from tiozin.model.component import Component


class Service(Component):
    """
    Base class for infrastructure services.

    Services represent system components like apps and registries.
    Each service instance is uniquely identified by a run_id.

    Attributes:
        kind: Service class name.
        name: Service name (equals kind).
        run_id: Unique execution identifier (UUID7).
        logger: Logger scoped to service name.

    Example:
        class MyService(Service):
            pass

        service = MyService()
        service.logger.info("Service started")
    """

    def __init__(self) -> None:
        super().__init__(name=type(self).__name__)
