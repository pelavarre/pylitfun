#!/usr/bin/env python3

r"""
usage: litword.py [-h]

take python input lines begun by shell verbs as shell input lines

options:
  -h, --help  show this help message and exit

examples:
  bin/litword.py --
"""

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import builtins  # (__builtins__ is vars(builtins)) or (__builtins__ is builtins)
import collections
import os
import pathlib
import shlex
import string
import subprocess
import sys
import traceback

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


def main() -> None:
    """Launch a Python Chat"""

    cls: type
    cls = LitShellWord
    cls = LitStackWord
    # last wins

    if cls is LitStackWord:
        LiteralTypes.append(object)  # includes type(None)

    cls.load_words_into(globals())
    sys.displayhook = sys_displayhook
    os.environ["PYTHONINSPECT"] = str(True)


def _exec_(pytext: str) -> None:  # todo: add callers of 'def _exec_'
    """Read, Eval, Print Repr, Loop across the Lines of the Text in order"""

    pylines = pytext.splitlines()
    for pyline in pylines:
        value = eval(pyline)
        repr(value)  # calls as if printing repr


#
# Cut back the Python Sys DisplayHook to call the Repr of a Value but not print it
#


LiteralTypes: list[type] = list()


class IneffableWord:
    """Cut back the Python Sys DisplayHook to call the Repr of a Value but not print it"""


def sys_displayhook(value: object) -> None:
    """Run as a Sys DisplayHook"""

    # Hook an IneffableWord, or a Tuple of them, as is

    hooking = False
    if isinstance(value, IneffableWord):
        hooking = True
    elif isinstance(value, tuple):
        if value and all(isinstance(v, IneffableWord) for v in value):
            hooking = True  # even when a Tuple of just one IneffableWord

    # Hook a Literal Value, as if it were an IneffableWord

    reppable = value
    if not hooking:
        for _type_ in LiteralTypes:
            if isinstance(value, _type_):
                reppable = LitStackWord.make_literal(value)
                hooking = True
                break

    # Run the Repr of what we hooked, for its side effect, and store it as '_'

    if hooking:
        assert reppable is not None, (reppable,)
        repr(reppable)  # calls as if printing repr

        setattr(builtins, "_", value)  # stores as if running sys.__displayhook__
        return

        # (__builtins__ is vars(builtins)) or (__builtins__ is builtins)
        # todo: should we be saying _ = value, or _ = reppable ?

    # Do this work for anything else

    sys.__displayhook__(value)


assert sys.displayhook is sys.__displayhook__, (sys.displayhook, sys.__displayhook__)


#
# Reconstruct a Shell Input Line,
#   from how Python calls its pieces after parsing it.
#


