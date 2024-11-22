from json import dumps, loads
from pathlib import Path
from typing import Optional

from libtmux import Server
from typer import Argument, Option, Typer
from typing_extensions import Annotated

from fsm.console import pretty_print, print_warning
from fsm.query import Picker, get_picker, get_pickers

CONFIG_FILE = "~/.config/fsm/fsm.json"

desc = "Set configuration options"
config_app = Typer(
    help=desc,
    pretty_exceptions_show_locals=False,
    add_help_option=False,
    add_completion=False,
    no_args_is_help=True,
)


class Config:
    # top-level directories to include in the search
    include: set[str] = {"~"}
    # path of directories to exclode from the search
    exclude: set[str] = set()
    # max depth to go into for the search
    max_depth: int = 1
    # default server socket_path
    socket_path: str = ""
    # default fuzzy finder app
    picker: str = "fzf"
    # attach to the newly created session or not
    attach_after_create: bool = False
    # confirm kill sessions
    confirm_kill: bool = True

    def __init__(self):
        file = Path(CONFIG_FILE).expanduser()
        if not file.exists():
            return

        with open(file, "r") as f:
            config_dict = loads(f.read())

        for attrname in dir(self):
            attr = getattr(self, attrname)
            if not callable(attr) and not attrname.startswith("_"):
                if attrname in config_dict:
                    setattr(self, attrname, config_dict.get(attrname))

    def save_to_file(self) -> None:
        """
        Save config to file ~/.config/fsm/fsm.json

        If the path doesn't exists, it is created automatically.
        """
        config_dict = {}
        for attrname in dir(self):
            attr = getattr(self, attrname)
            if not callable(attr) and not attrname.startswith("_"):
                config_dict[attrname] = attr

        file = Path(CONFIG_FILE).expanduser()
        directory = file.parent
        directory.mkdir(parents=True, exist_ok=True)
        with open(file, "w") as f:
            f.write(dumps(config_dict, indent=4))

    def __repr__(self):
        obj = {}
        for prop_name in dir(self):
            prop = getattr(self, prop_name)
            if not callable(prop) and not prop_name.startswith("_"):
                obj[prop_name] = prop

        return "\n".join(f"{k}={v!r}" for k, v in obj.items())

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.save_to_file()


@config_app.command("show")
def show(json: Annotated[bool, Option(help="Show JSON config file")] = False):
    """
    Display current configuration
    """
    if json:
        with open(Path(CONFIG_FILE).expanduser(), "r") as f:
            content = f.read()
            pretty_print(content)
    else:
        pretty_print(Config())


@config_app.command("add")
def add(path: Annotated[str, Argument(help="Path to include in search")]):
    """
    Add path to search list
    """
    with Config() as c:
        if Path(path).expanduser().exists():
            c.include.add(path)
        else:
            print_warning(f"{path} does not exists. Ignoring")


@config_app.command("rm")
def rm(path: Annotated[str, Argument(help="Path to remove from search")]):
    """
    Remove path from search list

    If path is not in the search list, path is excluded from search. (TODO)
    """
    with Config() as c:
        if Path(path).expanduser().exists():
            c.include.remove(path)
        else:
            print_warning(f"{path} does not exists. Ignoring")


@config_app.callback("config", invoke_without_command=True)
def main(
    maxdepth: Annotated[
        Optional[int],
        Option(
            metavar="",
            help="Max depth when traversing directories",
            show_default=False,
        ),
    ] = None,
    picker: Annotated[
        Optional[str], Option(metavar="", help="Fuzzy finder app", show_default=False)
    ] = None,
    socket_path: Annotated[
        Optional[str],
        Option(metavar="", help="Socket path of Tmux server", show_default=False),
    ] = None,
    attach: Annotated[
        Optional[bool],
        Option(metavar="", help="Attach to session after create", show_default=False),
    ] = None,
    confirm_kill: Annotated[
        Optional[bool],
        Option(metavar="", help="Confirm killing sessions", show_default=False),
    ] = None,
):
    """
    Set configuration of fsm.
    """
    # load configuration
    with Config() as c:
        # run options
        if maxdepth:
            if maxdepth > 0:
                c.max_depth = maxdepth
            else:
                print_warning("Maximum depth must be positive. Ignoring")
        if picker:
            if picker in get_pickers():
                c.picker = picker
            else:
                print_warning(f"{picker} not installed. Ignoring")
        if socket_path:
            if Path(socket_path).expanduser().exists():
                c.socket_path = socket_path
            else:
                print_warning(f"Socket path {socket_path} not found. Ignoring")
        if attach:
            c.attach_after_create = attach
        if confirm_kill:
            c.confirm_kill = confirm_kill


def load(config: Config) -> tuple[Server, Picker]:
    """
    Return a server and picker based on the config structure provided.
    """
    server = Server(socket_path=config.socket_path)
    picker = get_picker(config.picker)
    return server, picker
