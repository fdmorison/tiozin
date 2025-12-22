from ..registry import Registry


class PluginRegistry(Registry):
    """
    Internal registry that discovers and manages plugin classes in Tiozin.

    Scans modules within the `tiozin.family` package for classes implementing
    Transforms, Inputs, Outputs, and Runners, and registers them as objects
    for internal use. This allows job manifests to reference plugins without
    having to manage instantiation or discovery.

    The PluginRegistry is used internally by Tiozin and is not available in the
    Context for custom manipulation.
    """

    def __init__(self) -> None:
        super().__init__()
