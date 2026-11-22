import os
import subprocess
import sys


def test_import_should_silence_stderr_during_shell_completion():
    # Arrange
    env = {**os.environ, "_TIOZIN_COMPLETE": "complete_bash"}
    code = "import sys; import tiozin; sys.stderr.write('lorem ipsum')"

    # Act
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
    )

    # Assert
    actual = result.stderr
    expected = ""
    assert actual == expected


def test_import_should_keep_stderr_when_not_completing():
    # Arrange
    env = {k: v for k, v in os.environ.items() if k != "_TIOZIN_COMPLETE"}
    code = "import sys; import tiozin; sys.stderr.write('lorem ipsum')"

    # Act
    result = subprocess.run(
        [sys.executable, "-W", "ignore", "-c", code],
        env=env,
        capture_output=True,
        text=True,
    )

    # Assert
    actual = result.stderr
    expected = "lorem ipsum"
    assert actual == expected


def test_shell_completion_should_print_only_the_candidates():
    # Arrange
    env = {
        **os.environ,
        "_TIOZIN_COMPLETE": "complete_bash",
        "COMP_WORDS": "tiozin ru",
        "COMP_CWORD": "1",
    }
    code = "import sys; sys.argv[0] = 'tiozin'; from tiozin.cli import main; main()"

    # Act
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
    )

    # Assert
    actual = (
        result.stdout,
        result.stderr,
    )
    expected = (
        "run\n",
        "",
    )
    assert actual == expected
