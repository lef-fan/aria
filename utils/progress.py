from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeRemainingColumn,
)
from rich.console import Console
from contextlib import contextmanager

console = Console()


@contextmanager
def track_progress(description: str):
    """Context manager for tracking progress with a nice display"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[bold green]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(description, total=None)
        yield lambda x: progress.update(task, completed=x * 100)


@contextmanager
def show_status(message: str, style: str = "bold blue"):
    """Show a status message with a spinner"""
    with console.status(f"[{style}]{message}[/{style}]", spinner="dots") as status:
        yield status
