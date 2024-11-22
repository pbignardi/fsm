from rich.console import Console
from rich.style import Style
from rich.theme import Theme

theme = Theme(
    {
        "error": Style(color="red", bold=True),
        "warning": Style(color="yellow", italic=True),
    }
)
console = Console(theme=theme)


def print_error(message):
    console.print(f"Error: {message}", style="error")


def print_warning(message):
    console.print(f"Warning: {message}", style="warning")


def pretty_print(text):
    console.print(text)
