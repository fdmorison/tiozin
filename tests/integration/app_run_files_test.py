"""
Integration tests for TiozinApp - File-Based Jobs.

These tests demonstrate how to run jobs by loading job definitions
from files on disk.

This file focuses on file-based job execution and compares different
serialization formats supported by TiozinApp:

1. YAML files
2. JSON files

File-based job definitions are ideal for:
- production workloads
- version-controlled job specifications
- code review and change tracking
- separation of job definition from execution code
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from tiozin import TiozinApp


@pytest.fixture
def app():
    app = TiozinApp()
    yield app
    app.teardown()


# ============================================================================
# File-Based Jobs – YAML
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_from_yaml_file(_atexit, _signal, app: TiozinApp, tmp_path: Path):
    """
    Jobs can be loaded from YAML files.

    YAML is the recommended format for production jobs, as it provides
    good readability, supports comments, and integrates well with
    version control workflows.
    """
    # Arrange
    job_file = tmp_path / "simple_job.yaml"
    job_file.write_text(
        """
        kind: LinearJob
        name: file_yaml_job
        org: tiozin
        region: latam
        domain: sales
        product: orders
        model: daily_summary
        layer: refined
        runner:
          kind: NoOpRunner
        inputs:
          - kind: NoOpInput
            name: read_orders
        transforms:
          - kind: NoOpTransform
            name: aggregate
        outputs:
          - kind: NoOpOutput
            name: write_summary
        """
    )

    # Act
    app.run(str(job_file))

    # Assert
    assert app.status.is_success()


# ============================================================================
# File-Based Jobs – JSON
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_from_json_file(_atexit, _signal, app: TiozinApp, tmp_path: Path):
    """
    Jobs can also be loaded from JSON files.

    JSON is useful when job definitions are generated programmatically
    by external systems or APIs that already emit JSON payloads.
    """
    # Arrange
    job_file = tmp_path / "simple_job.json"
    job_file.write_text(
        """
        {
            "kind": "LinearJob",
            "name": "file_json_job",
            "org": "tiozin",
            "region": "latam",
            "domain": "sales",
            "product": "orders",
            "model": "daily_summary",
            "layer": "refined",
            "runner": {
                "kind": "NoOpRunner"
            },
            "inputs": [
                {
                    "kind": "NoOpInput",
                    "name": "read_orders"
                }
            ],
            "transforms": [
                {
                    "kind": "NoOpTransform",
                    "name": "aggregate"
                }
            ],
            "outputs": [
                {
                    "kind": "NoOpOutput",
                    "name": "write_summary"
                }
            ]
        }
        """
    )

    # Act
    app.run(str(job_file))

    # Assert
    assert app.status.is_success()


# ============================================================================
# File-Based Jobs – Full Job Definition (YAML)
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_from_full_yaml_file(_atexit, _signal, app: TiozinApp, tmp_path: Path):
    """
    Demonstrates a fully specified Job loaded from a YAML file.

    This example represents a maintenance job and showcases all supported
    job attributes, including identity, ownership, business taxonomy,
    and pipeline components.

    This is the canonical representation for production-grade jobs.
    """
    # Arrange
    job_file = tmp_path / "maintenance_job.yaml"
    job_file.write_text(
        """
        kind: LinearJob
        name: maintenance_cleanup_job
        description: Periodic maintenance job responsible for cleaning up obsolete data
        owner: data-platform
        maintainer: oncall-data-eng
        cost_center: cc-analytics-001
        labels:
          job_type: maintenance
          criticality: low
          schedule: weekly
        org: tiozin
        region: latam
        domain: platform
        product: data-platform
        model: maintenance
        layer: raw
        runner:
          kind: NoOpRunner
          description: Executes the job in maintenance mode with minimal retries.
          execution_mode: maintenance
          retry_attempts: 1
          timeout_minutes: 30
        inputs:
          - kind: NoOpInput
            name: scan_raw_storage
            description: Scans raw storage to identify obsolete or invalid data.
            path: /data/raw
            recursive: true
        transforms:
          - kind: NoOpTransform
            name: cleanup_obsolete_files
            description: Removes obsolete files based on retention policy.
            dry_run: false
            retention_days: 90
          - kind: NoOpTransform
            name: validate_data_integrity
            description: Performs lightweight validation checks on remaining data.
            fail_on_error: false
        outputs:
          - kind: NoOpOutput
            name: emit_maintenance_report
            description: Emits a summary report with maintenance actions and metrics.
            format: json
            destination: logs
        """
    )

    # Act
    app.run(str(job_file))

    # Assert
    assert app.status.is_success()


# ============================================================================
# File-Based Jobs – Template Variables (temp_workdir)
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_render_temp_workdir_in_yaml_file_templates(
    _atexit, _signal, app: TiozinApp, tmp_path: Path
):
    """
    Each job component (job, runner, and steps) runs inside its own temporary
    working directory.

    When rendering YAML templates:
    - `{{ temp_workdir }}` resolves to the temporary directory of the current
      component being configured (job, runner, or step).
    - `{{ job.temp_workdir }}` resolves to the job-level temporary directory, which is
      shared across the entire job and is accessible from runners and all steps.

    This allows:
    - runners to define their own workspaces while still accessing job-scoped files
    - steps to exchange files explicitly through the job temp_workdir
    - templates to construct paths without hardcoding filesystem locations

    This test verifies that both `temp_workdir` and `job.temp_workdir` are correctly rendered
    inside file-based YAML job definitions.
    """
    # Arrange
    job_file = tmp_path / "temp_workdir_job.yaml"
    job_file.write_text(
        """
        kind: LinearJob
        name: temp_workdir_demo
        org: tiozin
        region: latam
        domain: analytics
        product: reports
        model: daily
        layer: refined
        runner:
          kind: NoOpRunner
          workspace: "{{ temp_workdir }}/runner_workspace"
        inputs:
          - kind: NoOpInput
            name: download_data
            local_cache: "{{ temp_workdir }}/cache"
            output_path: "{{ job.temp_workdir }}/downloaded.csv"
        transforms:
          - kind: NoOpTransform
            name: process_data
            scratch_dir: "{{ temp_workdir }}/scratch"
            input_path: "{{ job.temp_workdir }}/downloaded.csv"
            output_path: "{{ job.temp_workdir }}/processed.parquet"
        outputs:
          - kind: NoOpOutput
            name: upload_results
            staging_dir: "{{ temp_workdir }}/staging"
            source_path: "{{ job.temp_workdir }}/processed.parquet"
        """
    )

    # Act
    app.run(str(job_file))

    # Assert
    assert app.status.is_success()
