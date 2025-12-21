from abc import ABC, abstractmethod
from typing import Any, Self


class Plugable(ABC):
    """
    Mixin for pluggable components intended to be used with Services and Resources.

    Plugins can be dynamically discovered, loaded, and executed with optional setup and teardown
    phases. The execute() method contains the plugin business logic, while setup() and teardown()
    provide optional extension points for initialization and cleanup.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def setup(self, **kwargs) -> None:
        """Optional initialization hook. Override if needed."""

    def teardown(self, **kwargs) -> None:
        """Optional cleanup hook. Override if needed."""

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Executes the main logic of the plugin. Must be implemented."""

    def __enter__(self) -> Self:
        self.setup()
        return self

    def __exit__(self, clazz, error, trace) -> None:
        self.teardown()
