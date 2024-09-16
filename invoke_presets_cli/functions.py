import os
import json
import uuid
import httpx
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlite_utils import Database
import sqlite3
import inquirer

from .helpers import feedback_message, create_table, add_rows_to_table, random_name

from . import INVOKE_AI_DIR, SNAPSHOTS

from rich.console import Console

console = Console()

# Get the package directory
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.path.join(INVOKE_AI_DIR, "databases", "invokeai.db")
SNAPSHOTS_DIR = os.path.join(PACKAGE_DIR, "snapshots")
SNAPSHOTS_JSON = os.path.join(SNAPSHOTS_DIR, "snapshots.json")

__all__ = [
    "get_presets_list",
    "create_snapshot",
    "list_snapshots",
    "delete_snapshot",
    "restore_snapshot",
]


def get_db() -> Database:
    return Database(DATABASE_PATH)


# ANCHOR: PRESET FUNCTIONS START
def get_presets_list(show_defaults: bool, show_all: bool) -> List[Dict[str, Any]]:
    db = get_db()
    base_query = "SELECT * FROM style_presets"

    conditions = {
        (False, False): "WHERE type = 'user'",
        (False, True): "",
        (True, False): "WHERE type = 'default'",
    }

    condition = conditions.get((show_defaults, show_all), "WHERE type = 'default'")
    query = f"{base_query} {condition}".strip()
    return list(db.query(query))


def process_preset_file(file_path: str) -> Dict[str, Any]:
    pass


def import_presets() -> None:
    source = inquirer.list_input(
        "Select import source", choices=["Local File", "URL", "Cancel"]
    )

    if source == "Cancel":
        console.print("Import cancelled.")
        return

    if source == "Local File":
        file_path = inquirer.text(message="Enter the path to the JSON file")
        try:
            with open(file_path, "r") as f:
                presets_to_import = json.load(f)
        except Exception as e:
            console.print(f"[bold red]Error reading file:[/bold red] {str(e)}")
            return
    else:  # URL
        url = inquirer.text(message="Enter the URL of the JSON file")
        try:
            response = httpx.get(url)
            response.raise_for_status()
            presets_to_import = response.json()
        except Exception as e:
            console.print(f"[bold red]Error fetching from URL:[/bold red] {str(e)}")
            return

    if not isinstance(presets_to_import, list):
        console.print(
            "[bold red]Error:[/bold red] Invalid JSON format. Expected a list of presets."
        )
        return

    db = get_db()
    existing_presets = {
        preset["name"]: preset
        for preset in get_presets_list(show_defaults=True, show_all=True)
    }

    presets_to_update = []
    presets_to_create = []

    for preset in presets_to_import:
        if not validate_preset(preset):
            console.print(
                f"[yellow]Skipping invalid preset: {preset.get('name', 'Unknown')}[/yellow]"
            )
            continue

        if preset["name"] in existing_presets:
            presets_to_update.append(preset)
        else:
            presets_to_create.append(preset)

    if presets_to_update:
        update_choice = inquirer.list_input(
            "Some presets already exist. How would you like to proceed?",
            choices=["Update All", "Select Individually", "Skip Updates"],
        )

        if update_choice == "Update All":
            presets_to_update_final = presets_to_update
        elif update_choice == "Select Individually":
            choices = [
                inquirer.Checkbox(
                    "selected_presets",
                    message="Select presets to update",
                    choices=[preset["name"] for preset in presets_to_update],
                )
            ]
            answers = inquirer.prompt(choices)
            presets_to_update_final = [
                preset
                for preset in presets_to_update
                if preset["name"] in answers["selected_presets"]
            ]
        else:
            presets_to_update_final = []

    # Create a snapshot before making changes
    create_snapshot()

    # Perform database operations
    try:
        with db.conn:  
            for preset in presets_to_update_final:
                update_preset(preset)

            for preset in presets_to_create:
                create_preset(preset) 

        console.print(
            f"[green]Import complete. Created {len(presets_to_create)} new presets and updated {len(presets_to_update_final)} existing presets.[/green]"
        )
    except Exception as e:
        console.print(f"[bold red]Error during import:[/bold red] {str(e)}")
        console.print("[yellow]All changes have been rolled back.[/yellow]")



def update_preset(preset: Dict[str, Any]) -> None:
    db = get_db()
    preset_data = json.dumps(preset["preset_data"])
    db.execute(
        "UPDATE style_presets SET preset_data = ?, updated_at = ? WHERE name = ?",
        [preset_data, datetime.now().isoformat(), preset["name"]],
    )


