import typer
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint
import questionary
from questionary import Style
import subprocess
import sys
from pathlib import Path
from cli.ollama_manager import select_model

app = typer.Typer()
console = Console()

custom_style = Style(
    [
        ("question", "fg:#ffffff bold"),
        ("answer", "fg:#39ff14"),
        ("pointer", "fg:#39ff14 bold"),
        ("highlighted", "fg:#0087ff"),
        ("selected", "fg:#39ff14"),
    ]
)


def start_default_server():
    server_path = Path(__file__).parent / "server" / "server.py"
    subprocess.run([sys.executable, str(server_path)])


def start_ollama_server(model_name: str = None):
    server_path = Path(__file__).parent / "server" / "server_ollama.py"
    if model_name:
        subprocess.run([sys.executable, str(server_path), "--model", model_name])
    else:
        if selected_model := select_model():
            subprocess.run(
                [sys.executable, str(server_path), "--model", selected_model]
            )


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Interactive CLI to start Aria server
    """
    if ctx.invoked_subcommand is None:
        console.print(Panel.fit("🤖 Welcome to Aria Server", border_style="blue"))

        server_type = questionary.select(
            "Choose your server type",
            choices=[
                {"name": "Original Aria Server", "value": "default"},
                {"name": "Ollama", "value": "ollama"},
            ],
            style=custom_style,
            qmark="➜",
        ).ask()

        if server_type == "ollama":
            start_ollama_server()
        else:
            start_default_server()


@app.command()
def start(server_type: str = "default", model: str = None):
    """
    Start server with specific configuration
    """
    if server_type == "ollama":
        start_ollama_server(model)
    else:
        start_default_server()


if __name__ == "__main__":
    app()
