from collections.abc import Callable
from typing import TypeVar

import wrapt

from tiozin.exceptions import DuplicateProxyDecoratorError, ProxyContractViolationError

from .constants import TIO_PROXY

TClass = TypeVar("TClass", bound=type)


def tioproxy(*proxy_classes: type[wrapt.ObjectProxy]) -> Callable[[TClass], TClass]:
    """
    Registers proxy classes to be automatically applied on instantiation.

    This decorator works with ProxyMeta to enable automatic proxy composition.
    Classes decorated with @tioproxy will have their proxies applied when
    instantiated, with proxies from parent classes applied first (base to derived).

    Args:
        *proxy_classes: One or more proxy classes (must inherit from wrapt.ObjectProxy)
                        that will wrap instances automatically.

    Example:
        @tioproxy(CoreProxy, TransformProxy)
        class Transform(Executable):
            pass

        @tioproxy(SparkProxy)
        class SparkTransform(Transform):
            pass

        instance = SparkTransform()
        # Result is CoreProxy(TransformProxy(SparkProxy(instance::SparkTransform)))

    Note:
        - The decorator adds a __tioproxy__ attribute to the class
        - Each class may only be decorated with @tioproxy once
        - Proxies are deduplicated across the inheritance hierarchy
        - Classes must use ProxyMeta as their metaclass (directly or inherited)
    """

    def decorator(wrapped_class: TClass) -> TClass:
        if TIO_PROXY in wrapped_class.__dict__:
            raise DuplicateProxyDecoratorError(wrapped_class)

        for proxy_class in proxy_classes:
            if not issubclass(proxy_class, wrapt.ObjectProxy):
                raise ProxyContractViolationError(proxy_class, wrapped_class)

        proxies = list(getattr(wrapped_class, TIO_PROXY, []))
        proxies.extend(proxy_classes)
        setattr(wrapped_class, TIO_PROXY, proxies)

        return wrapped_class

    return decorator
