from datetime import datetime

import typer

from ..api import Batch
from ..app import TiozinApp
from . import docs
from .render import announce, render_batches
from .utils import parse_params

REQUIRED = ...

batch_cli = typer.Typer(no_args_is_help=True)


@batch_cli.command()
def frontier(
    ctx: typer.Context,
    job: str = typer.Argument(REQUIRED, help=docs.JOB),
) -> None:
    """
    Show the batch at the frontier of a job's processed data.

    The frontier is the latest batch whose processing window still counts
    toward the job's progress. CANCELED batches are never returned, since an
    abandoned window does not advance the frontier.

    Examples:

        Show the frontier batch of a job:

        $ tiozin batch frontier dummy.yaml
    """
    announce(job)
    app: TiozinApp = ctx.obj
    manifest = app.resolve_manifest(job)
    batch = app.registries.batch.get_frontier(**manifest.to_resource_dict())
    if not batch:
        app.warning(f"No frontier found for job {manifest.name}.")
        return
    render_batches([batch], manifest.name)


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

    Examples:

        Show every batch awaiting processing for a job:

        $ tiozin batch backlog dummy.yaml
    """
    announce(job)
    app: TiozinApp = ctx.obj
    manifest = app.resolve_manifest(job)
    backlog = app.registries.batch.get_backlog(**manifest.to_resource_dict())
    if not backlog:
        app.warning(f"No backlog found for job {manifest.name}.")
        return
    render_batches(backlog, manifest.name)


@batch_cli.command()
def board(
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
    Show the full board of a job's batches, across every status.

    Results are ordered from the most to the least recently registered.
    Use --since and --limit to narrow the results.

    Examples:

        Show the 5 most recently registered batches:

        $ tiozin batch board dummy.yaml --limit 3

        Show batches registered on or after a given moment:

        $ tiozin batch board dummy.yaml --since 2026-01-01
    """
    announce(job)
    app: TiozinApp = ctx.obj
    manifest = app.resolve_manifest(job)
    backlog = app.registries.batch.get_board(
        limit=limit, since=since, **manifest.to_resource_dict()
    )
    if not backlog:
        app.warning(f"No batches found for job {manifest.name}.")
        return
    render_batches(backlog, manifest.name)


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
    bookmarks: list[str] = typer.Option(
        [],
        "--bookmark",
        "-b",
        help=docs.BOOKMARKS,
    ),
) -> None:
    """
    Register a new batch for a job.

    The batch is created in the PENDING state, identified by its nominal
    time, and becomes eligible for processing by future executions of the
    job. Registering a batch whose nominal time already exists fails.

    Examples:

        Register a batch for a nominal date:

        $ tiozin batch register dummy.yaml 2026-01-16

        Register a batch for a nominal time:

        $ tiozin batch register dummy.yaml 2026-01-16T00:00:00

        Register a batch with attributes and a bookmark:

        $ tiozin batch register dummy.yaml 2026-01-16T00:00:00 \\
            --attribute source.name=orders_api \\
            --attribute priority=5 \\
            --bookmark  source.offset=42
    """
    announce(job)
    app: TiozinApp = ctx.obj
    manifest = app.resolve_manifest(job)

    batch = Batch(
        **manifest.to_resource_dict(),
        nominal_time=nominal_time,
        attributes=parse_params(attributes, qualifier="attribute"),
        bookmarks=parse_params(bookmarks, qualifier="bookmark"),
    )
    batch = app.registries.batch.register(batch)

    app.info(f"Batch registered for job {job}, nominal time {nominal_time.isoformat()}.")
    render_batches([batch], manifest.name)


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
    bookmarks: list[str] = typer.Option(
        [],
        "--bookmark",
        "-b",
        help=docs.BOOKMARKS,
    ),
) -> None:
    """
    Cancel a batch of a job.

    The batch is moved to the CANCELED state and leaves the backlog, so
    executions of the job no longer pick it up. A canceled batch can be
    made eligible again with the replay command.

    Examples:

        Cancel a batch:

        $ tiozin batch cancel dummy.yaml 018f3a2b-1c4d-7e5f-8a9b-0c1d2e3f4a5b

        Cancel a batch and record why:

        $ tiozin batch cancel dummy.yaml 018f3a2b-1c4d-7e5f-8a9b-0c1d2e3f4a5b \\
            --attribute cancel.reason=duplicate \\
            --attribute cancel.approved=true
    """
    announce(job)
    app: TiozinApp = ctx.obj
    manifest = app.resolve_manifest(job)

    batch = app.registries.batch.get(id=batch_id, **manifest.to_resource_dict())
    batch.attributes |= parse_params(attributes, qualifier="attribute")
    batch.bookmarks |= parse_params(bookmarks, qualifier="bookmark")
    batch = batch.cancel()

    app.info(f"Batch {batch.id} cancelled.")
    render_batches([batch], manifest.name)


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
    bookmarks: list[str] = typer.Option(
        [],
        "--bookmark",
        "-b",
        help=docs.BOOKMARKS,
    ),
) -> None:
    """
    Replay a batch of a job.

    The batch is returned to the PENDING state, making it eligible again
    for processing by future executions of the job. Use it to reprocess
    canceled, quarantined, or already processed batches.

    Examples:

        Replay a batch:

        $ tiozin batch replay dummy.yaml 018f3a2b-1c4d-7e5f-8a9b-0c1d2e3f4a5b

        Replay a batch and reset its source bookmark:

        $ tiozin batch replay dummy.yaml 018f3a2b-1c4d-7e5f-8a9b-0c1d2e3f4a5b \\
            --attribute replay.reason=late_data \\
            --bookmark  source.offset=0
    """
    announce(job)
    app: TiozinApp = ctx.obj
    manifest = app.resolve_manifest(job)

    batch = app.registries.batch.get(id=batch_id, **manifest.to_resource_dict())
    batch.attributes |= parse_params(attributes, qualifier="attribute")
    batch.bookmarks |= parse_params(bookmarks, qualifier="bookmark")
    batch = batch.replay()

    app.info(f"Batch {batch.id} replayed.")
    render_batches([batch], manifest.name)


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
    bookmarks: list[str] = typer.Option(
        [],
        "--bookmark",
        "-b",
        help=docs.BOOKMARKS,
    ),
) -> None:
    """
    Quarantine a batch of a job.

    The batch is moved to the QUARANTINED state and excluded from the
    backlog until it is explicitly replayed. Quarantine also happens
    automatically when a failed batch exceeds the retry limit.

    Examples:

        Quarantine a batch:

        $ tiozin batch quarantine dummy.yaml 018f3a2b-1c4d-7e5f-8a9b-0c1d2e3f4a5b

        Quarantine a batch and record the failing check:

        $ tiozin batch quarantine dummy.yaml 018f3a2b-1c4d-7e5f-8a9b-0c1d2e3f4a5b \\
            --attribute quarantine.check=schema_drift \\
            --attribute quarantine.retries=3
    """
    announce(job)
    app: TiozinApp = ctx.obj
    manifest = app.resolve_manifest(job)

    batch = app.registries.batch.get(id=batch_id, **manifest.to_resource_dict())
    batch.attributes |= parse_params(attributes, qualifier="attribute")
    batch.bookmarks |= parse_params(bookmarks, qualifier="bookmark")
    batch = batch.quarantine()

    app.info(f"Batch {batch.id} quarantined.")
    render_batches([batch], manifest.name)
