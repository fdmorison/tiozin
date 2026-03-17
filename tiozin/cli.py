import typer
from rich.console import Console

from . import config
from .app import TiozinApp
from .exceptions import TiozinUsageError

REQUIRED = ...
OPTIONAL = None
TITLE = f"{config.app_title} v{config.app_version}"

cli = typer.Typer(
    help=TITLE,
    no_args_is_help=True,
    pretty_exceptions_show_locals=config.log_show_locals,
)
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
    job: str = typer.Argument(REQUIRED, help="Identifier of the job to be run."),
    settings_file: str = typer.Option(None, "--settings-file", help="Path to the settings file."),
) -> None:
    """
    Submit and run a job.

    TiozinApp must be responsible for logging and displaying the stacktrace.
    To avoid log duplication, this command only handles exit codes:

    - Exit code 2: TiozinError (expected errors like validation, bad state, etc)
    - Exit code 1: TiozinUnexpectedError or Exception (bugs, provider errors, etc)
    """
    console.print(ASCII_TIO)
    console.print(f"[green]▶ Starting job:[/green] [bold cyan]{job}[/bold cyan]\n")

    try:
        app = TiozinApp(settings_file)
        app.run(job)
    except TiozinUsageError:
        raise typer.Exit(code=2) from None
    except Exception:
        raise typer.Exit(code=1) from None


@cli.command()
def validate(
    jobs: list[str] = typer.Argument(REQUIRED, help="Identifiers of the jobs to validate."),
    settings_file: str = typer.Option(None, "--settings-file", help="Path to the settings file."),
) -> None:
    """
    Validate one or more job manifests without running them.

    Accepts one or more job identifiers resolvable via the job registry.
    Useful for CI/CD pipelines to catch manifest errors before execution.

    Exit codes:

    - Exit code 2: TiozinError (invalid manifest, missing fields, unknown identifier, etc)
    - Exit code 1: Unexpected error
    """
    console.print(f"[green]▶ Validating jobs:[/green] [bold cyan]{', '.join(jobs)}[/bold cyan]\n")

    try:
        app = TiozinApp(settings_file)
        app.validate(*jobs)
    except TiozinUsageError:
        raise typer.Exit(code=2) from None
    except Exception:
        raise typer.Exit(code=1) from None


@cli.command()
def version() -> None:
    """Show Tiozin version."""
    console.print(ASCII_TIO)


def main() -> None:
    cli()
