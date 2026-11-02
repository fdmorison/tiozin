import pytest

from tiozin import OutputMetrics


# ============================================================================
# Testing OutputMetrics - Values
# ============================================================================
def test_metrics_should_convert_numeric_strings_to_integers():
    # Act
    result = OutputMetrics(
        dataset="iceberg.default.sales",
        rows_written="2",
        rows_total="3",
        bytes_written="100",
        bytes_total="150",
    )

    # Assert
    actual = (
        result.rows_written,
        result.rows_total,
        result.bytes_written,
        result.bytes_total,
    )
    expected = (2, 3, 100, 150)
    assert actual == expected


def test_metrics_should_be_none_when_not_given():
    # Act
    result = OutputMetrics(dataset="iceberg.default.sales")

    # Assert
    actual = (
        result.rows_written,
        result.rows_total,
        result.bytes_written,
        result.bytes_total,
    )
    expected = (None, None, None, None)
    assert actual == expected


@pytest.mark.parametrize("zero", [0, "0"])
def test_metrics_should_keep_zero(zero: int | str):
    # Act
    result = OutputMetrics(
        dataset="iceberg.default.sales",
        rows_written=zero,
        rows_total=zero,
        bytes_written=zero,
        bytes_total=zero,
    )

    # Assert
    actual = (
        result.rows_written,
        result.rows_total,
        result.bytes_written,
        result.bytes_total,
    )
    expected = (0, 0, 0, 0)
    assert actual == expected


# ============================================================================
# Testing OutputMetrics - to_dict
# ============================================================================
def test_to_dict_should_return_all_fields():
    # Arrange
    metrics = OutputMetrics(
        dataset="iceberg.default.sales",
        mode="append",
        format="iceberg",
        rows_written=2,
        rows_total=3,
        bytes_written=100,
        bytes_total=150,
    )

    # Act
    result = metrics.to_dict()

    # Assert
    actual = result
    expected = {
        "dataset": "iceberg.default.sales",
        "mode": "append",
        "format": "iceberg",
        "rows_written": 2,
        "rows_total": 3,
        "bytes_written": 100,
        "bytes_total": 150,
    }
    assert actual == expected


def test_to_dict_should_include_missing_fields_as_none():
    # Arrange
    metrics = OutputMetrics(dataset="iceberg.default.sales")

    # Act
    result = metrics.to_dict()

    # Assert
    actual = result
    expected = {
        "dataset": "iceberg.default.sales",
        "mode": None,
        "format": None,
        "rows_written": None,
        "rows_total": None,
        "bytes_written": None,
        "bytes_total": None,
    }
    assert actual == expected


# ============================================================================
# Testing OutputMetrics - tags
# ============================================================================
def test_tags_should_return_dataset_mode_and_format():
    # Arrange
    metrics = OutputMetrics(
        dataset="iceberg.default.sales",
        mode="append",
        format="iceberg",
        rows_written=2,
        rows_total=3,
    )

    # Act
    result = metrics.tags()

    # Assert
    actual = result
    expected = {
        "dataset": "iceberg.default.sales",
        "mode": "append",
        "format": "iceberg",
    }
    assert actual == expected


def test_tags_should_skip_missing_fields():
    # Arrange
    metrics = OutputMetrics(dataset="iceberg.default.sales")

    # Act
    result = metrics.tags()

    # Assert
    actual = result
    expected = {"dataset": "iceberg.default.sales"}
    assert actual == expected


# ============================================================================
# Testing OutputMetrics - counts
# ============================================================================
def test_counts_should_return_rows_and_bytes_written():
    # Arrange
    metrics = OutputMetrics(
        dataset="iceberg.default.sales",
        mode="append",
        rows_written=2,
        rows_total=3,
        bytes_written=100,
        bytes_total=150,
    )

    # Act
    result = metrics.counts()

    # Assert
    actual = result
    expected = {
        "rows_written": 2,
        "bytes_written": 100,
    }
    assert actual == expected


def test_counts_should_skip_missing_metrics():
    # Arrange
    metrics = OutputMetrics(
        dataset="iceberg.default.sales",
        rows_written=2,
    )

    # Act
    result = metrics.counts()

    # Assert
    actual = result
    expected = {"rows_written": 2}
    assert actual == expected


def test_counts_should_keep_zero():
    # Arrange
    metrics = OutputMetrics(
        dataset="iceberg.default.sales",
        rows_written=0,
        bytes_written=0,
    )

    # Act
    result = metrics.counts()

    # Assert
    actual = result
    expected = {
        "rows_written": 0,
        "bytes_written": 0,
    }
    assert actual == expected


# ============================================================================
# Testing OutputMetrics - gauges
# ============================================================================
def test_gauges_should_return_total_rows_and_bytes():
    # Arrange
    metrics = OutputMetrics(
        dataset="iceberg.default.sales",
        mode="append",
        rows_written=2,
        rows_total=3,
        bytes_written=100,
        bytes_total=150,
    )

    # Act
    result = metrics.gauges()

    # Assert
    actual = result
    expected = {
        "rows_total": 3,
        "bytes_total": 150,
    }
    assert actual == expected


def test_gauges_should_skip_missing_metrics():
    # Arrange
    metrics = OutputMetrics(
        dataset="iceberg.default.sales",
        bytes_total=150,
    )

    # Act
    result = metrics.gauges()

    # Assert
    actual = result
    expected = {"bytes_total": 150}
    assert actual == expected


def test_gauges_should_keep_zero():
    # Arrange
    metrics = OutputMetrics(
        dataset="iceberg.default.sales",
        rows_total=0,
        bytes_total=0,
    )

    # Act
    result = metrics.gauges()

    # Assert
    actual = result
    expected = {
        "rows_total": 0,
        "bytes_total": 0,
    }
    assert actual == expected
