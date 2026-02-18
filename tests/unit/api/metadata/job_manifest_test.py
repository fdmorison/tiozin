from textwrap import dedent
from typing import Any

import pytest
from pydantic import ValidationError

from tiozin.api.metadata.job_manifest import (
    InputManifest,
    JobManifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)
from tiozin.exceptions import ManifestError

# ============================================================================
# JobManifest.__init__ tests
# ============================================================================


def test_manifest_should_accept_job():
    # Arrange
    data = dict(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner={"kind": "TestRunner"},
        inputs=[{"kind": "TestInput", "name": "reader"}],
        transforms=[{"kind": "TestTransform", "name": "transformer"}],
        outputs=[{"kind": "TestOutput", "name": "write_something"}],
    )

    # Act
    JobManifest(**data)

    # Assert
    assert True


def test_manifest_should_accept_job_with_multiple_inputs_transforms_and_outputs():
    # Arrange
    data = dict(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner={"kind": "TestRunner"},
        inputs=[
            {"kind": "TestInput", "name": "input_1"},
            {"kind": "TestInput", "name": "input_2"},
            {"kind": "TestInput", "name": "input_3"},
        ],
        transforms=[
            {"kind": "TestTransform", "name": "transform_1"},
            {"kind": "TestTransform", "name": "transform_2"},
        ],
        outputs=[
            {"kind": "TestOutput", "name": "output_1"},
            {"kind": "TestOutput", "name": "output_2"},
        ],
    )

    # Act
    manifest = JobManifest(**data)

    # Assert
    actual = manifest
    expected = JobManifest(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner=RunnerManifest(kind="TestRunner"),
        inputs=[
            InputManifest(kind="TestInput", name="input_1"),
            InputManifest(kind="TestInput", name="input_2"),
            InputManifest(kind="TestInput", name="input_3"),
        ],
        transforms=[
            TransformManifest(kind="TestTransform", name="transform_1"),
            TransformManifest(kind="TestTransform", name="transform_2"),
        ],
        outputs=[
            OutputManifest(kind="TestOutput", name="output_1"),
            OutputManifest(kind="TestOutput", name="output_2"),
        ],
    )
    assert actual == expected


def test_manifest_should_accept_job_without_transforms_and_outputs():
    # Arrange
    data = dict(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner={"kind": "TestRunner"},
        inputs=[{"kind": "TestInput", "name": "input_1"}],
    )

    # Act
    manifest = JobManifest(**data)

    # Assert
    actual = manifest
    expected = JobManifest(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner=RunnerManifest(kind="TestRunner"),
        inputs=[InputManifest(kind="TestInput", name="input_1")],
        transforms=[],
        outputs=[],
    )
    assert actual == expected


@pytest.mark.parametrize(
    "optional_field,optional_value",
    [
        ("owner", "team@example.com"),
        ("maintainer", "dev@example.com"),
        ("cost_center", "CC-12345"),
        ("description", "A test job description"),
        ("labels", {"env": "test"}),
        ("transforms", [TransformManifest(kind="TestTransform", name="foo")]),
        ("outputs", [OutputManifest(kind="TestOutput", name="foo")]),
    ],
)
def test_manifest_should_accept_job_with_optional_fields(optional_field: str, optional_value: Any):
    # Arrange
    data = dict(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner={"kind": "TestRunner"},
        inputs=[{"kind": "TestInput", "name": "read_something"}],
    )
    data[optional_field] = optional_value

    # Act
    manifest = JobManifest(**data)

    # Assert
    actual = getattr(manifest, optional_field)
    expected = optional_value
    assert actual == expected


