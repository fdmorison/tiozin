from __future__ import annotations

from typing import TYPE_CHECKING

import wrapt

from tiozin.exceptions import SecretNotFoundError
from tiozin.logs import register_sensitive

if TYPE_CHECKING:
    from tiozin import Secret, SecretRegistry


class SecretRegistryProxy(wrapt.ObjectProxy):
    """
    Internal proxy that wraps SecretRegistry implementations with core-level secret handling.

    Intercepts `get()` and raises `SecretNotFoundError` when the wrapped
    implementation returns `None`.

    This is an internal implementation detail. Callers rely on `SecretRegistry`
    and should not interact with this proxy directly.
    """

    def get(self, identifier: str) -> Secret:
        registry: SecretRegistry = self.__wrapped__

        try:
            secret = registry.get(identifier)
            if not secret:
                raise SecretNotFoundError(identifier)
        except SecretNotFoundError:
            if registry.failfast:
                raise
            registry.warning(f"Secret `{identifier}` could not be found")
            return None

        register_sensitive(secret)
        return secret
