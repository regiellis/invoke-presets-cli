import os
import json
from typing import List, Dict, Any, Final, Optional

import sqlite3
from sqlite_utils import Database

from .helpers import feedback_message, create_table, add_rows_to_table

from . import INVOKE_AI_DIR, SNAPSHOTS

from rich.console import Console
from rich.traceback import install

install()

console = Console()

DATABASE = Database(os.path.join(INVOKE_AI_DIR, "databases", "invokeai.db"))
PRESET_TABLE = DATABASE["style_presets"]

METADATA = {
    "name": PRESET_TABLE.name,
    "pk": PRESET_TABLE.pks,
    "foreign_keys": PRESET_TABLE.foreign_keys,
    "column_order": PRESET_TABLE.columns,
    "count": PRESET_TABLE.count,
}

__all__ = [
    "get_presets_list",
]


# ANCHOR: PRESET FUNCTIONS START
def get_presets_list(show_defaults: bool, show_all: bool) -> List[Dict[str, Any]]:
    base_query = "SELECT * FROM style_presets"

    conditions = {
        (False, False): "WHERE type = 'user'",
        (False, True): "",
        (True, False): "WHERE type = 'default'",
    }

    condition = conditions.get((show_defaults, show_all), "WHERE type = 'default'")
    query = f"{base_query} {condition}".strip()
    return DATABASE.execute(query).fetchall()

def process_preset_file(file_path: str) -> Dict[str, Any]:
    pass

def import_preset(preset: Dict[str, Any]) -> None:
    pass

def export_preset(preset: Dict[str, Any]) -> None:
    pass

def delete_preset(preset: Dict[str, Any]) -> None:
    pass

def update_preset(preset: Dict[str, Any]) -> None:
    pass


def display_presets(show_defaults: bool, show_all: bool) -> None:
    presets = get_presets_list(show_defaults, show_all)

    presets_table = create_table(
        "Available presets",
        [("ID", "yellow dim"), ("Name", "white"), ("Prompts", "white")],
    )
    for preset in presets:
        prompts_data = json.loads(preset[2])
        prompts_formmated = f"[blue]Positive Prompt: {prompts_data['positive_prompt']}[/blue] \
             \n[yellow dim]Negative Prompt: {prompts_data['negative_prompt']}[/yellow dim]"
        
        presets_table.add_row(
            preset[0],
            preset[1],
            str(prompts_formmated),
        )

    console.print(presets_table)
    
    
# ANCHOR: PRESET FUNCTIONS END

# ANCHOR: DATABASE FUNCTIONS START
def create_snapshot() -> None:
    pass

def list_snapshots() -> None:
    pass

def delete_snapshot() -> None:
    pass


# ANCHOR: DATABASE FUNCTIONS END

# ANCHOR: UTILS FUNCTIONS START

# ANCHOR: UTILS FUNCTIONS END

# ANCHOR: ABOUT FUNCTIONS START
def about() -> None:
    pass

def change_log() -> None:
    pass
# ANCHOR: ABOUT FUNCTIONS END