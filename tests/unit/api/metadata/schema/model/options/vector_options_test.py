from tiozin.api.metadata.schema.model import (
    DistanceMetric,
    VectorElementType,
    VectorOptions,
)


def test_vector_options_should_default_to_spec_values():
    # Act
    result = VectorOptions()

    # Assert
    actual = result.model_dump()
    expected = {
        "dimensions": None,
        "elementType": "float32",
        "distanceMetric": None,
        "embeddingModel": None,
        "embeddingModelVersion": None,
        "normalized": False,
    }
    assert actual == expected


def test_vector_options_should_write_element_type_member_as_text():
    # Act
    result = VectorOptions(elementType=VectorElementType.INT8)

    # Assert
    actual = result.to_yaml()
    expected = "elementType: int8\n"
    assert actual == expected


def test_vector_options_should_write_distance_metric_member_as_text():
    # Act
    result = VectorOptions(distanceMetric=DistanceMetric.COSINE)

    # Assert
    actual = result.to_yaml()
    expected = "distanceMetric: cosine\n"
    assert actual == expected
