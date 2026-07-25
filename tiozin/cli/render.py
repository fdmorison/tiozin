from datetime import datetime

from rich import box
from rich.console import Console
from rich.table import Column, Table

from ..api import Batch, BatchStatus
from ..utils import as_utc, dump_yaml, human_join, isozformat

console = Console()

STATUS_DOT = "●"
RIGHT_ARROW = "→"
EMPTY_CELL = "[dim]empty[/]"

# Horizontal rules plus discrete dashed vertical column separators (no outer borders).
BATCH_BOX = box.Box("    \n  ╎ \n ─┼ \n  ╎ \n ─┼ \n ─┼ \n  ╎ \n    \n")

BATCH_COLUMNS = (
    Column("#"),
    Column("ID", no_wrap=True),
    Column("NOMINAL_TIME"),
    Column("NOMINAL_WINDOW", justify="center"),
    Column("STATUS", no_wrap=True),
    Column("ATTEMPTS", justify="center"),
    Column("BOOKMARKS"),
    Column("ATTRIBUTES"),
    Column("CREATED_AT", justify="center"),
    Column("UPDATED_AT", justify="center"),
)

STATUS_STYLES = {
    "pending": "yellow",
    "running": "cyan",
    "failed": "red",
    "succeeded": "green",
    "quarantined": "magenta",
    "canceled": "bright_black",
}


def announce(job: str | list[str]) -> None:
    """
    Prints a command's opening status line — the one print a command makes outside the log.
    """
    label = human_join(job) if isinstance(job, list) else job
    console.print(f"[green]Jobs:[/green] [bold cyan]{label}[/bold cyan]\n")


def id_cell(batch: Batch) -> str:
    """
    Renders a batch's id across two lines: the id over its dim framework provenance.
    """
    return f"{batch.id}\n[dim]{batch.framework}[/]"


def status_cell(status: BatchStatus) -> str:
    """
    Renders a status as a colored dot followed by its neutral label.
    """
    style = STATUS_STYLES.get(status, "white")
    return f"[{style}]{STATUS_DOT}[/] {status}"


def window_cell(start: datetime, end: datetime) -> str:
    """
    Renders the window across three lines: the end over an up arrow over the
    start, matching the table's most-recent-first ordering.
    """
    diff = as_utc(start).diff(end).in_words()
    return f"{isozformat(start)} {RIGHT_ARROW} {isozformat(end)}\n[dim]{diff}[/]"


def mapping_cell(mapping: dict) -> str:
    """
    Renders a mapping as YAML, or a dim placeholder when empty.
    """
    return dump_yaml(mapping) if mapping else EMPTY_CELL


def timestamp_cell(dt: datetime) -> str:
    """
    Renders a timestamp across two lines: the relative time (e.g. `2 hours
    ago`) over its dim absolute value in seconds precision.
    """
    absolute = isozformat(dt, timespec="seconds")
    relative = as_utc(dt).diff_for_humans()
    return f"{absolute}\n[dim]{relative}[/]"


def render_batches(batches: list[Batch], job: str) -> None:
    """
    Renders batches as a Rich table.
    """
    batches = [batch for batch in batches if batch]
    if not batches:
        return

    title = (
        f"[bold][cornflower_blue]\nBatch Board of `{job}`[/]\n"
        f"[steel_blue]{batches[0].qualified_resource}[/]"
    )
    table = Table(
        *BATCH_COLUMNS,
        title=title,
        box=BATCH_BOX,
        show_header=True,
        show_lines=True,
        header_style="navy_blue",
        border_style="dim",
        padding=(0, 1),
        pad_edge=False,
        row_styles=[""],
        caption="\n",
    )

    for i, batch in enumerate(batches, start=1):
        table.add_row(
            str(i),
            id_cell(batch),
            isozformat(batch.nominal_time),
            window_cell(batch.nominal_start_time, batch.nominal_end_time),
            status_cell(batch.status),
            str(batch.attempts),
            mapping_cell(batch.bookmarks),
            mapping_cell(batch.attributes),
            timestamp_cell(batch.created_at),
            timestamp_cell(batch.updated_at),
        )

    console.print(table)
