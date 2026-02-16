# isort: skip_file
# flake8: noqa
from __future__ import annotations

from typing import TYPE_CHECKING

from .proxies.tioproxy import tioproxy, TioProxyMeta

from .templating.context_builder import TemplateContextBuilder
from .classproperty import classproperty

if TYPE_CHECKING:
    from .assembly.job_builder import JobBuilder as JobBuilder
    from .assembly.plugin_factory import PluginRegistry as PluginRegistry
    from .assembly.plugin_scanner import PluginScanner as PluginScanner
    from .proxies.job import JobProxy as JobProxy
    from .proxies.runner import RunnerProxy as RunnerProxy
    from .proxies.step import StepProxy as StepProxy
    from .templating.overlay import PluginTemplateOverlay as PluginTemplateOverlay
    from .templating.relative_date import RelativeDate as RelativeDate

_DEFERRED = {
    "JobBuilder": ".assembly.job_builder",
    "PluginRegistry": ".assembly.plugin_factory",
    "PluginScanner": ".assembly.plugin_scanner",
    "JobProxy": ".proxies.job",
    "RunnerProxy": ".proxies.runner",
    "StepProxy": ".proxies.step",
    "PluginTemplateOverlay": ".templating.overlay",
    "RelativeDate": ".templating.relative_date",
}


def __getattr__(name: str):
    if name in _DEFERRED:
        from importlib import import_module

        mod = import_module(_DEFERRED[name], __name__)
        val = getattr(mod, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Assembly
    "JobBuilder",
    "PluginRegistry",
    "PluginScanner",
    # Proxy
    "tioproxy",
    "TioProxyMeta",
    "JobProxy",
    "RunnerProxy",
    "StepProxy",
    # Templating
    "PluginTemplateOverlay",
    "TemplateContextBuilder",
    "RelativeDate",
    # Other
    "classproperty",
]
