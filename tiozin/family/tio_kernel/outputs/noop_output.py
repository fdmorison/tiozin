from typing import Any, Optional, Unpack

from tiozin.model import Context, Output
from tiozin.model.typehint import Taxonomy


class NoOpOutput(Output):
    """
    No-op Tiozin Output.

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

    def write(self, context: Context, data: Any) -> Any:
        return None
