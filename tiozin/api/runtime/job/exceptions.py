from __future__ import annotations

from tiozin.exceptions.base import TiozinInternalError


class JobRuntimeError(TiozinInternalError):
    """
    Raised when a job fails unexpectedly while running.

    Signals that execution could not be completed. Callers should provide a
    message describing what went wrong.
    """

    message = "An unexpected error occurred while executing the job."
