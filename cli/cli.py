import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich import print as rprint
import questionary
from questionary import Style
import subprocess
import sys
from pathlib import Path
from .ollama_manager import select_model, check_ollama_installed, install_ollama

console = Console()
app = typer.Typer()

custom_style = Style(
    [
        ("question", "fg:#ffffff bold"),
        ("answer", "fg:#39ff14"),
        ("pointer", "fg:#39ff14 bold"),
        ("highlighted", "fg:#0087ff"),
        ("selected", "fg:#39ff14"),
    ]
)


@app.command()
def main():
    console.print(Panel.fit("🤖 Welcome to Aria LLM Runner", border_style="blue"))

    llm_choice = questionary.select(
        "Choose your LLM backend",
        choices=[
            {"name": "Default LLM", "value": "default"},
            {"name": "Ollama", "value": "ollama"},
        ],
        style=custom_style,
        qmark="➜",
    ).ask()

    start_server_path = Path(__file__).parent.parent / "start_server.py"

    if llm_choice == "ollama":
        if not check_ollama_installed():
            if questionary.confirm(
                "Ollama is not installed. Would you like to install it?",
                default=True,
                style=custom_style,
            ).ask():
                if not install_ollama():
                    return
            else:
                return

        if model := select_model():
            rprint(f"[green]Starting Aria with Ollama using model: {model}[/green]")
            subprocess.run([sys.executable, str(start_server_path), "ollama", model])
    else:
        rprint("[green]Starting Aria with default LLM configuration[/green]")
        subprocess.run([sys.executable, str(start_server_path), "default"])


if __name__ == "__main__":
    app()