class LitShellWord(IneffableWord):
    """Reconstruct and run a Shell Input Line"""

    name: str
    argv: list[str]

    def __init__(self, name: str) -> None:

        self.name = name
        self.argv = list()

    def __str__(self) -> str:
        name = self.name
        return name

    #
    # Define some Unary and Binary Python Operators
    #

    def __pos__(self) -> LitShellWord:
        word = self._mention_()

        assert word.argv[0] == str(word), (word.argv[0], str(word))
        word.name = "+" + str(word)
        word.argv[0] = str(word)

        return word

    def __neg__(self) -> LitShellWord:
        word = self._mention_()

        assert word.argv[0] == str(word), (word.argv[0], str(word))
        word.name = "-" + str(word)
        word.argv[0] = str(word)

        return word

    def __add__(self, other: object) -> LitShellWord:
        word = self._mention_()

        argv = word.argv
        argv.append(str(other))  # consciously not:  argv.append("+" + str(other))

        return word

    def __sub__(self, other: object) -> LitShellWord:
        word = self._mention_()

        argv = word.argv
        argv.append("-" + str(other))

        return word

    def __or__(self, other: object) -> LitShellWord:
        word = self._mention_()

        argv = word.argv
        argv.append("|")  # runs the Shell Line through a Shell, when LitShellWord.__repr__ called

        if isinstance(other, LitShellWord):
            other = other._mention_()
            argv.extend(other.argv)
        else:
            argv.append(str(other))

        return word

    def _mention_(self) -> LitShellWord:
        """Say which ArgV to continue, else start a new LitShellWord with an ArgV of Self Name"""

        argv = self.argv

        if argv:
            return self

        word = LitShellWord(str(self))

        argv = word.argv
        argv.append(str(word))
        word.argv = argv

        return word

    #
    # Define Python Repr to mean Subprocess Run
    #

    def __repr__(self) -> str:

        word = self._mention_()
        argv = word.argv

        _argv_ = list()
        for i, arg in enumerate(argv):
            if arg.startswith("---"):  # patches first ---..., likely from __sub__, back to -- -...
                _argv_.append("--")
                _argv_.append(arg.removeprefix("--"))
                _argv_.extend(argv[i:][1:])
                break
            _argv_.append(arg)

        argv[::] = _argv_
        word._subprocess_run_()

        r = object.__repr__(self)
        return r

    def _subprocess_run_(self) -> None:
        """Trace & run the Shell Line"""

        argv = self.argv
        assert argv, (argv, self)

        piped = "|" in argv  # leaves the '|' Pipe unquoted, for the Shell to honor
        shline = " ".join(_ if _ == "|" else shlex.quote(_) for _ in argv)

        sys.stdout.flush()
        print("+", shline, file=sys.stderr)
        sys.stderr.flush()

        try:
            if argv[0] == "cd":
                self.do_chdir(argv)
            elif piped:
                subprocess.run(shline, shell=True)  # honors the '|' Pipe via the Shell
            else:
                subprocess.run(argv)
        except Exception as exc:
            texts = traceback.format_exception(exc, limit=0)  # colorize=stderr.isatty
            print(texts[0].rstrip())

        sys.stdout.flush()
        print("+", file=sys.stderr)
        sys.stderr.flush()

    #
    # Add a builtin Vocabulary of Shell Verbs & Options & Option Permutations into the Globals
    #

    @staticmethod  # todo: when to write into __builtins__ module/ dict instead of globals?
    def load_words_into(_globals_: dict[str, object]) -> None:
        """Pile up a Word per Shell Verb & per ASCII Letter, then copy them into the Globals"""

        # Declare our most favoured Shell Verbs

        # awk = LitShellWord("awk")
        bash = LitShellWord("bash")
        cal = LitShellWord("cal")
        cat = LitShellWord("cat")
        clear = LitShellWord("clear")
        cd = LitShellWord("cd")
        cp = LitShellWord("cp")
        curl = LitShellWord("curl")
        date = LitShellWord("date")  # date +'+%H:%M:%S'
        # dd = LitShellWord("dd")
        df = LitShellWord("df")
        diff = LitShellWord("diff")
        echo = LitShellWord("echo")
        find = LitShellWord("find")
        # head = LitShellWord("head")
        hexdump = LitShellWord("hexdump")
        # jq = LitShellWord("jq")
        # less = LitShellWord("less")
        ls = LitShellWord("ls")
        if str(sys.platform) == "linux":  # mentions of 'lsb_release' raise NameError elsewhere
            lsb_release = LitShellWord("lsb_release")
        man = LitShellWord("man")  # man +date
        md5sum = LitShellWord("md5sum")
        mkdir = LitShellWord("mkdir")
        mv = LitShellWord("mv")
        od = LitShellWord("od")
        _open_ = LitShellWord("open")
        pbpaste = LitShellWord("pbpaste")
        ps = LitShellWord("ps")
        pwd = LitShellWord("pwd")
        python = LitShellWord("python")
        python3 = LitShellWord("python3")
        screen = LitShellWord("screen")
        script = LitShellWord("script")
        sh = LitShellWord("sh")
        sleep = LitShellWord("sleep")
        sort = LitShellWord("sort")
        ssh = LitShellWord("ssh")
        stty = LitShellWord("stty")
        sudo = LitShellWord("sudo")
        if str(sys.platform) == "darwin":  # mentions of 'sw_vers' raise NameError elsewhere
            sw_vers = LitShellWord("sw_vers")
        tail = LitShellWord("tail")
        tee = LitShellWord("tee")
        # time = LitShellWord("time")  # todo: Python 'import time' vs Shell 'time'
        touch = LitShellWord("touch")
        tr = LitShellWord("tr")
        uptime = LitShellWord("uptime")
        # if sys.platform == "darwin":
        #     uptime = LitShellWord("uptime.py")  # todo: vs Shell 'uptime --pretty'
        # xargs = LitShellWord("xargs")
        zsh = LitShellWord("zsh")

        _ = _open_

        # Declare our most favoured Shell Option Permutations (not all possible Permutations)

        LSs = LitShellWord("LSs")  # curl -k -LSs +'http://example.com'
        bpru = LitShellWord("bpru")  # diff -bpru +a +b
        color = LitShellWord("color")  # ls --color
        hlAF = LitShellWord("hlAF")  # ls -hlAF -rt
        pretty = LitShellWord("pretty")  # uptime --pretty
        rt = LitShellWord("rt")  # bash -c +ls -d -hlAF -rt +'*'
        sane = LitShellWord("sane")  # stty +sane
        version = LitShellWord("version")  # python3 --version

        # Declare the US Ascii Letters, upper and lower case, as Shell Options

        _locals_ = locals()  # sampled after last change, because Oct/2024 Python 3.13 PEP 667
        for ch in string.ascii_letters:
            _locals_[ch] = LitShellWord(ch)

            # ducks Flake E741 = Variables named 'I', 'O', or 'l'

        # Publish these Words that we have declared as something much like Locals here

        for name, value in _locals_.items():
            if isinstance(value, LitShellWord):
                _globals_[name] = value

    #
    # Run in place of a Shell Command, when LitShellWord.__repr__ called
    #

    def do_chdir(self, argv: list[str]) -> None:
        """Work like the 'cd' Command of a Shell"""

        # Parse

        assert len(argv) in (1, 2, 3), (len(argv), argv)

        _argv_ = list(argv)
        if len(argv) == 1:
            _argv_.append("~/")

        # Sample

        getcwd = os.getcwd()

        default_eq_getcwd = getcwd
        oldpwd = os.environ.get("OLDPWD", default_eq_getcwd)

        # Choose where to go

        newpwd = os.path.expanduser(_argv_[1])
        verbose = False

        if len(argv) in (1, 2):

            if not _argv_[1]:
                newpwd = getcwd  # comes here again for:  cd ''
            elif _argv_[1] == "-":
                newpwd = oldpwd  # goes back there for:  cd -
                verbose = True

        else:
            assert len(argv) == 3, (len(argv), argv)

            stale = _argv_[1]
            fresh = _argv_[2]

            if stale not in getcwd:
                print(f"cd: string not in pwd: {stale}", file=sys.stderr)
                return  # todo: exit code 1

            default_eq_1 = 1  # steps nearby for:  cd stale fresh
            newpwd = getcwd.replace(stale, fresh, default_eq_1)
            verbose = True

        # Change and remember

        os.chdir(newpwd)

        if verbose:
            unexpanduser = self.unexpanduser(os.getcwd())
            print(unexpanduser)

        os.environ["OLDPWD"] = getcwd  # adds or replaces

    def unexpanduser(self, pathname: str) -> str:
        """Speak in terms of ~/ not in terms of $HOME/"""

        path = pathlib.Path(pathname)
        home = pathlib.Path.home()

        try:
            s = str(pathlib.Path("~") / path.relative_to(home))
            return s
        except ValueError:
            return pathname


