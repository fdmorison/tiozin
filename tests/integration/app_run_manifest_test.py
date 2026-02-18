"""
Integration tests for TiozinApp – JobManifest-Based Jobs.

These tests demonstrate how to run jobs defined explicitly as
JobManifest objects.

JobManifest-based execution is useful when:
- job definitions come from external systems (databases, APIs, registries)
- jobs are versioned and transported as structured data
- job metadata must be validated before execution
- execution is decoupled from job construction

This file focuses exclusively on JobManifest usage and does not cover:
- Job.builder
- inline YAML or JSON
- file-based job definitions
- direct job instantiation
"""

from unittest.mock import patch

import pytest

from tiozin import TiozinApp
from tiozin.api.metadata.job_manifest import (
    InputManifest,
    JobManifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)


@pytest.fixture
def app():
    app = TiozinApp()
    yield app
    app.teardown()


# ============================================================================
# JobManifest – Declarative Job (Minimal)
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_from_manifest_with_dicts(_atexit, _signal, app: TiozinApp):
    """
    Jobs can be executed from a JobManifest using plain dictionaries
    for plugin configuration.

    This is the most concise way to construct a JobManifest and is
    suitable when manifests are generated dynamically from external
    sources.
    """
    # Arrange
    manifest = JobManifest(
        kind="LinearJob",
        name="manifest_dict_job",
        org="tiozin",
        region="latam",
        domain="sales",
        subdomain="retail",
        product="orders",
        model="daily_summary",
        layer="refined",
        runner={
            "kind": "NoOpRunner",
        },
        inputs=[
            {
                "kind": "NoOpInput",
                "name": "read_orders",
            }
        ],
        transforms=[
            {
                "kind": "NoOpTransform",
                "name": "aggregate",
            }
        ],
        outputs=[
            {
                "kind": "NoOpOutput",
                "name": "write_summary",
            }
        ],
    )

    # Act
    app.run(manifest)

    # Assert
    assert app.status.is_success()


# ============================================================================
# JobManifest – Typed Tiozin Manifests
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_from_manifest_with_typed_plugins(_atexit, _signal, app: TiozinApp):
    """
    Jobs can be executed from a JobManifest using explicit plugin
    manifest objects.

    This approach provides better type safety, validation, and IDE
    support when constructing manifests programmatically.
    """
    # Arrange
    manifest = JobManifest(
        kind="LinearJob",
        name="manifest_explicit_job",
        org="tiozin",
        region="latam",
        domain="sales",
        subdomain="retail",
        product="orders",
        model="daily_summary",
        layer="refined",
        runner=RunnerManifest(
            kind="NoOpRunner",
        ),
        inputs=[
            InputManifest(
                kind="NoOpInput",
                name="read_orders",
            )
        ],
        transforms=[
            TransformManifest(
                kind="NoOpTransform",
                name="aggregate",
            )
        ],
        outputs=[
            OutputManifest(
                kind="NoOpOutput",
                name="write_summary",
            )
        ],
    )

    # Act
    app.run(manifest)

    # Assert
    assert app.status.is_success()


# ============================================================================
# JobManifest – Full Job Definition
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_from_full_manifest(_atexit, _signal, app: TiozinApp):
    """
    Demonstrates a fully specified Job defined as a JobManifest.

    This example represents a realistic maintenance job and showcases
    the canonical, structured representation of a job as data.
    """
    # Arrange
    manifest = JobManifest(
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
        subdomain="infrastructure",
        product="data-platform",
        model="maintenance",
        layer="raw",
        runner=RunnerManifest(
            kind="NoOpRunner",
            description="Executes the job in maintenance mode with minimal retries.",
            execution_mode="maintenance",
            retry_attempts=1,
            timeout_minutes=30,
        ),
        inputs=[
            InputManifest(
                kind="NoOpInput",
                name="scan_raw_storage",
                description="Scans raw storage to identify obsolete or invalid data.",
                path="/data/raw",
                recursive=True,
            )
        ],
        transforms=[
            TransformManifest(
                kind="NoOpTransform",
                name="cleanup_obsolete_files",
                description="Removes obsolete files based on retention policy.",
                dry_run=False,
                retention_days=90,
            ),
            TransformManifest(
                kind="NoOpTransform",
                name="validate_data_integrity",
                description="Performs lightweight validation checks on remaining data.",
                fail_on_error=False,
            ),
        ],
        outputs=[
            OutputManifest(
                kind="NoOpOutput",
                name="emit_maintenance_report",
                description="Emits a summary report with maintenance actions and metrics.",
                format="json",
                destination="logs",
            )
        ],
    )

    # Act
    app.run(manifest)

    # Assert
    assert app.status.is_success()


# ============================================================================
# JobManifest – Template Variables (temp_workdir)
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_render_temp_workdir_in_manifest_templates(_atexit, _signal, app: TiozinApp):
    """
    Each job component (job, runner, and steps) runs inside its own temporary
    working directory.

    When rendering templates in JobManifest:
    - `{{ temp_workdir }}` resolves to the temporary directory of the current
      component being configured (job, runner, or step).
    - `{{ job.temp_workdir }}` resolves to the job-level temporary directory, which is
      shared across the entire job and is accessible from runners and all steps.

    This allows:
    - runners to define their own workspaces while still accessing job-scoped files
    - steps to exchange files explicitly through the job temp_workdir
    - templates to construct paths without hardcoding filesystem locations

    This test verifies that both `temp_workdir` and `job.temp_workdir` are correctly rendered
    inside JobManifest-based job definitions.
    """
    # Arrange
    manifest = JobManifest(
        kind="LinearJob",
        name="temp_workdir_demo",
        org="tiozin",
        region="latam",
        domain="analytics",
        subdomain="reporting",
        product="reports",
        model="daily",
        layer="refined",
        runner=RunnerManifest(
            kind="NoOpRunner",
            workspace="{{ temp_workdir }}/runner_workspace",
        ),
        inputs=[
            InputManifest(
                kind="NoOpInput",
                name="download_data",
                local_cache="{{ temp_workdir }}/cache",
                output_path="{{ job.temp_workdir }}/downloaded.csv",
            )
        ],
        transforms=[
            TransformManifest(
                kind="NoOpTransform",
                name="process_data",
                scratch_dir="{{ temp_workdir }}/scratch",
                input_path="{{ job.temp_workdir }}/downloaded.csv",
                output_path="{{ job.temp_workdir }}/processed.parquet",
            )
        ],
        outputs=[
            OutputManifest(
                kind="NoOpOutput",
                name="upload_results",
                staging_dir="{{ temp_workdir }}/staging",
                source_path="{{ job.temp_workdir }}/processed.parquet",
            )
        ],
    )

    # Act
    app.run(manifest)

    # Assert
    assert app.status.is_success()
