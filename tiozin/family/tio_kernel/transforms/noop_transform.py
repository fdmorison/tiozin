from typing import Any, Optional, Unpack

from tiozin.model import Context, Transform
from tiozin.model.typehint import Taxonomy


class NoOpTransform(Transform):
    """
    No-op Tiozin Transform.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(
        self,
        name: str = "noop",
        description: Optional[str] = None,
        **kwargs: Unpack[Taxonomy],
    ) -> None:
        super().__init__(name, description, **kwargs)

    def transform(self, context: Context, *data: Any) -> Any:
        return None
