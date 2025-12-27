import logging
import re
from dataclasses import dataclass
from enum import StrEnum, auto
from importlib.metadata import EntryPoint
from typing import Optional

from tiozin.exceptions import PolicyViolationError

logger = logging.getLogger(__name__)


class PolicyDecision(StrEnum):
    ALLOW = auto()
    SKIP = auto()
    DENY = auto()

    def allow(self) -> bool:
        return self is PolicyDecision.ALLOW

    def deny(self) -> bool:
        return self is PolicyDecision.DENY

    def skip(self) -> bool:
        return self is PolicyDecision.SKIP


@dataclass(frozen=True)
class PolicyResult:
    policy: type
    decision: PolicyDecision
    message: Optional[str] = None

    def ok(self) -> bool:
        if self.decision is PolicyDecision.DENY:
            raise PolicyViolationError(self.policy, self.message)

        if self.decision is PolicyDecision.SKIP:
            logger.warning(self.message or "Policy skipped execution.")
            return False

        return True


class ProviderNamePolicy:
    prefix = "tio_"
    pattern = re.compile("^(?:tio_.+|.+\.tio_.+)$")

    @classmethod
    def eval(cls, provider: EntryPoint) -> PolicyResult:
        name_ok = cls.pattern.fullmatch(provider.name)
        package_ok = provider.value.endswith(f".{provider.name}")

        if name_ok and package_ok:
            return PolicyResult(cls, PolicyDecision.ALLOW)

        expected_name = cls.prefix + provider.name.removeprefix(cls.prefix)
        return PolicyResult(
            policy=cls,
            decision=PolicyDecision.SKIP,
            message=(
                "Skipping provider that does not match Tiozin's naming convention. "
                f"The provider '{provider.name}' should be prefixed with `tio_` and the "
                f"package '{provider.value}' should end with '{expected_name}'."
            ),
        )


class InputNamingPolicy:
    SUFFIXES = ("Input", "Source", "Reader")

    @classmethod
    def eval(cls, name: str) -> PolicyResult:
        if name.endswith(cls.SUFFIXES):
            return PolicyResult(cls, PolicyDecision.ALLOW)

        return PolicyResult(
            policy=cls,
            decision=PolicyDecision.SKIP,
            message=(
                f"Skipping input '{name}': input names must end with {', '.join(cls.SUFFIXES)}."
            ),
        )


class OutputNamingPolicy:
    SUFFIXES = ("Output", "Sink", "Writer")

    @classmethod
    def eval(cls, name: str) -> PolicyResult:
        if name.endswith(cls.SUFFIXES):
            return PolicyResult(cls, PolicyDecision.ALLOW)

        return PolicyResult(
            policy=cls,
            decision=PolicyDecision.SKIP,
            message=(
                f"Skipping output '{name}': output names must end with {', '.join(cls.SUFFIXES)}."
            ),
        )


class TransformNamingPolicy:
    SUFFIXES = ("Transform", "Transformer", "Mapper", "Processor")

    @classmethod
    def eval(cls, name: str) -> PolicyResult:
        if name.endswith(cls.SUFFIXES):
            return PolicyResult(cls, PolicyDecision.ALLOW)

        return PolicyResult(
            policy=cls,
            decision=PolicyDecision.SKIP,
            message=(
                f"Skipping transform '{name}': transform names must end with "
                f"{', '.join(cls.SUFFIXES)}."
            ),
        )


class RunnerNamingPolicy:
    SUFFIXES = ("Runner", "Runtime")

    @classmethod
    def eval(cls, name: str) -> PolicyResult:
        if name.endswith(cls.SUFFIXES):
            return PolicyResult(cls, PolicyDecision.ALLOW)

        return PolicyResult(
            policy=cls,
            decision=PolicyDecision.SKIP,
            message=(
                f"Skipping runner '{name}': runner names must end with {', '.join(cls.SUFFIXES)}."
            ),
        )


class RegistryNamingPolicy:
    SUFFIXES = ("Registry",)

    @classmethod
    def eval(cls, name: str) -> PolicyResult:
        if name.endswith(cls.SUFFIXES):
            return PolicyResult(cls, PolicyDecision.ALLOW)

        return PolicyResult(
            policy=cls,
            decision=PolicyDecision.SKIP,
            message=(
                f"Skipping registry '{name}': registry names must end with "
                f"{', '.join(cls.SUFFIXES)}."
            ),
        )
