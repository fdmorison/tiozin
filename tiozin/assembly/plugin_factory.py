from typing import Optional, TypeVar

from tiozin.exceptions import PluginAlreadyExistsError, PluginNotFoundError
from tiozin.model import Input, Output, Plugable, Registry, Resource, Runner, Transform

T = TypeVar("T", bound=Plugable)


class PluginFactory(Resource):
    """
    Internal factory that discovers and manages plugin classes in Tiozin.

    Scans modules within the `tiozin.family` package for classes implementing
    Transforms, Inputs, Outputs, and Runners, and registers them as objects
    for internal use. This allows job manifests to reference plugins without
    having to manage instantiation or discovery.

    The PluginFactory is used internally by Tiozin and is not available in the
    Context for custom manipulation.
    """

    def __init__(self) -> None:
        super().__init__()
        self.registry: dict[str, type[Plugable]] = {}

    def register(self, value: type[Plugable]) -> None:
        if not issubclass(value, Plugable):
            raise TypeError(f"Invalid plugin class '{value}'. Plugins must subclass Plugable.")

        name = value.__name__
        if name in self.registry:
            raise PluginAlreadyExistsError(name)

        self.registry[name] = value

    def get(self, kind: str, plugin_kind: Optional[type[T]] = None, **args) -> T:
        """
        Resolve and instantiate a plugin by kind.

        Parameters:
            kind:
                Plugin identifier used to look up the plugin class.
            plugin_kind:
                Optional plugin role (Input, Output, Transform, Runner, or Registry)
                used to restrict the lookup.
            **args:
                Keyword arguments forwarded to the plugin constructor.

        Raises:
            PluginNotFoundError:
                If the plugin does not exist or does not match the requested role.

        Returns:
            A new instance of the resolved plugin.
        """
        plugin = self.registry.get(kind)

        if not plugin:
            raise PluginNotFoundError(kind)

        if plugin_kind and not issubclass(plugin, plugin_kind):
            raise PluginNotFoundError(kind)

        return plugin(**args)

    def get_input(self, kind: str, **args) -> Input:
        return self.get(kind, Input, **args)

    def get_output(self, kind: str, **args) -> Output:
        return self.get(kind, Output, **args)

    def get_transform(self, kind: str, **args) -> Transform:
        return self.get(kind, Transform, **args)

    def get_runner(self, kind: str, **args) -> Runner:
        return self.get(kind, Runner, **args)

    def get_registry(self, kind: str, **args) -> Registry:
        return self.get(kind, Registry, **args)
