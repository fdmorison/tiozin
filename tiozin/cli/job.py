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
    Run one or more jobs.

    Each job is resolved through the job registry and executed. Jobs run
    in sequence, in the order given, and execution stops at the first
    job that fails.
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

    Each job manifest is resolved and checked for errors without building
    or executing the job. Validation stops at the first invalid job.
    Useful in CI/CD pipelines to catch manifest errors before deployment.
    """
    announce(jobs)
    app: TiozinApp = ctx.obj
    app.validate(*jobs)
    app.info(f"✔ All jobs valid: {human_join(jobs)}")
