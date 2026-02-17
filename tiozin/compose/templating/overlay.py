from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from tiozin.api import Tiozin
from tiozin.exceptions import InvalidInputError

from .. import reflection
from . import filters

JINJA_ENV = filters.create_jinja_environment()

TEMPLATE_PATTERN = re.compile(r"\{\{[^}]*\}\}")


class TiozinTemplateOverlay:
    """
    Temporarily renders Jinja templates found in string attributes of a Tiozin
    plugin and restores the original values afterwards.

    Any ``{{ ... }}`` placeholders in public attributes are rendered using
    ``context.template_vars``. This includes nested dicts, lists, and child
    Tiozin plugins. When the overlay exits, all attributes are restored to
    their original template strings.

    This makes it possible to use templated configuration values during
    execution without mutating the plugin permanently.

    Example::

        output = MyOutput(path="./data/{{domain}}/{{date}}")

        with TiozinTemplateOverlay(output):
            print(output.path)  # "./data/sales/2024-01-15"

        print(output.path)  # "./data/{{domain}}/{{date}}"

    Not thread-safe.
    """

    def __init__(self, tiozin: Tiozin, template_vars: Mapping[str, Any] = None) -> None:
        self._tiozin = tiozin
        self._template_vars = template_vars or {}
        self._templates: list[tuple] = []
        self._scan_templates(self._tiozin)

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
            case Tiozin() if isinstance(obj, self._tiozin.tiozin_role_class):
                for field, value in vars(obj).items():
                    if not field.startswith("_"):
                        self._scan_templates(value, *parents, field)

    def _render_templates(self) -> None:
        """Render each templated field by resolving placeholders with context values."""
        for *path, field, template in self._templates:
            obj = self._tiozin
            for key in path:
                obj = reflection.get(obj, key)

            try:
                rendered = JINJA_ENV.from_string(template).render(self._template_vars)
                reflection.set_field(obj, field, rendered)
            except Exception as e:
                raise InvalidInputError(f"Cannot render template {template} because {e}") from e

    def _restore_templates(self) -> None:
        """Restore each rendered field back to its original template string."""
        for *path, field, original in self._templates:
            obj = self._tiozin
            for key in path:
                obj = reflection.get(obj, key)
            reflection.set_field(obj, field, original)

    def __enter__(self) -> TiozinTemplateOverlay:
        self._render_templates()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._restore_templates()
