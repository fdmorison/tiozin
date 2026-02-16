from collections.abc import Callable
from functools import update_wrapper
from typing import Any, Generic, NoReturn, TypeVar

T = TypeVar("T")


class classproperty(Generic[T]):
    """
    Read-only decorator similar to @property, but bound to the class instead of instances.

    Usage::

        class MyClass:
            @classproperty
            def name(cls) -> str:
                return cls.__name__
    """

    def __init__(self, func: Callable[[type], T]) -> None:
        self.fget: Callable[[type], T] = func
        update_wrapper(self, func)

    def __get__(self, obj: Any, objtype: type | None = None) -> T:
        if objtype is None:
            objtype = type(obj)
        return self.fget(objtype)

    def __set__(self, obj: Any, value: Any) -> NoReturn:
        raise AttributeError("classproperty is read-only")
