from duckdb import DuckDBPyConnection

from tiozin.family.tio_duckdb import DuckdbWordCountTransform

# =============================================================================
# Testing DuckdbWordCountTransform - Core Behavior
# =============================================================================


def test_transform_should_count_words(duckdb_session: DuckDBPyConnection):
    """Counts word occurrences across all input rows."""
    # Arrange
    input_rel = duckdb_session.sql("""
        SELECT * FROM (VALUES
            ('lorem ipsum dolor sit amet'),
            ('lorem lorem dolor sit sit sit sit')
        ) AS t(value)
    """).set_alias("input")
    duckdb_session.register("input", input_rel)

    # Act
    relation = DuckdbWordCountTransform(
        name="test",
    ).transform(input_rel)

    # Assert
    actual = relation.fetchall()
    expected = [
        ("amet", 1),
        ("dolor", 2),
        ("ipsum", 1),
        ("lorem", 3),
        ("sit", 5),
    ]
    assert actual == expected


def test_transform_should_return_empty_when_input_is_empty(duckdb_session: DuckDBPyConnection):
    """Returns an empty result when the input has no rows."""
    # Arrange
    input_rel = duckdb_session.sql("""
        SELECT '' AS value WHERE false
    """).set_alias("input")
    duckdb_session.register("input", input_rel)

    # Act
    relation = DuckdbWordCountTransform(
        name="test",
    ).transform(input_rel)

    # Assert
    actual = relation.fetchall()
    expected = []
    assert actual == expected


# =============================================================================
# Testing DuckdbWordCountTransform - Lowercase Normalization
# =============================================================================


def test_transform_should_normalize_words_to_lowercase(duckdb_session: DuckDBPyConnection):
    """Normalizes tokens to lowercase before counting by default."""
    # Arrange
    input_rel = duckdb_session.sql("""
        SELECT * FROM (VALUES
            ('Lorem IPSUM DoLor SIT amET'),
            ('lorem ipsum doLOR sit SIT sIt Sit')
        ) AS t(value)
    """).set_alias("input")
    duckdb_session.register("input", input_rel)

    # Act
    relation = DuckdbWordCountTransform(
        name="test",
    ).transform(input_rel)

    # Assert
    actual = relation.fetchall()
    expected = [
        ("amet", 1),
        ("dolor", 2),
        ("ipsum", 2),
        ("lorem", 2),
        ("sit", 5),
    ]
    assert actual == expected


def test_transform_should_preserve_case_when_lowercase_is_disabled(
    duckdb_session: DuckDBPyConnection,
):
    """Preserves original token casing when lowercase normalization is disabled."""
    # Arrange
    input_rel = duckdb_session.sql("""
        SELECT * FROM (VALUES ('Hello hello HELLO')) AS t(value)
    """).set_alias("input")
    duckdb_session.register("input", input_rel)

    # Act
    relation = DuckdbWordCountTransform(
        name="test",
        lowercase=False,
    ).transform(input_rel)

    # Assert
    actual = relation.fetchall()
    expected = [
        ("HELLO", 1),
        ("Hello", 1),
        ("hello", 1),
    ]
    assert actual == expected


# =============================================================================
# Testing DuckdbWordCountTransform - Tokenization Rules
# =============================================================================


def test_transform_should_remove_punctuation(duckdb_session: DuckDBPyConnection):
    """Splits words correctly by removing punctuation and special characters."""
    # Arrange
    input_rel = duckdb_session.sql(r"""
        SELECT * FROM (VALUES
            ('lorem.ipsum, dolor-sit... amet-----'),
            (',lorem! lorem dolor sit\sit+sit#sit')
        ) AS t(value)
    """).set_alias("input")
    duckdb_session.register("input", input_rel)

    # Act
    relation = DuckdbWordCountTransform(
        name="test",
    ).transform(input_rel)

    # Assert
    actual = relation.fetchall()
    expected = [
        ("amet", 1),
        ("dolor", 2),
        ("ipsum", 1),
        ("lorem", 3),
        ("sit", 5),
    ]
    assert actual == expected


