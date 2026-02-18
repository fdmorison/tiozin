from dataclasses import fields
from pathlib import Path
from unittest.mock import ANY

import pendulum
import pytest
from assertpy import assert_that
from freezegun import freeze_time

from tests.stubs import InputStub, JobStub
from tiozin import Context
from tiozin.compose import RelativeDate
from tiozin.exceptions import TiozinUnexpectedError

FAKE_UUID = "01968e6a-0000-7000-8000-000000000001"
FROZEN_TIME = "2026-06-15T12:00:00+00:00"
FROZEN_TIME_OBJ = pendulum.parse(FROZEN_TIME)


# =============================================================================
# Testing Factories
# =============================================================================


@freeze_time(FROZEN_TIME)
def test_for_job_should_create_job_context(
    job_stub: JobStub, fake_domain: dict, fake_governance: dict
):
    # Job
    job = job_stub

    # Act
    context = Context.for_job(job_stub)

    # Assert
    actual = {
        f.name: getattr(context, f.name) for f in fields(context) if not f.name.startswith("_")
    }
    expected = {
        # Root reference
        "job": context,
        # Identity
        "name": job.name,
        "slug": job.slug,
        "kind": job.kind,
        "tiozin_role": job.tiozin_role,
        # Domain / Governance
        **fake_domain,
        **fake_governance,
        # Tiozin arguments
        "options": job.options,
        # Runtime Identity
        "run_id": ANY,
        "run_attempt": 1,
        "nominal_time": FROZEN_TIME_OBJ,
        # Runtime Lifecycle
        "runner": job.runner,
        "setup_at": None,
        "executed_at": None,
        "teardown_at": None,
        "finished_at": None,
        # Infra
        "temp_workdir": Path(f"/tmp/tiozin/{job.slug}/{context.run_id}"),
        "template_vars": ANY,
        "shared": {},
    }
    assert actual == expected


@freeze_time(FROZEN_TIME)
def test_for_step_should_create_step_context(input_stub: InputStub, fake_domain: dict):
    # Arrange
    step = input_stub

    # Act
    context = Context.for_step(input_stub)

    # Assert
    actual = {
        f.name: getattr(context, f.name) for f in fields(context) if not f.name.startswith("_")
    }
    expected = {
        # Root reference
        "job": None,
        # Identity
        "name": step.name,
        "slug": step.slug,
        "kind": step.kind,
        "tiozin_role": step.tiozin_role,
        # Domain / Governance
        **fake_domain,
        # Governance inheritance
        "maintainer": None,
        "cost_center": None,
        "owner": None,
        "labels": {},
        # Tiozin arguments
        "options": step.options,
        # Runtime Identity
        "run_id": ANY,
        "run_attempt": 1,
        "nominal_time": FROZEN_TIME_OBJ,
        # Runtime Lifecycle
        "runner": None,
        "setup_at": None,
        "executed_at": None,
        "teardown_at": None,
        "finished_at": None,
        # Infra
        "temp_workdir": Path(f"/tmp/tiozin/{step.slug}/{context.run_id}"),
        "template_vars": ANY,
        "shared": {},
    }
    assert actual == expected


def test_for_child_step_should_create_step_context_with_job_information(
    job_context: Context, input_stub: InputStub
):
    # Arrange
    step = input_stub

    # Act
    context = job_context.for_child_step(input_stub)

    # Assert
    actual = {
        f.name: getattr(context, f.name) for f in fields(context) if not f.name.startswith("_")
    }
    expected = {
        # Root reference
        "job": job_context,
        # Identity
        "name": step.name,
        "slug": step.slug,
        "kind": step.kind,
        "tiozin_role": step.tiozin_role,
        # Domain / Governance
        "org": job_context.org,
        "region": job_context.region,
        "domain": job_context.domain,
        "layer": job_context.layer,
        "product": job_context.product,
        "model": job_context.model,
        # Governance inheritance
        "maintainer": job_context.maintainer,
        "cost_center": job_context.cost_center,
        "owner": job_context.owner,
        "labels": job_context.labels,
        # Tiozin arguments
        "options": step.options,
        # Runtime Identity
        "run_id": f"{job_context.run_id}_{step.name}",
        "run_attempt": 1,
        "nominal_time": job_context.nominal_time,
        # Runtime Lifecycle
        "runner": job_context.runner,
        "setup_at": None,
        "executed_at": None,
        "teardown_at": None,
        "finished_at": None,
        # Infra
        "temp_workdir": Path(f"/tmp/tiozin/{job_context.slug}/{job_context.run_id}/{step.slug}"),
        "template_vars": ANY,
        "shared": job_context.shared,
    }
    assert actual == expected


# =============================================================================
# Testing Context - Lifecycle Delays
# =============================================================================


def test_context_should_calculate_lifecycle_delays(job_context: Context):
    # Arrange
    job_context.setup_at = pendulum.parse("2026-01-15T10:00:00+00:00")
    job_context.executed_at = pendulum.parse("2026-01-15T10:00:02+00:00")
    job_context.teardown_at = pendulum.parse("2026-01-15T10:00:10+00:00")
    job_context.finished_at = pendulum.parse("2026-01-15T10:00:11+00:00")

    # Act
    result = (
        job_context.delay,
        job_context.setup_delay,
        job_context.execution_delay,
        job_context.teardown_delay,
    )

    # Assert
    actual = result
    expected = (
        11.0,
        2.0,
        8.0,
        1.0,
    )
    assert actual == expected


