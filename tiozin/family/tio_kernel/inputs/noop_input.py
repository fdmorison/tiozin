from typing import Any, Optional, Unpack

from tiozin.model import Context, Input
from tiozin.model.typehint import Taxonomy


class NoOpInput(Input):
    """
    No-op Tiozin Input.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(
        self,
        name: str = "noop",
        description: Optional[str] = None,
        schema: Optional[str] = None,
        schema_subject: Optional[str] = None,
        schema_version: Optional[str] = None,
        **kwargs: Unpack[Taxonomy],
    ) -> None:
        super().__init__(name, description, schema, schema_subject, schema_version, **kwargs)

    def read(self, context: Context) -> Any:
        return None
