from typing import Any

from tiozin.api import Context, Input


class NoOpInput(Input):
    """
    No-op Tiozin Input.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, **options) -> None:
        super().__init__(**options)

    def read(self, context: Context) -> Any:
        return None
