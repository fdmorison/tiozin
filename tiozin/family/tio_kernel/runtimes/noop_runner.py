from typing import Any, Optional, Unpack

from tiozin.model import Context, Runner
from tiozin.model.typehint import Taxonomy


class NoOpRunner(Runner):
    """
    No-op Tiozin Runner.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(
        self,
        name: str = "noop",
        description: Optional[str] = None,
        streaming: bool = False,
        **kwargs: Unpack[Taxonomy],
    ) -> None:
        super().__init__(name, description, streaming, **kwargs)

    def run(self, context: Context, job: Any) -> None:
        return None