def test_transform_should_preserve_apostrophes(duckdb_session: DuckDBPyConnection):
    """Keeps apostrophes as part of tokens during word splitting."""
    # Arrange
    input_rel = duckdb_session.sql("""
        SELECT * FROM (VALUES
            ('lorem''s ipsum'' dolor sit amet'),
            ('lorem lorem dolor sit sit sit sit')
        ) AS t(value)
    """).set_alias("input")
    duckdb_session.register("input", input_rel)

    # Act
    relation = DuckdbWordCountTransform(
        name="test",
    ).transform(input_rel)

    # Assert
    actual = relation.fetchall()
    expected = [
        ("amet", 1),
        ("dolor", 2),
        ("ipsum'", 1),
        ("lorem", 2),
        ("lorem's", 1),
        ("sit", 5),
    ]
    assert actual == expected


def test_transform_should_handle_unicode_characters(duckdb_session: DuckDBPyConnection):
    """Correctly tokenizes and counts Unicode characters."""
    # Arrange
    input_rel = duckdb_session.sql("""
        SELECT * FROM (VALUES
            ('olá mundo café'),
            ('olá olá mundo')
        ) AS t(value)
    """).set_alias("input")
    duckdb_session.register("input", input_rel)

    # Act
    relation = DuckdbWordCountTransform(
        name="test",
    ).transform(input_rel)

    # Assert
    actual = relation.fetchall()
    expected = [
        ("café", 1),
        ("mundo", 2),
        ("olá", 3),
    ]
    assert actual == expected


# =============================================================================
# Testing DuckdbWordCountTransform - Grouping Behavior
# =============================================================================


def test_transform_should_count_words_grouped_by_single_column(
    duckdb_session: DuckDBPyConnection,
):
    """Scopes word counts by a single grouping column."""
    # Arrange
    input_rel = duckdb_session.sql("""
        SELECT * FROM (VALUES
            ('hamlet', 'lorem''s ipsum'' dolor sit amet'),
            ('sonnet', 'lorem lorem dolor sit sit sit sit')
        ) AS t(doc_id, value)
    """).set_alias("input")
    duckdb_session.register("input", input_rel)

    # Act
    relation = DuckdbWordCountTransform(
        name="test",
        count_by="doc_id",
    ).transform(input_rel)

    # Assert
    actual = relation.fetchall()
    expected = [
        ("hamlet", "amet", 1),
        ("hamlet", "dolor", 1),
        ("hamlet", "ipsum'", 1),
        ("hamlet", "lorem's", 1),
        ("hamlet", "sit", 1),
        ("sonnet", "dolor", 1),
        ("sonnet", "lorem", 2),
        ("sonnet", "sit", 4),
    ]
    assert actual == expected


def test_transform_should_count_words_grouped_by_multiple_columns(
    duckdb_session: DuckDBPyConnection,
):
    """Scopes word counts by multiple grouping columns."""
    # Arrange
    input_rel = duckdb_session.sql("""
        SELECT * FROM (VALUES
            ('hamlet', 'act1', 'hello world'),
            ('hamlet', 'act2', 'hello hello'),
            ('sonnet', 'act1', 'world world world')
        ) AS t(play, act, value)
    """).set_alias("input")
    duckdb_session.register("input", input_rel)

    # Act
    relation = DuckdbWordCountTransform(
        name="test",
        count_by=["play", "act"],
    ).transform(input_rel)

    # Assert
    actual = relation.fetchall()
    expected = [
        ("hamlet", "act1", "hello", 1),
        ("hamlet", "act1", "world", 1),
        ("hamlet", "act2", "hello", 2),
        ("sonnet", "act1", "world", 3),
    ]
    assert actual == expected


# =============================================================================
# Testing DuckdbWordCountTransform - Parameterization (Canonical Test)
# =============================================================================


def test_transform_should_apply_all_parameters(duckdb_session: DuckDBPyConnection):
    """Applies all constructor parameters to the transformation behavior."""
    # Arrange
    input_rel = duckdb_session.sql("""
        SELECT * FROM (VALUES
            ('doc1', 'Hello HELLO'),
            ('doc2', 'Hello world')
        ) AS t(doc_id, text)
    """).set_alias("input")
    duckdb_session.register("input", input_rel)

    # Act
    relation = DuckdbWordCountTransform(
        name="test",
        content_field="text",
        count_by="doc_id",
        lowercase=False,
    ).transform(input_rel)

    # Assert
    actual = relation.fetchall()
    expected = [
        ("doc1", "HELLO", 1),
        ("doc1", "Hello", 1),
        ("doc2", "Hello", 1),
        ("doc2", "world", 1),
    ]
    assert actual == expected
