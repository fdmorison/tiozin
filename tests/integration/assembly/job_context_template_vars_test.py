from unittest.mock import MagicMock

import pendulum

from tiozin.api import JobContext


def test_job_context_template_vars_should_include_fields_without_template_false():
    # Arrange
    runner = MagicMock()
    job_context = JobContext(
        id="job-123",
        name="test_job",
        kind="Job",
        plugin_kind="LinearJob",
        options={},
        runner=runner,
        nominal_time=pendulum.parse("2026-01-15T10:30:45+00:00"),
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

    # Assert - fields without metadata or with template=True should be included
    expected = {
        "id",
        "name",
        "kind",
        "plugin_kind",
        "options",
        "run_id",
        "setup_at",
        "executed_at",
        "teardown_at",
        "finished_at",
        "temp_workdir",
        "org",
        "region",
        "domain",
        "layer",
        "product",
        "model",
        "maintainer",
        "cost_center",
        "owner",
        "labels",
        "nominal_time",
    }
    actual = {k for k in expected if k in job_context.template_vars}
    assert actual == expected


def test_job_context_template_vars_should_exclude_fields_with_template_false():
    # Arrange
    runner = MagicMock()
    job_context = JobContext(
        id="job-123",
        name="test_job",
        kind="Job",
        plugin_kind="LinearJob",
        options={},
        runner=runner,
        nominal_time=pendulum.parse("2026-01-15T10:30:45+00:00"),
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

    # Assert - fields with metadata={"template": False} should be excluded
    excluded = {"runner", "template_vars", "session"}
    actual = {k for k in excluded if k in job_context.template_vars}
    expected = set()
    assert actual == expected
