from datetime import datetime

import typer

from ..api import Batch
from ..app import TiozinApp
from . import docs
from .render import announce, render_batches
from .utils import parse_attributes

REQUIRED = ...

batch_cli = typer.Typer(no_args_is_help=True)


@batch_cli.command()
def latest(
    ctx: typer.Context,
    job: str = typer.Argument(REQUIRED, help=docs.JOB),
) -> None:
    """
    Show the most recently registered batch of a job.

    The batch is selected by registration time and may be in any state.
    """
    announce(job)
    app: TiozinApp = ctx.obj
    resource = app.resolve_manifest(job).to_resource_dict()
    batch = app.registries.batch.get_latest(**resource)
    if not batch:
        app.warning(f"No batch found for job {job}.")
        return
    render_batches([batch])


@batch_cli.command()
def backlog(
    ctx: typer.Context,
    job: str = typer.Argument(REQUIRED, help=docs.JOB),
) -> None:
    """
    Show the batches awaiting processing for a job.

    The backlog includes batches in the PENDING, RUNNING, and FAILED states.
    FAILED batches remain eligible for retry until they exceed the retry
    limit or are quarantined. RUNNING batches are also included because an
    interrupted execution may terminate before the batch can be transitioned
    to FAILED, allowing it to be recovered and retried.
    """
    announce(job)
    app: TiozinApp = ctx.obj
    resource = app.resolve_manifest(job).to_resource_dict()
    batches = app.registries.batch.get_backlog(**resource)
    if not batches:
        app.warning(f"No backlog found for job {job}.")
        return
    render_batches(batches)


@batch_cli.command()
def history(
    ctx: typer.Context,
    job: str = typer.Argument(REQUIRED, help=docs.JOB),
    limit: int = typer.Option(
        None,
        "--limit",
        help=docs.LIMIT,
    ),
    since: datetime = typer.Option(
        None,
        "--since",
        parser=datetime.fromisoformat,
        help=docs.SINCE,
    ),
) -> None:
    """
    Show the registration history of a job's batches.

    History includes batches in every state, ordered from the most to the
    least recently registered. Use --since and --limit to narrow the results.
    """
    announce(job)
    app: TiozinApp = ctx.obj
    resource = app.resolve_manifest(job).to_resource_dict()
    batches = app.registries.batch.get_history(limit=limit, since=since, **resource)
    if not batches:
        app.warning(f"No history found for job {job}.")
        return
    render_batches(batches)


@batch_cli.command()
def register(
    ctx: typer.Context,
    job: str = typer.Argument(REQUIRED, help=docs.JOB),
    nominal_time: datetime = typer.Argument(
        REQUIRED,
        parser=datetime.fromisoformat,
        help=docs.NOMINAL_TIME,
    ),
    attributes: list[str] = typer.Option(
        [],
        "--attribute",
        "-a",
        help=docs.ATTRIBUTES,
    ),
) -> None:
    """
    Register a new batch for a job.

    The batch is created in the PENDING state, identified by its nominal
    time, and becomes eligible for processing by future executions of the
    job. Registering a batch whose nominal time already exists fails.
    """
    announce(job)
    app: TiozinApp = ctx.obj
    resource = app.resolve_manifest(job).to_resource_dict()

    batch = Batch(
        **resource,
        nominal_time=nominal_time,
        attributes=parse_attributes(attributes),
    )
    batch = app.registries.batch.register(batch)

    app.info(f"Batch registered for job {job}, nominal time {nominal_time.isoformat()}.")
    render_batches([batch])


@batch_cli.command()
def cancel(
    ctx: typer.Context,
    job: str = typer.Argument(REQUIRED, help=docs.JOB),
    batch_id: str = typer.Argument(REQUIRED, help=docs.BATCH_ID),
    attributes: list[str] = typer.Option(
        [],
        "--attribute",
        "-a",
        help=docs.ATTRIBUTES,
    ),
) -> None:
    """
    Cancel a batch of a job.

    The batch is moved to the CANCELED state and leaves the backlog, so
    executions of the job no longer pick it up. A canceled batch can be
    made eligible again with the replay command.
    """
    announce(job)
    app: TiozinApp = ctx.obj
    resource = app.resolve_manifest(job).to_resource_dict()

    batch = app.registries.batch.get(id=batch_id, **resource)
    batch.attributes |= parse_attributes(attributes)
    batch = app.registries.batch.cancel(batch)

    app.info(f"Batch {batch.id} cancelled.")
    render_batches([batch])


@batch_cli.command()
def replay(
    ctx: typer.Context,
    job: str = typer.Argument(REQUIRED, help=docs.JOB),
    batch_id: str = typer.Argument(REQUIRED, help=docs.BATCH_ID),
    attributes: list[str] = typer.Option(
        [],
        "--attribute",
        "-a",
        help=docs.ATTRIBUTES,
    ),
) -> None:
    """
    Replay a batch of a job.

    The batch is returned to the PENDING state, making it eligible again
    for processing by future executions of the job. Use it to reprocess
    canceled, quarantined, or already processed batches.
    """
    announce(job)
    app: TiozinApp = ctx.obj
    resource = app.resolve_manifest(job).to_resource_dict()

    batch = app.registries.batch.get(id=batch_id, **resource)
    batch.attributes |= parse_attributes(attributes)
    batch = app.registries.batch.replay(batch)

    app.info(f"Batch {batch.id} replayed.")
    render_batches([batch])


@batch_cli.command()
def quarantine(
    ctx: typer.Context,
    job: str = typer.Argument(REQUIRED, help=docs.JOB),
    batch_id: str = typer.Argument(REQUIRED, help=docs.BATCH_ID),
    attributes: list[str] = typer.Option(
        [],
        "--attribute",
        "-a",
        help=docs.ATTRIBUTES,
    ),
) -> None:
    """
    Quarantine a batch of a job.

    The batch is moved to the QUARANTINED state and excluded from the
    backlog until it is explicitly replayed. Quarantine also happens
    automatically when a failed batch exceeds the retry limit.
    """
    announce(job)
    app: TiozinApp = ctx.obj
    resource = app.resolve_manifest(job).to_resource_dict()

    batch = app.registries.batch.get(id=batch_id, **resource)
    batch.attributes |= parse_attributes(attributes)
    batch = app.registries.batch.quarantine(batch)

    app.info(f"Batch {batch.id} quarantined.")
    render_batches([batch])
