from typing import Any

from tiozin.api import Output, StepContext


class NoOpOutput(Output):
    """
    No-op Tiozin Output.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, verbose: bool = False, **options) -> None:
        super().__init__(**options)
        self.verbose = verbose

    def setup(self, context: StepContext, *data: Any) -> None:
        if self.verbose:
            self.info("Setup skipped.")

    def write(self, context: StepContext, data: Any) -> Any:
        if self.verbose:
            self.info("The write was skipped.")
            self.info("Properties:", **self.to_dict())
        return None

    def teardown(self, context: StepContext, *data: Any) -> None:
        if self.verbose:
            self.info("Teardown skipped.")
