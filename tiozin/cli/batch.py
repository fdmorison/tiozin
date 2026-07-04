from datetime import datetime

import typer

from ..api import Batch
from ..app import TiozinApp
from .render import announce, render_batches
from .utils import parse_attributes

REQUIRED = ...

batch_cli = typer.Typer(no_args_is_help=True)


@batch_cli.command()
def latest(
    ctx: typer.Context,
    job: str = typer.Argument(REQUIRED, help="Identifier of the job."),
) -> None:
    """
    Shows the most recently registered batch for a job.
    """
    announce(job)
    app: TiozinApp = ctx.obj
    resource = app.resolve_manifest(job).resource
    batch = app.registries.batch.get_latest(**resource)
    if not batch:
        app.warning(f"No batch found for job {job}.")
        return
    render_batches([batch])


@batch_cli.command()
def backlog(
    ctx: typer.Context,
    job: str = typer.Argument(REQUIRED, help="Identifier of the job."),
) -> None:
    """
    List the backlog of batches in pending, running, or failed state for a job.
    """
    announce(job)
    app: TiozinApp = ctx.obj
    resource = app.resolve_manifest(job).resource
    batches = app.registries.batch.get_backlog(**resource)
    if not batches:
        app.warning(f"No backlog found for job {job}.")
        return
    render_batches(batches)


@batch_cli.command()
def history(
    ctx: typer.Context,
    job: str = typer.Argument(REQUIRED, help="Identifier of the job."),
    limit: int = typer.Option(None, "--limit", help="Maximum number of batches to show."),
    since: datetime = typer.Option(
        None,
        "--since",
        parser=datetime.fromisoformat,
        help="Only show batches registered at or after this ISO 8601 datetime.",
    ),
) -> None:
    """
    Shows the most recently registered batches for a job, regardless of status.

    Useful for debugging watermark and backlog progression over time.
    """
    announce(job)
    app: TiozinApp = ctx.obj
    resource = app.resolve_manifest(job).resource
    batches = app.registries.batch.get_history(limit=limit, since=since, **resource)
    if not batches:
        app.warning(f"No history found for job {job}.")
        return
    render_batches(batches)


@batch_cli.command()
def register(
    ctx: typer.Context,
    job: str = typer.Argument(REQUIRED, help="Identifier of the job."),
    nominal_time: datetime = typer.Argument(
        REQUIRED,
        parser=datetime.fromisoformat,
        help="Nominal time to register, as an ISO 8601 datetime.",
    ),
    attributes: list[str] = typer.Option(
        [],
        "--attribute",
        "-a",
        callback=parse_attributes,
        help="Batch attribute as key=value. Can be specified multiple times.",
    ),
) -> None:
    """
    Creates a new pending batch for a job to work as watermark or backlog.
    """
    announce(job)
    app: TiozinApp = ctx.obj
    resource = app.resolve_manifest(job).resource

    batch = Batch(
        **resource,
        nominal_time=nominal_time,
        attributes=attributes,
    )
    batch = app.registries.batch.register(batch)

    app.info(f"Batch registered for job {job}, nominal time {nominal_time.isoformat()}.")
    render_batches([batch])
