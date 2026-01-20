from typing import Any

from tiozin.api import Context, JobContext, Runner


class NoOpRunner(Runner[Any]):
    """
    No-op Tiozin Runner.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, verbose: bool = False, **options) -> None:
        super().__init__(**options)
        self.verbose = verbose

    def setup(self, context: JobContext) -> None:
        if self.verbose:
            self.info("Setup skipped.")

    def run(self, context: Context, execution_plan: Any) -> Any:
        if self.verbose:
            args = self.to_dict(exclude={"description", "name"})
            args.update(args.pop("options"))
            self.info("The run was skipped.")
            self.info("Properties:", **args)
        return []

    def teardown(self, context: JobContext) -> None:
        if self.verbose:
            self.info("Teardown skipped.")
