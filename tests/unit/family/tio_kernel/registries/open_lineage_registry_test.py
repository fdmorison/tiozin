import pytest
from openlineage.client.generated.parent_run import ParentRunFacet

from tests.mocks.lineage.run_event import job_start_event, step_start_event
from tiozin import LineageDataset, LineageRunEvent, config
from tiozin.family.tio_kernel import OpenLineageRegistry


@pytest.fixture()
def registry() -> OpenLineageRegistry:
    return OpenLineageRegistry(location="http://localhost:5000").__wrapped__


# ============================================================================
# Constructor defaults
# ============================================================================


def test_registry_should_default_location_to_none():
    # Act
    registry = OpenLineageRegistry().__wrapped__

    # Assert
    actual = registry.location
    expected = None
    assert actual == expected


def test_registry_should_default_verify_to_true():
    # Act
    registry = OpenLineageRegistry().__wrapped__

    # Assert
    actual = registry.verify
    expected = True
    assert actual == expected


def test_registry_should_default_api_key_to_none():
    # Act
    registry = OpenLineageRegistry().__wrapped__

    # Assert
    actual = registry.api_key
    expected = None
    assert actual == expected


def test_registry_should_default_timeout_from_config():
    # Act
    registry = OpenLineageRegistry().__wrapped__

    # Assert
    actual = registry.timeout
    expected = config.registry_default_timeout
    assert actual == expected


def test_registry_should_default_readonly_from_config():
    # Act
    registry = OpenLineageRegistry().__wrapped__

    # Assert
    actual = registry.readonly
    expected = config.registry_default_readonly
    assert actual == expected


def test_registry_should_default_cache_from_config():
    # Act
    registry = OpenLineageRegistry().__wrapped__

    # Assert
    actual = registry.cache
    expected = config.registry_default_cache
    assert actual == expected


# ============================================================================
# _build_run_event — run fields
# ============================================================================


def test_build_run_event_should_map_run_fields(registry: OpenLineageRegistry):
    # Arrange
    event = job_start_event

    # Act
    result = registry._build_run_event(event)

    # Assert
    actual = (
        result.eventType,
        result.eventTime,
        result.producer,
    )
    expected = (
        LineageRunEvent.START,
        "2024-01-01T00:00:00.000+00:00",
        "tiozin/test",
    )
    assert actual == expected


def test_build_run_event_should_strip_job_run_id_prefix(registry: OpenLineageRegistry):
    # Arrange
    event = job_start_event

    # Act
    result = registry._build_run_event(event)

    # Assert
    actual = result.run.runId
    expected = "018f1a2b-3c4d-7e8f-9a0b-1c2d3e4f5a6b"
    assert actual == expected


def test_build_run_event_should_strip_step_run_id_prefix(registry: OpenLineageRegistry):
    # Arrange
    event = step_start_event

    # Act
    result = registry._build_run_event(event)

    # Assert
    actual = result.run.runId
    expected = "aabbccdd-eeff-0011-2233-445566778899"
    assert actual == expected


# ============================================================================
# _build_run_event — job facets
# ============================================================================


def test_build_run_event_should_map_job_fields(registry: OpenLineageRegistry):
    # Arrange
    event = job_start_event

    # Act
    result = registry._build_run_event(event)

    # Assert
    actual = (
        result.job.namespace,
        result.job.name,
    )
    expected = (
        "acme.latam.ecommerce.checkout",
        "test_job",
    )
    assert actual == expected


def test_build_run_event_should_include_job_type_facet(registry: OpenLineageRegistry):
    # Arrange
    event = job_start_event

    # Act
    result = registry._build_run_event(event)

    # Assert
    job_type_facet = result.job.facets["jobType"]
    actual = (
        job_type_facet.jobType,
        job_type_facet.processingType,
        job_type_facet.integration,
    )
    expected = (
        "JOB",
        "BATCH",
        "test_runner",
    )
    assert actual == expected


# ============================================================================
# _build_run_event — parent facet
# ============================================================================


def test_build_run_event_should_omit_parent_facet_when_no_parent(registry: OpenLineageRegistry):
    # Arrange
    event = job_start_event

    # Act
    result = registry._build_run_event(event)

    # Assert
    actual = "parent" in result.run.facets
    expected = False
    assert actual == expected


def test_build_run_event_should_include_parent_facet_when_parent_set(registry: OpenLineageRegistry):
    # Arrange
    event = step_start_event

    # Act
    result = registry._build_run_event(event)

    # Assert
    parent_facet: ParentRunFacet = result.run.facets["parent"]
    actual = (
        parent_facet.run.runId,
        parent_facet.job.name,
        parent_facet.job.namespace,
    )
    expected = (
        "018f1a2b-3c4d-7e8f-9a0b-1c2d3e4f5a6b",
        "test_job",
        "acme.latam.ecommerce.checkout",
    )
    assert actual == expected


def test_build_run_event_should_strip_parent_run_id_prefix(registry: OpenLineageRegistry):
    # Arrange
    event = step_start_event

    # Act
    result = registry._build_run_event(event)

    # Assert
    actual = result.run.facets["parent"].run.runId
    expected = "018f1a2b-3c4d-7e8f-9a0b-1c2d3e4f5a6b"
    assert actual == expected


# ============================================================================
# _build_run_event — tags facet
# ============================================================================


def test_build_run_event_should_map_tags(registry: OpenLineageRegistry):
    # Arrange
    event = job_start_event

    # Act
    result = registry._build_run_event(event)

    # Assert
    tags_facet = result.run.facets["tags"]
    actual = {f.key: f.value for f in tags_facet.tags}
    expected = {"org": "acme", "layer": "raw"}
    assert actual == expected


# ============================================================================
# _build_run_event — datasets
# ============================================================================


def test_build_run_event_should_map_input_datasets(registry: OpenLineageRegistry):
    # Arrange
    event = job_start_event.model_copy(
        update={
            "inputs": [
                LineageDataset(namespace="acme.latam.ecommerce.checkout", name="sales.orders"),
                LineageDataset(namespace="acme.latam.ecommerce.checkout", name="sales.customers"),
            ],
        }
    )

    # Act
    result = registry._build_run_event(event)

    # Assert
    actual = [(d.namespace, d.name) for d in result.inputs]
    expected = [
        ("acme.latam.ecommerce.checkout", "sales.orders"),
        ("acme.latam.ecommerce.checkout", "sales.customers"),
    ]
    assert actual == expected


def test_build_run_event_should_map_output_datasets(registry: OpenLineageRegistry):
    # Arrange
    event = job_start_event.model_copy(
        update={
            "outputs": [
                LineageDataset(namespace="acme.latam.ecommerce.checkout", name="sales.summary"),
            ],
        }
    )

    # Act
    result = registry._build_run_event(event)

    # Assert
    actual = [(d.namespace, d.name) for d in result.outputs]
    expected = [
        ("acme.latam.ecommerce.checkout", "sales.summary"),
    ]
    assert actual == expected


def test_build_run_event_should_default_datasets_to_empty(registry: OpenLineageRegistry):
    # Arrange
    event = job_start_event

    # Act
    result = registry._build_run_event(event)

    # Assert
    actual = (result.inputs, result.outputs)
    expected = ([], [])
    assert actual == expected
