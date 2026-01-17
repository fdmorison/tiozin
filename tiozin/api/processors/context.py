from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from pathlib import Path
from tempfile import mkdtemp
from types import MappingProxyType as FrozenMapping
from typing import Any

from pendulum import DateTime

from tiozin import config
from tiozin.utils.helpers import generate_id, utcnow


@dataclass(kw_only=True)
class Context:
    """
    Base runtime execution context used by all execution scopes in Tiozin.

    Context defines the common execution contract shared by JobContext,
    RunnerContext, and StepContext. It provides identity, runtime metadata,
    shared state, and timing information required during execution.

    This class represents infrastructure concerns only. It does not model
    business logic, data processing, or orchestration. Specialized contexts
    extend it to add job-, runner-, or step-specific information.

    In simple terms, Context answers:
    “What is executing, under which identity, and with which runtime state?”

    Context provides:
    - Execution identity (id, name, kind, plugin kind)
    - Plugin options passed to the executing component
    - A shared template variable scope used during execution
    - A shared session dictionary for exchanging state across execution layers
    - Runtime timestamps for lifecycle tracking and observability
    - Helper properties for computing execution durations
    - A temporary directory path (tmp_path) for intermediate files

    Context is created and managed by Tiozin's runtime layer. User code should
    treat it as a read-only view of the execution environment, except for
    explicitly shared session state.
    """

    # ------------------
    # Identity & Fundamentals
    # ------------------
    id: str = field(default_factory=generate_id)
    name: str
    kind: str
    plugin_kind: str
    options: Mapping[str, Any]

    # ------------------
    # Templating
    # ------------------
    template_vars: Mapping[str, Any] = field(default_factory=dict, metadata={"template": False})

    # ------------------
    # Shared state
    # ------------------
    session: Mapping[str, Any] = field(default_factory=dict, metadata={"template": False})

    # ------------------
    # Runtime
    # ------------------
    run_id: str = field(default_factory=generate_id)
    setup_at: DateTime = None
    executed_at: DateTime = None
    teardown_at: DateTime = None
    finished_at: DateTime = None

    # ------------------
    # Temporary storage
    # ------------------
    tempdir: Path = field(default=None, metadata={"template": True})

    def __post_init__(self):
        if self.tempdir is None:
            self.tempdir = Path(
                mkdtemp(prefix=f"{config.app_name}_{self.name}_"),
            )

        self.template_vars = FrozenMapping(
            {
                **self.template_vars,
                **{
                    f.name: getattr(self, f.name)
                    for f in fields(self)
                    if f.metadata.get("template", True)
                },
            }
        )

    # ------------------
    # Timing helpers
    # ------------------
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
