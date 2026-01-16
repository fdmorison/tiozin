from unittest.mock import MagicMock

import pendulum
import pytest

from tiozin.api import JobContext

ISO_2026_01_15T10_30_45Z = "2026-01-15T10:30:45+00:00"


@pytest.fixture
def runner() -> MagicMock:
    return MagicMock()


@pytest.fixture
def job_context(runner: MagicMock) -> JobContext:
    return JobContext(
        id="job-123",
        name="test_job",
        kind="Job",
        plugin_kind="LinearJob",
        options={},
        runner=runner,
        nominal_time=pendulum.parse(ISO_2026_01_15T10_30_45Z),
        org="acme",
        region="latam",
        domain="sales",
        layer="raw",
        product="orders",
        model="daily",
        maintainer="team@acme.com",
        cost_center="CC001",
        owner="john.doe",
        labels={"env": "prod"},
    )


# ============================================================================
# Testing JobContext template_vars - Datetime Components
# ============================================================================
def test_template_vars_should_contain_datetime_components(job_context: JobContext):
    # Assert
    actual = (
        job_context.template_vars["YYYY"],
        job_context.template_vars["MM"],
        job_context.template_vars["DD"],
        job_context.template_vars["HH"],
        job_context.template_vars["mm"],
        job_context.template_vars["ss"],
    )
    expected = ("2026", "01", "15", "10", "30", "45")
    assert actual == expected


# ============================================================================
# Testing JobContext template_vars - Relative Dates (D[n])
# ============================================================================
def test_template_vars_should_contain_relative_dates(job_context: JobContext):
    # Assert
    actual = (
        job_context.template_vars["D"][-1],
        job_context.template_vars["D"][0],
        job_context.template_vars["D"][1],
    )
    expected = ("2026-01-14", "2026-01-15", "2026-01-16")
    assert actual == expected


def test_template_vars_should_contain_full_range_of_relative_dates(job_context: JobContext):
    # Assert
    D = job_context.template_vars["D"]
    actual = (
        -30 in D,
        30 in D,
        len(D),
    )
    expected = (True, True, 62)  # range(-31, 31) = 62 elements
    assert actual == expected


# ============================================================================
# Testing JobContext template_vars - Today/Yesterday/Tomorrow
# ============================================================================
def test_template_vars_should_contain_today_formats(job_context: JobContext):
    # Assert
    actual = (
        job_context.template_vars["today"],
        job_context.template_vars["today_nodash"],
        job_context.template_vars["today_h"],
        job_context.template_vars["today_h_nodash"],
        job_context.template_vars["today_hm"],
        job_context.template_vars["today_hm_nodash"],
        job_context.template_vars["today_hms"],
        job_context.template_vars["today_hms_nodash"],
    )
    expected = (
        "2026-01-15",
        "20260115",
        "2026-01-15T10",
        "2026011510",
        "2026-01-15T10-30",
        "202601151030",
        "2026-01-15T10-30-45",
        "20260115103045",
    )
    assert actual == expected


def test_template_vars_should_contain_yesterday_formats(job_context: JobContext):
    # Assert
    actual = (
        job_context.template_vars["yesterday"],
        job_context.template_vars["yesterday_nodash"],
        job_context.template_vars["yesterday_h"],
        job_context.template_vars["yesterday_hms"],
    )
    expected = (
        "2026-01-14",
        "20260114",
        "2026-01-14T10",
        "2026-01-14T10-30-45",
    )
    assert actual == expected


def test_template_vars_should_contain_tomorrow_formats(job_context: JobContext):
    # Assert
    actual = (
        job_context.template_vars["tomorrow"],
        job_context.template_vars["tomorrow_nodash"],
        job_context.template_vars["tomorrow_h"],
        job_context.template_vars["tomorrow_hms"],
    )
    expected = (
        "2026-01-16",
        "20260116",
        "2026-01-16T10",
        "2026-01-16T10-30-45",
    )
    assert actual == expected


# ============================================================================
# Testing JobContext template_vars - Spark-style Partitions
# ============================================================================
def test_template_vars_should_contain_spark_style_partitions(job_context: JobContext):
    # Assert
    actual = (
        job_context.template_vars["year_month"],
        job_context.template_vars["year_month_day"],
        job_context.template_vars["year_month_day_hour"],
        job_context.template_vars["year_month_day_hour_min"],
    )
    expected = (
        "year=2026/month=01",
        "year=2026/month=01/day=15",
        "year=2026/month=01/day=15/hour=10",
        "year=2026/month=01/day=15/hour=10/min=30",
    )
    assert actual == expected


# ============================================================================
# Testing JobContext template_vars - Airflow Standard
# ============================================================================
def test_template_vars_should_contain_airflow_standard_variables(job_context: JobContext):
    # Assert
    actual = (
        job_context.template_vars["ds"],
        job_context.template_vars["ds_nodash"],
        job_context.template_vars["ts"],
        job_context.template_vars["ts_nodash"],
        job_context.template_vars["prev_ds"],
        job_context.template_vars["next_ds"],
        job_context.template_vars["yesterday_ds"],
        job_context.template_vars["tomorrow_ds"],
    )
    expected = (
        "2026-01-15",
        "20260115",
        "2026-01-15T10:30:45",
        "20260115103045",
        "2026-01-14",
        "2026-01-16",
        "2026-01-14",
        "2026-01-16",
    )
    assert actual == expected


# ============================================================================
# Testing JobContext template_vars - Special Variables
# ============================================================================
def test_template_vars_should_contain_now_as_pendulum_datetime(job_context: JobContext):
    # Assert
    actual = type(job_context.template_vars["now"])
    expected = pendulum.DateTime
    assert actual == expected


def test_template_vars_should_contain_timestamp_as_iso8601(job_context: JobContext):
    # Assert
    actual = job_context.template_vars["timestamp"]
    assert actual.startswith("2026-01-15T10:30:45")
    assert "+00:00" in actual


# ============================================================================
# Testing JobContext template_vars - Context Fields
# ============================================================================
def test_template_vars_should_contain_context_fields(job_context: JobContext):
    # Assert
    actual = (
        job_context.template_vars["id"],
        job_context.template_vars["name"],
        job_context.template_vars["org"],
        job_context.template_vars["domain"],
        job_context.template_vars["product"],
        job_context.template_vars["model"],
    )
    expected = (
        "job-123",
        "test_job",
        "acme",
        "sales",
        "orders",
        "daily",
    )
    assert actual == expected


# ============================================================================
# Testing JobContext template_vars - Immutability
# ============================================================================
def test_template_vars_should_be_immutable(job_context: JobContext):
    # Act/Assert
    with pytest.raises(TypeError):
        job_context.template_vars["new_key"] = "value"
