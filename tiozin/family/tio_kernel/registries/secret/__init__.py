from contextlib import suppress

from .env_registry import EnvSecretRegistry
from .noop_registry import NoOpSecretRegistry

__all__ = [
    "EnvSecretRegistry",
    "NoOpSecretRegistry",
]

with suppress(ImportError):
    from .aws_parameter_store_registry import AwsParameterStoreSecretRegistry

    __all__ += ["AwsParameterStoreSecretRegistry"]

with suppress(ImportError):
    from .google_secret_manager_registry import GoogleSecretManagerRegistry

    __all__ += ["GoogleSecretManagerRegistry"]
