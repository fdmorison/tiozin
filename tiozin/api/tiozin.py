from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from tiozin import config
from tiozin.api import Loggable
from tiozin.compose import TioProxyMeta, classproperty


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
        kind: str
        kind_class: type[Tiozin]
        provider: str
        uri: str
        tio_path: str
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
        self.description = description
        self.options = options

    def __init_subclass__(tiozin, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        name = tiozin.__name__
        kind_class = tiozin._detect_category()
        kind = kind_class.__name__
        provider = tiozin._detect_provider()
        tiozin.__tiometa__ = Tiozin.Metadata(
            name=name,
            kind=kind,
            kind_class=kind_class,
            provider=provider,
            uri=f"tiozin://{provider}/{kind.lower()}/{name}",
            tio_path=f"{provider}:{name}",
            python_path=f"{tiozin.__module__}.{tiozin.__qualname__}",
        )

    @classmethod
    def _detect_category(tiozin) -> type:
        for clazz in reversed(tiozin.__mro__):
            if clazz is not Tiozin and issubclass(clazz, Tiozin):
                return clazz

    @classmethod
    def _detect_provider(tiozin) -> str:
        module_path: list[str] = tiozin.__module__.split(".")
        prefixes = tuple(config.tiozin_provider_prefixes)

        for part in module_path:
            if part.startswith(prefixes):
                return part

        return config.tiozin_provider_unknown

    @classproperty
    def tiozin_name(cls) -> str:
        return cls.__tiometa__.name

    @classproperty
    def tiozin_kind(cls) -> str:
        return cls.__tiometa__.kind

    @classproperty
    def tiozin_kind_class(cls) -> type[Tiozin]:
        return cls.__tiometa__.kind_class

    @classproperty
    def tiozin_provider(cls) -> str:
        return cls.__tiometa__.provider

    @classproperty
    def tiozin_uri(cls) -> str:
        return cls.__tiometa__.uri

    @classproperty
    def tiozin_tio_path(cls) -> str:
        return cls.__tiometa__.tio_path

    @classproperty
    def tiozin_python_path(cls) -> str:
        return cls.__tiometa__.python_path

    @property
    def uri(self) -> str:
        if self.tiozin_uri.endswith(self.name):
            return self.tiozin_uri
        return f"{self.tiozin_uri}/{self.name}"

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
