from abc import ABC, abstractmethod

from ..registry import Registry
from .model import State


class StateRegistry(Registry[State], ABC):
    """
    Registry for tracking pipeline state in a transaction-like way.

    Storage-agnostic contract for state backends (databases, key-value stores, etc.).
    Supports both watermark tracking (single record per taxonomy) and pending-events
    tracking (multiple records per taxonomy partition).

    Available in Context for custom inspection in Transforms, Inputs, and Outputs.
    """

    @abstractmethod
    def register(self, state: State) -> State:
        """
        Persists a new state record, assigning timestamps and generating the id if absent.
        """

    @abstractmethod
    def latest_cursor(self, state: State) -> State | None:
        """
        Returns the state with the highest cursor for the given taxonomy, or None if absent.

        Used in watermark patterns to resume incremental processing from where the last
        successful execution left off.
        """

    @abstractmethod
    def list_pending(self, state: State) -> list[State]:
        """
        Returns all states in pending status for the given taxonomy.

        Used in pending-events patterns by jobs that can process multiple pending
        cursors in a single execution.
        """

    @abstractmethod
    def begin(self, state: State, attributes: dict = None) -> State:
        """
        Transitions the state to in-progress, indicating processing has begun.
        """

    @abstractmethod
    def commit(self, state: State, attributes: dict = None) -> State:
        """
        Marks the state as successfully completed.
        """

    @abstractmethod
    def fail(self, state: State, attributes: dict = None) -> State:
        """
        Marks the state as failed. Does not guarantee any data rollback.
        """

    @abstractmethod
    def cancel(self, state: State, attributes: dict = None) -> State:
        """
        Marks the state as cancelled, permanently abandoning this cursor.
        """

    @abstractmethod
    def quarantine(self, state: State, attributes: dict = None) -> State:
        """
        Isolates the state after an unrecoverable error, preventing further processing.
        """

    @abstractmethod
    def replay(self, state: State, attributes: dict = None) -> State:
        """
        Resets the state to pending, forcing reprocessing regardless of current status.
        """
