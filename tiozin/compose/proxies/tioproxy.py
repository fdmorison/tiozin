from collections.abc import Callable
from typing import TypeVar

import wrapt

from tiozin.exceptions import ProxyContractViolationError

from .constants import TIO_PROXY

TClass = TypeVar("TClass", bound=type)


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
            raise ProxyContractViolationError(proxy_class, wrapped_class)

        proxies = list(getattr(wrapped_class, TIO_PROXY, []))
        proxies.append(proxy_class)
        setattr(wrapped_class, TIO_PROXY, proxies)

        return wrapped_class

    return decorator
