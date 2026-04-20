from abc import abstractmethod

from tiozin.compose import tioproxy

from ..registry import Registry
from .model import Secret
from .proxy import SecretRegistryProxy


@tioproxy(SecretRegistryProxy)
class SecretRegistry(Registry[Secret]):
    """
    Manages secrets and credentials.

    Storage-agnostic contract for secret backends (like HashiCorp Vault or AWS Secrets Manager).
    Available in Context for secure credential handling in Transforms, Inputs, and Outputs.
    """

    @abstractmethod
    def get(self, identifier: str) -> Secret:
        """
        Retrieve a secret by identifier.

        Raises:
            NotFoundException: When not found and `failfast=True`.
        """

    @abstractmethod
    def register(self, identifier: str, value: Secret) -> None:
        """Register a secret in the registry."""
