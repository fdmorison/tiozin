import pytest

from tiozin.api import JobManifest
from tiozin.api.metadata.job_manifest import (
    InputManifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)
from tiozin.assembly.builder import JobBuilder
from tiozin.exceptions import InvalidInputError, TiozinUnexpectedError
from tiozin.family.tio_kernel import LinearJob, NoOpInput, NoOpOutput, NoOpRunner, NoOpTransform

TEST_TAXONOMY = {
    "org": "tiozin",
    "region": "latam",
    "domain": "quality",
    "product": "test_cases",
    "model": "some_case",
    "layer": "test",
    "description": "test",
}


def test_builder_should_build_job_from_fluent_interface():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.kind("LinearJob")
        .name("test_job")
        .org("tiozin")
        .region("latam")
        .domain("quality")
        .product("test_cases")
        .model("some_case")
        .layer("test")
        .runner({"kind": "NoOpRunner"})
        .inputs({"kind": "NoOpInput", "name": "read_something"})
        .transforms({"kind": "NoOpTransform", "name": "transform_something"})
        .outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    assert isinstance(job, LinearJob)


def test_builder_should_build_from_job_manifest():
    # Arrange
    manifest = JobManifest(
        kind="LinearJob",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        product="test_cases",
        model="some_case",
        layer="test",
        runner=RunnerManifest(kind="NoOpRunner"),
        inputs=[
            InputManifest(kind="NoOpInput", name="read_something"),
        ],
        transforms=[
            TransformManifest(kind="NoOpTransform", name="transform_something"),
        ],
        outputs=[
            OutputManifest(kind="NoOpOutput", name="write_something"),
        ],
    )
    builder = JobBuilder()

    # Act
    builder.from_manifest(manifest).build()

    # Assert
    assert True


def test_builder_should_build_from_plugin_manifests():
    # Arrange
    builder = JobBuilder()

    # Act
    (
        builder.kind("LinearJob")
        .name("test_job")
        .org("tiozin")
        .region("latam")
        .domain("quality")
        .product("test_cases")
        .model("some_case")
        .layer("test")
        .runner(
            RunnerManifest(kind="NoOpRunner"),
        )
        .inputs(
            InputManifest(kind="NoOpInput", name="read_something"),
        )
        .transforms(
            TransformManifest(kind="NoOpTransform", name="transform_something"),
        )
        .outputs(
            OutputManifest(kind="NoOpOutput", name="write_something"),
        )
        .build()
    )

    # Assert
    assert True


def test_builder_should_build_from_plugin_instances():
    # Arrange
    builder = JobBuilder()

    # Act
    (
        builder.kind("LinearJob")
        .name("test_job")
        .org("tiozin")
        .region("latam")
        .domain("quality")
        .product("test_cases")
        .model("some_case")
        .layer("test")
        .runner(
            NoOpRunner(),
        )
        .inputs(
            NoOpInput(name="read_something", **TEST_TAXONOMY),
        )
        .transforms(
            NoOpTransform(name="transform_something", **TEST_TAXONOMY),
        )
        .outputs(
            NoOpOutput(name="write_something", **TEST_TAXONOMY),
        )
        .build()
    )

    # Assert
    assert True


def test_builder_should_build_from_plugin_dicts():
    # Arrange
    builder = JobBuilder()

    # Act
    (
        builder.kind("LinearJob")
        .name("test_job")
        .org("tiozin")
        .region("latam")
        .domain("quality")
        .product("test_cases")
        .model("some_case")
        .layer("test")
        .runner(
            {"kind": "NoOpRunner"},
        )
        .inputs(
            {"kind": "NoOpInput", "name": "read_something", **TEST_TAXONOMY},
        )
        .transforms(
            {"kind": "NoOpTransform", "name": "transform_something", **TEST_TAXONOMY},
        )
        .outputs(
            {"kind": "NoOpOutput", "name": "write_something", **TEST_TAXONOMY},
        )
        .build()
    )

    # Assert
    assert True


def test_builder_should_accept_multiple_inputs():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.kind("LinearJob")
        .name("test_job")
        .org("tiozin")
        .region("latam")
        .domain("quality")
        .product("test_cases")
        .model("some_case")
        .layer("test")
        .runner({"kind": "NoOpRunner"})
        .inputs(
            {"kind": "NoOpInput", "name": "input1"},
            {"kind": "NoOpInput", "name": "input2"},
        )
        .outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    assert len(job.inputs) == 2


def test_builder_should_accept_multiple_transforms():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.kind("LinearJob")
        .name("test_job")
        .org("tiozin")
        .region("latam")
        .domain("quality")
        .product("test_cases")
        .model("some_case")
        .layer("test")
        .runner({"kind": "NoOpRunner"})
        .inputs({"kind": "NoOpInput", "name": "read_something"})
        .transforms(
            {"kind": "NoOpTransform", "name": "transform1"},
            {"kind": "NoOpTransform", "name": "transform2"},
        )
        .outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    assert len(job.transforms) == 2


