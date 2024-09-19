import pytest
from typer.testing import CliRunner
from invokeai_presets_cli.cli import invoke_presets_cli


def test_commands(runner, command, args, expected_output):
    result = runner.invoke(invoke_presets_cli, command)
    # print(f"Command: {command}")
    # print(f"Exit Code: {result.exit_code}")
    # print(f"Output: {result.stdout}")
    assert result.exit_code == args
    if expected_output:
        assert expected_output in result.stdout


def test_invalid_command(runner):
    result = runner.invoke(
        invoke_presets_cli, ["nonexistent-command"], catch_exceptions=False
    )
    # print("Command: nonexistent-command")
    # print(f"Exit Code: {result.exit_code}")
    # print(f"Output: {result.stdout}")
    assert result.exit_code == 2
    assert "No such command 'nonexistent-command'." in result.stdout
