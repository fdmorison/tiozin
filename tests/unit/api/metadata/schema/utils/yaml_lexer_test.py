from pygments.token import Comment, Name, Punctuation, String, Text

from tiozin.api.metadata.schema.utils import SchemaYamlLexer


def test_get_tokens_should_read_plain_value_as_string():
    # Arrange
    text = "name: customers\n"

    # Act
    result = SchemaYamlLexer().get_tokens(text)

    # Assert
    actual = list(result)
    expected = [
        (Name.Tag, "name"),
        (Punctuation, ":"),
        (Text.Whitespace, " "),
        (String, "customers"),
        (Text.Whitespace, "\n"),
    ]
    assert actual == expected


def test_get_tokens_should_preserve_other_tokens():
    # Arrange
    text = "tags: [sales]\n# owned by sales\n"

    # Act
    result = SchemaYamlLexer().get_tokens(text)

    # Assert
    actual = list(result)
    expected = [
        (Name.Tag, "tags"),
        (Punctuation, ":"),
        (Text.Whitespace, " "),
        (Punctuation.Indicator, "["),
        (Name.Variable, "sales"),
        (Punctuation.Indicator, "]"),
        (Text.Whitespace, "\n"),
        (Comment.Single, "# owned by sales"),
        (Text.Whitespace, "\n"),
    ]
    assert actual == expected
