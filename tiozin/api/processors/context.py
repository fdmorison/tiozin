from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import gettempdir
from typing import Any

from pendulum import DateTime

from tiozin import config
from tiozin.assembly.template_context_builder import TemplateContextBuilder
from tiozin.utils.helpers import generate_id, utcnow

_TEMP_DIR = Path(gettempdir())


@dataclass(kw_only=True)
class Context:
    """
    Base runtime execution context used by all execution scopes in Tiozin.

    Context defines the common execution contract shared by JobContext and
    StepContext. It provides identity, domain metadata, runtime state, and
    timing information required during execution.

    This class represents infrastructure concerns only. It does not model
    business logic, data processing, or orchestration. Specialized contexts
    extend it to add job- or step-specific information.

    In simple terms, Context answers:
    "What is executing, under which identity, and with which runtime state?"

    Context provides:
    - Execution identity (id, name, kind, plugin kind)
    - Domain metadata (org, region, domain, layer, product, model)
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
    # Domain Metadata
    # ------------------
    org: str
    region: str
    domain: str
    layer: str
    product: str
    model: str

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
    temp_workdir: Path = field(default=None, metadata={"template": True})

    def __post_init__(self):
        if self.temp_workdir is None:
            base_dir = _TEMP_DIR / config.app_name / self.name / self.run_id
            base_dir.mkdir(parents=True, exist_ok=True)
            self.temp_workdir = base_dir

        self.template_vars = (
            TemplateContextBuilder().with_variables(self.template_vars).with_context(self).build()
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
