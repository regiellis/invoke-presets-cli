from .__version__ import __version__
import typer
from typing_extensions import Annotated


from .functions import (
    ensure_snapshots_dir,
    display_presets,
    list_snapshots,
    delete_snapshot,
    restore_snapshot,
    create_snapshot,
    export_presets,
    import_presets,
    delete_presets,
    about_cli,
)

from rich.traceback import install

install()


"""
=========================================================================
Invoke Preset CLI - Simplified Tool for installing Invoke AI styling presets
=========================================================================

Invoke preset is a simplified tool for installing and updating Invoke AI
styles presets from the command line.


Usage:
$ pipx install invoke-presets (recommended)
$ pipx install . (if you want to install it globally)
$ pip install -e . (if you want to install it locally and poke around, 
make sure to create a virtual environment)
$ invoke-presets [OPTIONS] [COMMAND] [ARGS]

Commands:

invoke-presets about --readme --changelog --version [-c, -r, -v]
invoke-presets list [--all, --only-defaults]
invoke-presets database create-snapshot
invoke-presets database list-snapshots
invoke-presets database delete-snapshot
invoke-presets database restore-snapshot
invoke-presets tools
invoke-presets export 
invoke-presets import 
invoke-presets delete
"""

__all__ = ["invoke_presets_cli"]
__version__ = __version__

invoke_presets_cli = typer.Typer()
database_cli = typer.Typer()
utils_cli = typer.Typer()

invoke_presets_cli.add_typer(
    database_cli,
    name="database",
    help="Manage the snapshots of the Invoke AI database.",
    no_args_is_help=True,
)
invoke_presets_cli.add_typer(
    utils_cli, name="tools", help="Utilities.", no_args_is_help=True
)


@database_cli.command(
    "create-snapshot", help="Create a snapshot of the Invoke AI database."
)
def datebase_create_command():
    create_snapshot()


@database_cli.command("list-snapshots", help="List all available snapshots.")
def database_list_command():
    list_snapshots()


@database_cli.command(
    "delete-snapshot", help="Delete a snapshot of the Invoke AI database."
)
def database_delete_command():
    delete_snapshot()


@database_cli.command(
    "restore-snapshot", help="Restore a snapshot of the Invoke AI database."
)
def database_restore_command():
    restore_snapshot()


@invoke_presets_cli.command("import", help="Import a style preset")
def styles_import_command(
    project_type: Annotated[
        bool,
        typer.Option(
            "--project",
            "-p",
            help="The type of preset to import, either 'user' or 'project'. Default is 'user'",
            show_default="False",
        ),
    ] = False
):
    import_presets(project_type)


@invoke_presets_cli.command("export", help="Export a style preset")
def styles_export_command():
    export_presets()


@invoke_presets_cli.command("delete", help="Delete a style preset")
def styles_delete_command():
    delete_presets()


@invoke_presets_cli.command("list", help="List all available style presets.")
def styles_list_command(
    show_defaults: Annotated[
        bool,
        typer.Option(
            "--only-defaults",
            help="Show presets installed by Invoke AI Team.",
            show_default="False",
        ),
    ] = False,
    show_all: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Show all presets.",
            show_default="False",
        ),
    ] = False,
    show_project: Annotated[
        bool,
        typer.Option(
            "--projects",
            help="Show project presets.",
            show_default="False",
        ),
    ] = False,
    page: Annotated[
        int,
        typer.Option(
            "--page",
            help="Page number to display.",
            show_default="1",
        ),
    ] = 1,
    items_per_page: Annotated[
        int,
        typer.Option(
            "--items-per-page",
            help="Number of items to display per page.",
            show_default="10",
        ),
    ] = 10,
):
    display_presets(show_defaults, show_all, show_project, page, items_per_page)


@invoke_presets_cli.command("about", help="Functions for information on this tool.")
def about_command(
    readme: bool = typer.Option(
        True, "--readme", "-r", help="Show the README.md content"
    ),
    changelog: bool = typer.Option(
        False, "--changelog", "-c", help="Show the CHANGELOG.md content"
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show the current version",
    ),
):
    """
    Show README.md and/or CHANGELOG.md content.
    """

    if version:
        typer.echo(f"InvokeAI Preset CLI version: {__version__}", color=True)
        return

    about_cli(readme, changelog)
