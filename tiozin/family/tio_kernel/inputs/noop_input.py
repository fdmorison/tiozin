from typing import Any

from tiozin.api import Input, StepContext


class NoOpInput(Input):
    """
    No-op Tiozin Input.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, verbose: bool = False, force_error: bool = False, **options) -> None:
        super().__init__(**options)
        self.verbose = verbose
        self.force_error = force_error

    def setup(self, context: StepContext) -> None:
        if self.verbose:
            self.info("Setup skipped.")

    def read(self, context: StepContext) -> Any:
        if self.verbose:
            args = self.to_dict(exclude={"description", "name"})
            args.update(args.pop("options"))
            self.info("The read was skipped.")
            self.info("Properties:", **args)

        if self.force_error:
            raise RuntimeError("Forced error for testing purposes")

        return None

    def teardown(self, context: StepContext) -> None:
        if self.verbose:
            self.info("Teardown skipped.")
