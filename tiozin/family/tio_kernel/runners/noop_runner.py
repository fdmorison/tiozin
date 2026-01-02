from typing import Any

from tiozin.api import Context, Runner


class NoOpRunner(Runner[Any]):
    """
    No-op Tiozin Runner.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, **options) -> None:
        super().__init__(**options)

    def run(self, context: Context, execution_plan: Any) -> Any:
        return []
