from unittest.mock import MagicMock

import pytest

from tiozin import Dataset
from tiozin.api.metadata.schema.model import Schema
from tiozin.exceptions import RequiredArgumentError

# ============================================================================
# Dataset.__init__ — data validation
# ============================================================================


def test_dataset_should_raise_when_data_is_none():
    # Act / Assert
    with pytest.raises(RequiredArgumentError):
        Dataset(data=None)


def test_dataset_should_accept_empty_list_as_data():
    # Act
    result = Dataset(data=[])

    # Assert
    actual = result.tiozin_data
    expected = []
    assert actual == expected


def test_dataset_should_accept_zero_as_data():
    # Act
    result = Dataset(data=0)

    # Assert
    actual = result.tiozin_data
    expected = 0
    assert actual == expected


def test_dataset_should_accept_empty_string_as_data():
    # Act
    result = Dataset(data="")

    # Assert
    actual = result.tiozin_data
    expected = ""
    assert actual == expected


# ============================================================================
# Dataset.wrap — factory
# ============================================================================


def test_wrap_should_raise_when_given_none():
    # Act / Assert
    with pytest.raises(RequiredArgumentError):
        Dataset.wrap(None)


def test_wrap_should_return_self_when_already_a_dataset():
    # Arrange
    dataset = Dataset(data="df", namespace="s3://bucket", name="path/file")

    # Act
    result = Dataset.wrap(dataset)

    # Assert
    assert result is dataset


def test_wrap_should_create_dataset_when_given_plain_object():
    # Arrange
    df = object()

    # Act
    result = Dataset.wrap(df)

    # Assert
    actual = (
        type(result).__name__,
        result.tiozin_data is df,
    )
    expected = (
        "Dataset",
        True,
    )
    assert actual == expected


# ============================================================================
# Dataset — proxy transparency
# ============================================================================


def test_dataset_should_delegate_str_to_wrapped_object():
    # Arrange
    class Describable:
        def __str__(self) -> str:
            return "describable-object"

    dataset = Dataset(data=Describable())

    # Act
    result = str(dataset)

    # Assert
    actual = result
    expected = "describable-object"
    assert actual == expected


def test_dataset_should_delegate_attribute_access_to_wrapped_object():
    # Arrange
    class DataFrameLike:
        columns = ["id", "name"]

    dataset = Dataset(data=DataFrameLike())

    # Act
    result = dataset.columns

    # Assert
    actual = result
    expected = ["id", "name"]
    assert actual == expected


def test_dataset_should_proxy_list_operations():
    # Arrange
    data = [1, 2, 3]
    dataset = Dataset(data=data)

    # Act
    dataset.append(4)

    # Assert
    actual = list(dataset)
    expected = [1, 2, 3, 4]
    assert actual == expected


def test_dataset_should_proxy_dict_operations():
    # Arrange
    data = {"id": 1, "name": "orders"}
    dataset = Dataset(data=data)

    # Act
    result = list(dataset.items())

    # Assert
    actual = result
    expected = [("id", 1), ("name", "orders")]
    assert actual == expected


def test_dataset_should_proxy_str_operations():
    # Arrange
    data = "raw-data"
    dataset = Dataset(data=data)

    # Act
    result = dataset.upper()

    # Assert
    actual = result
    expected = "RAW-DATA"
    assert actual == expected


# ============================================================================
# Dataset.__repr__
# ============================================================================


def test_repr_should_include_namespace_and_name():
    # Arrange
    dataset = Dataset(data="stub", namespace="s3://bucket", name="data/orders")

    # Act
    result = repr(dataset)

    # Assert
    actual = (
        "namespace=s3://bucket" in result,
        "name=data/orders" in result,
    )
    expected = (True, True)
    assert actual == expected


# ============================================================================
# Dataset — enrichment (first-write-wins)
# ============================================================================


def test_with_namespace_should_set_namespace_when_unset():
    # Arrange
    dataset = Dataset(data="stub")

    # Act
    result = dataset.with_namespace("s3://bucket")

    # Assert
    actual = result.tiozin_namespace
    expected = "s3://bucket"
    assert actual == expected


def test_with_namespace_should_not_overwrite_existing_namespace():
    # Arrange
    dataset = Dataset(data="stub", namespace="s3://original")

    # Act
    result = dataset.with_namespace("s3://other")

    # Assert
    actual = result.tiozin_namespace
    expected = "s3://original"
    assert actual == expected


def test_with_name_should_set_name_when_unset():
    # Arrange
    dataset = Dataset(data="stub")

    # Act
    result = dataset.with_name("data/orders")

    # Assert
    actual = result.tiozin_name
    expected = "data/orders"
    assert actual == expected


def test_with_name_should_not_overwrite_existing_name():
    # Arrange
    dataset = Dataset(data="stub", name="data/original")

    # Act
    result = dataset.with_name("data/other")

    # Assert
    actual = result.tiozin_name
    expected = "data/original"
    assert actual == expected