def create_preset(preset: Dict[str, Any]) -> None:
    db = get_db()
    preset_id = str(uuid.uuid4())
    preset_data = json.dumps(preset["preset_data"])
    now = datetime.now().isoformat()
    db.execute(
        "INSERT INTO style_presets (id, name, preset_data, type, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        [preset_id, preset["name"], preset_data, preset["type"], now, now],
    )


def validate_preset(preset: Dict[str, Any]) -> bool:
    required_keys = ["name", "type", "preset_data"]
    if not all(key in preset for key in required_keys):
        return False
    if not isinstance(preset["preset_data"], dict):
        return False
    if (
        "positive_prompt" not in preset["preset_data"]
        or "negative_prompt" not in preset["preset_data"]
    ):
        return False
    return True


def export_presets() -> None:
    presets = get_presets_list(show_defaults=False, show_all=True)

    if not presets:
        console.print("[yellow]No presets found to export.[/yellow]")
        return

    choices = [f"{preset['name']} (ID: {preset['id']})" for preset in presets]
    questions = [
        inquirer.Checkbox(
            "selected_presets", message="Select presets to export", choices=choices
        )
    ]

    answers = inquirer.prompt(questions)

    if not answers or not answers["selected_presets"]:
        console.print("Export cancelled.")
        return

    selected_presets = [
        preset
        for preset in presets
        if f"{preset['name']} (ID: {preset['id']})" in answers["selected_presets"]
    ]

    export_data = []
    for preset in selected_presets:
        export_data.append(
            {
                "name": preset["name"],
                "type": preset["type"],
                "preset_data": json.loads(preset["preset_data"]),
            }
        )

    export_filename = inquirer.text(
        message="Enter the export filename (without extension)"
    )
    export_path = f"{export_filename}.json"

    try:
        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2)
        console.print(f"[green]Presets exported successfully to {export_path}[/green]")
    except Exception as e:
        console.print(f"[bold red]Error exporting presets:[/bold red] {str(e)}")


def delete_presets() -> None:
    db = get_db()
    
    delete_source = inquirer.list_input(
        "Select delete source",
        choices=["Select from list", "Import from file", "Import from URL", "Cancel"]
    )

    if delete_source == "Cancel":
        console.print("Deletion cancelled.")
        return

    presets_to_delete = []

    if delete_source == "Select from list":
        all_presets = get_presets_list(show_defaults=False, show_all=True)
        choices = [f"{preset['name']} (ID: {preset['id']})" for preset in all_presets]
        questions = [
            inquirer.Checkbox('selected_presets',
                              message="Select presets to delete",
                              choices=choices)
        ]
        answers = inquirer.prompt(questions)
        if not answers or not answers['selected_presets']:
            console.print("No presets selected for deletion.")
            return
        presets_to_delete = [preset for preset in all_presets 
                             if f"{preset['name']} (ID: {preset['id']})" in answers['selected_presets']]
    elif delete_source in ["Import from file", "Import from URL"]:
        if delete_source == "Import from file":
            file_path = inquirer.text(message="Enter the path to the JSON file")
            try:
                with open(file_path, 'r') as f:
                    preset_names = json.load(f)
            except Exception as e:
                console.print(f"[bold red]Error reading file:[/bold red] {str(e)}")
                return
        else:  # Import from URL
            url = inquirer.text(message="Enter the URL of the JSON file")
            try:
                response = httpx.get(url)
                response.raise_for_status()
                preset_names = response.json()
            except Exception as e:
                console.print(f"[bold red]Error fetching from URL:[/bold red] {str(e)}")
                return

        if not isinstance(preset_names, list):
            console.print("[bold red]Error:[/bold red] Invalid JSON format. Expected a list of preset names.")
            return

        all_presets = get_presets_list(show_defaults=False, show_all=True)
        presets_to_delete = [preset for preset in all_presets if preset['name'] in preset_names]

    if not presets_to_delete:
        console.print("[yellow]No presets found to delete.[/yellow]")
        return

    # Confirmation
    preset_names = ", ".join([preset['name'] for preset in presets_to_delete])
    confirm = inquirer.confirm(
        f"Are you sure you want to delete the following presets: {preset_names}? This action is irreversible."
    )
    if not confirm:
        console.print("Deletion cancelled.")
        return

    # Create a snapshot before making changes
    create_snapshot()

    # Perform deletion
    try:
        with db.conn:  # This automatically manages transactions
            for preset in presets_to_delete:
                db.execute("DELETE FROM style_presets WHERE id = ?", [preset['id']])

        console.print(f"[green]Successfully deleted {len(presets_to_delete)} presets.[/green]")
    except Exception as e:
        console.print(f"[bold red]Error during deletion:[/bold red] {str(e)}")
        console.print("[yellow]All changes have been rolled back.[/yellow]")


