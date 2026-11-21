from __future__ import annotations

from collections.abc import Iterable
from typing import Self

from ..exceptions import SchemaError

PATH_SEPARATOR = "."


class PropertyPath(tuple[str, ...]):
    """
    The path to a nested property, such as "friends.name".

    Accepts a dotted string or a sequence of names. No name can be empty.
    Use a sequence when a name has a dot in it.

    Examples:

        ```python
        PropertyPath("friends.name")
        # ('friends', 'name')

        PropertyPath(["address", "zip.code"])
        # ('address', 'zip.code')

        PropertyPath("friends..name")
        # SchemaError: Invalid property path `friends..name`
        ```
    """

    def __new__(cls, path: str | Iterable[str]) -> Self:
        names = tuple(path.split(PATH_SEPARATOR)) if isinstance(path, str) else tuple(path)

        SchemaError.raise_if(
            not names or not all(names),
            f"Invalid property path `{path}`",
        )

        return super().__new__(cls, names)

    @property
    def parents(self) -> tuple[str, ...]:
        """
        The path without its last name.

        Examples:

            ```python
            PropertyPath("profile.address.city").parents
            # ('profile', 'address')

            PropertyPath("name").parents
            # ()
            ```
        """
        return self[:-1]

    @property
    def name(self) -> str:
        """
        The last name of the path.

        Examples:

            ```python
            PropertyPath("profile.address.city").name
            # 'city'
            ```
        """
        return self[-1]

    def __str__(self) -> str:
        return PATH_SEPARATOR.join(self)
