import typer

from ..app import TiozinApp
from ..utils import human_join
from .render import announce

REQUIRED = ...

job_cli = typer.Typer(no_args_is_help=True)


@job_cli.command()
def run(
    ctx: typer.Context,
    jobs: list[str] = typer.Argument(REQUIRED, help="Identifiers of the jobs to run."),
) -> None:
    """
    Submit and run one or more jobs.
    """
    announce(jobs)
    app: TiozinApp = ctx.obj
    app.run(*jobs)


@job_cli.command()
def validate(
    ctx: typer.Context,
    jobs: list[str] = typer.Argument(REQUIRED, help="Identifiers of the jobs to validate."),
) -> None:
    """
    Validate one or more jobs without running them.

    Accepts one or more job identifiers resolvable via the job registry.
    Useful for CI/CD pipelines to catch manifest errors before execution.
    """
    announce(jobs)
    app: TiozinApp = ctx.obj
    app.validate(*jobs)
    app.info(f"✔ All jobs valid: {human_join(jobs)}")
