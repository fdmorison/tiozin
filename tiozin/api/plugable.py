from __future__ import annotations

from dataclasses import dataclass

from tiozin.utils import helpers


@dataclass(frozen=True)
class PluginMetadata:
    kind: str
    tio_kind: str
    python_kind: str
    provider: str


class Plugable:
    """
    Mixin for resources that can be discovered and loaded as plugins.

    Provides plugin metadata and discovery capabilities for resources that are
    dynamically loaded by the framework. Used by Jobs, Inputs, Transforms,
    Outputs, Runners, and Registries.
    """

    __tiometa__: PluginMetadata = None

    def __init__(self, *args, **options) -> None:
        super().__init__(*args, **options)
        self.plugin_kind = helpers.detect_base_kind(self, Plugable)
