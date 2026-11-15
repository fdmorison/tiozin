from contextlib import suppress

from .noop_registry import NoOpBatchRegistry

__all__ = [
    "NoOpBatchRegistry",
]

with suppress(ImportError):
    from .iceberg import IcebergBatchRegistry

    __all__ += ["IcebergBatchRegistry"]
