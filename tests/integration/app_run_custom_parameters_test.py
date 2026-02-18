"""
Integration tests for TiozinApp - Tiozin Custom Parameters.

These tests demonstrate that Tiozin plugins can receive arbitrary
custom parameters beyond `kind` and `name`.

The goal of this file is educational:
- to show how plugin configuration is passed through the system
- to demonstrate that Tiozin does not constrain plugin-specific options
- to illustrate realistic configuration payloads using NoOp plugins

This file focuses exclusively on plugin parameterization and does not
aim to validate business logic or parameter semantics.
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
# Tiozin Parameters – Runner
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_with_custom_runner_parameters(_atexit, _signal, app: TiozinApp):
    """
    Runners can receive arbitrary custom parameters.

    This example demonstrates runner-level configuration such as
    execution mode, retry behavior, and timeouts.
    """
    # Arrange
    yaml_job = """
        kind: LinearJob
        name: runner_parameters_job
        org: tiozin
        region: latam
        domain: platform
        subdomain: infrastructure
        product: execution
        model: maintenance
        layer: raw
        runner:
          kind: NoOpRunner
          execution_mode: maintenance
          retry_attempts: 2
          timeout_minutes: 45
          fail_fast: true
        inputs:
          - kind: NoOpInput
            name: noop
    """

    # Act
    app.run(yaml_job)

    # Assert
    assert app.status.is_success()


# ============================================================================
# Tiozin Parameters – Input
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_with_custom_input_parameters(_atexit, _signal, app: TiozinApp):
    """
    Inputs can receive arbitrary custom parameters.

    This example demonstrates input-specific configuration such as
    paths, formats, encodings, and recursive flags.
    """
    # Arrange
    yaml_job = """
        kind: LinearJob
        name: input_parameters_job
        org: tiozin
        region: latam
        domain: ingestion
        subdomain: pipeline
        product: documents
        model: scan
        layer: raw
        runner:
          kind: NoOpRunner
        inputs:
          - kind: NoOpInput
            name: read_documents
            path: /data/documents
            format: text
            encoding: utf-8
            recursive: true
    """

    # Act
    app.run(yaml_job)

    # Assert
    assert app.status.is_success()


# ============================================================================
# Tiozin Parameters – Transform
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_with_custom_transform_parameters(_atexit, _signal, app: TiozinApp):
    """
    Transforms can receive arbitrary custom parameters.

    Although NoOpTransform does not implement real logic, this example
    resembles a word normalization and filtering step.
    """
    # Arrange
    yaml_job = """
        kind: LinearJob
        name: transform_parameters_job
        org: tiozin
        region: latam
        domain: analytics
        subdomain: reporting
        product: text
        model: normalize
        layer: refined
        runner:
          kind: NoOpRunner
        inputs:
          - kind: NoOpInput
            name: read_text
        transforms:
          - kind: NoOpTransform
            name: normalize_words
            lowercase: true
            remove_punctuation: true
            min_word_length: 3
            stopwords:
              - the
              - and
              - of
    """

    # Act
    app.run(yaml_job)

    # Assert
    assert app.status.is_success()


# ============================================================================
# Tiozin Parameters – Output
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_with_custom_output_parameters(_atexit, _signal, app: TiozinApp):
    """
    Outputs can receive arbitrary custom parameters.

    This example demonstrates output configuration such as
    destination, write mode, and partitioning hints.
    """
    # Arrange
    yaml_job = """
        kind: LinearJob
        name: output_parameters_job
        org: tiozin
        region: latam
        domain: analytics
        subdomain: reporting
        product: metrics
        model: export
        layer: refined
        runner:
          kind: NoOpRunner
        inputs:
          - kind: NoOpInput
            name: read_metrics
        outputs:
          - kind: NoOpOutput
            name: write_metrics
            destination: warehouse
            mode: overwrite
            partition_by:
              - execution_date
    """

    # Act
    app.run(yaml_job)

    # Assert
    assert app.status.is_success()


# ============================================================================
# Tiozin Parameters – All Components Combined
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_run_job_with_custom_parameters_across_all_plugins(
    _atexit, _signal, app: TiozinApp
):
    """
    Custom parameters can be provided consistently across all plugin types.

    This example combines runner, input, transform, and output parameters in a single job definition
    to demonstrate end-to-end configuration pass-through.
    """
    # Arrange
    yaml_job = """
        kind: LinearJob
        name: full_parameterized_job
        org: tiozin
        region: latam
        domain: analytics
        subdomain: reporting
        product: text
        model: wordcount
        layer: refined
        runner:
          kind: NoOpRunner
          parallelism: 4
          retry_attempts: 3
        inputs:
          - kind: NoOpInput
            name: read_documents
            path: /data/docs
            recursive: true
        transforms:
          - kind: NoOpTransform
            name: count_words
            lowercase: true
            min_word_length: 3
        outputs:
          - kind: NoOpOutput
            name: write_wordcount
            destination: warehouse
            mode: append
    """

    # Act
    app.run(yaml_job)

    # Assert
    assert app.status.is_success()
