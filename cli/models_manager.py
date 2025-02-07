from pathlib import Path
import questionary
from rich.console import Console
from rich.panel import Panel
from questionary import Style
import shutil

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


def check_models_exist(directory: Path) -> dict:
    """Check which models exist in the given directory"""
    required_models = {
        "vad": "vad/silero_vad.onnx",
        "stt": "stt/whisper-large-v3",
        "tts": "tts/xtts_v2",
    }

    found_models = {}
    for model_type, path in required_models.items():
        model_path = directory / path
        found_models[model_type] = model_path.exists()

    return found_models


def handle_existing_models(project_dir: Path, default_dir: Path) -> tuple[Path, bool]:
    """Handle existing model installations"""
    project_models = check_models_exist(project_dir)
    default_models = check_models_exist(default_dir)

    if any(project_models.values()) or any(default_models.values()):
        # Show detected models
        console.print("\n[bold cyan]Detected models:[/bold cyan]")
        if any(project_models.values()):
            console.print(f"\nProject directory ({project_dir}):")
            for model_type, exists in project_models.items():
                status = "✓" if exists else "✗"
                console.print(f"  {status} {model_type.upper()}")

        if any(default_models.values()):
            console.print(f"\nDefault directory ({default_dir}):")
            for model_type, exists in default_models.items():
                status = "✓" if exists else "✗"
                console.print(f"  {status} {model_type.upper()}")

        # Ask what to do with existing models
        action = questionary.select(
            "\nFound existing models. What would you like to do?",
            choices=[
                "Use existing models",
                "Remove and download to new location",
                "Keep existing and download missing models",
            ],
            style=custom_style,
            qmark="➜",
        ).ask()

        if action == "Use existing models":
            # Use directory with most complete models
            project_count = sum(project_models.values())
            default_count = sum(default_models.values())

            if project_count >= default_count:
                return project_dir, False
            return default_dir, False

        elif action == "Keep existing and download missing models":
            # Choose directory for new downloads
            target_dir = questionary.select(
                "Where should missing models be downloaded?",
                choices=[
                    {
                        "name": f"Project directory ({project_dir})",
                        "value": project_dir,
                    },
                    {
                        "name": f"Default directory ({default_dir})",
                        "value": default_dir,
                    },
                ],
                style=custom_style,
                qmark="➜",
            ).ask()
            return target_dir, True

        # Remove and download new
        if any(project_models.values()):
            shutil.rmtree(project_dir, ignore_errors=True)
        if any(default_models.values()):
            shutil.rmtree(default_dir, ignore_errors=True)

    return select_new_model_location(project_dir, default_dir), True


def select_new_model_location(project_dir: Path, default_dir: Path) -> Path:
    """Select location for new model installation"""
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
        return Path(custom_path)
    return selected


def setup_models_directory() -> Path:
    """Setup the directory for storing models"""
    project_dir = Path(__file__).parent.parent / "models"
    default_dir = Path.home() / ".aria_models"

    # Handle existing model installations
    models_dir, need_download = handle_existing_models(project_dir, default_dir)

    # Create directory structure
    models_dir.mkdir(parents=True, exist_ok=True)
    for subdir in ["vad", "stt", "tts"]:
        (models_dir / subdir).mkdir(exist_ok=True)

    if need_download:
        console.print("\n[yellow]Checking for missing models...[/yellow]")
        missing_models = [
            model_type
            for model_type, exists in check_models_exist(models_dir).items()
            if not exists
        ]

        if missing_models:
            console.print(
                f"[yellow]Missing models: {', '.join(missing_models)}[/yellow]"
            )
            # TODO: Add your model download logic here
            console.print("[green]Models downloaded successfully![/green]")

    console.print(f"\n[green]Models directory: {models_dir}[/green]")
    return models_dir
