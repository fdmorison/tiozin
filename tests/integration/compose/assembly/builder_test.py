import pytest

from tiozin.api import JobManifest
from tiozin.api.metadata.job_manifest import (
    InputManifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)
from tiozin.compose import JobBuilder
from tiozin.exceptions import InvalidInputError, TiozinUnexpectedError
from tiozin.family.tio_kernel import LinearJob, NoOpInput, NoOpOutput, NoOpRunner, NoOpTransform

TEST_TAXONOMY = {
    "org": "tiozin",
    "region": "latam",
    "domain": "quality",
    "subdomain": "pipeline",
    "layer": "test",
    "product": "test_cases",
    "model": "some_case",
    "description": "test",
}


def test_builder_should_accept_job_manifest():
    # Arrange
    manifest = JobManifest(
        kind="LinearJob",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        layer="test",
        product="test_cases",
        model="some_case",
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


def test_builder_should_accept_plugin_dicts():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.with_kind("LinearJob")
        .with_name("test_job")
        .with_org("tiozin")
        .with_region("latam")
        .with_domain("quality")
        .with_subdomain("pipeline")
        .with_layer("test")
        .with_product("test_cases")
        .with_model("some_case")
        .with_runner(
            {
                "kind": "NoOpRunner",
            }
        )
        .with_inputs(
            {
                "kind": "NoOpInput",
                "name": "read_something",
            }
        )
        .with_transforms(
            {
                "kind": "NoOpTransform",
                "name": "transform_something",
            }
        )
        .with_outputs(
            {
                "kind": "NoOpOutput",
                "name": "write_something",
            }
        )
        .build()
    )

    # Assert
    assert isinstance(job, LinearJob)


def test_builder_should_accept_plugin_manifests():
    # Arrange
    builder = JobBuilder()

    # Act
    (
        builder.with_kind("LinearJob")
        .with_name("test_job")
        .with_org("tiozin")
        .with_region("latam")
        .with_domain("quality")
        .with_subdomain("pipeline")
        .with_layer("test")
        .with_product("test_cases")
        .with_model("some_case")
        .with_runner(
            RunnerManifest(kind="NoOpRunner"),
        )
        .with_inputs(
            InputManifest(kind="NoOpInput", name="read_something"),
        )
        .with_transforms(
            TransformManifest(kind="NoOpTransform", name="transform_something"),
        )
        .with_outputs(
            OutputManifest(kind="NoOpOutput", name="write_something"),
        )
        .build()
    )

    # Assert
    assert True


