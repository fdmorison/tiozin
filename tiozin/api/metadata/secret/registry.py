from tiozin.compose import SecretRegistryProxy, tioproxy

from ...registry import Registry
from .model import Secret


@tioproxy(SecretRegistryProxy)
class SecretRegistry(Registry[Secret]):
    """
    Manages secrets and credentials.

    Storage-agnostic contract for secret backends (like HashiCorp Vault or AWS Secrets Manager).
    Available in Context for secure credential handling in Transforms, Inputs, and Outputs.
    """
