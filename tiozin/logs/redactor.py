from typing import Any

from tiozin import config

_MASK = "***"


class SecretRedactor:
    """
    Structlog processor that redacts known secrets from log messages.

    Secrets shorter than ``config.log_redact_min_length`` are ignored to
    reduce false positives. Very short values (e.g. "", "a") commonly appear
    in unrelated log fields and would lead to excessive and incorrect masking.

    In general, secrets should have sufficient length and entropy; short
    strings are both less secure and more likely to collide with regular data.
    """

    def __init__(self) -> None:
        self._known_secrets: set[str] = set()
        self._sorted_secrets: list[str] = []

    def add(self, secret: str) -> None:
        """Register a secret."""
        if not secret or len(secret) < config.log_redact_min_length:
            return

        if secret in self._known_secrets:
            return

        self._known_secrets.add(secret)
        self._sorted_secrets = sorted(self._known_secrets, key=len, reverse=True)

    def __call__(self, logger: Any, method: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        if not self._sorted_secrets:
            return event_dict

        for key, value in event_dict.items():
            if isinstance(value, str):
                for secret in self._sorted_secrets:
                    value = value.replace(secret, _MASK)
                event_dict[key] = value

        return event_dict
