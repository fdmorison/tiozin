from __future__ import annotations

from typing import TYPE_CHECKING

import wrapt

if TYPE_CHECKING:
    from .model import State
    from .registry import StateRegistry


class StateRegistryProxy(wrapt.ObjectProxy):
    """
    Proxy that enforces state machine transitions before delegating to the
    wrapped registry.

    Registry implementations receive a fully mutated State and are
    responsible only for persistence. Transition validation happens here
    regardless of whether the registry is called through State methods or
    directly.
    """

    def begin(self, state: State) -> State:
        registry: StateRegistry = self.__wrapped__

        if state.status.is_running():
            registry.warning("The state was already in RUNNING state.")

        state.status = state.status.to_running(failfast=registry.failfast)
        return registry.begin(state)

    def commit(self, state: State) -> State:
        registry: StateRegistry = self.__wrapped__

        if state.status.is_succeeded():
            registry.warning("The state was already in SUCCEEDED state.")

        state.status = state.status.to_succeeded(failfast=registry.failfast)
        return registry.commit(state)

    def fail(self, state: State) -> State:
        registry: StateRegistry = self.__wrapped__

        if state.failure_count > registry.retries:
            return self.quarantine(state)

        if state.status.is_failed():
            registry.warning("The state was already in FAILED state.")

        state.status = state.status.to_failed(failfast=registry.failfast)
        return registry.fail(state)

    def cancel(self, state: State) -> State:
        registry: StateRegistry = self.__wrapped__

        if state.status.is_canceled():
            registry.warning("The state was already in CANCELED state.")

        state.status = state.status.to_canceled(failfast=registry.failfast)
        return registry.cancel(state)

    def quarantine(self, state: State) -> State:
        registry: StateRegistry = self.__wrapped__

        if state.status.is_quarantined():
            registry.warning("The state was already in QUARANTINED state.")

        state.status = state.status.to_quarantined(failfast=registry.failfast)
        return registry.quarantine(state)

    def replay(self, state: State) -> State:
        registry: StateRegistry = self.__wrapped__

        if state.status.is_pending():
            registry.warning("The state was already in PENDING state.")

        state.status = state.status.to_pending(failfast=registry.failfast)
        return registry.replay(state)
