from typing import Any

from tiozin.api import Transform


class NoOpTransform(Transform):
    """
    No-op Tiozin Transform.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, verbose: bool = True, force_error: bool = False, **options) -> None:
        super().__init__(**options)
        self.verbose = verbose
        self.force_error = force_error

    def setup(self, *data: Any) -> None:
        if self.verbose:
            self.info("Tiozin is preparing transform")

    def transform(self, *data: Any) -> Any:
        if self.verbose:
            args = self.to_dict(exclude="name")
            args.update(args.pop("options"))
            self.info("Tiozin is transforming data", **args)

        if self.force_error:
            raise RuntimeError("Forced error for testing purposes")

        return None

    def teardown(self, *data: Any) -> None:
        if self.verbose:
            self.info("Tiozin is finishing transform lifecycle")
