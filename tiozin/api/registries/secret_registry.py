from ..registry import Registry


class SecretRegistry(Registry[object]):
    """
    Manages secrets and credentials.

    Storage-agnostic contract for secret backends (like HashiCorp Vault or AWS Secrets Manager).
    Available in Context for secure credential handling in Transforms, Inputs, and Outputs.
    """
