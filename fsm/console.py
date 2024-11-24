from libtmux import Session
from rich.console import Console
from rich.style import Style
from rich.theme import Theme

theme = Theme(
    {
        "error": Style(color="red", bold=True),
        "warning": Style(color="yellow", italic=True),
        "info": Style(color="cyan"),
    }
)
console = Console(theme=theme)


def print_error(message):
    console.print(f"Error: {message}", style="error")


def print_warning(message):
    console.print(f"Warning: {message}", style="warning")


def pretty_print(text):
    console.print(text)


def print_list(array: list, header: str = "", repr: bool = False):
    if array and header:
        console.print(header, style="info")

    for a in array:
        if repr:
            console.print(f" - {a!r}")
        else:
            console.print(f" - {a}")


def confirm(prompt):
    console.print(f"{prompt}")


def mark_as_ssh(text):
    return f"{text} ([green]SSH[/green])"