def test_builder_should_accept_multiple_outputs():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.kind("LinearJob")
        .name("test_job")
        .org("tiozin")
        .region("latam")
        .domain("quality")
        .product("test_cases")
        .model("some_case")
        .layer("test")
        .runner({"kind": "NoOpRunner"})
        .inputs({"kind": "NoOpInput", "name": "read_something"})
        .outputs(
            {"kind": "NoOpOutput", "name": "output1"},
            {"kind": "NoOpOutput", "name": "output2"},
        )
        .build()
    )

    # Assert
    assert len(job.outputs) == 2


def test_builder_should_set_labels():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.kind("LinearJob")
        .name("test_job")
        .org("tiozin")
        .region("latam")
        .domain("quality")
        .product("test_cases")
        .model("some_case")
        .layer("test")
        .label("env", "dev")
        .label("team", "data")
        .runner({"kind": "NoOpRunner"})
        .inputs({"kind": "NoOpInput", "name": "read_something"})
        .outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    assert job.labels == {"env": "dev", "team": "data"}


def test_builder_should_set_labels_dict():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.kind("LinearJob")
        .name("test_job")
        .org("tiozin")
        .region("latam")
        .domain("quality")
        .product("test_cases")
        .model("some_case")
        .layer("test")
        .labels({"env": "dev", "team": "data"})
        .runner({"kind": "NoOpRunner"})
        .inputs({"kind": "NoOpInput", "name": "read_something"})
        .outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    assert job.labels == {"env": "dev", "team": "data"}


def test_builder_should_set_optional_fields():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.kind("LinearJob")
        .name("test_job")
        .description("A test job")
        .owner("team-data")
        .maintainer("team-platform")
        .cost_center("engineering")
        .org("tiozin")
        .region("latam")
        .domain("quality")
        .product("test_cases")
        .model("some_case")
        .layer("test")
        .runner({"kind": "NoOpRunner"})
        .inputs({"kind": "NoOpInput", "name": "read_something"})
        .outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    assert job.description == "A test job"
    assert job.owner == "team-data"
    assert job.maintainer == "team-platform"
    assert job.cost_center == "engineering"


def test_builder_should_handle_unplanned_fields():
    # Arrange
    builder = JobBuilder()

    # Act
    (
        builder.kind("LinearJob")
        .name("test_job")
        .org("tiozin")
        .region("latam")
        .domain("quality")
        .product("test_cases")
        .model("some_case")
        .layer("test")
        .runner({"kind": "NoOpRunner"})
        .inputs({"kind": "NoOpInput", "name": "read_something"})
        .outputs({"kind": "NoOpOutput", "name": "write_something"})
        .set("custom_field", "custom_value")
        .build()
    )

    # Assert
    assert True


def test_builder_should_reject_invalid_runner_type():
    # Arrange
    builder = JobBuilder()

    # Act & Assert
    with pytest.raises(InvalidInputError, match="Invalid runner definition"):
        builder.runner(12345)


def test_builder_should_reject_invalid_input_type():
    # Arrange
    builder = JobBuilder()

    # Act & Assert
    with pytest.raises(InvalidInputError, match="Invalid input definition"):
        builder.inputs("invalid")


def test_builder_should_reject_invalid_transform_type():
    # Arrange
    builder = JobBuilder()

    # Act & Assert
    with pytest.raises(InvalidInputError, match="Invalid transform definition"):
        builder.transforms(12345)


def test_builder_should_reject_invalid_output_type():
    # Arrange
    builder = JobBuilder()

    # Act & Assert
    with pytest.raises(InvalidInputError, match="Invalid output definition"):
        builder.outputs(None)


def test_builder_should_fail_when_used_twice():
    # Arrange
    builder = (
        JobBuilder()
        .kind("LinearJob")
        .name("test_job")
        .org("tiozin")
        .region("latam")
        .domain("quality")
        .product("test_cases")
        .model("some_case")
        .layer("test")
        .runner({"kind": "NoOpRunner"})
        .inputs({"kind": "NoOpInput", "name": "read_something"})
        .outputs({"kind": "NoOpOutput", "name": "write_something"})
    )

    # Act/Assert
    with pytest.raises(TiozinUnexpectedError, match="can only be used once"):
        builder.build()
        builder.build()


def test_builder_should_warn_about_unplanned_fields(caplog):
    # Arrange
    manifest = JobManifest(
        kind="LinearJob",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        product="test_cases",
        model="some_case",
        layer="test",
        runner=RunnerManifest(kind="NoOpRunner"),
        inputs=[InputManifest(kind="NoOpInput", name="read_something")],
        transforms=[],
        outputs=[OutputManifest(kind="NoOpOutput", name="write_something")],
        unplanned_field="value",
    )
    builder = JobBuilder()

    # Act
    builder.from_manifest(manifest).build()

    # Assert
    assert "Unplanned job properties" in caplog.text
