from typing import Any

from tiozin.model import Context, Input


class NoOpInput(Input):
    """
    No-op Tiozin Input.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, name: str = "noop", **options) -> None:
        super().__init__(name, **options)

    def read(self, context: Context) -> Any:
        return None
