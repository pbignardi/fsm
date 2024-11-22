import os
from collections import deque
from pathlib import Path

import typer
from rich.prompt import Confirm

from fsm.config import Config, config_app, load
from fsm.utils import clean_session_name, get_hosts

desc = "Fuzzily create and manage Tmux session for directories and SSH hosts."
app = typer.Typer(
    help=desc,
    pretty_exceptions_show_locals=False,
    add_help_option=False,
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode=None,
)
app.add_typer(config_app, name="config")


@app.command()
def switch():
    """
    Switch to existing session
    """
    # load config
    config_table = Config()
    server, picker = load(config_table)
    sessions = [s.name for s in server.sessions if s.name]
    session_name = picker.choose(sessions)
    if session_name:
        if "TMUX" in os.environ:
            server.switch_client(session_name)
        else:
            server.attach_session(session_name)


@app.command()
def create():
    """
    Create new session, or switch if already exists
    """
    # load config from file
    config_table = Config()
    server, picker = load(config_table)
    paths: deque[Path] = deque()

    # scan all include-dirs
    for include_path in config_table.include:
        path = Path(include_path).expanduser().absolute()
        glob_pattern = "/".join(config_table.max_depth * "*")
        paths.extend(deque(path.glob(glob_pattern)))

    # filter all directories and query
    dirs = {str(p): p for p in filter(lambda path: path.is_dir(), paths)}
    pick_name = picker.choose(dirs)

    # define session name
    selected_dir = dirs.get(pick_name, None)
    if not selected_dir:
        return

    session_name = clean_session_name(selected_dir.name)

    if not server.has_session(session_name):
        server.new_session(session_name=session_name, start_directory=pick_name)

    if config_table.attach_after_create:
        if "TMUX" in os.environ:
            server.switch_client(session_name)
        else:
            server.attach_session(session_name)


@app.command()
def ssh():
    """
    Create or switch to session that connects to SSH host.

    Future improvements: Export a Tmux global variable that mark if the session is SSH.
    """
    config = Config()
    server, picker = load(config)
    hosts = get_hosts(reversed=True)
    pick_name = picker.choose(hosts)
    if not pick_name:
        return

    session_name = f"SSH-{clean_session_name(pick_name)}"
    if not server.has_session(session_name):
        server.new_session(session_name=session_name, start_directory="~")

    if config.attach_after_create:
        if "TMUX" in os.environ:
            server.switch_client(session_name)
        else:
            server.attach_session(session_name)


@app.command()
def kill():
    """
    Kill selected session.
    """
    config = Config()
    server, picker = load(config)

    sessions = [s.name for s in server.sessions if s.name]
    to_kill = picker.multiselect(sessions)

    if to_kill and config.confirm_kill:
        session_prompt = "Killing: "
        session_prompt += ", ".join([f"[bold]{s}[/bold]" for s in to_kill])
        session_prompt += ". Confirm?"
        confirm = Confirm.ask(session_prompt, default=False)
    else:
        confirm = True

    if confirm:
        for name in to_kill:
            server.kill_session(name)
    else:
        raise typer.Abort()


def main():
    app()
