from typing import Any

from tiozin.api import StepContext, Transform


class NoOpTransform(Transform):
    """
    No-op Tiozin Transform.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, verbose: bool = False, **options) -> None:
        super().__init__(**options)
        self.verbose = verbose

    def setup(self, context: StepContext, *data: Any) -> None:
        if self.verbose:
            self.info("Setup skipped.")

    def transform(self, context: StepContext, *data: Any) -> Any:
        if self.verbose:
            args = self.to_dict(exclude={"description", "name"})
            args.update(args.pop("options"))
            self.info("The transformation was skipped.")
            self.info("Properties:", **args)
        return None

    def teardown(self, context: StepContext, *data: Any) -> None:
        if self.verbose:
            self.info("Teardown skipped.")
