from tiozin.api.metadata.schema.model import VectorOptions


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
