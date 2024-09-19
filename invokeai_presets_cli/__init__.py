import os
import inquirer
from pathlib import Path
from typing import Final
from dotenv import load_dotenv, set_key

from .helpers import feedback_message


def get_required_input(prompt: str) -> str:
    """
    Prompt for invoke install location [required].

    :param prompt: The prompt to display to the user.
    :return: The non-empty user input.
    """
    while True:
        questions = [
            inquirer.Text(
                "response", message=prompt, validate=lambda _, x: x.strip() != ""
            )
        ]
        answers = inquirer.prompt(questions)
        if answers and answers["response"]:
            return answers["response"].strip()
        feedback_message("Required. Please enter a valid location.", "warning")


def validate_directory(path: str) -> str:
    """
    Validate that the given path is a directory and create it if it doesn't exist.

    :param path: The directory path to validate.
    :return: The validated directory path.
    """
    dir_path = Path(path).expanduser().resolve()
    if not dir_path.exists():
        try:
            dir_path.mkdir(parents=True)
            feedback_message(f"Created directory: {dir_path}", "info")
        except Exception as e:
            feedback_message(f"Error creating directory: {e}", "error")
            return validate_directory(
                get_required_input("Please enter a valid directory path: ")
            )
    elif not dir_path.is_dir():
        feedback_message(f"{dir_path} is not a directory.", "error")
        return validate_directory(
            get_required_input("Please enter a valid directory path: ")
        )
    return str(dir_path)


def create_env_file(env_path: Path) -> None:
    """
    Create a new .env file with user input for required environment variables.

    :param env_path: Path where the .env file will be created.
    """
    feedback_message(f"Creating new .env file at {env_path}", "info")

    # stable
    invokeai_dir = validate_directory(
        get_required_input("The path to your Invoke AI install directory: ")
    )
    set_key(env_path, "INVOKE_AI_DIR", invokeai_dir)

    feedback_message(f".env file created successfully at {env_path}", "info")


def load_environment_variables() -> None:
    """
    Load environment variables from a .env file or create one if not found.

    :raises FileNotFoundError: If the .env file is not found in any of the
    searched locations and user chooses not to create one.
    """
    env_locations = [
        "~/.config/invokeai-presets-itsjustregi/.env",
        "~/.invokeai-presets-itsjustregi/.env",
        "~/.env",
        "./.env",
    ]

    # fetch
    env_path = None
    for path in env_locations:
        env_path = Path(path).expanduser().resolve()
        if env_path.is_file():
            load_dotenv(env_path)
            return

    # create
    feedback_message(
        ".env file not found in any of the following locations:", "warning"
    )
    for path in env_locations:
        print(f"  - {Path(path).expanduser()}")

    create_new = inquirer.confirm(
        "Would you like to create a new .env file?", default=True
    )
    if create_new:
        default_path = Path("~/.config/invokeai-presets-itsjustregi/.env").expanduser()
        questions = [
            inquirer.Path(
                "env_path",
                message="Enter path for new .env file",
                default=str(default_path),
                exists=False,
                path_type=inquirer.Path.DIRECTORY,
            )
        ]
        answers = inquirer.prompt(questions)
        env_path = Path(answers["env_path"]).expanduser() if answers else default_path
        env_path.parent.mkdir(parents=True, exist_ok=True)
        create_env_file(env_path)
        load_dotenv(env_path)
    else:
        raise FileNotFoundError("No .env file found and user chose not to create one.")


# use
load_environment_variables()

# set
os.environ["INVOKE_AI_DIR"] = os.getenv("INVOKE_AI_DIR", "")
os.environ["SNAPSHOTS"] = os.getenv("SNAPSHOTS", "")

# define
INVOKE_AI_DIR: Final = os.environ["INVOKE_AI_DIR"]
SNAPSHOTS: Final = os.environ["SNAPSHOTS"]
