from typing import Any

from tiozin import Input
from tiozin.utils import isozformat, utcnow


class NoOpInput(Input):
    """
    No-op Tiozin Input.

    Does nothing. Returns an empty dataset for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, verbose: bool = True, force_error: bool = False, **options) -> None:
        super().__init__(**options)
        self.verbose = verbose
        self.force_error = force_error

    def setup(self) -> None:
        if self.verbose:
            self.info("Tiozin is preparing input")

    def read(self) -> Any:
        if self.verbose:
            args = self.to_dict(exclude="name")
            args.update(args.pop("options"))
            self.info("Tiozin is reading data", **args)

        if self.force_error:
            raise RuntimeError("Forced error for testing purposes")

        mark1 = self.context.get_job_managed_bookmark("noop_mark")
        mark2 = self.context.set_job_managed_bookmark("noop_mark", utcnow())
        self.info(f"🔖 Bookmark advanced from `{isozformat(mark1)}` to `{isozformat(mark2)}`")
        return []

    def teardown(self) -> None:
        if self.verbose:
            self.info("Tiozin is finishing input lifecycle")
