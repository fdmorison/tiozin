from abc import abstractmethod
from datetime import datetime
from typing import Any

from tiozin.assembly import ProxyMeta
from tiozin.utils.helpers import utcnow


class Executable(metaclass=ProxyMeta):
    """
    Mixin for resources that can be executed.

    Defines the execution contract for data processing components (Jobs, Inputs,
    Transforms, Outputs) and Runners that perform computational work.
    Registries are Plugable but not Executable.

    Uses ProxyMeta to automatically apply proxies registered via @tioproxy
    decorator, enabling automatic instrumentation, logging, and lifecycle
    management for all executable components.
    """

    def __init__(self, *args, **options) -> None:
        super().__init__(*args, **options)

        self.run_id: str = None
        self.created_at: datetime = utcnow()
        self.executed_at: datetime = None
        self.finished_at: datetime = None

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

    @property
    def execution_time(self) -> float:
        """
        Returns the execution duration in seconds.

        Calculated as the difference between executed_at and finished_at.
        If the execution hasn't started or finished yet, uses current time
        as fallback to provide a partial/elapsed time measurement.

        Returns:
            float: Execution time in seconds, or 0.0 if not started.
        """
        now = utcnow()
        begin = self.executed_at or now
        end = self.finished_at or now
        return (end - begin).total_seconds()
