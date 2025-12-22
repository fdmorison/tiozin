from __future__ import annotations

from abc import ABC
from typing import Any

from tiozin.utils import helpers


class Plugable(ABC):
    """
    Mixin for operators that can be plugged into Tiozin jobs.

    Defines a common execution contract for operators that are dynamically
    discovered and orchestrated by the framework. Intended to be combined
    with Registry and Operator base classes.
    """

    def __init__(self, *args, **options) -> None:
        super().__init__(*args, **options)
        self.plugin_kind = helpers.detect_base_kind(self, Plugable)

    def execute(self, **kwargs) -> Any:
        """
        Executes the core logic of the plugin.

        This method is invoked by the framework's core. Implementations should focus
        solely on the plugin's responsibility and avoid orchestration logic.

        Args:
            **kwargs: Runtime parameters required for execution.

        Returns:
            Any value produced by the execution (e.g. transformed data,
            execution result, or a handle for further processing).
        """
