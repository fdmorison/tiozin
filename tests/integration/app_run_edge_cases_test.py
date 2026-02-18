"""
Integration tests for TiozinApp - Pipeline Edge Cases.

These tests demonstrate structurally valid but non-standard pipeline
configurations supported by TiozinApp.

The goal of this file is to document edge cases in pipeline topology,
showing that certain components may be omitted or repeated without
invalidating the job.

This file focuses on pipeline structure, not on:
- plugin parameter customization
- job construction APIs (builder, manifest, files)
- business logic or validation errors
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
# Pipeline Variations – Input Only
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_with_input_only(_atexit, _signal, app: TiozinApp):
    """
    Jobs can run with only inputs.

    This is useful for validation jobs, probes, or dry-run scenarios
    where no transformation or output is required.
    """
    # Arrange
    yaml_job = """
        kind: LinearJob
        name: input_only_job
        org: tiozin
        region: latam
        domain: platform
        subdomain: infrastructure
        product: validation
        model: source_check
        layer: raw
        runner:
          kind: NoOpRunner
        inputs:
          - kind: NoOpInput
            name: validate_source
    """

    # Act
    app.run(yaml_job)

    # Assert
    assert app.status.is_success()


# ============================================================================
# Pipeline Variations – No Transforms
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_without_transforms(_atexit, _signal, app: TiozinApp):
    """
    Jobs can run without transforms.

    This represents direct data movement pipelines, such as copy or
    replication jobs.
    """
    # Arrange
    yaml_job = """
        kind: LinearJob
        name: no_transform_job
        org: tiozin
        region: latam
        domain: ingestion
        subdomain: pipeline
        product: raw_data
        model: copy
        layer: raw
        runner:
          kind: NoOpRunner
        inputs:
          - kind: NoOpInput
            name: read_source
        outputs:
          - kind: NoOpOutput
            name: write_destination
    """

    # Act
    app.run(yaml_job)

    # Assert
    assert app.status.is_success()


# ============================================================================
# Pipeline Variations – No Outputs
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_without_outputs(_atexit, _signal, app: TiozinApp):
    """
    Jobs can run without outputs.

    This is useful for pipelines where side effects happen inside
    transforms, such as external API calls or notifications.
    """
    # Arrange
    yaml_job = """
        kind: LinearJob
        name: no_output_job
        org: tiozin
        region: latam
        domain: analytics
        subdomain: reporting
        product: events
        model: process
        layer: raw
        runner:
          kind: NoOpRunner
        inputs:
          - kind: NoOpInput
            name: read_events
        transforms:
          - kind: NoOpTransform
            name: process_events
    """

    # Act
    app.run(yaml_job)

    # Assert
    assert app.status.is_success()


# ============================================================================
# Pipeline Variations – Multiple Inputs
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_with_multiple_inputs(_atexit, _signal, app: TiozinApp):
    """
    Jobs can have multiple inputs.

    This pattern is common for join, enrichment, or reconciliation
    pipelines.
    """
    # Arrange
    yaml_job = """
        kind: LinearJob
        name: multi_input_job
        org: tiozin
        region: latam
        domain: sales
        subdomain: retail
        product: orders
        model: enriched
        layer: refined
        runner:
          kind: NoOpRunner
        inputs:
          - kind: NoOpInput
            name: read_orders
          - kind: NoOpInput
            name: read_customers
          - kind: NoOpInput
            name: read_products
        transforms:
          - kind: NoOpTransform
            name: join_data
        outputs:
          - kind: NoOpOutput
            name: write_enriched
    """

    # Act
    app.run(yaml_job)

    # Assert
    assert app.status.is_success()


# ============================================================================
# Pipeline Variations – Multiple Transforms
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_with_multiple_transforms(_atexit, _signal, app: TiozinApp):
    """
    Jobs can have multiple transforms executed sequentially.

    This pattern supports complex processing pipelines composed of
    multiple logical steps.
    """
    # Arrange
    yaml_job = """
        kind: LinearJob
        name: multi_transform_job
        org: tiozin
        region: latam
        domain: analytics
        subdomain: reporting
        product: orders
        model: aggregated
        layer: refined
        runner:
          kind: NoOpRunner
        inputs:
          - kind: NoOpInput
            name: read_orders
        transforms:
          - kind: NoOpTransform
            name: filter_valid
          - kind: NoOpTransform
            name: deduplicate
          - kind: NoOpTransform
            name: aggregate
        outputs:
          - kind: NoOpOutput
            name: write_aggregated
    """

    # Act
    app.run(yaml_job)

    # Assert
    assert app.status.is_success()


# ============================================================================
# Pipeline Variations – Multiple Outputs
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_with_multiple_outputs(_atexit, _signal, app: TiozinApp):
    """
    Jobs can write to multiple outputs.

    This is useful for fan-out scenarios such as writing to a data
    warehouse, cache, and archive simultaneously.
    """
    # Arrange
    yaml_job = """
        kind: LinearJob
        name: multi_output_job
        org: tiozin
        region: latam
        domain: analytics
        subdomain: reporting
        product: orders
        model: distributed
        layer: refined
        runner:
          kind: NoOpRunner
        inputs:
          - kind: NoOpInput
            name: read_orders
        transforms:
          - kind: NoOpTransform
            name: process
        outputs:
          - kind: NoOpOutput
            name: write_to_warehouse
          - kind: NoOpOutput
            name: write_to_cache
          - kind: NoOpOutput
            name: write_to_archive
    """

    # Act
    app.run(yaml_job)

    # Assert
    assert app.status.is_success()


# ============================================================================
# Pipeline Variations – Multiple Inputs, Transforms, and Outputs Combined
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_with_multiple_inputs_transforms_and_outputs(
    _atexit, _signal, app: TiozinApp
):
    """
    Jobs can combine multiple inputs, transforms, and outputs in a single pipeline.

    This test represents a fully composed pipeline topology and demonstrates
    that TiozinApp supports complex fan-in and fan-out workflows without
    requiring special configuration.
    """
    # Arrange
    yaml_job = """
        kind: LinearJob
        name: fully_composed_pipeline_job
        org: tiozin
        region: latam
        domain: analytics
        subdomain: reporting
        product: orders
        model: enriched_aggregated
        layer: refined
        runner:
          kind: NoOpRunner
        inputs:
          - kind: NoOpInput
            name: read_orders
          - kind: NoOpInput
            name: read_customers
          - kind: NoOpInput
            name: read_products
        transforms:
          - kind: NoOpTransform
            name: join_entities
          - kind: NoOpTransform
            name: filter_valid_records
          - kind: NoOpTransform
            name: aggregate_metrics
        outputs:
          - kind: NoOpOutput
            name: write_to_warehouse
          - kind: NoOpOutput
            name: write_to_cache
          - kind: NoOpOutput
            name: write_to_archive
    """

    # Act
    app.run(yaml_job)

    # Assert
    assert app.status.is_success()
