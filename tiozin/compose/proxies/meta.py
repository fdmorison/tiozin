from abc import ABCMeta

import wrapt

from tiozin.exceptions import ProxyContractViolationError

from .constants import TIO_PROXY


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
        proxies = [proxy for clazz in cls.__mro__ for proxy in getattr(clazz, TIO_PROXY, [])]

        for proxy_class in reversed(dict.fromkeys(proxies)):
            if not issubclass(proxy_class, wrapt.ObjectProxy):
                raise ProxyContractViolationError(proxy_class, wrapped)
            wrapped = proxy_class(wrapped)

        return wrapped
