from typing import Any

from tiozin.api import Context, Output


class NoOpOutput(Output):
    """
    No-op Tiozin Output.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, verbose: bool = True, force_error: bool = False, **options) -> None:
        super().__init__(**options)
        self.verbose = verbose
        self.force_error = force_error

    def setup(self, context: Context, *data: Any) -> None:
        if self.verbose:
            self.info("Tiozin is preparing output")

    def write(self, context: Context, data: Any) -> Any:
        if self.verbose:
            args = self.to_dict(exclude="name")
            args.update(args.pop("options"))
            self.info("Tiozin is writing output data", **args)

        if self.force_error:
            raise RuntimeError("Forced error for testing purposes")

        return None

    def teardown(self, context: Context, *data: Any) -> None:
        if self.verbose:
            self.info("Tiozin is finishing output lifecycle")
