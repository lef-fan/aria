import subprocess
import platform
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
import questionary
from questionary import Style
from utils.progress import track_progress, show_status

console = Console()

custom_style = Style(
    [
        ("question", "fg:#ffffff bold"),
        ("answer", "fg:#39ff14"),  # Bright green for selected
        ("pointer", "fg:#39ff14 bold"),  # Bright green for pointer
        ("highlighted", "fg:#0087ff"),  # Blue for highlighted
        ("selected", "fg:#39ff14"),  # Bright green for selected
    ]
)


def check_ollama_installed():
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def install_ollama():
    system = platform.system().lower()
    if system == "linux":
        with track_progress("Installing Ollama") as update_progress:
            try:
                process = subprocess.Popen(
                    ["curl", "-L", "https://ollama.ai/install.sh"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for i, _ in enumerate(process.stdout):
                    update_progress(i / 100)  # Approximate progress
                return True
            except subprocess.CalledProcessError:
                console.print(
                    "[red]Failed to install Ollama. Please install manually from https://ollama.ai[/red]"
                )
                return False
    else:
        console.print(
            "[red]Please install Ollama manually from https://ollama.ai[/red]"
        )
        return False


def get_available_models():
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode == 0:
            models = []
            for line in result.stdout.split("\n")[1:]:
                if line.strip():
                    models.append(line.split()[0])
            return models
        return []
    except:
        return []


def select_model():
    if not check_ollama_installed():
        console.print("[red]Ollama is not installed. Please install it first.[/red]")
        return None

    models = get_available_models()
    if not models:
        console.print(
            "[yellow]No models found. Pulling default llama2 model...[/yellow]"
        )
        with track_progress("Downloading llama2 model") as update_progress:
            process = subprocess.Popen(
                ["ollama", "pull", "llama2"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for i, line in enumerate(process.stdout):
                update_progress(min(i / 100, 0.99))  # Show progress up to 99%
            update_progress(1.0)  # Complete the progress bar
        models = ["llama2"]

    console.print("\n[blue]Available Models:[/blue]")
    selected_model = questionary.select(
        "",
        choices=models,
        default=models[0] if models else None,
        style=custom_style,
        qmark="➜",  # Changed from use_pointer to qmark
    ).ask()

    return selected_model
