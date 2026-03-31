from tiozin.api.runtime.catalog import RuntimeCatalog, StepRecord
from tiozin.api.runtime.dataset import Dataset
from tiozin.family.tio_kernel import NoOpInput


def mock_step(name: str = "test") -> NoOpInput:
    return NoOpInput(
        name=name,
        org="acme",
        region="latam",
        domain="d",
        layer="l",
        product="p",
        model="m",
    )


def mock_dataset(name: str) -> Dataset:
    return Dataset(data=[], namespace="s3://bucket", name=name)


# ============================================================================
# RuntimeCatalog.register
# ============================================================================


def test_register_should_return_step_record():
    # Arrange
    catalog = RuntimeCatalog()
    step = mock_step()

    # Act
    result = catalog.register(step)

    # Assert
    actual = type(result)
    expected = StepRecord
    assert actual == expected


def test_register_should_store_inputs():
    # Arrange
    catalog = RuntimeCatalog()
    step = mock_step()
    inputs = [mock_dataset("orders"), mock_dataset("customers")]

    # Act
    catalog.register(step, inputs=inputs)

    # Assert
    actual = [d.name for d in catalog.get(step).inputs]
    expected = ["orders", "customers"]
    assert actual == expected


def test_register_should_wrap_raw_inputs_as_datasets():
    # Arrange
    catalog = RuntimeCatalog()
    step = mock_step()
    raw = "raw-data"

    # Act
    catalog.register(step, inputs=[raw])

    # Assert
    actual = type(catalog.get(step).inputs[0])
    expected = Dataset
    assert actual == expected


def test_register_should_store_output():
    # Arrange
    catalog = RuntimeCatalog()
    step = mock_step()
    output = mock_dataset("summary")

    # Act
    catalog.register(step, output=output)

    # Assert
    actual = catalog.get(step).output.name
    expected = "summary"
    assert actual == expected


def test_register_should_wrap_raw_output_as_dataset():
    # Arrange
    catalog = RuntimeCatalog()
    step = mock_step()

    # Act
    catalog.register(step, output="raw-result")

    # Assert
    actual = type(catalog.get(step).output)
    expected = Dataset
    assert actual == expected


def test_register_should_accumulate_inputs_across_calls():
    # Arrange
    catalog = RuntimeCatalog()
    step = mock_step()

    # Act
    catalog.register(step, inputs=[mock_dataset("orders")])
    catalog.register(step, inputs=[mock_dataset("customers")])

    # Assert
    actual = [d.name for d in catalog.get(step).inputs]
    expected = ["orders", "customers"]
    assert actual == expected


def test_register_should_merge_output_on_repeated_calls():
    # Arrange
    catalog = RuntimeCatalog()
    step = mock_step()
    first = Dataset(data=[], namespace="s3://bucket", name="summary")
    second = Dataset(data=[], namespace="s3://other")

    # Act
    catalog.register(step, output=first)
    catalog.register(step, output=second)

    # Assert — first-write-wins: namespace and name from first call are kept
    actual = (
        catalog.get(step).output.namespace,
        catalog.get(step).output.name,
    )
    expected = ("s3://bucket", "summary")
    assert actual == expected


# ============================================================================
# RuntimeCatalog.get
# ============================================================================


def test_get_should_find_record():
    # Arrange
    catalog = RuntimeCatalog()
    step = mock_step()
    catalog.register(step)

    # Act
    result = catalog.get(step)

    # Assert
    actual = type(result)
    expected = StepRecord
    assert actual == expected


def test_get_should_return_none_when_step_is_not_registered():
    # Arrange
    catalog = RuntimeCatalog()
    step = mock_step()

    # Act
    result = catalog.get(step)

    # Assert
    actual = result
    expected = None
    assert actual == expected


def test_get_should_accept_slug_string():
    # Arrange
    catalog = RuntimeCatalog()
    step = mock_step(name="load orders")
    catalog.register(step)

    # Act
    result = catalog.get("load-orders")

    # Assert
    actual = type(result)
    expected = StepRecord
    assert actual == expected


# ============================================================================
# RuntimeCatalog.get_all
# ============================================================================


def test_get_all_should_return_records_for_all_registered_steps():
    # Arrange
    catalog = RuntimeCatalog()
    step1 = mock_step("load orders")
    step2 = mock_step("load customers")
    catalog.register(step1)
    catalog.register(step2)

    # Act
    result = catalog.get_all([step1, step2])

    # Assert
    actual = len(result)
    expected = 2
    assert actual == expected


def test_get_all_should_skip_unregistered_steps():
    # Arrange
    catalog = RuntimeCatalog()
    step1 = mock_step("load orders")
    step2 = mock_step("load customers")
    catalog.register(step1)

    # Act
    result = catalog.get_all([step1, step2])

    # Assert
    actual = len(result)
    expected = 1
    assert actual == expected


# ============================================================================
# RuntimeCatalog.get_input_datasets
# ============================================================================


def test_get_input_datasets_should_return_all_inputs_across_steps():
    # Arrange
    catalog = RuntimeCatalog()
    step1 = mock_step("load orders")
    step2 = mock_step("load customers")
    catalog.register(step1, inputs=[mock_dataset("orders")])
    catalog.register(step2, inputs=[mock_dataset("customers")])

    # Act
    result = catalog.get_input_datasets([step1, step2])

    # Assert
    actual = [d.name for d in result]
    expected = ["orders", "customers"]
    assert actual == expected


def test_get_input_datasets_should_return_empty_when_no_inputs_registered():
    # Arrange
    catalog = RuntimeCatalog()
    step = mock_step()
    catalog.register(step)

    # Act
    result = catalog.get_input_datasets([step])

    # Assert
    actual = result
    expected = []
    assert actual == expected


# ============================================================================
# RuntimeCatalog.get_output_datasets
# ============================================================================


def test_get_output_datasets_should_return_outputs_from_steps():
    # Arrange
    catalog = RuntimeCatalog()
    step1 = mock_step("transform a")
    step2 = mock_step("transform b")
    catalog.register(step1, output=mock_dataset("result-a"))
    catalog.register(step2, output=mock_dataset("result-b"))

    # Act
    result = catalog.get_output_datasets([step1, step2])

    # Assert
    actual = [d.name for d in result]
    expected = ["result-a", "result-b"]
    assert actual == expected


def test_get_output_datasets_should_skip_steps_without_output():
    # Arrange
    catalog = RuntimeCatalog()
    step1 = mock_step("load orders")
    step2 = mock_step("transform")
    catalog.register(step1, inputs=[mock_dataset("orders")])
    catalog.register(step2, output=mock_dataset("summary"))

    # Act
    result = catalog.get_output_datasets([step1, step2])

    # Assert
    actual = [d.name for d in result]
    expected = ["summary"]
    assert actual == expected
