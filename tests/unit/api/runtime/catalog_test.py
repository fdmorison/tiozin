from tiozin.api.runtime.catalog import RunCatalog, RunRecord
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
# RunCatalog.register
# ============================================================================


def test_register_should_return_runtime_record():
    # Arrange
    catalog = RunCatalog()
    step = mock_step()

    # Act
    result = catalog.register(step)

    # Assert
    actual = type(result)
    expected = RunRecord
    assert actual == expected


def test_register_should_store_inputs():
    # Arrange
    catalog = RunCatalog()
    step = mock_step()
    inputs = [mock_dataset("orders"), mock_dataset("customers")]

    # Act
    catalog.register(step, inputs=inputs)

    # Assert
    actual = [d.tiozin_name for d in catalog.get(step).inputs]
    expected = ["orders", "customers"]
    assert actual == expected


def test_register_should_wrap_raw_inputs_as_datasets():
    # Arrange
    catalog = RunCatalog()
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
    catalog = RunCatalog()
    step = mock_step()
    output = mock_dataset("summary")

    # Act
    catalog.register(step, output=output)

    # Assert
    actual = catalog.get(step).output.tiozin_name
    expected = "summary"
    assert actual == expected


def test_register_should_wrap_raw_output_as_dataset():
    # Arrange
    catalog = RunCatalog()
    step = mock_step()

    # Act
    catalog.register(step, output="raw-result")

    # Assert
    actual = type(catalog.get(step).output)
    expected = Dataset
    assert actual == expected


def test_register_should_accumulate_inputs_across_calls():
    # Arrange
    catalog = RunCatalog()
    step = mock_step()

    # Act
    catalog.register(step, inputs=[mock_dataset("orders")])
    catalog.register(step, inputs=[mock_dataset("customers")])

    # Assert
    actual = [d.tiozin_name for d in catalog.get(step).inputs]
    expected = ["orders", "customers"]
    assert actual == expected


def test_register_should_merge_output_on_repeated_calls():
    # Arrange
    catalog = RunCatalog()
    step = mock_step()
    first = Dataset(data=[], namespace="s3://bucket", name="summary")
    second = Dataset(data=[], namespace="s3://other")

    # Act
    catalog.register(step, output=first)
    catalog.register(step, output=second)

    # Assert — first-write-wins: namespace and name from first call are kept
    actual = (
        catalog.get(step).output.tiozin_namespace,
        catalog.get(step).output.tiozin_name,
    )
    expected = ("s3://bucket", "summary")
    assert actual == expected


# ============================================================================
# RunCatalog.get
# ============================================================================


def test_get_should_find_record():
    # Arrange
    catalog = RunCatalog()
    step = mock_step()
    catalog.register(step)

    # Act
    result = catalog.get(step)

    # Assert
    actual = type(result)
    expected = RunRecord
    assert actual == expected


def test_get_should_return_none_when_step_is_not_registered():
    # Arrange
    catalog = RunCatalog()
    step = mock_step()

    # Act
    result = catalog.get(step)

    # Assert
    actual = result
    expected = None
    assert actual == expected


def test_get_should_accept_slug_string():
    # Arrange
    catalog = RunCatalog()
    step = mock_step(name="load orders")
    catalog.register(step)

    # Act
    result = catalog.get("load-orders")

    # Assert
    actual = type(result)
    expected = RunRecord
    assert actual == expected


# ============================================================================
# RunCatalog.get_records
# ============================================================================


def test_get_records_should_return_records_for_all_registered_runtimes():
    # Arrange
    catalog = RunCatalog()
    step1 = mock_step("load orders")
    step2 = mock_step("load customers")
    catalog.register(step1)
    catalog.register(step2)

    # Act
    result = catalog.get_records([step1, step2])

    # Assert
    actual = len(result)
    expected = 2
    assert actual == expected


def test_get_records_should_accept_single_runtime():
    # Arrange
    catalog = RunCatalog()
    step = mock_step()
    catalog.register(step)

    # Act
    result = catalog.get_records(step)

    # Assert
    actual = len(result)
    expected = 1
    assert actual == expected


def test_get_records_should_skip_unregistered_runtimes():
    # Arrange
    catalog = RunCatalog()
    step1 = mock_step("load orders")
    step2 = mock_step("load customers")
    catalog.register(step1)

    # Act
    result = catalog.get_records([step1, step2])

    # Assert
    actual = len(result)
    expected = 1
    assert actual == expected


# ============================================================================
# RunCatalog.get_inputs
# ============================================================================


def test_get_inputs_should_return_all_inputs_across_runtimes():
    # Arrange
    catalog = RunCatalog()
    step1 = mock_step("load orders")
    step2 = mock_step("load customers")
    catalog.register(step1, inputs=[mock_dataset("orders")])
    catalog.register(step2, inputs=[mock_dataset("customers")])

    # Act
    result = catalog.get_inputs([step1, step2])

    # Assert
    actual = [d.tiozin_name for d in result]
    expected = ["orders", "customers"]
    assert actual == expected


def test_get_inputs_should_accept_single_runtime():
    # Arrange
    catalog = RunCatalog()
    step = mock_step()
    catalog.register(step, inputs=[mock_dataset("orders")])

    # Act
    result = catalog.get_inputs(step)

    # Assert
    actual = [d.tiozin_name for d in result]
    expected = ["orders"]
    assert actual == expected


def test_get_inputs_should_return_empty_when_no_inputs_registered():
    # Arrange
    catalog = RunCatalog()
    step = mock_step()
    catalog.register(step)

    # Act
    result = catalog.get_inputs([step])

    # Assert
    actual = result
    expected = []
    assert actual == expected


# ============================================================================
# RunCatalog.get_outputs
# ============================================================================


def test_get_outputs_should_return_outputs_from_runtimes():
    # Arrange
    catalog = RunCatalog()
    step1 = mock_step("transform a")
    step2 = mock_step("transform b")
    catalog.register(step1, output=mock_dataset("result-a"))
    catalog.register(step2, output=mock_dataset("result-b"))

    # Act
    result = catalog.get_outputs([step1, step2])

    # Assert
    actual = [d.tiozin_name for d in result]
    expected = ["result-a", "result-b"]
    assert actual == expected


def test_get_outputs_should_accept_single_runtime():
    # Arrange
    catalog = RunCatalog()
    step = mock_step()
    catalog.register(step, output=mock_dataset("summary"))

    # Act
    result = catalog.get_outputs(step)

    # Assert
    actual = [d.tiozin_name for d in result]
    expected = ["summary"]
    assert actual == expected


def test_get_outputs_should_skip_runtimes_without_output():
    # Arrange
    catalog = RunCatalog()
    step1 = mock_step("load orders")
    step2 = mock_step("transform")
    catalog.register(step1, inputs=[mock_dataset("orders")])
    catalog.register(step2, output=mock_dataset("summary"))

    # Act
    result = catalog.get_outputs([step1, step2])

    # Assert
    actual = [d.tiozin_name for d in result]
    expected = ["summary"]
    assert actual == expected