def test_manifest_should_apply_defaults():
    # Arrange
    data = dict(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner={"kind": "TestRunner"},
        inputs=[{"kind": "TestInput", "name": "read_something"}],
    )

    # Act
    manifest = JobManifest(**data)

    # Assert
    actual = manifest
    expected = JobManifest(
        kind="Job",
        name="test_job",
        description=None,
        owner=None,
        maintainer=None,
        cost_center=None,
        labels={},
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner=RunnerManifest(kind="TestRunner"),
        inputs=[InputManifest(kind="TestInput", name="read_something")],
        transforms=[],
        outputs=[],
    )
    assert actual == expected


@pytest.mark.parametrize(
    "field_to_remove",
    [
        "kind",
        "name",
        "org",
        "region",
        "domain",
        "subdomain",
        "layer",
        "product",
        "model",
        "runner",
        "inputs",
    ],
)
def test_manifest_should_reject_job_without_required_field(field_to_remove):
    # Arrange
    data = dict(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner={"kind": "TestRunner"},
        inputs=[{"kind": "TestInput", "name": "reader"}],
        transforms=[{"kind": "TestTransform", "name": "transformer"}],
        outputs=[{"kind": "TestOutput", "name": "write_something"}],
    )
    del data[field_to_remove]

    # Act
    with pytest.raises(ValidationError):
        JobManifest(**data)


def test_manifest_should_reject_job_with_empty_inputs():
    # Arrange
    data = dict(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner={"kind": "TestRunner"},
        inputs=[],
        transforms=[{"kind": "TestTransform", "name": "transform_something"}],
        outputs=[{"kind": "TestOutput", "name": "write_something"}],
    )

    # Act
    with pytest.raises(ValidationError):
        JobManifest(**data)


@pytest.mark.parametrize(
    "field_name,invalid_value",
    [
        ("kind", 123),
        ("name", 456),
        ("labels", "not_a_dict"),
        ("inputs", "not_a_list"),
        ("runner", "not_a_dict"),
    ],
)
def test_manifest_should_reject_job_with_invalid_field_types(field_name, invalid_value):
    # Arrange
    data = dict(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner={"kind": "TestRunner"},
        inputs=[{"kind": "TestInput", "name": "reader"}],
        transforms=[{"kind": "TestTransform", "name": "transformer"}],
        outputs=[{"kind": "TestOutput", "name": "write_something"}],
    )
    data[field_name] = invalid_value

    # Act
    with pytest.raises(ValidationError):
        JobManifest(**data)


# ============================================================================
# JobManifest.to_yaml() tests
# ============================================================================


def test_to_yaml_should_serialize_manifest_to_yaml_string():
    # Arrange
    manifest = JobManifest(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner=RunnerManifest(kind="TestRunner"),
        inputs=[InputManifest(kind="TestInput", name="reader")],
        transforms=[TransformManifest(kind="TestTransform", name="transformer")],
        outputs=[OutputManifest(kind="TestOutput", name="writer")],
    )

    # Act
    yaml_output = manifest.to_yaml()

    # Assert
    actual = yaml_output
    expected = dedent("""
        kind: Job
        name: test_job
        org: tiozin
        region: latam
        domain: quality
        subdomain: pipeline
        layer: test
        product: test_cases
        model: some_case
        runner:
          kind: TestRunner
        inputs:
        - kind: TestInput
          name: reader
        transforms:
        - kind: TestTransform
          name: transformer
        outputs:
        - kind: TestOutput
          name: writer
    """).lstrip()
    assert actual == expected


def test_to_yaml_should_not_render_unset_values():
    # Arrange
    manifest = JobManifest(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner=RunnerManifest(kind="TestRunner"),
        inputs=[InputManifest(kind="TestInput", name="reader")],
    )

    # Act
    yaml_string = manifest.to_yaml()

    # Assert
    actual = all(
        [
            "description:" in yaml_string,
            "transforms:" in yaml_string,
            "outputs:" in yaml_string,
        ]
    )
    expected = False
    assert actual == expected


# ============================================================================
# JobManifest.to_json() tests
# ============================================================================


