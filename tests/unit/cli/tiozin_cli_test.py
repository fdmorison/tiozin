import typer
from typer.testing import CliRunner

from tiozin.cli import TiozinCli


def test_main_should_exit_with_command_exit_code_when_command_exits():
    # Arrange
    app = typer.Typer(cls=TiozinCli)

    @app.callback()
    def root() -> None:
        pass

    @app.command()
    def stop() -> None:
        raise typer.Exit(code=3)

    # Act
    result = CliRunner().invoke(app, ["stop"])

    # Assert
    actual = result.exit_code
    expected = 3
    assert actual == expected


def test_main_should_raise_abort_when_command_aborts():
    # Arrange
    app = typer.Typer(cls=TiozinCli)

    @app.callback()
    def root() -> None:
        pass

    @app.command()
    def stop() -> None:
        raise typer.Abort()

    # Act
    result = CliRunner().invoke(app, ["stop"], standalone_mode=False)

    # Assert
    assert isinstance(result.exception, typer.Abort)
