import typer

from typing import Dict, Any
from rich.console import Console
from rich.table import Table

console = Console(soft_wrap=True)

__all__ = [
    "feedback_message",
    "create_table",
    "add_rows_to_table",
]


def feedback_message(message: str, type: str = "info") -> None:
    options = {
        "types": {
            "simple": "white",
            "info": "white",
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "exception": "red",
        },
        "titles": {
            "info": "Information",
            "success": "Success",
            "warning": "Warning",
            "error": "Error Message",
            "exception": "Exception Message",
        },
    }

    if type not in options["types"]:
        return None

    if type == "simple":
        console.print(message)
        # return message with a exclamation icon
        console.print(f"[yellow]![/yellow] {message}")
        return None

    feedback_message_table = Table(style=options["types"][type])
    feedback_message_table.add_column(options["titles"][type])
    feedback_message_table.add_row(message)

    if type == "exception":
        console.print_exception(feedback_message_table)
        raise typer.Exit()
    console.print(feedback_message_table)
    return None


def create_table(title: str, columns: list) -> Table:
    table = Table(title=title, title_justify="left")
    for col_name, style in columns:
        table.add_column(col_name, style=style)
    return table


def add_rows_to_table(table: Table, data: Dict[str, Any]) -> None:
    for key, value in data.items():
        if isinstance(value, list):
            value = ", ".join(map(str, value))
        table.add_row(key, str(value))
