"""
Integration tests for TiozinApp - Inline Job Definitions.

These tests demonstrate how to run jobs whose definitions are provided
inline as strings.

Inline job definitions are useful when:
- job definitions come from user input
- jobs are generated dynamically at runtime
- integrating with APIs or UIs that emit YAML or JSON
- quick prototyping and experimentation

This file focuses exclusively on inline execution and does not cover:
- file-based jobs
- Job.builder usage
- plugin parameter customization
- direct job instantiation
"""

from unittest.mock import patch

import pytest

from tiozin import TiozinApp


@pytest.fixture
def app():
    app = TiozinApp()
    yield app
    app.teardown()


# ============================================================================
# Inline Jobs – YAML
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_from_inline_yaml(_atexit, _signal, app: TiozinApp):
    """
    Jobs can be defined as inline YAML strings.

    This is the most common inline format due to its readability
    and expressiveness.
    """
    # Arrange
    yaml_job = """
        kind: LinearJob
        name: inline_yaml_job
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

    # Act
    app.run(yaml_job)

    # Assert
    assert app.status.is_success()


# ============================================================================
# Inline Jobs – JSON
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_from_inline_json(_atexit, _signal, app: TiozinApp):
    """
    Jobs can also be defined as inline JSON strings.

    JSON is useful when job definitions originate from systems
    that already operate on JSON payloads, such as REST APIs.
    """
    # Arrange
    json_job = """
        {
            "kind": "LinearJob",
            "name": "inline_json_job",
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

    # Act
    app.run(json_job)

    # Assert
    assert app.status.is_success()


# ============================================================================
# Inline Jobs – Full Job Definition (YAML)
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_full_job_from_inline_yaml(_atexit, _signal, app: TiozinApp):
    """
    Demonstrates a fully specified Job defined inline as a YAML string.

    This example represents a realistic maintenance job and showcases
    that inline definitions support the same expressive power as files
    or manifests.
    """
    # Arrange
    yaml_job = """
        kind: LinearJob
        name: maintenance_cleanup_job
        description: Periodic maintenance job responsible for cleaning up obsolete data
        owner: data-platform
        maintainer: oncall-data-eng
        cost_center: cc-analytics-001
        labels:
          job_type: maintenance
          schedule: weekly
        org: tiozin
        region: latam
        domain: platform
        product: data-platform
        model: maintenance
        layer: raw
        runner:
          kind: NoOpRunner
          description: Executes the job in maintenance mode.
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
            retention_days: 90
        outputs:
          - kind: NoOpOutput
            name: emit_maintenance_report
            description: Emits a summary report with maintenance actions and metrics.
            destination: logs
    """

    # Act
    app.run(yaml_job)

    # Assert
    assert app.status.is_success()


# ============================================================================
# Inline Jobs – Template Variables (temp_workdir)
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_render_temp_workdir_in_yaml_templates(_atexit, _signal, app: TiozinApp):
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
    inside YAML templates across different execution scopes.
    """
    # Arrange
    yaml_job = """
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

    # Act
    app.run(yaml_job)

    # Assert
    assert app.status.is_success()


@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_render_temp_workdir_in_json_templates(_atexit, _signal, app: TiozinApp):
    """
    Each job component (job, runner, and steps) runs inside its own temporary
    working directory.

    When rendering JSON templates:
    - `{{ temp_workdir }}` resolves to the temporary directory of the current
      component being configured (job, runner, or step).
    - `{{ job.temp_workdir }}` resolves to the job-level temporary directory, which is
      shared across the entire job and is accessible from runners and all steps.

    This test verifies that both `temp_workdir` and `job.temp_workdir` are correctly rendered
    inside inline JSON job definitions.
    """
    # Arrange
    json_job = """
        {
            "kind": "LinearJob",
            "name": "temp_workdir_demo",
            "org": "tiozin",
            "region": "latam",
            "domain": "analytics",
            "product": "reports",
            "model": "daily",
            "layer": "refined",
            "runner": {
                "kind": "NoOpRunner",
                "workspace": "{{ temp_workdir }}/runner_workspace"
            },
            "inputs": [
                {
                    "kind": "NoOpInput",
                    "name": "download_data",
                    "local_cache": "{{ temp_workdir }}/cache",
                    "output_path": "{{ job.temp_workdir }}/downloaded.csv"
                }
            ],
            "transforms": [
                {
                    "kind": "NoOpTransform",
                    "name": "process_data",
                    "scratch_dir": "{{ temp_workdir }}/scratch",
                    "input_path": "{{ job.temp_workdir }}/downloaded.csv",
                    "output_path": "{{ job.temp_workdir }}/processed.parquet"
                }
            ],
            "outputs": [
                {
                    "kind": "NoOpOutput",
                    "name": "upload_results",
                    "staging_dir": "{{ temp_workdir }}/staging",
                    "source_path": "{{ job.temp_workdir }}/processed.parquet"
                }
            ]
        }
    """

    # Act
    app.run(json_job)

    # Assert
    assert app.status.is_success()
