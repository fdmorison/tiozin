from tiozin.api.metadata.schema.model import TimestampOptions


def test_timestamp_options_should_default_to_spec_values():
    # Act
    result = TimestampOptions()

    # Assert
    actual = result.model_dump()
    expected = {
        "format": None,
        "minimum": None,
        "exclusiveMinimum": None,
        "maximum": None,
        "exclusiveMaximum": None,
        "timezone": None,
        "defaultTimezone": "Etc/UTC",
    }
    assert actual == expected
