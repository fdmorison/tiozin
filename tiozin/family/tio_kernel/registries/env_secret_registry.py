import os

from tiozin.api import SecretRegistry
from tiozin.api.metadata.secret.model import Secret


class EnvSecretRegistry(SecretRegistry):
    """
    Secret registry backed by environment variables.

    Reads secrets from environment variables using the identifier as the
    variable name (case-sensitive). Suitable for local development and
    container-based deployments where secrets are injected as env vars.
    """

    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location or self.tiozin_uri, **options)

    def get(self, identifier: str) -> Secret:
        value = os.environ.get(identifier)
        if value is None:
            return None
        return Secret(value)

    def register(self, identifier: str, value: Secret) -> None:
        os.environ[identifier] = str(value)
