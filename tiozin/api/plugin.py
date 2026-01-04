from dataclasses import dataclass
from typing import ClassVar

from tiozin import config
from tiozin.api import Resource


class PlugIn(Resource):
    """
    Mixin for resources that can be discovered and loaded as plugins.

    Provides plugin metadata and discovery capabilities for resources that are
    dynamically loaded by the framework. Used by Jobs, Inputs, Transforms,
    Outputs, Runners, and Registries.
    """

    @dataclass(frozen=True)
    class Metadata:
        name: str
        kind: str
        provider: str
        uri: str
        tio_path: str
        python_path: str

    __tiometa__: ClassVar[Metadata]

    def __init_subclass__(plugin, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        name = plugin.__name__
        kind = plugin._detect_category()
        provider = plugin._detect_provider()
        plugin.__tiometa__ = PlugIn.Metadata(
            name=name,
            kind=kind,
            provider=provider,
            uri=f"tiozin://{provider}/{kind.lower()}/{name}",
            tio_path=f"{provider}:{name}",
            python_path=f"{plugin.__module__}.{plugin.__qualname__}",
        )

    @classmethod
    def _detect_category(plugin) -> str:
        for clazz in reversed(plugin.__mro__):
            if clazz is not PlugIn and issubclass(clazz, PlugIn):
                return clazz.__name__

    @classmethod
    def _detect_provider(plugin) -> str:
        module_path: list[str] = plugin.__module__.split(".")

        for part in module_path:
            if part.startswith(config.plugin_provider_prefix):
                return part

        return config.plugin_provider_unknown

    @property
    def uri(self) -> str:
        class_uri = self.__tiometa__.uri
        if class_uri.endswith(self.name):
            return class_uri
        return f"{class_uri}/{self.name}"
