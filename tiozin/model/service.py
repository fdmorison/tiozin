from tiozin.model.component import Component


class Service(Component):
    """
    Base class for infrastructure services.

    Services represent long-lived or supporting system components such as
    applications, registries, and coordinators. They do not carry business
    or Data Mesh metadata and are identified by their class name.
    """

    def __init__(self) -> None:
        super().__init__(name=type(self).__name__)
