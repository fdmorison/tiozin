from abc import ABCMeta
from collections.abc import Callable
from typing import TypeVar

import wrapt

from tiozin.exceptions import PluginProxyError

TIOPROXY = "__tioproxy__"

TClass = TypeVar("TClass", bound=type)


class ProxyMeta(ABCMeta):
    """
    Metaclass that automatically applies proxies on instantiation.

    Classes decorated with @tioproxy will have their proxies applied
    automatically when instantiated, composing the entire proxy chain
    from the inheritance hierarchy.

    Example:
        class Executable(metaclass=ProxyMeta):
            pass

        @tioproxy(TransformProxy)
        class Transform(Executable):
            pass

        @tioproxy(SparkProxy)
        class SparkTransform(Transform):
            pass

        instance = SparkTransform()
        # Result is TransformProxy(SparkProxy(instance::SparkTransform))
    """

    def __call__(cls, *args, **kwargs):
        wrapped = super().__call__(*args, **kwargs)
        proxies: list[type] = [
            proxy for clazz in cls.__mro__ for proxy in getattr(clazz, TIOPROXY, [])
        ]

        for proxy in reversed(dict.fromkeys(proxies)):
            if not issubclass(proxy, wrapt.ObjectProxy):
                raise PluginProxyError(
                    f"Proxy class {proxy.__name__} must inherit from wrapt.ObjectProxy. "
                    f"Found on class {cls.__name__}."
                )
            wrapped = proxy(wrapped)

        return wrapped


def tioproxy(proxy_class: type[wrapt.ObjectProxy]) -> Callable[[TClass], TClass]:
    """
    Registers a proxy class to be automatically applied on instantiation.

    This decorator works with ProxyMeta to enable automatic proxy composition.
    Classes decorated with @tioproxy will have their proxies applied when
    instantiated, with proxies from parent classes applied first (base to derived).

    Args:
        proxy_class: Proxy class (typically inherits from wrapt.ObjectProxy)
                     that will wrap instances automatically.

    Example:
        @tioproxy(CoreProxy)
        @tioproxy(TransformProxy)
        class Transform(Executable):
            pass

        @tioproxy(SparkProxy)
        class SparkTransform(Transform):
            pass

        instance = MyInput()
        # Result is CoreProxy(TransformProxy(SparkProxy(instance::MyInput)))

    Note:
        - The decorator adds a __tioproxy__ attribute to the class
        - Proxies are deduplicated across the inheritance hierarchy
        - Classes must use ProxyMeta as their metaclass (directly or inherited)
    """

    def decorator(wrapped_class: TClass) -> TClass:
        if not issubclass(proxy_class, wrapt.ObjectProxy):
            raise PluginProxyError(
                f"Proxy class {proxy_class.__name__} must inherit from wrapt.ObjectProxy."
            )

        proxies = getattr(wrapped_class, TIOPROXY, [])
        proxies.append(proxy_class)
        setattr(wrapped_class, TIOPROXY, proxies)

        return wrapped_class

    return decorator