# =============================================================================
# Testing Context._build_template_vars
# =============================================================================


def test_build_template_vars_should_exclude_fields_with_template_false(job_context: Context):
    # Act
    result = job_context._build_template_vars()

    # Assert
    excluded = {
        "runner",
        "shared",
        "template_vars",
        "setup_at",
        "executed_at",
        "teardown_at",
        "finished_at",
    }
    actual = excluded.intersection(result.keys())
    expected = set()
    assert actual == expected


def test_build_template_vars_should_include_relative_date(
    job_context: Context,
):
    # Act
    result = job_context._build_template_vars()

    # Assert
    actual = isinstance(result["DAY"], RelativeDate)
    expected = True
    assert actual == expected


def test_build_template_vars_should_expose_correct_relative_date_values(
    job_context: Context,
):
    # Act
    result = job_context._build_template_vars()

    # Assert
    actual = {
        "ds": result["ds"],
        "iso": result["iso"],
        "YYYY": result["YYYY"],
        "MM": result["MM"],
        "DD": result["DD"],
    }
    expected = {
        "ds": job_context.nominal_time.format("YYYY-MM-DD"),
        "iso": job_context.nominal_time.to_iso8601_string(),
        "YYYY": job_context.nominal_time.format("YYYY"),
        "MM": job_context.nominal_time.format("MM"),
        "DD": job_context.nominal_time.format("DD"),
    }
    assert actual == expected


def test_build_template_vars_should_override_base_with_context_fields(job_context: Context):
    # Arrange
    base = {
        "name": "overridden_name",
        "custom_key": "custom_value",
    }

    # Act
    result = job_context._build_template_vars(base=base)

    # Assert
    actual = (
        result["name"],
        result["custom_key"],
    )
    expected = (
        job_context.name,
        "custom_value",
    )
    assert actual == expected


def test_build_template_vars_should_override_base_with_relative_date(
    job_context: Context,
):
    # Arrange
    base = {
        "ds": "base_value",
        "YYYY": "9999",
    }

    # Act
    result = job_context._build_template_vars(base=base)

    # Assert
    actual = {
        "ds": result["ds"],
        "YYYY": result["YYYY"],
    }

    expected = {
        "ds": job_context.nominal_time.format("YYYY-MM-DD"),
        "YYYY": job_context.nominal_time.format("YYYY"),
    }

    assert actual == expected


def test_build_template_vars_should_return_immutable_result(job_context: Context):
    # Act
    result = job_context._build_template_vars()

    # Assert
    with pytest.raises(TypeError):
        result["new_key"] = "value"


# =============================================================================
# Testing Context._build_template_vars - ENV Namespace
# =============================================================================


def test_build_template_vars_should_include_env_from_os(
    monkeypatch: pytest.MonkeyPatch,
    job_context: Context,
):
    # Arrange
    monkeypatch.setenv("TIOZIN_BUILD_TEST", "hello")

    # Act
    result = job_context._build_template_vars()

    # Assert
    actual = result["ENV"]["TIOZIN_BUILD_TEST"]
    expected = "hello"
    assert actual == expected


def test_build_template_vars_should_isolate_env_from_context_fields(
    monkeypatch: pytest.MonkeyPatch,
    job_context: Context,
):
    # Arrange
    monkeypatch.setenv("name", "from_os")

    # Act
    result = job_context._build_template_vars()

    # Assert
    actual = (
        result["name"],
        result["ENV"]["name"],
    )
    expected = (
        job_context.name,
        "from_os",
    )
    assert actual == expected


def test_build_template_vars_should_merge_base_env_with_os_env(
    monkeypatch: pytest.MonkeyPatch,
    job_context: Context,
):
    # Arrange
    monkeypatch.setenv("OS_VAR", "from_os")
    base = {"ENV": {"USER_VAR": "from_user"}}

    # Act
    result = job_context._build_template_vars(base=base)

    # Assert
    actual = result["ENV"]
    expected = {
        "OS_VAR": "from_os",
        "USER_VAR": "from_user",
    }
    assert_that(expected).is_subset_of(actual)


def test_build_template_vars_should_give_precedence_to_os_env_over_base_env(
    monkeypatch: pytest.MonkeyPatch,
    job_context: Context,
):
    # Arrange
    monkeypatch.setenv("SHARED_KEY", "from_os")
    base = {"ENV": {"SHARED_KEY": "from_base"}}

    # Act
    result = job_context._build_template_vars(base=base)

    # Assert
    actual = result["ENV"]["SHARED_KEY"]
    expected = "from_os"
    assert actual == expected


def test_build_template_vars_should_raise_if_env_is_not_a_mapping(job_context: Context):
    # Arrange
    base = {"ENV": "not-a-mapping"}

    # Act & Assert
    with pytest.raises(TiozinUnexpectedError, match="ENV must be a mapping"):
        job_context._build_template_vars(base=base)
