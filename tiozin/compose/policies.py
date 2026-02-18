import logging
from dataclasses import dataclass
from enum import StrEnum, auto
from importlib.metadata import EntryPoint

import tiozin.family.tio_kernel as tio_kernel
from tiozin import config
from tiozin.exceptions import PolicyViolationError
from tiozin.utils import human_join

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
    message: str | None = None

    def ok(self) -> bool:
        if self.decision is PolicyDecision.DENY:
            raise PolicyViolationError(self.policy, self.message)

        if self.decision is PolicyDecision.SKIP:
            logger.warning(self.message or "Policy skipped execution.")
            return False

        return True


class FamilyNamePolicy:
    prefixes = tuple(config.tiozin_family_prefixes)

    core_names = {
        tio_kernel.__name__.split(".")[-1],
        config.tiozin_family_unknown,
    }

    core_packages = {
        tio_kernel.__name__,
    }

    @classmethod
    def eval(cls, family: EntryPoint) -> PolicyResult:
        name_ok = family.name.startswith(cls.prefixes)
        package_ok = family.value.endswith(f".{family.name}")
        reserved_ok = any(
            [
                family.name not in cls.core_names,
                family.name in cls.core_names and family.value in cls.core_packages,
            ]
        )

        if name_ok and package_ok and reserved_ok:
            return PolicyResult(cls, PolicyDecision.ALLOW)

        return PolicyResult(
            policy=cls,
            decision=PolicyDecision.SKIP,
            message=(
                f"Skipping invalid family '{family.name}'. "
                f"Family names must be prefixed with one of {cls.prefixes} "
                f"and must not use reserved names: {human_join(cls.core_names)}."
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
