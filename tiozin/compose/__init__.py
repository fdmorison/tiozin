# isort: skip_file
# flake8: noqa
from __future__ import annotations

from typing import TYPE_CHECKING

from .proxies.tioproxy import tioproxy, TioProxyMeta
from .templating.env import TemplateEnv as TemplateEnv
from .templating.date import TemplateDate as TemplateDate

from .classproperty import classproperty

if TYPE_CHECKING:
    from .assembly.job_builder import JobBuilder as JobBuilder
    from .assembly.tiozin_registry import TiozinRegistry as TiozinRegistry
    from .assembly.tiozin_scanner import TiozinScanner as TiozinScanner
    from .proxies.job import JobProxy as JobProxy
    from .proxies.registry import RegistryProxy as RegistryProxy
    from .proxies.runner import RunnerProxy as RunnerProxy
    from .proxies.step import StepProxy as StepProxy
    from .templating.overlay import TiozinTemplateOverlay as TiozinTemplateOverlay

_DEFERRED = {
    "JobBuilder": ".assembly.job_builder",
    "TiozinRegistry": ".assembly.tiozin_registry",
    "TiozinScanner": ".assembly.tiozin_scanner",
    "JobProxy": ".proxies.job",
    "RegistryProxy": ".proxies.registry",
    "RunnerProxy": ".proxies.runner",
    "StepProxy": ".proxies.step",
    "TiozinTemplateOverlay": ".templating.overlay",
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
    "TiozinRegistry",
    "TiozinScanner",
    # Proxy
    "tioproxy",
    "TioProxyMeta",
    "JobProxy",
    "RegistryProxy",
    "RunnerProxy",
    "StepProxy",
    # Templating
    "TiozinTemplateOverlay",
    "TemplateDate",
    "TemplateEnv",
    # Other
    "classproperty",
]
