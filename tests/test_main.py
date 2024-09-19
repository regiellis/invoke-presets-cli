import os
import re
import io
import pytest
import json
import sqlite3


from typer.testing import CliRunner
from invokeai_presets_cli.cli import invoke_presets_cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_db(tmp_path):
    # Create a temporary database file
    db_path = tmp_path / "test_presets.db"
    os.environ["INVOKEAI_PRESETS_DB"] = str(db_path)

    # Create the database and set up the schema
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create the necessary tables (adjust according to your actual schema)
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS presets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        type TEXT NOT NULL,
        preset_data TEXT NOT NULL
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        timestamp TEXT NOT NULL
    )
    """
    )

    conn.commit()
    conn.close()

    yield db_path

    # Clean up
    if os.path.exists(db_path):
        os.unlink(db_path)
    else:
        print(f"Warning: Database file {db_path} not found during cleanup")


# TODO Finish write tests when the boy is sleep


def strip_ansi(text):
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def simplify_rich_output(text):
    text = strip_ansi(text)
    text = re.sub(r"[│├─┤┌┐└┘┏┓┗┛]", "+", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def test_create_snapshot(runner, mock_db):
    result = runner.invoke(invoke_presets_cli, ["database", "create-snapshot"])
    simplified_output = simplify_rich_output(result.stdout)
    assert result.exit_code == 0
    assert re.search(r"Created snapshot: .+\.db", simplified_output)
    assert "Success" in simplified_output


def test_list_snapshots(runner, mock_db):
    runner.invoke(invoke_presets_cli, ["database", "create-snapshot"])
    result = runner.invoke(invoke_presets_cli, ["database", "list-snapshots"])
    simplified_output = simplify_rich_output(result.stdout)
    assert result.exit_code == 0
    assert "Database Snapshots" in simplified_output
    assert re.search(r"\d{4}-\d{2}-\d{2}", simplified_output)


def test_list_presets(runner, mock_db):
    result = runner.invoke(invoke_presets_cli, ["list"])
    simplified_output = simplify_rich_output(result.stdout)
    print(f"List presets output: {simplified_output}")  # Debug print
    assert result.exit_code == 0
    assert (
        "Available presets:" in simplified_output
        or "No presets found" in simplified_output
    )


def test_nonexistent_command(runner):
    result = runner.invoke(invoke_presets_cli, ["nonexistent"])
    simplified_output = simplify_rich_output(result.stdout)
    assert result.exit_code != 0
    assert "No such command" in simplified_output


def test_invalid_option(runner):
    result = runner.invoke(
        invoke_presets_cli, ["database", "list-snapshots", "--invalid-option"]
    )
    simplified_output = simplify_rich_output(result.stdout)
    assert result.exit_code != 0
    assert (
        "root database list-snapshots [OPTIONS] Try 'root database list-snapshots"
        in simplified_output
    )