def test_with_methods_should_be_chainable():
    # Arrange
    dataset = Dataset(data="stub")

    # Act
    result = dataset.with_namespace("s3://bucket").with_name("data/orders")

    # Assert
    actual = (result.tiozin_namespace, result.tiozin_name)
    expected = ("s3://bucket", "data/orders")
    assert actual == expected


# ============================================================================
# Dataset.merge
# ============================================================================


def test_merge_should_enrich_with_other_dataset_values():
    # Arrange
    schema = MagicMock(spec=Schema)
    target = Dataset(data="stub")
    source = Dataset(data="stub", namespace="s3://bucket", name="data/orders", schema=schema)

    # Act
    result = target.merge(source)

    # Assert
    actual = (result.tiozin_namespace, result.tiozin_name, result.tiozin_schema)
    expected = ("s3://bucket", "data/orders", schema)
    assert actual == expected


def test_merge_should_not_overwrite_existing_values():
    # Arrange
    source_schema = MagicMock(spec=Schema)
    other_schema = MagicMock(spec=Schema)
    target = Dataset(data="stub", namespace="s3://source", name="data/source", schema=source_schema)
    source = Dataset(data="stub", namespace="s3://other", name="data/other", schema=other_schema)

    # Act
    result = target.merge(source)

    # Assert
    actual = (result.tiozin_namespace, result.tiozin_name, result.tiozin_schema)
    expected = ("s3://source", "data/source", source_schema)
    assert actual == expected


def test_merge_should_be_safe_when_other_is_none():
    # Arrange
    target = Dataset(data="stub", namespace="s3://bucket", name="data/orders")

    # Act
    result = target.merge(None)

    # Assert
    actual = (result.tiozin_namespace, result.tiozin_name)
    expected = ("s3://bucket", "data/orders")
    assert actual == expected


def test_merge_should_return_self():
    # Arrange
    dataset = Dataset(data="stub")
    other = Dataset(data="stub", namespace="s3://bucket", name="data/orders")

    # Act
    result = dataset.merge(other)

    # Assert
    assert result is dataset


# ============================================================================
# Dataset.from_uri — factory
# ============================================================================


@pytest.mark.parametrize(
    "uri, expected_namespace, expected_name",
    [
        ("s3://my-bucket/data/file.parquet", "s3://my-bucket", "data/file.parquet"),
        ("gs://my-bucket/data/file.parquet", "gs://my-bucket", "data/file.parquet"),
        ("az://my-container/data/file.parquet", "az://my-container", "data/file.parquet"),
    ],
)
def test_from_uri_should_split_object_storage_into_bucket_and_path(
    uri: str, expected_namespace: str, expected_name: str
):
    # Act
    result = Dataset.from_uri(uri)

    # Assert
    actual = (result.tiozin_namespace, result.tiozin_name)
    expected = (expected_namespace, expected_name)
    assert actual == expected


@pytest.mark.parametrize(
    "uri, expected_namespace",
    [
        ("http://example.com/data/file.csv", "http://example.com"),
        ("https://example.com/data/file.csv", "https://example.com"),
    ],
)
def test_from_uri_should_split_http_into_host_namespace_and_path_name(
    uri: str, expected_namespace: str
):
    # Act
    result = Dataset.from_uri(uri)

    # Assert
    actual = (result.tiozin_namespace, result.tiozin_name)
    expected = (
        expected_namespace,
        "data/file.csv",
    )
    assert actual == expected


def test_from_uri_should_split_file_into_file_namespace_and_path():
    # Act
    result = Dataset.from_uri("file:///data/warehouse/file.parquet")

    # Assert
    actual = (result.tiozin_namespace, result.tiozin_name)
    expected = (
        "file",
        "data/warehouse/file.parquet",
    )
    assert actual == expected


def test_from_uri_should_keep_relative_path_as_is_when_no_scheme():
    # Act
    result = Dataset.from_uri("data/lake/customers.parquet")

    # Assert
    actual = (result.tiozin_namespace, result.tiozin_name)
    expected = (
        "file",
        "data/lake/customers.parquet",
    )
    assert actual == expected


@pytest.mark.parametrize(
    "uri, expected_namespace, expected_name",
    [
        ("s3://my-bucket/data/orders/", "s3://my-bucket", "data/orders"),
        (".output/lake-ecommerce-raw/orders/", "file", ".output/lake-ecommerce-raw/orders"),
    ],
    ids=["object-storage-trailing-slash", "relative-path-trailing-slash"],
)
def test_from_uri_should_strip_trailing_slash_from_name(
    uri: str, expected_namespace: str, expected_name: str
):
    # Act
    result = Dataset.from_uri(uri)

    # Assert
    actual = (result.tiozin_namespace, result.tiozin_name)
    expected = (
        expected_namespace,
        expected_name,
    )
    assert actual == expected
