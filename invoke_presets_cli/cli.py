from .__version__ import __version__
import typer
from typing_extensions import Annotated


from .functions import display_presets

from rich.traceback import install

install()


"""
=========================================================================
Invoke styles - Simplified Tool for installing Invoke AI styling presets
=========================================================================

Invoke styles is a simplified tool for installing and updating Invoke AI
styles presets from the command line..


Usage:
$ pipx install invoke-styles (recommended)
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


@database_cli.command("create", help="Create a snapshot of the Invoke AI database.")
def datebase_create_command():
    pass


@database_cli.command("list", help="List all available snapshots.")
def database_list_command():
    pass


@invoke_styles_cli.command("import", help="Import a style preset")
def styles_import_command():
    pass


@invoke_styles_cli.command("export", help="Export a style preset")
def styles_export_command():
    pass


@invoke_styles_cli.command("list", help="List all available style presets.")
def styles_list_command(
    show_defaults: Annotated[
        bool,
        typer.Option(
            "--with-defaults",
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