#
# Reconstruct an RPN Stack Calculator Input Line,
#   from how Python calls its pieces after parsing it.
#


class LitStackWord(IneffableWord):
    """Reconstruct and run an RPN Stack Calculator Input Line"""

    stack: list[object] = list()

    action: collections.abc.Callable[[], None]

    def __init__(self, action: collections.abc.Callable[[], None]) -> None:
        self.action = action

    def __str__(self) -> str:
        action = self.action
        _str_ = str(action)
        return _str_

    @staticmethod
    def make_literal(value: object) -> IneffableWord:

        def action(value: object) -> None:
            LitStackWord.push_value(value)

        ineffable = LitStackWord(lambda: action(value))
        return ineffable

    #
    # Define Python Repr to mean Press Calculator Button
    #

    def __repr__(self) -> str:
        stack = LitStackWord.stack

        self.action()
        print(stack)

        r = object.__repr__(self)
        return r

    #
    # Add a builtin Vocabulary of Calculator Buttons to press
    #

    @staticmethod
    def load_words_into(_globals_: dict[str, object]) -> None:
        """Pile up this Class's own Words, then copy them into the Globals"""

        chs = LitStackWord(LitStackWord.do_chs)
        clstk = LitStackWord(LitStackWord.do_clstk)
        dup = LitStackWord(LitStackWord.do_dup)
        pop = LitStackWord(LitStackWord.do_pop)
        swap = LitStackWord(LitStackWord.do_swap)

        # Publish these Words that we have declared as something much like Locals here

        _locals_ = locals()  # sampled after last change, because Oct/2024 Python 3.13 PEP 667
        for name, value in _locals_.items():
            if isinstance(value, LitStackWord):
                _globals_[name] = value

    #
    # Press a Calculator Button
    #

    @staticmethod
    def push_value(value: object) -> None:
        stack = LitStackWord.stack
        stack.append(value)

    @staticmethod
    def do_chs() -> None:
        """Change Sign, else push -1"""

        stack = LitStackWord.stack
        x = stack.pop() if stack else 1  # 'chs' pushes -1 when given no X

        assert isinstance(x, float | int | bool), (type(x), x)

        nx = -x
        stack.append(nx)

    @staticmethod
    def do_clstk() -> None:
        """Clear the Stack"""

        stack = LitStackWord.stack
        stack.clear()

    @staticmethod
    def do_dup() -> None:
        """Duplicate X, else do nothing when given no X"""

        stack = LitStackWord.stack
        if stack:
            x = stack[-1]
            stack.append(x)

    @staticmethod
    def do_pop() -> None:
        """Drop X, else do nothing when given no X"""

        stack = LitStackWord.stack
        if stack:
            stack.pop()

    @staticmethod
    def do_swap() -> None:
        """Swap X and Y, else do nothing when given fewer than two"""

        stack = LitStackWord.stack
        if len(stack) >= 2:
            x = stack.pop()
            y = stack.pop()
            stack.append(x)
            stack.append(y)

    # todo0: clstk = ...  """Clear the Stack (drop all of its Values)"""
    # todo0: dup = ...  """Push an Alias of X, else push one 0"""
    # todo0: pop = ...  """Pop X, else silently do nothing"""
    # todo0: swap = ...  """Swap X with Y, else silently do nothing"""


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litword.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
