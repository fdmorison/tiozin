"""
Utilities for runtime behavior that can be used by providers in the public API.

This module exposes helpers that depend on an active execution context and are
intended to support provider implementations (e.g. SQL, Spark, DuckDB, Redshift).
"""

import re
from collections.abc import Sequence
from typing import Any

_TIO_ALIAS = "_tio_alias"
_SELF_TOKEN_PATTERN = re.compile(r"@self(\d*)")


def tio_alias(obj: Any, value: str | None = None) -> str:
    """
    Gets or sets the tiozin runtime alias associated with an object.

    This function provides reflective access to runtime metadata attached
    to objects participating in a tiozin execution.

    The alias represents the SQL-visible identity of the object as registered
    by the execution proxy. It does not affect engine-level semantics and is
    intended for internal use only.
    """
    if value is not None:
        setattr(obj, _TIO_ALIAS, value)
        return value

    if not obj:
        return obj

    return getattr(obj, _TIO_ALIAS, None)


def active_session() -> Any:
    """
    Returns the session associated with the currently active runner.

    The active session is managed by the runner execution scope and is propagated via
    context-local state, making it safe to use across threads, async tasks, and nested
    runner executions.

    Raises:
        NotInitializedError: If called outside of an active runner scope.
    """
    from tiozin.compose import RunnerProxy
    from tiozin.exceptions import NotInitializedError

    try:
        return RunnerProxy.active_session.get()
    except LookupError:
        raise NotInitializedError(
            "No active runner session found. "
            "Ensure you are calling this method within a runner execution scope."
        ) from None


def bind_self_tokens(sql: str, inputs: Sequence[str | None]) -> str:
    """
    Resolve ``@self`` tokens in a SQL query to concrete input identifiers.

    This function replaces ``@self`` and ``@selfN`` tokens with the corresponding
    SQL identifiers provided by the runtime, enabling SQL steps to reference
    their input relations without hard-coding upstream step names.

    Resolution rules:
        - ``@self``  or ``@self0`` → first input
        - ``@selfN``               → N-th input (0-based)

    The function enforces a strict runtime contract:
        - At least one input must be provided
        - Every referenced ``@selfN`` must exist
        - Referenced inputs must not be ``None``

    Any violation of this contract results in an immediate error, preventing
    invalid or ambiguous SQL from reaching the execution engine.

    Args:
        sql:
            SQL query that may contain ``@self`` tokens.
        inputs:
            Ordered sequence of SQL identifiers representing the runtime
            inputs. Identifiers are typically table or view names.

    Returns:
        The SQL query with all ``@self`` tokens resolved to concrete identifiers.

    Raises:
        InvalidInputError:
            If no inputs are provided, if a referenced ``@selfN`` index is
            out of range, or if a referenced input is ``None``.
    """
    from tiozin.exceptions import InvalidInputError

    InvalidInputError.raise_if(
        not inputs,
        "@self tokens require at least one input",
    )

    def replace(match: re.Match) -> str:
        index_text = match.group(1)
        index = int(index_text) if index_text else 0

        try:
            value = inputs[index]
        except IndexError:
            raise InvalidInputError(f"@self{index} refers to a missing input") from None

        InvalidInputError.raise_if(
            value is None,
            f"@self{index} refers to a null input",
        )

        return value

    return _SELF_TOKEN_PATTERN.sub(replace, sql)