def test_to_json_should_serialize_manifest_to_json_string():
    # Arrange
    manifest = JobManifest(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner=RunnerManifest(kind="TestRunner"),
        inputs=[InputManifest(kind="TestInput", name="reader")],
        transforms=[TransformManifest(kind="TestTransform", name="transformer")],
        outputs=[OutputManifest(kind="TestOutput", name="writer")],
    )

    # Act
    json_string = manifest.to_json()

    # Assert
    actual = json_string
    expected = dedent("""
    {
      "kind": "Job",
      "name": "test_job",
      "org": "tiozin",
      "region": "latam",
      "domain": "quality",
      "subdomain": "pipeline",
      "layer": "test",
      "product": "test_cases",
      "model": "some_case",
      "runner": {
        "kind": "TestRunner"
      },
      "inputs": [
        {
          "kind": "TestInput",
          "name": "reader"
        }
      ],
      "transforms": [
        {
          "kind": "TestTransform",
          "name": "transformer"
        }
      ],
      "outputs": [
        {
          "kind": "TestOutput",
          "name": "writer"
        }
      ]
    }
    """).lstrip()
    assert actual == expected


def test_to_json_should_not_render_unset_fields():
    # Arrange
    manifest = JobManifest(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner=RunnerManifest(kind="TestRunner"),
        inputs=[InputManifest(kind="TestInput", name="reader")],
    )

    # Act
    json_string = manifest.to_json()

    # Assert
    actual = all(
        [
            "description:" in json_string,
            "transforms:" in json_string,
            "outputs:" in json_string,
        ]
    )
    expected = False
    assert actual == expected


# ============================================================================
# JobManifest.from_yaml_or_json() tests
# ============================================================================


def test_from_yaml_or_json_should_deserialize_yaml():
    # Arrange
    text = dedent("""
        kind: Job
        name: test_job
        labels: {}
        org: tiozin
        region: latam
        domain: quality
        subdomain: pipeline
        layer: test
        product: test_cases
        model: some_case
        runner:
          kind: TestRunner
          streaming: false
        inputs:
        - kind: TestInput
          name: reader
        transforms:
        - kind: TestTransform
          name: transformer
        outputs:
        - kind: TestOutput
          name: writer
    """).lstrip()

    # Act
    manifest = JobManifest.from_yaml_or_json(text)

    # Assert
    actual = manifest
    expected = JobManifest(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner=RunnerManifest(kind="TestRunner"),
        inputs=[InputManifest(kind="TestInput", name="reader")],
        transforms=[TransformManifest(kind="TestTransform", name="transformer")],
        outputs=[OutputManifest(kind="TestOutput", name="writer")],
    )
    assert actual == expected


def test_from_yaml_or_json_should_deserialize_json():
    # Arrange
    text = dedent("""
    {
      "kind": "Job",
      "name": "test_job",
      "labels": {},
      "org": "tiozin",
      "region": "latam",
      "domain": "quality",
      "subdomain": "pipeline",
      "layer": "test",
      "product": "test_cases",
      "model": "some_case",
      "runner": {
        "kind": "TestRunner",
        "streaming": false
      },
      "inputs": [
        {
          "kind": "TestInput",
          "name": "reader"
        }
      ],
      "transforms": [
        {
          "kind": "TestTransform",
          "name": "transformer"
        }
      ],
      "outputs": [
        {
          "kind": "TestOutput",
          "name": "writer"
        }
      ]
    }
    """).strip()

    # Act
    manifest = JobManifest.from_yaml_or_json(text)

    # Assert
    actual = manifest
    expected = JobManifest(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner=RunnerManifest(kind="TestRunner"),
        inputs=[InputManifest(kind="TestInput", name="reader")],
        transforms=[TransformManifest(kind="TestTransform", name="transformer")],
        outputs=[OutputManifest(kind="TestOutput", name="writer")],
    )
    assert actual == expected


