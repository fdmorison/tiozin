from __future__ import annotations

import os
from collections.abc import Mapping
from contextvars import ContextVar, Token
from dataclasses import dataclass, field, fields
from pathlib import Path
from types import MappingProxyType as FrozenMapping
from typing import TYPE_CHECKING, Any

from pendulum import DateTime

from tiozin.compose import RelativeDate
from tiozin.exceptions import TiozinUnexpectedError
from tiozin.utils import create_local_temp_dir, generate_id, utcnow

if TYPE_CHECKING:
    from tiozin import EtlStep, Job, Runner


_current_context: ContextVar[Context | None] = ContextVar(
    "tiozin_current_context",
    default=None,
)


@dataclass(slots=True, kw_only=True)
class Context:
    # ==================================================
    # Root reference (controlado nas factories)
    # ==================================================
    job: Context = field(init=False, repr=False)

    # ==================================================
    # Identity
    # ==================================================
    name: str
    kind: str
    tiozin_kind: str

    # ==================================================
    # Domain
    # ==================================================
    org: str
    region: str
    domain: str
    layer: str
    product: str
    model: str

    # ==================================================
    # Governance
    # ==================================================
    maintainer: str | None = None
    cost_center: str | None = None
    owner: str | None = None
    labels: dict[str, str] = field(default_factory=dict)

    # ==================================================
    # Tiozin arguments
    # ==================================================
    options: dict[str, Any]

    # ==================================================
    # Runtime Identity
    # ==================================================
    run_id: str = field(init=False)
    run_attempt: int = field(default=1)
    nominal_time: DateTime = field(init=False)

    # ==================================================
    # Runtime Lifecycle
    # ==================================================
    runner: Runner = field(default=None, metadata={"template": False})
    setup_at: DateTime | None = field(default=None, metadata={"template": False})
    executed_at: DateTime | None = field(default=None, metadata={"template": False})
    teardown_at: DateTime | None = field(default=None, metadata={"template": False})
    finished_at: DateTime | None = field(default=None, metadata={"template": False})

    # ==================================================
    # Infra
    # ==================================================
    shared: dict[str, Any] = field(default_factory=dict, metadata={"template": False})
    template_vars: Mapping[str, Any] = field(init=False, metadata={"template": False})
    temp_workdir: Path = field(init=False)

    _tokens: list[Token] = field(
        init=False,
        repr=False,
        default_factory=list,
        metadata={"template": False},
    )

    # ==================================================
    # Active Context Management
    # ==================================================

    def __enter__(self) -> Context:
        """
        Activate this Context as the current execution scope.

        Context is reentrant and supports nested activation. Each
        __enter__ call pushes a new ContextVar token onto an internal
        stack, and __exit__ restores the previous scope accordingly.
        """
        token = _current_context.set(self)
        self._tokens.append(token)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """
        Deactivate the current execution scope and restore the previous one.

        Supports nested scopes by popping the most recent activation token.
        """
        if not self._tokens:
            return
        token = self._tokens.pop()
        _current_context.reset(token)

    @staticmethod
    def current() -> Context:
        ctx = _current_context.get()
        TiozinUnexpectedError.raise_if(
            ctx is None,
            "Tiozin has no active execution context",
        )
        return ctx

    # ==================================================
    # Factories
    # ==================================================

    @classmethod
    def for_job(cls, job: Job) -> Context:
        job_uuid: str = generate_id()

        ctx = cls(
            name=job.name,
            kind=job.tiozin_name,
            tiozin_kind=job.tiozin_kind,
            org=job.org,
            region=job.region,
            domain=job.domain,
            layer=job.layer,
            product=job.product,
            model=job.model,
            maintainer=job.maintainer,
            cost_center=job.cost_center,
            owner=job.owner,
            labels=job.labels,
            options=job.options,
        )
        ctx.job = ctx
        ctx.runner = job.runner
        ctx.run_id = f"job_{job_uuid}"
        ctx.nominal_time = utcnow()
        ctx.temp_workdir = create_local_temp_dir(ctx.name, ctx.run_id)
        ctx.template_vars = ctx._build_template_vars()
        return ctx

    @classmethod
    def for_step(cls, step: EtlStep) -> Context:
        ctx = cls(
            name=step.name,
            kind=step.tiozin_name,
            tiozin_kind=step.tiozin_kind,
            org=step.org,
            region=step.region,
            domain=step.domain,
            layer=step.layer,
            product=step.product,
            model=step.model,
            maintainer=None,
            cost_center=None,
            owner=None,
            labels={},
            options=step.options,
        )
        ctx.job = None
        ctx.runner = None
        ctx.run_id = f"job_{generate_id()}_{step.name}"
        ctx.nominal_time = utcnow()
        ctx.temp_workdir = create_local_temp_dir(ctx.name, ctx.run_id)
        ctx.template_vars = ctx._build_template_vars()
        return ctx

    def for_child_step(self, step: EtlStep) -> Context:
        ctx = Context(
            name=step.name,
            kind=step.tiozin_name,
            tiozin_kind=step.tiozin_kind,
            org=step.org or self.org,
            region=step.region or self.region,
            domain=step.domain or self.domain,
            layer=step.layer or self.layer,
            product=step.product or self.product,
            model=step.model or self.model,
            maintainer=self.maintainer,
            cost_center=self.cost_center,
            owner=self.owner,
            labels=self.labels,
            shared=self.shared,
            options=step.options,
        )
        ctx.job = self.job
        ctx.runner = self.job.runner
        ctx.run_id = f"{self.job.run_id}_{step.name}"
        ctx.nominal_time = self.job.nominal_time
        ctx.temp_workdir = create_local_temp_dir(self.job.temp_workdir, step.name)
        ctx.template_vars = ctx._build_template_vars(base=self.template_vars)
        return ctx

    # ==================================================
    # Template Builder
    # ==================================================

    def _build_template_vars(
        self,
        base: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        result: dict[str, Any] = {}

        # defaults
        if base:
            result |= base

        # context (authoritative)
        context_data = {
            field.name: getattr(self, field.name)
            for field in fields(self)
            if field.metadata.get("template", True)
        }
        result |= context_data

        # ENV namespace
        base_env = result.get("ENV") or {}

        TiozinUnexpectedError.raise_if(
            not isinstance(base_env, Mapping),
            f"ENV must be a mapping, got {base_env!r}",
        )

        result["ENV"] = {
            **base_env,
            **os.environ,
        }

        # RelativeDate fields
        relative_date = RelativeDate(self.nominal_time)
        result |= relative_date.to_dict()
        result["DAY"] = relative_date

        return FrozenMapping(result)

    # ==================================================
    # Metrics
    # ==================================================

    @property
    def delay(self) -> float:
        now = utcnow()
        begin = self.setup_at or now
        end = self.finished_at or now
        return (end - begin).total_seconds()

    @property
    def setup_delay(self) -> float:
        now = utcnow()
        begin = self.setup_at or now
        end = self.executed_at or now
        return (end - begin).total_seconds()

    @property
    def execution_delay(self) -> float:
        now = utcnow()
        begin = self.executed_at or now
        end = self.teardown_at or now
        return (end - begin).total_seconds()

    @property
    def teardown_delay(self) -> float:
        now = utcnow()
        begin = self.teardown_at or now
        end = self.finished_at or now
        return (end - begin).total_seconds()
