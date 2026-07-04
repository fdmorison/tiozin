import typer
from ruamel.yaml import YAML

yaml = YAML(typ="safe")


def parse_attributes(attributes: list[str] = None) -> dict:
    """
    Parses key=value attribute options into a dict, loading each value as YAML.
    """
    parsed = {}
    for item in attributes or []:
        key, sep, value = item.partition("=")
        if not sep:
            raise typer.BadParameter(f"Invalid attribute '{item}'. Expected key=value.")
        try:
            parsed[key] = yaml.load(value)
        except Exception as e:
            raise typer.BadParameter(f"Invalid value for attribute '{key}': {value}") from e
    return parsed
