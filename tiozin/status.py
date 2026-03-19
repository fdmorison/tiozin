from enum import StrEnum, auto
from typing import ClassVar, Self


class AppStatus(StrEnum):
    """
    Represents the lifecycle states of a Tiozin application.

    Tracks application lifecycle only, not job execution state.
    Job execution is independent and not reflected here.
    """

    CREATED = auto()
    BOOTING = auto()
    READY = auto()
    SHUTDOWN = auto()

    __transitions__: ClassVar[dict[Self, set[Self]]] = {
        CREATED: {CREATED, BOOTING, SHUTDOWN},
        BOOTING: {BOOTING, READY, SHUTDOWN},
        READY: {READY, SHUTDOWN},
        SHUTDOWN: {SHUTDOWN},
    }

    def can_transition_to(self, target: Self) -> bool:
        """Checks if the transition to the target state is valid."""
        return target in self.__transitions__[self]

    def transition_to(self, target: Self, failfast: bool = True) -> Self:
        """
        Performs a safe transition to target state.

        Args:
            target: The desired target state
            failfast: If True, raises exception on invalid transitions

        Returns:
            Target state if allowed, otherwise current state (when failfast=False)

        Raises:
            ValueError: If transition is invalid (when failfast=True)
        """
        if not self.can_transition_to(target):
            if failfast:
                valid_transitions = ", ".join(self.__transitions__[self])
                raise ValueError(
                    f"Invalid transition: {self} -> {target}. "
                    f"Expected: {valid_transitions or 'none'}"
                )
            return self
        return target

    def set_booting(self, failfast: bool = True) -> Self:
        return self.transition_to(self.BOOTING, failfast)

    def set_ready(self, failfast: bool = True) -> Self:
        return self.transition_to(self.READY, failfast)

    def set_shutdown(self, failfast: bool = True) -> Self:
        return self.transition_to(self.SHUTDOWN, failfast)

    def is_created(self) -> bool:
        return self is self.CREATED

    def is_booting(self) -> bool:
        return self is self.BOOTING

    def is_ready(self) -> bool:
        return self is self.READY

    def is_shutdown(self) -> bool:
        return self is self.SHUTDOWN
