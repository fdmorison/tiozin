import os

import click
import typer

from .. import config
from ..api.loggable import Loggable
from ..app import TiozinApp
from ..exceptions import TiozinUsageError
from .batch import batch_cli
from .job import job_cli
from .render import console

TITLE = f"{config.app_title} v{config.app_version}"

TIO_BANNER = rf"""
 _____ ___ ___ ________ _   _
|_   _|_ _/ _ \__  /_ _| \ | |     _====_
  | |  | | | | |/ / | ||  \| |    @(■ᴗ■⌐)@  Transform Inputs into Outputs,
  | |  | | |_| / /_ | || |\  |     /(:::)\  and let's get this job running :)
  |_| |___\___/____|___|_| \_|      /   \

  {TITLE} - Your friendly ETL framework 🤓
"""


class TiozinCli(Loggable, typer.core.TyperGroup):
    """
    Root of the Tiozin CLI, owning the CLI-wide error policy.

    Every command runs through this group's `main`, so error handling lives here once instead of
    per command — including errors from the callback, where the app is built and `@ensure_setup`
    triggers setup.

    - Exit code 2: TiozinUsageError (expected: validation, bad state, unknown job, etc.)
    - Exit code 1: any other exception (bugs, provider errors, etc.)
    """

    def main(self, *args, **kwargs):
        try:
            return super().main(*args, **kwargs)
        except TiozinUsageError as e:
            self.error(e.message)
            raise SystemExit(2)
        except (click.exceptions.Exit, click.exceptions.Abort, SystemExit):
            raise
        except Exception as e:
            self.exception(f"Unexpected error: {e}")
            raise SystemExit(1)


cli = typer.Typer(
    cls=TiozinCli,
    no_args_is_help=True,
    pretty_exceptions_show_locals=config.log_show_locals,
)


@cli.callback()
def bootstrap(
    ctx: typer.Context,
    settings_path: str = typer.Option(None, "--settings-path", help="Path to the settings file."),
) -> None:
    """
    Builds the application once and hands it to every command via the context.
    """
    ctx.obj = TiozinApp(settings_path)


# job commands (run, validate) live at the top level; batch is a sub-app.
cli.add_typer(job_cli)
cli.add_typer(batch_cli, name="batch", help="Inspect and manage job batches.")


@cli.command()
def version() -> None:
    """Show Tiozin version."""
    console.print(TITLE)


@cli.command()
def help(ctx: typer.Context) -> None:
    """Show this help message."""
    console.print(ctx.parent.get_help())


def main() -> None:
    if "_TIOZIN_COMPLETE" not in os.environ:
        console.print(TIO_BANNER)
    cli()
