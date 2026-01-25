import typer
from rich.console import Console

from . import config
from .app import TiozinApp
from .exceptions import TiozinError, TiozinUnexpectedError

REQUIRED = ...
OPTIONAL = None
TITLE = f"{config.app_title} v{config.app_version}"

cli = typer.Typer(
    help=TITLE,
    no_args_is_help=True,
    pretty_exceptions_show_locals=config.log_show_locals,
)
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
    """
    Submit and run a job.

    TiozinApp must be responsible for logging and displaying the stacktrace.
    To avoid log duplication, this command only handles exit codes:

    - Exit code 2: TiozinError (expected errors like validation, bad state, etc)
    - Exit code 1: TiozinUnexpectedError or Exception (bugs, provider errors, etc)
    """
    console.print(ASCII_TIO)
    console.print(f"[green]▶ Starting job:[/green] [bold cyan]{name}[/bold cyan]\n")
    try:
        app.run(name)
    except TiozinError:
        raise typer.Exit(code=2) from None
    except TiozinUnexpectedError:
        raise typer.Exit(code=1) from None
    except Exception:
        raise typer.Exit(code=1) from None


@cli.command()
def version() -> None:
    """Show Tiozin version."""
    console.print(ASCII_TIO)


def main() -> None:
    cli()
