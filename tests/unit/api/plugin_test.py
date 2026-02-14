from tiozin.family.tio_kernel import NoOpInput


# ============================================================================
# Testing PlugIn.to_dict
# ============================================================================
def test_to_dict_should_return_all_attributes():
    # Arrange
    plugin = NoOpInput(
        name="test_input",
        description="A test input",
        org="acme",
        region="latam",
        domain="sales",
        layer="raw",
        product="orders",
        model="transactions",
    )

    # Act
    result = plugin.to_dict()

    # Assert
    actual = result.keys()
    expected = plugin.__dict__.keys()
    assert actual == expected


def test_to_dict_should_exclude_fields_when_requested():
    # Arrange
    plugin = NoOpInput(
        name="test_input",
        org="acme",
        region="latam",
        domain="sales",
        layer="raw",
        product="orders",
        model="transactions",
    )

    # Act
    result = plugin.to_dict(exclude={"name", "org"})

    # Assert
    actual = ("name" not in result, "org" not in result)
    expected = (True, True)
    assert actual == expected


def test_to_dict_should_include_none_by_default():
    # Arrange
    plugin = NoOpInput(
        name="test_input",
        description=None,
        org="acme",
        region="latam",
        domain="sales",
        layer="raw",
        product="orders",
        model="transactions",
    )

    # Act
    result = plugin.to_dict()

    # Assert
    assert "description" in result


def test_to_dict_should_exclude_none_when_requested():
    # Arrange
    plugin = NoOpInput(
        name="test_input",
        description=None,
        org="acme",
        region="latam",
        domain="sales",
        layer="raw",
        product="orders",
        model="transactions",
    )

    # Act
    result = plugin.to_dict(exclude_none=True)

    # Assert
    assert None not in result.values()


def test_to_dict_should_apply_both_filters_when_requested():
    # Arrange
    plugin = NoOpInput(
        name="test_input",
        description=None,
        org="acme",
        region="latam",
        domain="sales",
        layer="raw",
        product="orders",
        model="transactions",
    )

    # Act
    result = plugin.to_dict(
        exclude={"org", "region"},
        exclude_none=True,
    )

    # Assert
    actual = ("org" not in result, "region" not in result, "description" not in result)
    expected = (True, True, True)
    assert actual == expected


def test_to_dict_should_return_new_dict_each_call():
    # Arrange
    plugin = NoOpInput(
        name="test_input",
        org="acme",
        region="latam",
        domain="sales",
        layer="raw",
        product="orders",
        model="transactions",
    )

    # Act
    result1 = plugin.to_dict()
    result2 = plugin.to_dict()

    # Assert
    assert result1 is not result2
