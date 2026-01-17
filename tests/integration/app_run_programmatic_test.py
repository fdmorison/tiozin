"""
Integration tests for TiozinApp - Programmatic Jobs.

These tests demonstrate how to run jobs programmatically using
the fluent Job.builder API as well as direct job instantiation.

This file focuses on programmatic job definitions and compares
different levels of explicitness when configuring jobs,
including but not limited to the Builder approach:

1. Declarative programmatic jobs (using dictionaries)
2. Typed programmatic jobs (using explicit plugin manifests)
3. Fully programmatic jobs (using concrete runtime objects)
4. Direct job instantiation without the Builder

The programmatic APIs are ideal for:
- programmatic job generation
- SDKs and libraries
- dynamic job creation with IDE support
"""

from unittest.mock import patch

import pytest

from tiozin import Job, TiozinApp
from tiozin.api.metadata.job_manifest import (
    InputManifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)
from tiozin.family.tio_kernel import (
    LinearJob,
    NoOpInput,
    NoOpOutput,
    NoOpRunner,
    NoOpTransform,
)


@pytest.fixture
def app():
    app = TiozinApp()
    yield app
    app.teardown()


# ============================================================================
# Builder – Declarative Programmatic Jobs (Dictionaries)
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_programmatic_job_with_dicts(_atexit, _signal, app: TiozinApp):
    """
    Jobs can be created programmatically using dictionaries.

    This is the most concise way to use the Builder API and works well
    for simple jobs or cases where plugin configuration is generated
    dynamically.
    """
    # Arrange
    job = (
        Job.builder()
        .kind("LinearJob")
        .name("builder_dict_job")
        .org("tiozin")
        .region("latam")
        .domain("sales")
        .product("orders")
        .model("daily_summary")
        .layer("refined")
        .runner({"kind": "NoOpRunner"})
        .inputs(
            {
                "kind": "NoOpInput",
                "name": "read_orders",
            }
        )
        .transforms(
            {
                "kind": "NoOpTransform",
                "name": "aggregate",
            }
        )
        .outputs(
            {
                "kind": "NoOpOutput",
                "name": "write_summary",
            }
        )
        .build()
    )

    # Act
    app.run(job)

    # Assert
    assert app.status.is_success()


# ============================================================================
# Builder – Typed Programmatic Jobs (Explicit Manifests)
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_programmatic_job_with_manifests(_atexit, _signal, app: TiozinApp):
    """
    Jobs can be created programmatically using explicit plugin manifests.

    This approach provides better IDE autocompletion, validation, and
    type safety when configuring runners, inputs, transforms, and outputs.
    """
    # Arrange
    job = (
        Job.builder()
        .kind("LinearJob")
        .name("builder_manifest_job")
        .org("tiozin")
        .region("latam")
        .domain("sales")
        .product("orders")
        .model("daily_summary")
        .layer("refined")
        .runner(
            RunnerManifest(
                kind="NoOpRunner",
            ),
        )
        .inputs(
            InputManifest(
                kind="NoOpInput",
                name="read_orders",
            )
        )
        .transforms(
            TransformManifest(
                kind="NoOpTransform",
                name="aggregate",
            )
        )
        .outputs(
            OutputManifest(
                kind="NoOpOutput",
                name="write_summary",
            )
        )
        .build()
    )

    # Act
    app.run(job)

    # Assert
    assert app.status.is_success()


# ============================================================================
# Builder – Fully Programmatic Jobs (Concrete Runtime Objects)
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_programmatic_job_with_full_definition(_atexit, _signal, app: TiozinApp):
    """
    Demonstrates a fully programmatic Job created using the fluent
    Job.builder API with concrete runtime objects.

    In this example, all pipeline components are instantiated directly
    as real plugin objects, without using dictionaries, manifests, or YAML.

    This represents the most explicit and imperative way of defining
    a job in Tiozin.
    """
    # Arrange
    job = (
        Job.builder()
        .kind("LinearJob")
        .name("maintenance_cleanup_job")
        .description(
            "Periodic maintenance job responsible for cleaning up obsolete data, "
            "validating data sources, and emitting operational reports."
        )
        .owner("data-platform")
        .maintainer("oncall-data-eng")
        .cost_center("cc-analytics-001")
        .labels(
            {
                "job_type": "maintenance",
                "criticality": "low",
                "schedule": "weekly",
            }
        )
        .org("tiozin")
        .region("latam")
        .domain("platform")
        .product("data-platform")
        .model("maintenance")
        .layer("raw")
        .runner(
            NoOpRunner(
                description="Executes the job in maintenance mode with minimal retries.",
                execution_mode="maintenance",
                retry_attempts=1,
                timeout_minutes=30,
            )
        )
        .inputs(
            NoOpInput(
                name="scan_raw_storage",
                description="Scans raw storage to identify obsolete or invalid data.",
                path="/data/raw",
                recursive=True,
            )
        )
        .transforms(
            NoOpTransform(
                name="cleanup_obsolete_files",
                description="Removes obsolete files based on retention policy.",
                dry_run=False,
                retention_days=90,
            ),
            NoOpTransform(
                name="validate_data_integrity",
                description="Performs lightweight validation checks on remaining data.",
                fail_on_error=False,
            ),
        )
        .outputs(
            NoOpOutput(
                name="emit_maintenance_report",
                description="Emits a summary report with maintenance actions and metrics.",
                format="json",
                destination="logs",
            )
        )
        .build()
    )

    # Act
    app.run(job)

    # Assert
    assert app.status.is_success()


# ============================================================================
# Fully Programmatic Jobs (Direct Job Instantiation)
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_programmatically_with_full_definition(_atexit, _signal, app: TiozinApp):
    """
    Demonstrates a fully specified Job created programmatically by declaring
    all components as concrete classes.

    This example represents a maintenance job and shows the most explicit
    and imperative way of defining a job in Tiozin.
    """
    # Arrange
    job = LinearJob(
        kind="LinearJob",
        name="maintenance_cleanup_job",
        description=(
            "Periodic maintenance job responsible for cleaning up obsolete data, "
            "validating data sources, and emitting operational reports."
        ),
        owner="data-platform",
        maintainer="oncall-data-eng",
        cost_center="cc-analytics-001",
        labels={
            "job_type": "maintenance",
            "criticality": "low",
            "schedule": "weekly",
        },
        org="tiozin",
        region="latam",
        domain="platform",
        product="data-platform",
        model="maintenance",
        layer="raw",
        runner=NoOpRunner(
            description="Executes the job in maintenance mode with minimal retries.",
            execution_mode="maintenance",
            retry_attempts=1,
            timeout_minutes=30,
        ),
        inputs=[
            NoOpInput(
                name="scan_raw_storage",
                description="Scans raw storage to identify obsolete or invalid data.",
                path="/data/raw",
                recursive=True,
            )
        ],
        transforms=[
            NoOpTransform(
                name="cleanup_obsolete_files",
                description="Removes obsolete files based on retention policy.",
                dry_run=False,
                retention_days=90,
            ),
            NoOpTransform(
                name="validate_data_integrity",
                description="Performs lightweight validation checks on remaining data.",
                fail_on_error=False,
            ),
        ],
        outputs=[
            NoOpOutput(
                name="emit_maintenance_report",
                description="Emits a summary report with maintenance actions and metrics.",
                format="json",
                destination="logs",
            )
        ],
    )

    # Act
    app.run(job)

    # Assert
    assert app.status.is_success()
