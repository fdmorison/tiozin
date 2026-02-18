from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from tiozin.api import Loggable
from tiozin.compose import TioProxyMeta, classproperty
from tiozin.compose.reflection import detect_family, detect_role
from tiozin.utils import slugify

from .runtime.context import Context


class Tiozin(Loggable, metaclass=TioProxyMeta):
    """
    Base class for all Tiozin plugins.

    Provides metadata and discovery capabilities for Tiozin plugins that are
    dynamically loaded by the framework. Used by Jobs, Inputs, Transforms,
    Outputs, Runners, and Registries.
    """

    @dataclass(frozen=True)
    class Metadata:
        name: str
        role: str
        role_class: type[Tiozin]
        family: str
        uri: str
        family_path: str
        python_path: str

    __tiometa__: ClassVar[Metadata]

    def __init__(
        self,
        name: str = None,
        description: str = None,
        **options,
    ) -> None:
        self.kind = self.tiozin_name
        self.name = name or self.kind
        self.slug = slugify(self.name)
        self.description = description
        self.options = options

    def __init_subclass__(tiozin, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        name = tiozin.__name__
        role_class = detect_role(tiozin)
        role = role_class.__name__
        family = detect_family(tiozin)
        tiozin.__tiometa__ = Tiozin.Metadata(
            name=name,
            role=role,
            role_class=role_class,
            family=family,
            uri=f"tiozin://{family}/{role.lower()}/{name}",
            family_path=f"{family}:{name}",
            python_path=f"{tiozin.__module__}.{tiozin.__qualname__}",
        )

    @classproperty
    def tiozin_name(cls) -> str:
        return cls.__tiometa__.name

    @classproperty
    def tiozin_role(cls) -> str:
        return cls.__tiometa__.role

    @classproperty
    def tiozin_role_class(cls) -> type[Tiozin]:
        return cls.__tiometa__.role_class

    @classproperty
    def tiozin_family(cls) -> str:
        return cls.__tiometa__.family

    @classproperty
    def tiozin_family_path(cls) -> str:
        return cls.__tiometa__.family_path

    @classproperty
    def tiozin_python_path(cls) -> str:
        return cls.__tiometa__.python_path

    @classproperty
    def tiozin_uri(cls) -> str:
        return cls.__tiometa__.uri

    @property
    def uri(self) -> str:
        if self.tiozin_uri.endswith(self.name):
            return self.tiozin_uri
        return f"{self.tiozin_uri}/{self.name}"

    @property
    def context(self) -> Context:
        """
        Returns the active execution Context.

        Raises:
            TiozinUnexpectedError if no execution scope is active.
        """
        return Context.current()

    def setup(self, *args, **kwargs) -> None:
        """
        Optional initialization hook.

        Called when the resource enters its execution context.
        Override if the resource requires setup logic such as establishing
        connections, initializing sessions, or allocating resources.
        """
        return None

    def teardown(self, *args, **kwargs) -> None:
        """
        Optional cleanup hook.

        Called when the resource exits its execution context.
        Override if the resource requires cleanup logic such as closing
        connections, releasing resources, or performing final operations.
        """
        return None

    def to_dict(
        self,
        *,
        exclude: set[str] | None = None,
        exclude_none: bool = False,
    ) -> dict[str, Any]:
        """
        Returns a shallow dictionary representation of the resource state.

        Args:
            exclude: Field names to exclude from the output.
            exclude_none: If True, fields with None values are excluded.
        """
        result: dict[str, Any] = {}
        exclude = exclude or set()

        for key, value in vars(self).items():
            if key in exclude:
                continue
            if exclude_none and value is None:
                continue
            result[key] = value

        return result

    def __str__(self) -> str:
        """Returns a simple string representation of the resource."""
        return self.name

    def __repr__(self) -> str:
        """Returns a concise string representation of the resource."""
        return f"{self.name}"
