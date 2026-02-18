import os
from collections.abc import Mapping


class SafeEnv(Mapping[str, str]):
    """
    Environment view for templating.

    Wraps ``os.environ`` as a read-only mapping with a safe representation,
    preventing environment variables from being exposed in logs, diffs, or
    debug output while remaining fully usable in templates.
    """

    def __init__(self):
        self._env = os.environ

    def __getitem__(self, key: str) -> str:
        return self._env[key]

    def __iter__(self):
        return iter(self._env)

    def __len__(self) -> int:
        return len(self._env)

    def __repr__(self) -> str:
        return "SafeEnv()"
