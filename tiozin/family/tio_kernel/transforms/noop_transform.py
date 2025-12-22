from typing import Any

from tiozin.model import Context, Transform


class NoOpTransform(Transform):
    """
    No-op Tiozin Transform.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, name: str = "noop", **options) -> None:
        super().__init__(name, **options)

    def transform(self, context: Context, *data: Any) -> Any:
        return None