def update_preset(preset: Dict[str, Any]) -> None:
    pass


def display_presets(show_defaults: bool, show_all: bool) -> None:
    presets = get_presets_list(show_defaults, show_all)

    presets_table = create_table(
        "Available presets",
        [("ID", "yellow"), ("Name", "white"), ("Prompts", "white")],
    )
    for preset in presets:
        prompts_data = json.loads(preset["preset_data"])
        prompts_formatted = f"[blue]Positive Prompt: {prompts_data['positive_prompt']}[/blue] \
             \n[yellow]Negative Prompt: {prompts_data['negative_prompt']}[/yellow]"

        presets_table.add_row(
            str(preset.get("id", "Unknown UID")),
            preset.get("name", "Unknown name"),
            prompts_formatted,
        )

    console.print(presets_table)


# ANCHOR: PRESET FUNCTIONS END


# ANCHOR: DATABASE FUNCTIONS START
def create_snapshot() -> None:
    if not os.access(SNAPSHOTS_DIR, os.W_OK):
        console.print(
            "[bold red]Error:[/bold red] No write permission for the snapshots directory."
        )
        return

    # Generate a human-readable timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    snapshot_name = f"{random_name()}_{timestamp.replace(':', '-')}.db"
    snapshot_path = os.path.join(SNAPSHOTS_DIR, snapshot_name)

    try:
        # Use SQLite backup API
        with sqlite3.connect(DATABASE_PATH) as source_conn:
            with sqlite3.connect(snapshot_path) as dest_conn:
                source_conn.backup(dest_conn)

        snapshots = load_snapshots()
        snapshots.append({"name": snapshot_name, "timestamp": timestamp})

        if len(snapshots) > int(SNAPSHOTS):
            oldest_snapshot = snapshots.pop(0)
            old_snapshot_path = os.path.join(SNAPSHOTS_DIR, oldest_snapshot["name"])
            if os.path.exists(old_snapshot_path):
                os.remove(old_snapshot_path)
                console.print(f"Removed oldest snapshot: {oldest_snapshot['name']}")

        save_snapshots(snapshots)
        console.print(f"[green]Snapshot created successfully: {snapshot_name}[/green]")
    except Exception as e:
        console.print(f"[bold red]Error creating snapshot:[/bold red] {str(e)}")


