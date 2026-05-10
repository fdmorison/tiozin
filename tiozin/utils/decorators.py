from typing import TypeVar

import wrapt

T = TypeVar("T")


def ensure_setup(cls: type[T]):
    for name, attr in vars(cls).items():
        if callable(attr) and not name.startswith(("_", "setup", "teardown")):

            @wrapt.decorator
            @wrapt.synchronized
            def wrapper(wrapped, instance, args, kwargs) -> T:
                if instance:
                    ready = getattr(instance, "ready", False)
                    ensuring = getattr(instance, "_ensuring_setup", False)

                    if not ready and not ensuring:
                        instance._ensuring_setup = True
                        try:
                            instance.setup()
                            instance.ready = True
                        finally:
                            instance._ensuring_setup = False

                return wrapped(*args, **kwargs)

            setattr(cls, name, wrapper(attr))

    return cls
