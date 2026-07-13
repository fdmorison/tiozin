from rich.console import Console
from rich.table import Table

from ..api import Batch
from ..utils import human_join, isozformat

console = Console()

BATCH_COLUMNS = (
    "id",
    "nominal_time",
    "status",
    "failure_count",
    "state",
    "attributes",
    "created_at",
    "updated_at",
)


def announce(job: str | list[str]) -> None:
    """
    Prints a command's opening status line — the one print a command makes outside the log.
    """
    label = human_join(job) if isinstance(job, list) else job
    console.print(f"[green]Jobs:[/green] [bold cyan]{label}[/bold cyan]\n")


def render_batches(batches: list[Batch]) -> None:
    """
    Renders batches as a Rich table.
    """
    batches = [batch for batch in batches if batch]
    if not batches:
        return

    table = Table(show_header=True, header_style="bold")
    for column in BATCH_COLUMNS:
        table.add_column(column)

    for batch in batches:
        table.add_row(
            batch.id,
            isozformat(batch.nominal_time),
            batch.status.value,
            str(batch.failure_count),
            str(batch.state.model_dump(mode="json")),
            str(batch.attributes),
            isozformat(batch.created_at),
            isozformat(batch.updated_at),
        )
    console.print(table)
