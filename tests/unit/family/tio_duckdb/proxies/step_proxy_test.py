from duckdb import DuckDBPyConnection

from tiozin.family.tio_duckdb import DuckdbWordCountTransform

# =============================================================================
# Testing DuckdbStepProxy._register_view — slug as view name
# =============================================================================


def test_proxy_should_register_view_using_step_slug(duckdb_session: DuckDBPyConnection):
    """View is registered under the slug, not the raw step name."""
    # Arrange
    step = DuckdbWordCountTransform(name="my word count step")
    relation = duckdb_session.sql("SELECT 'hello world' AS value").set_alias("raw_input")
    duckdb_session.register("raw_input", relation)

    # Act
    result = step.transform(relation)

    # Assert
    actual = result.alias
    expected = "my_word_count_step"
    assert actual == expected


def test_proxy_should_make_view_queryable_by_slug(duckdb_session: DuckDBPyConnection):
    """After registration, the view is accessible by its slug in SQL."""
    # Arrange
    step = DuckdbWordCountTransform(name="my word count step")
    relation = duckdb_session.sql("SELECT 'hello world' AS value").set_alias("raw_input")
    duckdb_session.register("raw_input", relation)

    # Act
    step.transform(relation)

    # Assert — slug is a valid SQL identifier and the view is queryable
    actual = duckdb_session.sql("SELECT * FROM my_word_count_step").fetchall()
    assert len(actual) > 0


def test_proxy_should_preserve_slug_when_name_has_special_characters(
    duckdb_session: DuckDBPyConnection,
):
    """Slug handles hyphens, mixed case, and extra spaces in the step name."""
    # Arrange
    step = DuckdbWordCountTransform(name="Word Count - 2024!")
    relation = duckdb_session.sql("SELECT 'hello world' AS value").set_alias("raw_input")
    duckdb_session.register("raw_input", relation)

    # Act
    result = step.transform(relation)

    # Assert
    actual = result.alias
    expected = "word_count_2024"
    assert actual == expected