def load_snapshots() -> List[Dict[str, str]]:
    if os.path.exists(SNAPSHOTS_JSON):
        try:
            with open(SNAPSHOTS_JSON, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            console.print(
                "[bold yellow]Warning:[/bold yellow] Snapshots file is corrupted. Starting with an empty list."
            )
    return []


def save_snapshots(snapshots: List[Dict[str, str]]) -> None:
    try:
        with open(SNAPSHOTS_JSON, "w") as f:
            json.dump(snapshots, f, indent=2)
    except Exception as e:
        console.print(f"[bold red]Error saving snapshots metadata:[/bold red] {str(e)}")


def list_snapshots() -> None:
    snapshots = load_snapshots()
    if not snapshots:
        console.print("[yellow]No snapshots found.[/yellow]")
        return

    snapshots_table = create_table(
        "Database Snapshots",
        [("Name", "white"), ("Timestamp", "yellow dim")],
    )
    for snapshot in snapshots:
        snapshots_table.add_row(snapshot["name"], snapshot["timestamp"])
    console.print(snapshots_table)


def delete_snapshot() -> None:
    snapshots = load_snapshots()

    if not snapshots:
        console.print("[yellow]No snapshots found to delete.[/yellow]")
        return

    # Create choices for the inquirer prompt
    choices = [f"{s['name']} ({s['timestamp']})" for s in snapshots]
    choices.append("Cancel")

    # Create the selection prompt
    questions = [
        inquirer.List(
            "snapshot",
            message="Select a snapshot to delete",
            choices=choices,
            default="Cancel",
        )
    ]

    # Present the selection menu
    answers = inquirer.prompt(questions)

    if not answers or answers["snapshot"] == "Cancel":
        console.print("Deletion cancelled.")
        return

    # Extract the snapshot name from the selection
    snapshot_name = answers["snapshot"].split(" (")[0]
    snapshot_to_delete = next(
        (s for s in snapshots if s["name"] == snapshot_name), None
    )

    if not snapshot_to_delete:
        console.print(f"[yellow]Error: Selected snapshot not found.[/yellow]")
        return

    # Confirmation prompt
    confirm = inquirer.confirm(
        "Are you sure you want to delete this snapshot? This action is irreversible."
    )

    if not confirm:
        console.print("Deletion cancelled.")
        return

    snapshots = [s for s in snapshots if s["name"] != snapshot_name]
    save_snapshots(snapshots)

    snapshot_path = os.path.join(SNAPSHOTS_DIR, snapshot_name)
    if os.path.exists(snapshot_path):
        try:
            os.remove(snapshot_path)
            console.print(
                f"[green]Snapshot '{snapshot_name}' deleted successfully.[/green]"
            )
        except Exception as e:
            console.print(
                f"[bold red]Error deleting snapshot file:[/bold red] {str(e)}"
            )
    else:
        console.print(
            f"[yellow]Warning: Snapshot file '{snapshot_name}' not found on disk.[/yellow]"
        )


def restore_snapshot():
    snapshots = load_snapshots()

    if not snapshots:
        console.print("[yellow]No snapshots found to restore.[/yellow]")
        return

    # Create choices for the inquirer prompt
    choices = [f"{s['name']} ({s['timestamp']})" for s in snapshots]
    choices.append("Cancel")

    # Create the selection prompt
    questions = [
        inquirer.List(
            "snapshot",
            message="Select a snapshot to restore",
            choices=choices,
            default="Cancel",
        )
    ]

    # Present the selection menu
    answers = inquirer.prompt(questions)

    if not answers or answers["snapshot"] == "Cancel":
        console.print("Restoration cancelled.")
        return

    # Extract the snapshot name from the selection
    snapshot_name = answers["snapshot"].split(" (")[0]
    snapshot_to_restore = next(
        (s for s in snapshots if s["name"] == snapshot_name), None
    )

    if not snapshot_to_restore:
        console.print("[bold red]Error:[/bold red] Selected snapshot not found.")
        return

    # Confirmation prompt
    confirm = inquirer.confirm(
        "Are you sure you want to restore this snapshot? This will replace your current database."
    )

    if not confirm:
        console.print("Restoration cancelled.")
        return

    snapshot_path = os.path.join(SNAPSHOTS_DIR, snapshot_name)
    if not os.path.exists(snapshot_path):
        console.print(
            f"[bold red]Error:[/bold red] Snapshot file '{snapshot_name}' not found on disk."
        )
        return

    # Backup current database
    backup_path = DATABASE_PATH + ".backup"
    try:
        shutil.copy2(DATABASE_PATH, backup_path)
        console.print(f"[green]Current database backed up to {backup_path}[/green]")
    except Exception as e:
        console.print(
            f"[bold red]Error backing up current database:[/bold red] {str(e)}"
        )
        return

    # Restore snapshot
    try:
        shutil.copy2(snapshot_path, DATABASE_PATH)
        console.print(
            f"[green]Snapshot '{snapshot_name}' successfully restored.[/green]"
        )
    except Exception as e:
        console.print(f"[bold red]Error restoring snapshot:[/bold red] {str(e)}")
        # If restoration fails, try to restore the backup
        try:
            shutil.copy2(backup_path, DATABASE_PATH)
            console.print(
                "[yellow]Restoration failed. Original database has been restored.[/yellow]"
            )
        except Exception as e2:
            console.print(
                f"[bold red]Error restoring original database:[/bold red] {str(e2)}"
            )
            console.print(
                "[bold yellow]Please manually restore your database from the backup file.[/bold yellow]"
            )
    finally:
        # Clean up the backup file
        if os.path.exists(backup_path):
            os.remove(backup_path)


def ensure_snapshots_dir():
    if not os.path.exists(SNAPSHOTS_DIR):
        try:
            os.makedirs(SNAPSHOTS_DIR)
            console.print(
                f"[green]Created snapshots directory: {SNAPSHOTS_DIR}[/green]"
            )
        except Exception as e:
            console.print(
                f"[bold red]Error creating snapshots directory:[/bold red] {str(e)}"
            )
            return False
    return True


# ANCHOR: DATABASE FUNCTIONS END


# ANCHOR: ABOUT FUNCTIONS START
def about() -> None:
    pass


def changelog() -> None:
    pass


# ANCHOR: ABOUT FUNCTIONS END
