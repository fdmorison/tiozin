from typing import Any


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
