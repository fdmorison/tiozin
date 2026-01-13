import pytest

from tiozin.api import JobManifest
from tiozin.api.metadata.job_manifest import (
    InputManifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)
from tiozin.assembly.job_builder import JobBuilder
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


def test_builder_should_propagate_taxonomy_to_inputs():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.kind("LinearJob")
        .name("test_job")
        .org("tiozin")
        .region("europe")
        .domain("marketing")
        .product("user_events")
        .model("order_completed")
        .layer("refined")
        .runner({"kind": "NoOpRunner"})
        .inputs({"kind": "NoOpInput", "name": "read_something"})
        .outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    input_operator = job.inputs[0]
    actual = {
        "org": input_operator.org,
        "region": input_operator.region,
        "domain": input_operator.domain,
        "product": input_operator.product,
        "model": input_operator.model,
        "layer": input_operator.layer,
    }
    expected = {
        "org": "tiozin",
        "region": "europe",
        "domain": "marketing",
        "product": "user_events",
        "model": "order_completed",
        "layer": "refined",
    }
    assert actual == expected


def test_builder_should_propagate_taxonomy_to_outputs():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.kind("LinearJob")
        .name("test_job")
        .org("tiozin")
        .region("europe")
        .domain("marketing")
        .product("user_events")
        .model("order_completed")
        .layer("refined")
        .runner({"kind": "NoOpRunner"})
        .inputs({"kind": "NoOpInput", "name": "read_something"})
        .outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    output_operator = job.outputs[0]
    actual = {
        "org": output_operator.org,
        "region": output_operator.region,
        "domain": output_operator.domain,
        "product": output_operator.product,
        "model": output_operator.model,
        "layer": output_operator.layer,
    }
    expected = {
        "org": "tiozin",
        "region": "europe",
        "domain": "marketing",
        "product": "user_events",
        "model": "order_completed",
        "layer": "refined",
    }
    assert actual == expected


def test_builder_should_propagate_taxonomy_to_transforms():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.kind("LinearJob")
        .name("test_job")
        .org("tiozin")
        .region("europe")
        .domain("marketing")
        .product("user_events")
        .model("order_completed")
        .layer("refined")
        .runner({"kind": "NoOpRunner"})
        .inputs({"kind": "NoOpInput", "name": "read_something"})
        .transforms({"kind": "NoOpTransform", "name": "transform_something"})
        .outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    transform_operator = job.transforms[0]
    actual = {
        "org": transform_operator.org,
        "region": transform_operator.region,
        "domain": transform_operator.domain,
        "product": transform_operator.product,
        "model": transform_operator.model,
        "layer": transform_operator.layer,
    }
    expected = {
        "org": "tiozin",
        "region": "europe",
        "domain": "marketing",
        "product": "user_events",
        "model": "order_completed",
        "layer": "refined",
    }
    assert actual == expected


def test_builder_should_not_overwrite_input_taxonomy_when_already_set():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.kind("LinearJob")
        .name("test_job")
        .org("tiozin")
        .region("europe")
        .domain("marketing")
        .product("user_events")
        .model("order_completed")
        .layer("refined")
        .runner({"kind": "NoOpRunner"})
        .inputs(
            {
                "kind": "NoOpInput",
                "name": "read_something",
                "org": "custom_org",
                "region": "custom_region",
                "domain": "custom_domain",
                "product": "custom_product",
                "model": "custom_model",
                "layer": "custom_layer",
            }
        )
        .outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    input_operator = job.inputs[0]
    actual = {
        "org": input_operator.org,
        "region": input_operator.region,
        "domain": input_operator.domain,
        "product": input_operator.product,
        "model": input_operator.model,
        "layer": input_operator.layer,
    }
    expected = {
        "org": "custom_org",
        "region": "custom_region",
        "domain": "custom_domain",
        "product": "custom_product",
        "model": "custom_model",
        "layer": "custom_layer",
    }
    assert actual == expected


def test_builder_should_not_overwrite_output_taxonomy_when_already_set():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.kind("LinearJob")
        .name("test_job")
        .org("tiozin")
        .region("europe")
        .domain("marketing")
        .product("user_events")
        .model("order_completed")
        .layer("refined")
        .runner({"kind": "NoOpRunner"})
        .inputs({"kind": "NoOpInput", "name": "read_something"})
        .outputs(
            {
                "kind": "NoOpOutput",
                "name": "write_something",
                "org": "custom_org",
                "region": "custom_region",
                "domain": "custom_domain",
                "product": "custom_product",
                "model": "custom_model",
                "layer": "custom_layer",
            }
        )
        .build()
    )

    # Assert
    output_operator = job.outputs[0]
    actual = {
        "org": output_operator.org,
        "region": output_operator.region,
        "domain": output_operator.domain,
        "product": output_operator.product,
        "model": output_operator.model,
        "layer": output_operator.layer,
    }
    expected = {
        "org": "custom_org",
        "region": "custom_region",
        "domain": "custom_domain",
        "product": "custom_product",
        "model": "custom_model",
        "layer": "custom_layer",
    }
    assert actual == expected


def test_builder_should_not_overwrite_transform_taxonomy_when_already_set():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.kind("LinearJob")
        .name("test_job")
        .org("tiozin")
        .region("europe")
        .domain("marketing")
        .product("user_events")
        .model("order_completed")
        .layer("refined")
        .runner({"kind": "NoOpRunner"})
        .inputs({"kind": "NoOpInput", "name": "read_something"})
        .transforms(
            {
                "kind": "NoOpTransform",
                "name": "transform_something",
                "org": "custom_org",
                "region": "custom_region",
                "domain": "custom_domain",
                "product": "custom_product",
                "model": "custom_model",
                "layer": "custom_layer",
            }
        )
        .outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    transform_operator = job.transforms[0]
    actual = {
        "org": transform_operator.org,
        "region": transform_operator.region,
        "domain": transform_operator.domain,
        "product": transform_operator.product,
        "model": transform_operator.model,
        "layer": transform_operator.layer,
    }
    expected = {
        "org": "custom_org",
        "region": "custom_region",
        "domain": "custom_domain",
        "product": "custom_product",
        "model": "custom_model",
        "layer": "custom_layer",
    }
    assert actual == expected


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
