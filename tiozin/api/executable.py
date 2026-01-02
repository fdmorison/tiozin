from abc import ABC, abstractmethod
from typing import Any

from tiozin.utils.helpers import utcnow


class Executable(ABC):
    """
    Mixin for resources that can be executed.

    Defines the execution contract for processors and runners that perform
    computational work. Registries are Plugable but not Executable.
    """

    def __init__(self, *args, **options) -> None:
        super().__init__(*args, **options)

        self.run_id = None
        self.created_at = utcnow()
        self.executed_at = None
        self.finished_at = None

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Executes the core logic of the resource.

        This method is invoked by the framework's core. Plugin implementations should focus
        solely on the plugin's responsibility and avoid orchestration logic.

        Args:
            **kwargs: Runtime parameters required for execution.

        Returns:
            Any value produced by the execution, like transformed data, execution result, a handle
            for further processing, or just nothing.
        """
