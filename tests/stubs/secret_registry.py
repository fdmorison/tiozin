from tiozin.api.metadata.secret.exceptions import SecretNotFoundError
from tiozin.api.metadata.secret.model import Secret
from tiozin.api.metadata.secret.registry import SecretRegistry


class SecretRegistryStub(SecretRegistry):
    def __init__(self):
        super().__init__(location="stub://secret")

    def get(self, identifier: str = None, version: str = None) -> Secret:
        return None

    def register(self, identifier: str, value: Secret) -> None:
        pass


class MissingSecretRegistryStub(SecretRegistry):
    def __init__(self):
        super().__init__(location="stub://secret")

    def get(self, identifier: str) -> Secret:
        raise SecretNotFoundError(identifier)

    def register(self, identifier: str, value: Secret) -> None:
        pass


class FailingSecretRegistryStub(SecretRegistry):
    def __init__(self):
        super().__init__(location="stub://secret")

    def get(self, identifier: str) -> Secret:
        raise RuntimeError("secret registry unavailable")

    def register(self, identifier: str, value: Secret) -> None:
        pass
