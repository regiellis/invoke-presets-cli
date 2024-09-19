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
$ invoke-styles [OPTIONS] [COMMAND] [ARGS]

Options:
    
    --help                                             Show this message and exit.

Examples:

$ invoke-styles 
"""

__all__ = ["invoke_styles_cli"]
__version__ = __version__

invoke_styles_cli = typer.Typer()
database_cli = typer.Typer()
utils_cli = typer.Typer()

invoke_styles_cli.add_typer(
    database_cli,
    name="database",
    help="Manage the snapshots of the Invoke AI database.",
    no_args_is_help=True,
)
invoke_styles_cli.add_typer(
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


@invoke_styles_cli.command("import", help="Import a style preset")
def styles_import_command():
    import_presets()


@invoke_styles_cli.command("export", help="Export a style preset")
def styles_export_command():
    export_presets()


@invoke_styles_cli.command("delete", help="Delete a style preset")
def styles_delete_command():
    delete_presets()


@invoke_styles_cli.command("list", help="List all available style presets.")
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
):
    display_presets(show_defaults, show_all)


@invoke_styles_cli.command("about", help="Functions for information on this tool.")
def about_command():
    pass


ensure_snapshots_dir()
