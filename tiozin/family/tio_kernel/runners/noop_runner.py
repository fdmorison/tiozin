from typing import Any

from tiozin.api import Context, Runner


class NoOpRunner(Runner):
    """
    No-op Tiozin Runner.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, **options) -> None:
        super().__init__(**options)

    def run(self, context: Context, job: Any) -> None:
        return None

    def setup(self, **kwargs) -> None:
        return None

    def teardown(self, **kwargs) -> None:
        return None
