from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from tiozin.exceptions import RequiredArgumentError

if TYPE_CHECKING:
    from tiozin.api import SecretRegistry
    from tiozin.api.metadata.secret.model import Secret


class TemplateSecret(Mapping):
    """
    Secret accessor for templating.

    Provides attribute and item access to secrets via the active SecretRegistry.
    Available in templates as ``SECRET``.

    Example:
        ```yaml
        inputs:
        - kind: DatabaseInput
            name: load_it
            url: postgres://user:{{ SECRET.db_password }}@host:5432/dbname

        - kind: JdbcInput
            name: load_jdbc
            url: jdbc:postgresql://host:5432/db?user=app&password={{ SECRET["db_password"] }}
        ```
    """

    def __init__(self, registry: SecretRegistry) -> None:
        RequiredArgumentError.raise_if_missing(
            registry=registry,
        )
        self._registry = registry

    def __getitem__(self, name: str) -> Secret:
        return self._registry.get(name)

    def __iter__(self):
        return iter([])

    def __len__(self) -> int:
        return 0

    def __repr__(self) -> str:
        return "TemplateSecret()"
