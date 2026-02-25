"""
Utilities for runtime behavior that can be used by providers in the public API.

This module exposes helpers that depend on an active execution context and are
intended to support provider implementations (e.g. SQL, Spark, DuckDB, Redshift).
"""

import re
from collections.abc import Sequence
from typing import Any

_TIO_ALIAS = "_tio_alias"
_DATA_TOKEN_PATTERN = re.compile(r"@data(\d*)(?!\w)")


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


def bind_data_tokens(sql: str, inputs: Sequence[str | None]) -> str:
    """
    Resolve ``@data`` tokens in a SQL query to concrete input identifiers.

    This function replaces ``@data`` and ``@dataN`` tokens with the corresponding
    SQL identifiers provided by the runtime, enabling SQL steps to reference
    their input relations without hard-coding upstream step names.

    Resolution rules:
        - ``@data``  or ``@data0`` → first input
        - ``@dataN``               → N-th input (0-based)

    The function enforces a strict runtime contract:
        - At least one input must be provided
        - Every referenced ``@dataN`` must exist
        - Referenced inputs must not be ``None``

    Any violation of this contract results in an immediate error, preventing
    invalid or ambiguous SQL from reaching the execution engine.

    Args:
        sql:
            SQL query that may contain ``@data`` tokens.
        inputs:
            Ordered sequence of SQL identifiers representing the runtime
            inputs. Identifiers are typically table or view names.

    Returns:
        The SQL query with all ``@data`` tokens resolved to concrete identifiers.

    Raises:
        InvalidInputError:
            If no inputs are provided, if a referenced ``@dataN`` index is
            out of range, or if a referenced input is ``None``.
    """
    from tiozin.exceptions import TiozinInputError

    TiozinInputError.raise_if(
        not inputs,
        "@data tokens require at least one input",
    )

    def replace(match: re.Match) -> str:
        index_text = match.group(1)
        index = int(index_text) if index_text else 0

        try:
            value = inputs[index]
        except IndexError:
            raise TiozinInputError(f"@data{index} refers to a missing input") from None

        TiozinInputError.raise_if(
            value is None,
            f"@data{index} refers to a null input",
        )

        return value

    return _DATA_TOKEN_PATTERN.sub(replace, sql)
