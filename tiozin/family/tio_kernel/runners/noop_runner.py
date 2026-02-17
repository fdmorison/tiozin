from typing import Any

from tiozin.api import Runner


class NoOpRunner(Runner[Any, None, list]):
    """
    No-op Tiozin Runner.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, verbose: bool = True, force_error: bool = False, **options) -> None:
        super().__init__(**options)
        self.verbose = verbose
        self.force_error = force_error

    @property
    def session(self) -> None:
        return None

    def setup(self) -> None:
        if self.verbose:
            self.info("Tiozin is preparing runner")

    def run(self, execution_plan: Any) -> Any:
        if self.verbose:
            args = self.to_dict()
            args.update(args.pop("options"))
            self.info("Tiozin is executing runner plan", **args)

        if self.force_error:
            raise RuntimeError("Forced error for testing purposes")

        return []

    def teardown(self) -> None:
        if self.verbose:
            self.info("Tiozin is finishing runner lifecycle")
