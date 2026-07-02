from typing import TypeVar

import wrapt

T = TypeVar("T")


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