def test_from_yaml_or_json_should_fail_when_manifest_has_duplicated_keys():
    # Arrange
    text = dedent("""
        kind: Job
        name: test_job
        labels: {}
        org: tiozin
        region: latam
        domain: quality
        subdomain: pipeline
        layer: test
        product: test_cases_1
        product: test_cases_2
        model: some_case
        runner:
          kind: TestRunner
          streaming: false
        inputs:
        - kind: TestInput
          name: reader
        transforms:
        - kind: TestTransform
          name: transformer
        outputs:
        - kind: TestOutput
          name: writer
    """).lstrip()

    # Act
    with pytest.raises(ManifestError, match="duplicate key"):
        JobManifest.from_yaml_or_json(text)


# ============================================================================
# JobManifest.try_from_yaml_or_json() tests
# ============================================================================


def test_try_from_yaml_or_json_should_return_manifest_when_valid_yaml():
    # Arrange
    text = dedent("""
        kind: Job
        name: test_job
        labels: {}
        org: tiozin
        region: latam
        domain: quality
        subdomain: pipeline
        layer: test
        product: test_cases
        model: some_case
        runner:
          kind: TestRunner
          streaming: false
        inputs:
        - kind: TestInput
          name: reader
    """).lstrip()

    # Act
    manifest = JobManifest.try_from_yaml_or_json(text)

    # Assert
    actual = manifest is None
    expected = False
    assert actual == expected


def test_try_from_yaml_or_json_should_return_none_when_invalid_yaml():
    # Arrange
    text = "invalid: yaml: content: ["

    # Act
    manifest = JobManifest.try_from_yaml_or_json(text)

    # Assert
    actual = manifest
    expected = None
    assert actual == expected


def test_try_from_yaml_or_json_should_return_none_when_not_string():
    # Arrange
    data = {"kind": "Job", "name": "test"}

    # Act
    manifest = JobManifest.try_from_yaml_or_json(data)

    # Assert
    actual = manifest
    expected = None
    assert actual == expected


def test_try_from_yaml_or_json_should_return_none_when_validation_fails():
    # Arrange
    text = dedent("""
        kind: Job
        name: test_job
    """).lstrip()

    # Act
    manifest = JobManifest.try_from_yaml_or_json(text)

    # Assert
    actual = manifest
    expected = None
    assert actual == expected


def test_try_from_yaml_or_json_should_return_manifest_when_already_manifest():
    # Arrange
    data = JobManifest(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner=RunnerManifest(kind="TestRunner"),
        inputs=[InputManifest(kind="TestInput", name="reader")],
    )

    # Act
    manifest = JobManifest.try_from_yaml_or_json(data)

    # Assert
    actual = manifest
    expected = data
    assert actual == expected


# ============================================================================
# Roundtrip tests (serialization + deserialization)
# ============================================================================


def test_yaml_roundtrip_should_preserve_data():
    # Arrange
    manifest = JobManifest(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner=RunnerManifest(kind="TestRunner"),
        inputs=[InputManifest(kind="TestInput", name="reader")],
        transforms=[TransformManifest(kind="TestTransform", name="transformer")],
        outputs=[OutputManifest(kind="TestOutput", name="writer")],
    )

    # Act
    text = manifest.to_yaml()
    restored = JobManifest.from_yaml_or_json(text)

    # Assert
    actual = restored
    expected = manifest
    assert actual == expected


def test_json_roundtrip_should_preserve_data():
    # Arrange
    original = JobManifest(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
        runner=RunnerManifest(kind="TestRunner"),
        inputs=[InputManifest(kind="TestInput", name="reader")],
        transforms=[TransformManifest(kind="TestTransform", name="transformer")],
        outputs=[OutputManifest(kind="TestOutput", name="writer")],
    )

    # Act
    text = original.to_json()
    restored = JobManifest.from_yaml_or_json(text)

    # Assert
    actual = restored
    expected = original
    assert actual == expected
