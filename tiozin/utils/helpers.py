import inspect
from typing import Any


def is_package(obj: Any) -> bool:
    return inspect.ismodule(obj) and hasattr(obj, "__path__")


def is_plugin(plugin: Any) -> bool:
    from tiozin.api import Plugable, Registry

    return (
        inspect.isclass(plugin)
        and issubclass(plugin, Plugable)
        and plugin is not Plugable
        and Plugable not in plugin.__bases__
        and Registry not in plugin.__bases__
        and not inspect.isabstract(plugin)
    )


def detect_base_kind(instance: Any, interface: type) -> type:
    """
    Returns the class immediately below the given boundary in the MRO.

    Example:
        detect_base_kind(self, Plugable) -> Input
    """
    mro = type(instance).__mro__
    idx = mro.index(interface)
    if idx == 0:
        raise RuntimeError(f"{interface.__name__} cannot be instantiated directly")
    return mro[idx - 1]
