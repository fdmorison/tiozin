from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tiozin import config
from tiozin.api import Resource
from tiozin.assembly import ProxyMeta


class PlugIn(Resource, metaclass=ProxyMeta):
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

        for part in module_path:
            if part.startswith(config.plugin_provider_prefix):
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
