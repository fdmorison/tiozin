from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from tiozin.api import PlugIn
from tiozin.exceptions import InvalidInputError
from tiozin.utils import helpers, jinja

if TYPE_CHECKING:
    from tiozin.api import JobContext, RunnerContext, StepContext

JINJA_ENV = jinja.create_jinja_environment()

TEMPLATE_PATTERN = re.compile(r"\{\{[^}]*\}\}")


class PluginTemplateOverlay:
    """
    Context manager that temporarily interpolates string attributes of a plugin.

    During the execution scope, all string attributes of the plugin that contain
    template placeholders are resolved using a runtime context. Once the context
    is exited, the plugin is restored to its original state, allowing the same
    plugin instance to be safely reused across executions.

    Args:
        plugin: Plugin instance whose attributes will be temporarily interpolated.
        context: Runtime values used to resolve template placeholders.

    Example:
        >>> plugin = MyOutput(path="./data/{{domain}}/{{date}}")
        >>> context = {"domain": "sales", "date": "2024-01-15"}
        >>> with PluginTemplateOverlay(plugin, context):
        ...     print(plugin.path)  # "./data/sales/2024-01-15"
        >>> print(plugin.path)  # "./data/{{domain}}/{{date}}" (restored)

    Notes:
        - Only public attributes (not starting with '_') are considered
        - Recursively traverses nested dicts, lists, tuples, and PlugIn instances
        - Immutable sequences (tuples) are not modified, but mutable objects
          within them (dicts, lists) are processed
        - Resolution happens only within the execution scope
        - The original plugin state is always restored on exit
        - Not thread-safe: a plugin instance must not be accessed or modified
          concurrently while an overlay is active
    """

    def __init__(self, plugin: PlugIn, context: JobContext | StepContext | RunnerContext) -> None:
        self._plugin = plugin
        self._context = context.template_vars
        self._templates: list[tuple] = []
        self._scan_templates(self._plugin)

    def _scan_templates(self, obj: Any, *parents) -> None:
        match obj:
            case str() if TEMPLATE_PATTERN.search(obj):
                self._templates.append((*parents, obj))
            case list():
                for index, value in enumerate(obj):
                    self._scan_templates(value, *parents, index)
            case tuple():
                for index, value in enumerate(obj):
                    if isinstance(value, (list, tuple, dict)):
                        self._scan_templates(value, *parents, index)
            case dict():
                for field, value in obj.items():
                    self._scan_templates(value, *parents, field)
            case PlugIn() if isinstance(obj, self._plugin.plugin_kind_class):
                for field, value in vars(obj).items():
                    if not field.startswith("_"):
                        self._scan_templates(value, *parents, field)

    def _render_templates(self) -> None:
        """Render each templated field by resolving placeholders with context values."""
        for *path, field, template in self._templates:
            obj = self._plugin
            for key in path:
                obj = helpers.get(obj, key)

            try:
                rendered = JINJA_ENV.from_string(template).render(self._context)
                helpers.set_field(obj, field, rendered)
            except Exception as e:
                raise InvalidInputError(f"Cannot render template {template} because {e}") from e

    def _restore_templates(self) -> None:
        """Restore each rendered field back to its original template string."""
        for *path, field, original in self._templates:
            obj = self._plugin
            for key in path:
                obj = helpers.get(obj, key)
            helpers.set_field(obj, field, original)

    def __enter__(self) -> PluginTemplateOverlay:
        self._render_templates()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._restore_templates()
