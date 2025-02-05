from pathlib import Path
import questionary
from rich.console import Console
from rich.panel import Panel
from questionary import Style

console = Console()
custom_style = Style(
    [
        ("question", "fg:#ffffff bold"),
        ("answer", "fg:#39ff14"),
        ("pointer", "fg:#39ff14 bold"),
    ]
)


def create_project_models_dir() -> Path:
    """Create and initialize project models directory"""
    project_dir = Path(__file__).parent.parent / "models"
    project_dir.mkdir(exist_ok=True)

    # Create .gitkeep to preserve directory structure
    (project_dir / ".gitkeep").touch(exist_ok=True)

    # Create model type subdirectories
    subdirs = ["vad", "stt", "tts"]
    for subdir in subdirs:
        (project_dir / subdir).mkdir(exist_ok=True)

    return project_dir


def setup_models_directory() -> Path:
    """Setup the directory for storing models"""
    project_dir = Path(__file__).parent.parent / "models"
    default_dir = Path.home() / ".aria_models"

    console.print(Panel.fit("📦 Model Storage Configuration", border_style="cyan"))

    choices = [
        {"name": f"Project directory ({project_dir})", "value": project_dir},
        {"name": f"Home directory ({default_dir})", "value": default_dir},
        {"name": "Custom directory", "value": "custom"},
    ]

    selected = questionary.select(
        "Where would you like to store the models?",
        choices=choices,
        style=custom_style,
        qmark="➜",
    ).ask()

    if selected == "custom":
        custom_path = questionary.path(
            "Enter custom directory path:", only_directories=True, style=custom_style
        ).ask()
        selected = Path(custom_path)
    elif selected == project_dir:
        selected = create_project_models_dir()

    # Ensure directory exists
    selected.mkdir(parents=True, exist_ok=True)

    # Create subdirectories if they don't exist
    for subdir in ["vad", "stt", "tts"]:
        (selected / subdir).mkdir(exist_ok=True)

    console.print(f"\n[green]Models will be stored in: {selected}[/green]")
    return selected
