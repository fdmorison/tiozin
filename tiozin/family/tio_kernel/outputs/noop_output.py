from typing import Any

from tiozin.model import Context, Output


class NoOpOutput(Output):
    """
    No-op Tiozin Output.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, name: str = "noop", **options) -> None:
        super().__init__(name, **options)

    def write(self, context: Context, data: Any) -> Any:
        return None
