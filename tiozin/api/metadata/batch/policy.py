from typing import Self

from tiozin import config
from tiozin.api.enums import LowerEnum
from tiozin.utils import default


class BatchSourcePolicy(LowerEnum):
    """
    Defines where a job's batches come from.

    NONE jobs run without batches. SELF jobs produce their own batches from
    their cursor. UPSTREAM jobs consume batches produced by an upstream layer.

    Each policy carries how it behaves: whether it produces its own batches,
    whether it consumes a backlog, and whether it runs when the backlog is empty.
    """

    produces_batches: bool
    consumes_backlog: bool
    runs_on_empty_backlog: bool

    #              produces  consumes  runs_on_empty
    NONE = "none", False, False, True
    SELF = "self", True, True, False
    UPSTREAM = "upstream", False, True, False

    def __new__(
        cls,
        value: str,
        produces_batches: bool,
        consumes_backlog: bool,
        runs_on_empty_backlog: bool,
    ) -> Self:
        member = str.__new__(cls, value)
        member._value_ = value
        member.produces_batches = produces_batches
        member.consumes_backlog = consumes_backlog
        member.runs_on_empty_backlog = runs_on_empty_backlog
        return member

    @classmethod
    def default(cls, batch_source: Self = None) -> Self:
        """
        Resolves an optional batch policy, falling back to the configured
        default when absent.
        """
        return cls(default(batch_source, config.default_batch_source))