def test_builder_should_accept_plugin_objects():
    # Arrange
    builder = JobBuilder()

    # Act
    (
        builder.with_kind("LinearJob")
        .with_name("test_job")
        .with_org("tiozin")
        .with_region("latam")
        .with_domain("quality")
        .with_subdomain("pipeline")
        .with_layer("test")
        .with_product("test_cases")
        .with_model("some_case")
        .with_runner(
            NoOpRunner(),
        )
        .with_inputs(
            NoOpInput(name="read_something", **TEST_TAXONOMY),
        )
        .with_transforms(
            NoOpTransform(name="transform_something", **TEST_TAXONOMY),
        )
        .with_outputs(
            NoOpOutput(name="write_something", **TEST_TAXONOMY),
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
        builder.with_kind("LinearJob")
        .with_name("test_job")
        .with_org("tiozin")
        .with_region("latam")
        .with_domain("quality")
        .with_subdomain("pipeline")
        .with_layer("test")
        .with_product("test_cases")
        .with_model("some_case")
        .with_runner({"kind": "NoOpRunner"})
        .with_inputs(
            {"kind": "NoOpInput", "name": "input1"},
            {"kind": "NoOpInput", "name": "input2"},
        )
        .with_outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    assert len(job.inputs) == 2


def test_builder_should_accept_multiple_transforms():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.with_kind("LinearJob")
        .with_name("test_job")
        .with_org("tiozin")
        .with_region("latam")
        .with_domain("quality")
        .with_subdomain("pipeline")
        .with_layer("test")
        .with_product("test_cases")
        .with_model("some_case")
        .with_runner({"kind": "NoOpRunner"})
        .with_inputs({"kind": "NoOpInput", "name": "read_something"})
        .with_transforms(
            {"kind": "NoOpTransform", "name": "transform1"},
            {"kind": "NoOpTransform", "name": "transform2"},
        )
        .with_outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    assert len(job.transforms) == 2


def test_builder_should_accept_multiple_outputs():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.with_kind("LinearJob")
        .with_name("test_job")
        .with_org("tiozin")
        .with_region("latam")
        .with_domain("quality")
        .with_subdomain("pipeline")
        .with_layer("test")
        .with_product("test_cases")
        .with_model("some_case")
        .with_runner({"kind": "NoOpRunner"})
        .with_inputs({"kind": "NoOpInput", "name": "read_something"})
        .with_outputs(
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
        builder.with_kind("LinearJob")
        .with_name("test_job")
        .with_org("tiozin")
        .with_region("latam")
        .with_domain("quality")
        .with_subdomain("pipeline")
        .with_layer("test")
        .with_product("test_cases")
        .with_model("some_case")
        .with_label("env", "dev")
        .with_label("team", "data")
        .with_runner({"kind": "NoOpRunner"})
        .with_inputs({"kind": "NoOpInput", "name": "read_something"})
        .with_outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    assert job.labels == {"env": "dev", "team": "data"}


def test_builder_should_set_labels_dict():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.with_kind("LinearJob")
        .with_name("test_job")
        .with_org("tiozin")
        .with_region("latam")
        .with_domain("quality")
        .with_subdomain("pipeline")
        .with_layer("test")
        .with_product("test_cases")
        .with_model("some_case")
        .with_labels({"env": "dev", "team": "data"})
        .with_runner({"kind": "NoOpRunner"})
        .with_inputs({"kind": "NoOpInput", "name": "read_something"})
        .with_outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    assert job.labels == {"env": "dev", "team": "data"}


def test_builder_should_set_optional_fields():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.with_kind("LinearJob")
        .with_name("test_job")
        .with_description("A test job")
        .with_owner("team-data")
        .with_maintainer("team-platform")
        .with_cost_center("engineering")
        .with_org("tiozin")
        .with_region("latam")
        .with_domain("quality")
        .with_subdomain("pipeline")
        .with_layer("test")
        .with_product("test_cases")
        .with_model("some_case")
        .with_runner({"kind": "NoOpRunner"})
        .with_inputs({"kind": "NoOpInput", "name": "read_something"})
        .with_outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    actual = (job.description, job.owner, job.maintainer, job.cost_center)
    expected = ("A test job", "team-data", "team-platform", "engineering")
    assert actual == expected


def test_builder_should_handle_unplanned_fields():
    # Arrange
    builder = JobBuilder()

    # Act
    (
        builder.with_kind("LinearJob")
        .with_name("test_job")
        .with_org("tiozin")
        .with_region("latam")
        .with_domain("quality")
        .with_subdomain("pipeline")
        .with_layer("test")
        .with_product("test_cases")
        .with_model("some_case")
        .with_runner({"kind": "NoOpRunner"})
        .with_inputs({"kind": "NoOpInput", "name": "read_something"})
        .with_outputs({"kind": "NoOpOutput", "name": "write_something"})
        .with_field("custom_field", "custom_value")
        .build()
    )

    # Assert
    assert True


def test_builder_should_reject_invalid_runner_type():
    # Arrange
    builder = JobBuilder()

    # Act & Assert
    with pytest.raises(InvalidInputError, match="Invalid runner definition"):
        builder.with_runner(12345)


def test_builder_should_reject_invalid_input_type():
    # Arrange
    builder = JobBuilder()

    # Act & Assert
    with pytest.raises(InvalidInputError, match="Invalid input definition"):
        builder.with_inputs("invalid")


def test_builder_should_reject_invalid_transform_type():
    # Arrange
    builder = JobBuilder()

    # Act & Assert
    with pytest.raises(InvalidInputError, match="Invalid transform definition"):
        builder.with_transforms(12345)


def test_builder_should_reject_invalid_output_type():
    # Arrange
    builder = JobBuilder()

    # Act & Assert
    with pytest.raises(InvalidInputError, match="Invalid output definition"):
        builder.with_outputs(None)


def test_builder_should_propagate_taxonomy_to_inputs():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.with_kind("LinearJob")
        .with_name("test_job")
        .with_org("tiozin")
        .with_region("europe")
        .with_domain("marketing")
        .with_subdomain("analytics")
        .with_layer("refined")
        .with_product("user_events")
        .with_model("order_completed")
        .with_runner({"kind": "NoOpRunner"})
        .with_inputs({"kind": "NoOpInput", "name": "read_something"})
        .with_outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    input_operator = job.inputs[0]
    actual = {
        "org": input_operator.org,
        "region": input_operator.region,
        "domain": input_operator.domain,
        "subdomain": input_operator.subdomain,
        "layer": input_operator.layer,
        "product": input_operator.product,
        "model": input_operator.model,
    }
    expected = {
        "org": "tiozin",
        "region": "europe",
        "domain": "marketing",
        "subdomain": "analytics",
        "layer": "refined",
        "product": "user_events",
        "model": "order_completed",
    }
    assert actual == expected


def test_builder_should_propagate_taxonomy_to_outputs():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.with_kind("LinearJob")
        .with_name("test_job")
        .with_org("tiozin")
        .with_region("europe")
        .with_domain("marketing")
        .with_subdomain("analytics")
        .with_layer("refined")
        .with_product("user_events")
        .with_model("order_completed")
        .with_runner({"kind": "NoOpRunner"})
        .with_inputs({"kind": "NoOpInput", "name": "read_something"})
        .with_outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    output_operator = job.outputs[0]
    actual = {
        "org": output_operator.org,
        "region": output_operator.region,
        "domain": output_operator.domain,
        "subdomain": output_operator.subdomain,
        "layer": output_operator.layer,
        "product": output_operator.product,
        "model": output_operator.model,
    }
    expected = {
        "org": "tiozin",
        "region": "europe",
        "domain": "marketing",
        "subdomain": "analytics",
        "layer": "refined",
        "product": "user_events",
        "model": "order_completed",
    }
    assert actual == expected


def test_builder_should_propagate_taxonomy_to_transforms():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.with_kind("LinearJob")
        .with_name("test_job")
        .with_org("tiozin")
        .with_region("europe")
        .with_domain("marketing")
        .with_subdomain("analytics")
        .with_layer("refined")
        .with_product("user_events")
        .with_model("order_completed")
        .with_runner({"kind": "NoOpRunner"})
        .with_inputs({"kind": "NoOpInput", "name": "read_something"})
        .with_transforms({"kind": "NoOpTransform", "name": "transform_something"})
        .with_outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    transform_operator = job.transforms[0]
    actual = {
        "org": transform_operator.org,
        "region": transform_operator.region,
        "domain": transform_operator.domain,
        "subdomain": transform_operator.subdomain,
        "layer": transform_operator.layer,
        "product": transform_operator.product,
        "model": transform_operator.model,
    }
    expected = {
        "org": "tiozin",
        "region": "europe",
        "domain": "marketing",
        "subdomain": "analytics",
        "layer": "refined",
        "product": "user_events",
        "model": "order_completed",
    }
    assert actual == expected


def test_builder_should_not_overwrite_input_taxonomy_when_already_set():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.with_kind("LinearJob")
        .with_name("test_job")
        .with_org("tiozin")
        .with_region("europe")
        .with_domain("marketing")
        .with_subdomain("analytics")
        .with_layer("refined")
        .with_product("user_events")
        .with_model("order_completed")
        .with_runner({"kind": "NoOpRunner"})
        .with_inputs(
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
        .with_outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    input_operator = job.inputs[0]
    actual = {
        "org": input_operator.org,
        "region": input_operator.region,
        "domain": input_operator.domain,
        "subdomain": input_operator.subdomain,
        "layer": input_operator.layer,
        "product": input_operator.product,
        "model": input_operator.model,
    }
    expected = {
        "org": "custom_org",
        "region": "custom_region",
        "domain": "custom_domain",
        "subdomain": "analytics",
        "layer": "custom_layer",
        "product": "custom_product",
        "model": "custom_model",
    }
    assert actual == expected


def test_builder_should_not_overwrite_output_taxonomy_when_already_set():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.with_kind("LinearJob")
        .with_name("test_job")
        .with_org("tiozin")
        .with_region("europe")
        .with_domain("marketing")
        .with_subdomain("analytics")
        .with_layer("refined")
        .with_product("user_events")
        .with_model("order_completed")
        .with_runner({"kind": "NoOpRunner"})
        .with_inputs({"kind": "NoOpInput", "name": "read_something"})
        .with_outputs(
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
        "subdomain": output_operator.subdomain,
        "layer": output_operator.layer,
        "product": output_operator.product,
        "model": output_operator.model,
    }
    expected = {
        "org": "custom_org",
        "region": "custom_region",
        "domain": "custom_domain",
        "subdomain": "analytics",
        "layer": "custom_layer",
        "product": "custom_product",
        "model": "custom_model",
    }
    assert actual == expected


def test_builder_should_not_overwrite_transform_taxonomy_when_already_set():
    # Arrange
    builder = JobBuilder()

    # Act
    job = (
        builder.with_kind("LinearJob")
        .with_name("test_job")
        .with_org("tiozin")
        .with_region("europe")
        .with_domain("marketing")
        .with_subdomain("analytics")
        .with_layer("refined")
        .with_product("user_events")
        .with_model("order_completed")
        .with_runner({"kind": "NoOpRunner"})
        .with_inputs({"kind": "NoOpInput", "name": "read_something"})
        .with_transforms(
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
        .with_outputs({"kind": "NoOpOutput", "name": "write_something"})
        .build()
    )

    # Assert
    transform_operator = job.transforms[0]
    actual = {
        "org": transform_operator.org,
        "region": transform_operator.region,
        "domain": transform_operator.domain,
        "subdomain": transform_operator.subdomain,
        "layer": transform_operator.layer,
        "product": transform_operator.product,
        "model": transform_operator.model,
    }
    expected = {
        "org": "custom_org",
        "region": "custom_region",
        "domain": "custom_domain",
        "subdomain": "analytics",
        "layer": "custom_layer",
        "product": "custom_product",
        "model": "custom_model",
    }
    assert actual == expected


def test_builder_should_fail_when_used_twice():
    # Arrange
    builder = (
        JobBuilder()
        .with_kind("LinearJob")
        .with_name("test_job")
        .with_org("tiozin")
        .with_region("latam")
        .with_domain("quality")
        .with_subdomain("pipeline")
        .with_layer("test")
        .with_product("test_cases")
        .with_model("some_case")
        .with_runner({"kind": "NoOpRunner"})
        .with_inputs({"kind": "NoOpInput", "name": "read_something"})
        .with_outputs({"kind": "NoOpOutput", "name": "write_something"})
    )

    # Act/Assert
    with pytest.raises(TiozinUnexpectedError, match="can only be used once"):
        builder.build()
        builder.build()
