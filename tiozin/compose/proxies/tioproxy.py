from abc import ABCMeta
from collections.abc import Callable
from typing import Any, TypeVar

import wrapt

from tiozin.exceptions import ProxyError

TIO_PROXY = "__tioproxy__"


TClass = TypeVar("TClass", bound=type)


class TioProxyMeta(ABCMeta):
    """
    Metaclass that applies proxies registered with @tioproxy when a class is instantiated.

    The @tioproxy decorator only registers proxies. This metaclass builds the proxy chain at
    runtime, respecting inheritance order (parent proxies first, child proxies after).
    """

    @property
    def tioproxy(cls) -> list[type[wrapt.ObjectProxy]]:
        return list(getattr(cls, TIO_PROXY, []))

    def __call__(cls, *args, **kwargs) -> Any | wrapt.ObjectProxy:
        wrapped = super().__call__(*args, **kwargs)

        for proxy_class in reversed(cls.tioproxy):
            wrapped = proxy_class(wrapped)

        return wrapped


def tioproxy(*proxy_classes: type[wrapt.ObjectProxy]) -> Callable[[TClass], TClass]:
    """
    Registers the proxies that should wrap instances of a class.

    Subclasses keep the proxies registered in parent classes and may register
    new ones. If the same proxy appears more than once in the hierarchy, only
    the topmost occurrence is kept.

    Proxies are applied in inheritance order. Proxies defined in parent classes
    wrap first, and proxies defined in child classes wrap afterwards. This
    produces a predictable and composable proxy chain.

    A class may only use @tioproxy once. If multiple proxies are needed, pass
    them as arguments in a single decorator call.

    Args:
        *proxy_classes:
            Proxy classes that must inherit from ``wrapt.ObjectProxy``.

    Raises:
        ProxyError:
            If @tioproxy is declared more than once on the same class, or if
            a provided proxy does not inherit from ``wrapt.ObjectProxy``.

    Example::

        @tioproxy(CoreProxy, TransformProxy)
        class Transform(Executable):
            pass

        @tioproxy(SparkProxy)
        class SparkTransform(Transform):
            pass

        instance = SparkTransform()
        # CoreProxy(TransformProxy(SparkProxy(instance)))
    """

    def decorator(wrapped_class: TClass) -> TClass:
        if TIO_PROXY in wrapped_class.__dict__:
            raise ProxyError(
                f"Class `{wrapped_class.__name__}` already has @tioproxy applied. "
                "Use @tioproxy(ProxyA, ProxyB) to register multiple proxies."
            )

        for proxy_class in proxy_classes:
            if not issubclass(proxy_class, wrapt.ObjectProxy):
                raise ProxyError(
                    f"Class `{proxy_class.__name__}` does not inherit from "
                    f"`{wrapt.ObjectProxy.__name__}` and cannot be used as a proxy "
                    f"for `{wrapped_class.__name__}`."
                )

        proxies = list(getattr(wrapped_class, TIO_PROXY, []))
        proxies.extend(proxy_classes)
        unique_proxies = list(dict.fromkeys(proxies))
        setattr(wrapped_class, TIO_PROXY, unique_proxies)

        return wrapped_class

    return decorator
