import typer
from benedict import benedict

from tiozin.utils import load_yaml


def parse_params(params: list[str] = None, qualifier: str = None) -> dict:
    """
    Parses key=value parameters options into a dict, loading each value as YAML.

    A dotted key (e.g. `a.b.c=value`) is expanded into a nested value.
    """
    parsed = benedict({})
    qualifier = qualifier or "parameter"

    for item in params or []:
        key, sep, value = item.partition("=")
        if not sep:
            raise typer.BadParameter(f"Invalid {qualifier} '{item}'. Expected key=value.")
        try:
            parsed[key] = load_yaml(value)
        except Exception as e:
            raise typer.BadParameter(f"Invalid {qualifier} value for '{key}': {value}") from e
    return parsed.dict()
