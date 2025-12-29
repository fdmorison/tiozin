from typing import Any

from tiozin.api import Context, Transform


class NoOpTransform(Transform):
    """
    No-op Tiozin Transform.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, **options) -> None:
        super().__init__(**options)

    def transform(self, context: Context, *data: Any) -> Any:
        return None
