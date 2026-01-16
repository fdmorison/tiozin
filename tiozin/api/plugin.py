from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from tiozin import config
from tiozin.api import Loggable
from tiozin.assembly import ProxyMeta


class PlugIn(Loggable, metaclass=ProxyMeta):
    """
    Base class for resources that can be discovered and loaded as plugins.

    Provides plugin metadata and discovery capabilities for resources that are
    dynamically loaded by the framework. Used by Jobs, Inputs, Transforms,
    Outputs, Runners, and Registries.
    """

    @dataclass(frozen=True)
    class Metadata:
        name: str
        kind: str
        kind_class: type[PlugIn]
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
        self.kind = self.plugin_name
        self.name = name or self.kind
        self.description = description
        self.options = options

    def __init_subclass__(plugin, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        name = plugin.__name__
        kind_class = plugin._detect_category()
        kind = kind_class.__name__
        provider = plugin._detect_provider()
        plugin.__tiometa__ = PlugIn.Metadata(
            name=name,
            kind=kind,
            kind_class=kind_class,
            provider=provider,
            uri=f"tiozin://{provider}/{kind.lower()}/{name}",
            tio_path=f"{provider}:{name}",
            python_path=f"{plugin.__module__}.{plugin.__qualname__}",
        )

    @classmethod
    def _detect_category(plugin) -> type:
        for clazz in reversed(plugin.__mro__):
            if clazz is not PlugIn and issubclass(clazz, PlugIn):
                return clazz

    @classmethod
    def _detect_provider(plugin) -> str:
        module_path: list[str] = plugin.__module__.split(".")
        prefixes = tuple(config.plugin_provider_prefixes)

        for part in module_path:
            if part.startswith(prefixes):
                return part

        return config.plugin_provider_unknown

    @property
    def plugin_name(self) -> str:
        return self.__tiometa__.name

    @property
    def plugin_kind(self) -> str:
        return self.__tiometa__.kind

    @property
    def plugin_kind_class(self) -> type[PlugIn]:
        return self.__tiometa__.kind_class

    @property
    def plugin_provider(self) -> str:
        return self.__tiometa__.provider

    @property
    def plugin_uri(self) -> str:
        return self.__tiometa__.uri

    @property
    def plugin_tio_path(self) -> str:
        return self.__tiometa__.tio_path

    @property
    def plugin_python_path(self) -> str:
        return self.__tiometa__.python_path

    @property
    def uri(self) -> str:
        if self.plugin_uri.endswith(self.name):
            return self.plugin_uri
        return f"{self.plugin_uri}/{self.name}"

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
