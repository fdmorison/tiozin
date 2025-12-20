from rich.console import Console
import typer

from . import config
from .app import TiozinApp

REQUIRED = ...
OPTIONAL = None

app = typer.Typer(help=f"Tiozin v{config.app_version}", no_args_is_help=True)
tiozin_app = TiozinApp()
console = Console()

ASCII_TIO = rf"""
 _____ ___ ___ ________ _   _
|_   _|_ _/ _ \__  /_ _| \ | |     _====_
  | |  | | | | |/ / | ||  \| |    @(■ᴗ■⌐)@  Transform Inputs into Outputs,
  | |  | | |_| / /_ | || |\  |     /(:::)\  and let's get this job running :)
  |_| |___\___/____|___|_| \_|      /   \

  Tiozin v{config.app_version} - Your friendly ETL framework 🤓
"""


@app.command()
def run(
    name: str = typer.Argument(REQUIRED, help="Name of the job to create."),
) -> None:
    """Submit and run a job."""
    console.print(ASCII_TIO)
    console.print(f"[green]▶ Starting job:[/green] [bold cyan]{name}[/bold cyan]\n")
    tiozin_app.run(job_uri=name)


@app.command()
def version() -> None:
    """Show Tiozin version."""
    console.print(ASCII_TIO)


def main() -> None:
    app()
