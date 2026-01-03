from typing import Any

from tiozin.api import Context, Output


class NoOpOutput(Output):
    """
    No-op Tiozin Output.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def write(self, context: Context, data: Any) -> Any:
        return None
