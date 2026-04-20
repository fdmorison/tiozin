from tiozin.api import SecretRegistry
from tiozin.api.metadata.secret.model import Secret


class NoOpSecretRegistry(SecretRegistry):
    """
    No-op secret registry.

    Does nothing. Useful for testing or when secret management is disabled.
    """

    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location or self.tiozin_uri, **options)

    def get(self, identifier: str) -> Secret:
        return Secret("secret123")

    def register(self, identifier: str, value: Secret) -> None:
        return None
