from shutil import which
from subprocess import PIPE, Popen
from typing import Iterable

__PICKERS = {}


def get_pickers():
    """
    Return all registered Picker objects.
    """
    return __PICKERS.items()


def get_picker(name):
    """
    Return the Picker object with the corresponding `name`.
    """
    return __PICKERS.get(name, Fzf())


def cli_fuzzy_finder(name, *args: str, multiple_opt: str = ""):
    """
    Build a Picker object that calls a fuzzy finder as subprocess.
    Input is passed through stdin, and output is captured from stdout.
    `select` is passed through `which` to check if it exists,
    if not, the class is not registered (i.e. added to `__PICKER`).

    The `choose` and `multiselect` methods are class methods,
    so no instantiation of the `Picker` object is required.
    """

    def choose(options: Iterable[str]) -> str:
        """
        Run `select` with the provided options and return the result.
        """
        cmd = args
        proc = Popen(cmd, stdin=PIPE, stdout=PIPE, text=True)
        stdin = "\n".join(options)
        try:
            stdout, _ = proc.communicate(stdin)
        except:
            stdout = ""
        finally:
            output = stdout.strip()

        return output

    def multiselect(options: Iterable[str]) -> list[str]:
        """
        Run `command` with the provided options and return the result.
        """
        if multiple_opt:
            cmd = (*args, multiple_opt)
        else:
            cmd = args

        proc = Popen(cmd, stdin=PIPE, stdout=PIPE, text=True)
        stdin = "\n".join(options)
        try:
            stdout, _ = proc.communicate(stdin)
        except:
            stdout = ""
        finally:
            if stdout == "":
                output = []
            else:
                output = stdout.strip().split("\n")

        return output

    def wrapper(cls):
        # register class
        if which(args[0]):
            __PICKERS[name] = cls
        else:
            return cls
        # mark with name
        setattr(cls, "name", name)
        # add @classmethod choose
        setattr(cls, "choose", choose)
        if multiple_opt:
            setattr(cls, "multiselect", multiselect)
        return cls

    return wrapper


class Picker:
    """
    Soft interface to implement a fuzzy finder.
    """

    name: str

    @classmethod
    def choose(cls, *args) -> str:
        """
        Entry point to fuzzy finder selector.
        """
        raise NotImplementedError()

    def __init__(self):
        pass

    @classmethod
    def multiselect(cls, *args) -> list[str]:
        """
        Entry point to fuzzy finder multiple selector.
        """
        raise NotImplementedError()


@cli_fuzzy_finder("fzf", "fzf", multiple_opt="-m")
class Fzf(Picker):
    pass


@cli_fuzzy_finder("fzy", "fzy")
class Fzy(Picker):
    pass


@cli_fuzzy_finder("pick", "pick")
class Pick(Picker):
    pass


@cli_fuzzy_finder("gum", "gum", "filter", multiple_opt="--no-limit")
class Gum(Picker):
    pass
