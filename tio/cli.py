from rich.console import Console
import typer

from . import config
from .app import TioApp

REQUIRED = ...
OPTIONAL = None

app = typer.Typer(help="CLI do Tio :)", no_args_is_help=True)
tio_app = TioApp()
console = Console()

ASCII_TIO = rf"""
  _____ ___ ___       _====_
 |_   _|_ _/ _ \     @(■ᴗ■⌐)@   Hello, I'm {config.app_title} v{config.app_version}!
   | |  | | | | |     /(:::)\   Let's get this job running :)
   | |  | | |_| |      /   \
   |_| |___\___/
"""


@app.command()
def run(
    job_uri: str = typer.Argument(REQUIRED, help="URI to the job manifest. Eg: job.yaml."),
) -> None:
    console.print(ASCII_TIO)
    console.print(f"[green]Tio is now running the job:[/green] {job_uri}\n\n")
    tio_app.run(job_uri=job_uri)


@app.command()
def noop() -> None:
    pass


def main() -> None:
    app()
