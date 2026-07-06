from __future__ import annotations

MASK = "***"


class Secret(str):
    """
    A sensitive string value that masks itself in repr.

    Secret is a str subtype, so it is accepted anywhere a plain string is
    expected — Jinja templates, Pydantic models, connection libraries — with
    no explicit conversion. When combined with plain strings via concatenation,
    the result is a new Secret where only the sensitive segments are masked.

    Example:
        >>> s = Secret("mypassword")
        >>> str(s)
        'mypassword'
        >>> repr(s)
        '***'

        >>> url = "jdbc:postgresql://host/db?password=" + s
        >>> str(url)
        'jdbc:postgresql://host/db?password=mypassword'
        >>> repr(url)
        'jdbc:postgresql://host/db?password=***'
    """

    __slots__ = ("_parts",)

    def __new__(cls, value: str) -> Secret:
        obj = super().__new__(cls, value)
        obj._parts = ((value, True),)
        return obj

    @classmethod
    def _from_parts(cls, *parts: tuple[str, bool]) -> Secret:
        obj = super().__new__(cls, "".join(v for v, _ in parts))
        obj._parts = tuple(parts)
        return obj

    def __add__(self, other: object) -> Secret:
        if isinstance(other, Secret):
            return Secret._from_parts(*self._parts, *other._parts)
        return Secret._from_parts(*self._parts, (str(other), False))

    def __radd__(self, other: object) -> Secret:
        if isinstance(other, Secret):
            return Secret._from_parts(*other._parts, *self._parts)
        return Secret._from_parts((str(other), False), *self._parts)

    def __repr__(self) -> str:
        return "".join(MASK if is_secret else text for text, is_secret in self._parts)
