from abc import abstractmethod

from typing_extensions import Unpack

from tiozin import config
from tiozin.compose import tioproxy
from tiozin.utils import default

from ...typehint import ResourceKwargs
from ..registry import Registry
from .model import State
from .proxy import StateRegistryProxy


@tioproxy(StateRegistryProxy)
class StateRegistry(Registry[State]):
    """
    Storage-agnostic registry for pipeline states.

    The registry persists and manages the lifecycle of batches represented by `State` objects.
    Implementations may use REST backends, relational databases, key-value stores, or table
    formats such as Iceberg or DuckLake.

    Besides state transitions, the registry exposes derived views over the collection of states,
    such as watermarks and backlogs.

    Attributes:
        retries:
            Maximum number of times a failed batch is retried before being
            escalated to QUARANTINED.
    """

    def __init__(self, retries: int = None, **options) -> None:
        super().__init__(**options)
        self.retries = default(retries, config.default_state_retries)

    @abstractmethod
    def register(self, state: State) -> State:
        """
        Creates a new state.

        Raises:
            StateAlreadyExistsError: If a state with the same natural key already exists.
        """

    @abstractmethod
    def begin(self, state: State) -> State:
        """Transitions the state to RUNNING and persists it."""

    @abstractmethod
    def commit(self, state: State) -> State:
        """Transitions the state to SUCCEEDED and persists it."""

    @abstractmethod
    def fail(self, state: State) -> State:
        """Transitions the state to FAILED and persists it."""

    @abstractmethod
    def cancel(self, state: State) -> State:
        """Transitions the state to CANCELED and persists it."""

    @abstractmethod
    def quarantine(self, state: State) -> State:
        """Transitions the state to QUARANTINED and persists it."""

    @abstractmethod
    def replay(self, state: State) -> State:
        """Transitions the state to PENDING and persists it."""

    @abstractmethod
    def get_watermark(self, **resource: Unpack[ResourceKwargs]) -> State | None:
        """
        Returns the watermark for the resource.

        The watermark is the state with the highest successfully processed batch_key,
        or `None` if no watermark exists.
        """

    @abstractmethod
    def get_backlog(self, **resource: Unpack[ResourceKwargs]) -> list[State]:
        """
        Returns the backlog for the resource.

        The backlog contains all batches currently awaiting processing.
        """
