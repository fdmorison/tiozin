from abc import ABC
import logging


class Registry(ABC):

    def __init__(self):
        self.name = type(self).__name__
        self.ready = False
        self.logger = logging.getLogger(self.name)

    def setup(self) -> None:
        """
        Prepare and initialize the registry.

        This method is called during application startup. Override this method in subclasses to
        define setup logic such as connecting to databases, initializing clients, or registering
        background tasks.
        """

    def shutdown(self) -> None:
        """
        Gracefully shut down the registry.

        This method is called during application shutdown. Override it to release resources, close
        connections, flush data or stop background processes.
        """

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'"{self.name}"'
