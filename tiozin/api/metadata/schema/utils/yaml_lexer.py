from pygments.lexers import YamlLexer
from pygments.token import Literal, String


class SchemaYamlLexer(YamlLexer):
    """
    A Pygments YAML lexer that reads plain values as strings, so that every
    color theme gives them a color. Schema.show uses it to print schemas.

    Examples:

        ```python
        from rich.console import Console
        from rich.syntax import Syntax

        Console().print(Syntax(schema.to_yaml(), SchemaYamlLexer(), theme="nord"))
        ```
    """

    def get_tokens_unprocessed(self, text=None, context=None):
        for index, token, value in super().get_tokens_unprocessed(text, context):
            yield index, String if token is Literal.Scalar.Plain else token, value
