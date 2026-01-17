from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType as FrozenMapping
from typing import TYPE_CHECKING

from pendulum import DateTime

from tiozin.utils.helpers import utcnow

from .context import Context

if TYPE_CHECKING:
    from tiozin import Runner


@dataclass
class JobContext(Context):
    """
    Runtime context representing a single execution of a Job in Tiozin.

    JobContext is created when a job starts and carries all job-level information
    needed during execution. It includes metadata, runtime references, shared
    state, and the logical time used as a reference for data processing.

    This context is passed to the job and propagated to the runner and all steps,
    serving as the main source of job-level information during the run.

    In simple terms, JobContext answers:
    “Which job is running, with which metadata, and for which point in time?”

    JobContext provides:
    - Job identity, ownership, and organizational metadata
    - A reference to the Runner executing the job
    - A shared session for exchanging state between job, runner, and steps
    - Runtime timestamps for logging, metrics, and observability
    - A root scope of template variables used by all steps

    Nominal time:

    The `nominal_time` defines the logical time reference of the job. It represents
    the time slice of the data being processed, not necessarily the wall-clock
    execution time.

    Tiozin does not define schedules or execution frequency. When no external
    scheduler is used, `nominal_time` defaults to the wall-clock time at job start.
    Its meaning (daily, hourly, etc.) is defined by the job logic or an external
    orchestrator.

    All built-in date and time template variables are derived from `nominal_time`,
    ensuring deterministic behavior across retries, backfills, and replays.

    JobContext does not orchestrate execution. It only represents the execution
    environment of a single job run.
    """

    # ------------------
    # Fundamentals
    # -------------------
    org: str
    region: str
    domain: str
    layer: str
    product: str
    model: str

    maintainer: str
    cost_center: str
    owner: str
    labels: dict[str, str]

    # ------------------
    # Runtime
    # ------------------
    runner: Runner = field(metadata={"template": False})
    nominal_time: DateTime = field(default_factory=utcnow)

    def __post_init__(self):
        super().__post_init__()
        today = self.nominal_time
        yesterday = today.subtract(days=1)
        tomorrow = today.add(days=1)
        self.template_vars = FrozenMapping(
            {
                # === User fields ===
                **self.template_vars,
                # === Datetime components ===
                **{
                    format: today.format(format)
                    for format in ["YYYY", "MM", "DD", "HH", "mm", "ss", "Z"]
                },
                # === Relative datetime ===
                "D": {n: today.add(days=n).to_date_string() for n in range(-31, 31)},
                # === Special DateTime object for custom formatting ===
                "now": today,
                # === ISO timestamp (full precision with microseconds + TZ) ===
                "timestamp": today.to_iso8601_string(),  # 2026-01-14T01:59:57.745604+00:00
                # === Dates (Filesystem safe) ===
                "today": today.to_date_string(),  # 2026-01-14
                "today_nodash": today.format("YYYYMMDD"),  # 20260114
                "today_h": today.format("YYYY-MM-DD[T]HH"),  # 2026-01-14T01
                "today_h_nodash": today.format("YYYYMMDDHH"),  # 2026011401
                "today_hm": today.format("YYYY-MM-DD[T]HH-mm"),  # 2026-01-14T01-59
                "today_hm_nodash": today.format("YYYYMMDDHHmm"),  # 202601140159
                "today_hms": today.format("YYYY-MM-DD[T]HH-mm-ss"),  # 2026-01-14T01-59-57
                "today_hms_nodash": today.format("YYYYMMDDHHmmss"),  # 20260114015957
                "yesterday": yesterday.to_date_string(),  # 2026-01-13
                "yesterday_nodash": yesterday.format("YYYYMMDD"),  # 20260113
                "yesterday_h": yesterday.format("YYYY-MM-DD[T]HH"),  # 2026-01-13T01
                "yesterday_h_nodash": yesterday.format("YYYYMMDDHH"),  # 2026011301
                "yesterday_hm": yesterday.format("YYYY-MM-DD[T]HH-mm"),  # 2026-01-13T01-59
                "yesterday_hm_nodash": yesterday.format("YYYYMMDDHHmm"),  # 202601130159
                "yesterday_hms": yesterday.format("YYYY-MM-DD[T]HH-mm-ss"),  # 2026-01-13T01-59-57
                "yesterday_hms_nodash": yesterday.format("YYYYMMDDHHmmss"),  # 20260113015957
                "tomorrow": tomorrow.to_date_string(),  # 2026-01-15
                "tomorrow_nodash": tomorrow.format("YYYYMMDD"),  # 20260115
                "tomorrow_h": tomorrow.format("YYYY-MM-DD[T]HH"),  # 2026-01-15T01
                "tomorrow_h_nodash": tomorrow.format("YYYYMMDDHH"),  # 2026011501
                "tomorrow_hm": tomorrow.format("YYYY-MM-DD[T]HH-mm"),  # 2026-01-15T01-59
                "tomorrow_hm_nodash": tomorrow.format("YYYYMMDDHHmm"),  # 202601150159
                "tomorrow_hms": tomorrow.format("YYYY-MM-DD[T]HH-mm-ss"),  # 2026-01-15T01-59-57
                "tomorrow_hms_nodash": tomorrow.format("YYYYMMDDHHmmss"),  # 20260115015957
                # === Path partitions (Spark-style) ===
                "year_month": today.format("[year]=YYYY/[month]=MM"),
                "year_month_day": today.format("[year]=YYYY/[month]=MM/[day]=DD"),
                "year_month_day_hour": today.format("[year]=YYYY/[month]=MM/[day]=DD/[hour]=HH"),
                "year_month_day_hour_min": today.format(
                    "[year]=YYYY/[month]=MM/[day]=DD/[hour]=HH/[min]=mm"
                ),
                # === Airflow standard ===
                "ds": today.to_date_string(),  # 2026-01-14
                "ds_nodash": today.format("YYYYMMDD"),  # 20260114
                "ts": today.format("YYYY-MM-DD[T]HH:mm:ss"),  # 2026-01-14T01:59:57
                "ts_nodash": today.format("YYYYMMDDHHmmss"),  # 20260114015957
                "ts_nodash_with_tz": today.format("YYYYMMDDHHmmssZ"),  # 20260114015957+0000
                "prev_ds": yesterday.to_date_string(),  # 2026-01-13
                "next_ds": tomorrow.to_date_string(),  # 2026-01-15
                "yesterday_ds": yesterday.to_date_string(),  # 2026-01-13
                "tomorrow_ds": tomorrow.to_date_string(),  # 2026-01-15
            }
        )
