import typer
from rich.console import Console

from . import config
from .app import TiozinApp

REQUIRED = ...
OPTIONAL = None
TITLE = f"{config.app_title} v{config.app_version}"

cli = typer.Typer(help=TITLE, no_args_is_help=True)
app = TiozinApp()
console = Console()

ASCII_TIO = rf"""
 _____ ___ ___ ________ _   _
|_   _|_ _/ _ \__  /_ _| \ | |     _====_
  | |  | | | | |/ / | ||  \| |    @(■ᴗ■⌐)@  Transform Inputs into Outputs,
  | |  | | |_| / /_ | || |\  |     /(:::)\  and let's get this job running :)
  |_| |___\___/____|___|_| \_|      /   \

  {TITLE} - Your friendly ETL framework 🤓
"""


@cli.command()
def run(
    name: str = typer.Argument(REQUIRED, help="Name of the job to create."),
) -> None:
    """Submit and run a job."""
    console.print(ASCII_TIO)
    console.print(f"[green]▶ Starting job:[/green] [bold cyan]{name}[/bold cyan]\n")
    app.run(name)


@cli.command()
def version() -> None:
    """Show Tiozin version."""
    console.print(ASCII_TIO)


def main() -> None:
    cli()
