from collections.abc import Callable
from time import perf_counter
from typing import TypeVar

import pendulum
import wrapt

from tiozin import logs
from tiozin.api.loggable import Loggable

T = TypeVar("T")

logger = logs.get_logger("utils")


def log_delay(operation: str, debug: bool = False) -> Callable:
    """
    Decorator that logs how long the decorated callable took.

    Args:
        operation:
            Human-readable name of the operation, used to open the log message.

        debug:
            If True, successful calls are logged as debug instead of info, keeping
            chatty operations out of the default output. Failures are always errors.
    """

    @wrapt.decorator
    def measure(wrapped, instance, args, kwargs):
        target = instance if isinstance(instance, Loggable) else logger
        log = target.debug if debug else target.info
        log(f"▶️  {operation} started")
        begin = perf_counter()
        try:
            result = wrapped(*args, **kwargs)
        except Exception:
            delay = pendulum.duration(seconds=perf_counter() - begin)
            target.error(f"❌ {operation} failed in {delay.in_words()}")
            raise
        else:
            delay = pendulum.duration(seconds=perf_counter() - begin)
            log(f"✅ {operation} completed in {delay.in_words()}")
            return result

    return measure


def ensure_setup(cls: type[T]) -> type[T]:
    """
    Class decorator that lazily runs `setup()` on first use of any public member.

    Wraps every public method and property so that touching the instance — calling a method or
    reading a property — triggers `setup()` once, before the member runs. `setup`/`teardown` and
    private members are left untouched.
    """

    @wrapt.decorator
    @wrapt.synchronized
    def ensure(wrapped, instance, args, kwargs):
        # wrapt binds `instance` for methods, but passes instance=None for property
        # getters/setters, with the real object as args[0]. Recover it either way.
        target = instance if instance is not None else (args[0] if args else None)

        if target is not None:
            ready = getattr(target, "ready", False)
            ensuring = getattr(target, "_ensuring_setup", False)
            if not ready and not ensuring:
                target._ensuring_setup = True
                try:
                    target.setup()
                    target.ready = True
                finally:
                    target._ensuring_setup = False

        return wrapped(*args, **kwargs)

    for name, attr in vars(cls).items():
        if name.startswith("_") or name in ("setup", "teardown"):
            continue
        if isinstance(attr, property):
            fget = ensure(attr.fget) if attr.fget else None
            fset = ensure(attr.fset) if attr.fset else None
            setattr(cls, name, property(fget, fset, attr.fdel, attr.__doc__))
        elif callable(attr):
            setattr(cls, name, ensure(attr))

    return cls
