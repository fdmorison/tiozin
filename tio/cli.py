from rich.console import Console
import typer

app = typer.Typer(help="CLI do Tio :)", no_args_is_help=True)
console = Console()

ASCII_TIO = r"""
  _____ ___ ___       _====_
 |_   _|_ _/ _ \     @(■ᴗ■⌐)@   v0.1.0
   | |  | | | | |     /(:::)\
   | |  | | |_| |      /   \ 
   |_| |___\___/ 
"""


@app.command()
def run(
    path: str = typer.Argument(..., help="Path to the job settings. Eg: job.yaml."),
) -> None:
    console.print(ASCII_TIO)
    console.print(f"[green]Running job:[/green] {path}\n\n")


@app.command()
def noop() -> None:
    pass


def main() -> None:
    app()
