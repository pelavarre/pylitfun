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
import codeop
import collections
import functools
import inspect
import math
import operator
import os
import pathlib
import random
import shlex
import string
import subprocess
import sys
import traceback
import types

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


def main() -> None:
    """Launch a Python Chat"""

    cls: type
    cls = LitShellWord  # todo: add callers of LitShellWord
    cls = LitStackWord
    # last wins

    if cls is LitStackWord:
        LiteralTypes.append(object)  # includes type(None)
        sys.excepthook = LitStackWord.sys_excepthook  # takes '5 7' as if it were '5' then '7'

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


class IneffableNotImplementedError(NotImplementedError):
    """Set apart the NotImplementedError raised by 'def do_unimplemented'"""


def sys_displayhook(value: object) -> None:
    """Run as a Sys DisplayHook"""

    word_by_builtin = LitStackWord.word_by_builtin

    # Hook an IneffableWord, or a Tuple of them, as is

    hooking = False
    if isinstance(value, IneffableWord):
        hooking = True
    elif isinstance(value, tuple):
        if value and all(isinstance(v, IneffableWord) for v in value):
            hooking = True  # even when a Tuple of just one IneffableWord

    # Hook a Builtin that a Word is named for, such as 'range', as the Word

    reppable = value
    if not hooking:
        for _builtin_, word in word_by_builtin.items():
            if value is _builtin_:
                reppable = word
                hooking = True
                break

    # Hook a Literal Value, as if it were an IneffableWord

    if not hooking:
        for _type_ in LiteralTypes:
            if isinstance(value, _type_):
                reppable = LitStackWord.make_literal_push(value)
                hooking = True
                break

    # Run the Repr of what we hooked, for its side effect, and store it as '_'

    if hooking:
        assert reppable is not None, (reppable,)

        try:
            repr(reppable)  # calls as if standard Sys DisplayHook printing Repr
        except IneffableNotImplementedError as exc:  # prints Exc without Traceback
            print(f"NotImplementedError: {exc}", file=sys.stderr)  # names Superclass, not Exc Class
            return

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
    # Add the Builtin Vocabulary of this Class into the Globals, via some Locals
    #

    @staticmethod  # todo: when to write into __builtins__ module/ dict instead of globals?
    def load_words_into(_globals_: dict[str, object]) -> None:
        """Add the Builtin Vocabulary of this Class into the Globals, via some Locals"""

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
    operator_by_mark: dict[str, LitStackWord] = dict()
    word_by_builtin: dict[object, LitStackWord] = dict()

    name: str
    action: collections.abc.Callable[[], None]

    def __init__(self, action: collections.abc.Callable[[], None], name: str | None = None) -> None:
        self.action = action
        self.name = action.__name__ if name is None else name

    def __str__(self) -> str:
        name = self.name
        return name

    @staticmethod
    def make_literal_push(value: object) -> IneffableWord:

        def do_literal_push() -> None:
            LitStackWord._push_literal_value_(value)

        ineffable = LitStackWord(do_literal_push, name=shlex.quote(str(value)))

        return ineffable

    @staticmethod
    def make_constant(name: str, value: object) -> LitStackWord:

        def do_constant() -> None:
            stack = LitStackWord.stack
            stack.append(value)

        ineffable = LitStackWord(do_constant, name=name)

        return ineffable

    @staticmethod
    def make_unary(name: str, func: collections.abc.Callable[..., object]) -> LitStackWord:

        def do_unary() -> None:
            stack = LitStackWord.stack
            if not stack:
                return

            x = stack[-1]
            _x_ = func(x)  # invites Func to raise Exception before Stack-Pop Side-Effect
            stack.pop()
            stack.append(_x_)

        ineffable = LitStackWord(do_unary, name=name)

        return ineffable

    @staticmethod
    def make_binop(
        mark: str,
        func: collections.abc.Callable[..., object],
        unary: collections.abc.Callable[..., object] | None = None,
        empty: int | None = None,
    ) -> LitStackWord:

        def do_binop() -> None:
            LitStackWord._do_binop_(func, unary=unary, empty=empty)

        ineffable = LitStackWord(do_binop, name=mark)

        return ineffable

    @staticmethod
    def make_ternary(name: str, func: collections.abc.Callable[..., object]) -> LitStackWord:

        def do_ternary() -> None:
            stack = LitStackWord.stack
            if len(stack) < 3:
                return

            z = stack[-3]
            y = stack[-2]
            x = stack[-1]

            _x_ = func(z, y, x)  # invites Func to raise Exception before Stack-Pop Side-Effect

            stack.pop()
            stack.pop()
            stack.pop()
            stack.append(_x_)

        ineffable = LitStackWord(do_ternary, name=name)

        return ineffable

    @staticmethod
    def make_unimplemented(name: str) -> LitStackWord:

        def do_unimplemented() -> None:
            raise IneffableNotImplementedError(name)

        ineffable = LitStackWord(do_unimplemented, name=name)

        return ineffable

    @staticmethod
    def pyfunc_arity(func: collections.abc.Callable[..., object]) -> int:
        """Count the Values a Python Func wants off the Stack: 1, 2, 3, else 0 to skip it"""

        try:
            params = list(inspect.signature(func).parameters.values())
        except (ValueError, TypeError):
            return 1  # e.g. math.log gives no signature, so take it as unary

        if any(p.kind is p.VAR_POSITIONAL for p in params):
            return 2  # e.g. math.gcd/hypot/lcm take *args, so take two off the Stack

        required = [
            p
            for p in params
            if (p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)) and (p.default is p.empty)
        ]

        n = len(required)
        return n if n in (1, 2, 3) else 0  # 0 skips four-plus-arg Funcs and any zero-arg Func

    #
    # Duck the SyntaxErrors resolved by splitting one Repl Input into several
    #

    @staticmethod
    def sys_excepthook(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: types.TracebackType | None,
    ) -> None:
        """Duck the SyntaxErrors resolved by splitting one Repl Input into several"""

        if (not isinstance(exc_value, SyntaxError)) or (exc_value.text is None):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Take as much as doesn't raise SyntaxError, again and again till no more remains

        text = exc_value.text
        rstrip = text.rstrip()

        execables: list[types.CodeType] = list()
        while rstrip:
            execable, tail = LitStackWord.split_syntax_error(rstrip)
            if execable is None:  # a bare Operator Mark, such as * or /, isn't Python
                execable, tail = LitStackWord.split_operator_mark(rstrip)

            assert rstrip.endswith(tail), (tail, rstrip)

            # Fall back to default when taking less Input doesn't resolve a SyntaxError

            if execable is None:
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            # Else take some now, and try for more

            execables.append(execable)

            assert tail == tail.rstrip(), (tail, tail.rstrip())  # because .endswith above
            rstrip = tail

        # Run each Input in order

        main_vars = vars(sys.modules["__main__"])
        for execable in execables:
            exec(execable, main_vars)  # calls sys.displayhook because symbol="single"

    @staticmethod
    def split_syntax_error(line: str) -> tuple[types.CodeType | None, str]:
        """Take as much as doesn't raise SyntaxError, and return the rest of the Line"""

        for length in range(len(line), 0, -1):
            head, tail = (line[:length], line[length:])

            try:
                execable = codeop.compile_command(head, filename="<repl>", symbol="single")
                return (execable, tail)
            except SyntaxError:
                pass

        return (None, line)

    @staticmethod
    def split_operator_mark(line: str) -> tuple[types.CodeType | None, str]:
        """Take one Python Operator Mark, such as <= or *, and return the rest of the Line"""

        operator_by_mark = LitStackWord.operator_by_mark

        lstrip = line.lstrip()
        for mark in operator_by_mark:
            if lstrip.startswith(mark):
                py = f"LitStackWord.operator_by_mark[{mark!r}]"
                tail = lstrip[len(mark) :]

                execable = codeop.compile_command(py, filename="<repl>", symbol="single")
                return (execable, tail)

        return (None, line)

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
    # Add the Builtin Vocabulary of this Class into the Globals, via some Locals
    #

    @staticmethod
    def load_words_into(_globals_: dict[str, object]) -> None:
        """Add the Builtin Vocabulary of this Class into the Globals, via some Locals"""

        word_by_builtin = LitStackWord.word_by_builtin

        def add_button(name: str, word: LitStackWord) -> None:
            if hasattr(builtins, name):  # our Sys DisplayHook resolves Button vs BuiltIns
                word_by_builtin[getattr(builtins, name)] = word
            else:
                _globals_[name] = word

        _abs_ = LitStackWord.make_unary("abs", func=builtins.abs)

        chs = LitStackWord(LitStackWord.do_chs)
        clstk = LitStackWord(LitStackWord.do_clstk)
        dup = LitStackWord(LitStackWord.do_dup)
        nip = LitStackWord(LitStackWord.do_nip)
        over = LitStackWord(LitStackWord.do_over)
        pop = LitStackWord(LitStackWord.do_pop)
        randint = LitStackWord(LitStackWord.do_randint)
        _range_ = LitStackWord(LitStackWord.do_range)
        roll = LitStackWord(LitStackWord.do_roll)
        rot = LitStackWord(LitStackWord.do_rot)
        shuffle = LitStackWord(LitStackWord.do_shuffle)
        _sum_ = LitStackWord(LitStackWord.do_sum)
        swap = LitStackWord(LitStackWord.do_swap)

        # Publish these Words that we have declared as something much like Locals here

        _locals_ = locals()  # sampled after last change, because Oct/2024 Python 3.13 PEP 667

        for name, value in _locals_.items():
            if isinstance(value, LitStackWord):
                strip = name.strip("_")
                add_button(strip, word=value)

        # Adopt the 'math' Module Vocabulary, one Word per Name that doesn't start with '_'

        unimplemented_math_names = ("dist", "frexp", "fsum", "modf", "pow", "prod", "sumprod")
        for math_name in dir(math):
            if math_name.startswith("_"):
                continue

            if math_name in unimplemented_math_names:
                add_button(math_name, word=LitStackWord.make_unimplemented(math_name))
                continue

                # def dist(sequence, sequence) -> float
                # def frexp(float) -> tuple[float, int]
                # def fsum(sequence) -> float
                # def modf(float) -> tuple[float, float]
                # def pow(number, number) -> number  # as builtins.pow, or as math.pow
                # def pow(number, number, modulo) -> number  # only as builtins.pow
                # def prod(sequence) -> number
                # def sumprod(sequence, sequence) -> number

            math_value = getattr(math, math_name)
            if not callable(math_value):
                add_button(math_name, word=LitStackWord.make_constant(math_name, value=math_value))
                continue

            arity = LitStackWord.pyfunc_arity(math_value)
            if arity == 1:
                add_button(math_name, word=LitStackWord.make_unary(math_name, func=math_value))
            elif arity == 2:
                add_button(math_name, word=LitStackWord.make_binop(math_name, func=math_value))
            elif arity == 3:
                add_button(math_name, word=LitStackWord.make_ternary(math_name, func=math_value))

        func_by_mark: dict[str, collections.abc.Callable[..., object]] = {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "/": operator.truediv,
            "//": operator.floordiv,
            "%": operator.mod,
            "**": operator.pow,
            "@": operator.matmul,
            "&": operator.and_,
            "|": operator.or_,
            "^": operator.xor,
            "<<": operator.lshift,
            ">>": operator.rshift,
            "<": operator.lt,
            "<=": operator.le,
            ">": operator.gt,
            ">=": operator.ge,
            "==": operator.eq,
            "!=": operator.ne,
        }

        unop_by_mark: dict[str, collections.abc.Callable[..., object]] = {
            "+": operator.pos,
            "-": operator.neg,
            "*": lambda x: x * x,
            "/": lambda x: 1 / x,
            "//": lambda x: x // 1,
            "%": lambda x: x % 1,
            "**": lambda x: 10**x,
            "^": lambda x: x ^ -1,
            "<<": lambda x: 1 << x,
            ">>": lambda x: x >> 1,
            "<": lambda x: x < 0,
            "<=": lambda x: x <= 0,
            ">": lambda x: x > 0,
            ">=": lambda x: x >= 0,
            "==": lambda x: x == 0,
            "!=": lambda x: x != 0,
        }

        empty_by_mark: dict[str, int] = {
            "+": 0,
            "-": 0,
            "*": 1,
            "/": 1,
            "//": 1,
            "**": 1,
            "&": -1,
            "|": 0,
            "^": 0,
            "<<": 0,
            ">>": 0,
        }

        # Order by Mark length, longest first, so 'split_operator_mark' matches ** before *

        LitStackWord.operator_by_mark = {
            mark: LitStackWord.make_binop(
                mark,
                func=func_by_mark[mark],
                unary=unop_by_mark.get(mark),
                empty=empty_by_mark.get(mark),
            )
            for mark in sorted(func_by_mark, key=len, reverse=True)
        }

    #
    # Press a Calculator Button
    #

    @staticmethod
    def _push_literal_value_(value: object) -> None:
        stack = LitStackWord.stack
        stack.append(value)

    @staticmethod
    def do_chs() -> None:
        """Change Sign, else push -1"""

        stack = LitStackWord.stack
        x = stack[-1] if stack else 1

        assert isinstance(x, (float, int, bool)), (type(x), x)

        if stack:
            stack.pop()

        _x_ = -x
        stack.append(_x_)

        # todo: '5 - 7' comes through subtraction,
        # astonishingly not the same as '5 7 chs', especially astonishing when input as '5 -7'

    @staticmethod
    def do_clstk() -> None:
        """Clear the Stack"""

        stack = LitStackWord.stack
        stack.clear()

    @staticmethod
    def do_dup() -> None:
        """Duplicate X, else push one 0"""

        stack = LitStackWord.stack
        x = stack[-1] if stack else 0
        stack.append(x)

    @staticmethod
    def do_nip() -> None:
        """Drop Y, else do nothing when given fewer than two"""

        stack = LitStackWord.stack
        if len(stack) >= 2:
            del stack[-2]

    @staticmethod
    def do_over() -> None:
        """Push an Alias of Y, else do nothing when given fewer than two"""

        stack = LitStackWord.stack
        if len(stack) >= 2:
            y = stack[-2]
            stack.append(y)

    @staticmethod
    def do_pop() -> None:
        """Drop X, else do nothing when given no X"""

        stack = LitStackWord.stack
        if stack:
            stack.pop()

    @staticmethod
    def do_randint() -> None:
        """Push randint(Y, X), else randint(1, X) for one Value, else randint(1, 6) for none"""

        stack = LitStackWord.stack
        if len(stack) >= 2:
            y = stack[-2]
            x = stack[-1]
            assert isinstance(y, int) and isinstance(x, int), stack
            _x_ = random.randint(y, x)
            stack.pop()
            stack.pop()
            stack.append(_x_)
        elif len(stack) == 1:
            x = stack[-1]
            assert isinstance(x, int), stack
            _x_ = random.randint(1, x)
            stack.pop()
            stack.append(_x_)
        else:
            stack.append(random.randint(1, 6))

    @staticmethod
    def do_range() -> None:
        """Push range() of up to three Stack Values as Z Y X, else range(10) for an empty Stack"""

        stack = LitStackWord.stack
        n = min(len(stack), 3)

        if n == 3:
            z, y, x = stack[-3], stack[-2], stack[-1]
            assert isinstance(z, int) and isinstance(y, int) and isinstance(x, int), stack
            values = list(range(z, y, x))
        elif n == 2:
            y, x = stack[-2], stack[-1]
            assert isinstance(y, int) and isinstance(x, int), stack
            values = list(range(y, x))
        elif n == 1:
            x = stack[-1]
            assert isinstance(x, int), stack
            values = list(range(x))
        else:
            values = list(range(10))

        del stack[len(stack) - n :]
        stack.extend(values)

    @staticmethod
    def do_roll() -> None:
        """Take the count U, then roll the U-deep Value up to the top, else do nothing"""

        stack = LitStackWord.stack
        if not stack:
            return

        u = stack[-1]
        if (not isinstance(u, int)) or (u < 0) or (len(stack) < u + 2):
            return

        stack.pop()
        x = stack.pop(-(u + 1))
        stack.append(x)

    @staticmethod
    def do_rot() -> None:
        """Rotate Z up above Y and X, else do nothing when given fewer than three"""

        stack = LitStackWord.stack
        if len(stack) >= 3:
            z = stack[-3]
            y = stack[-2]
            x = stack[-1]
            stack[-3] = y
            stack[-2] = x
            stack[-1] = z

    @staticmethod
    def do_shuffle() -> None:
        """Shuffle the whole Stack, changing nothing for fewer than two Values"""

        stack = LitStackWord.stack
        random.shuffle(stack)

    @staticmethod
    def do_sum() -> None:
        """Replace the whole Stack with its sum, else push an int 0"""

        stack = LitStackWord.stack  # reducing '+' from 0 ducks Mypy vs Sum List[Object]
        _sum_ = functools.reduce(operator.add, stack, 0)

        stack.clear()
        stack.append(_sum_)

    @staticmethod
    def do_swap() -> None:
        """Swap X and Y, else do nothing when given fewer than two"""

        stack = LitStackWord.stack
        if len(stack) >= 2:
            x = stack[-1]
            y = stack[-2]
            stack[-1] = y
            stack[-2] = x

    @staticmethod
    def _do_binop_(
        func: collections.abc.Callable[..., object],
        unary: collections.abc.Callable[..., object] | None = None,
        empty: int | None = None,
    ) -> None:
        """Work with 2 args, else with 1 arg, else with 0 args"""

        stack = LitStackWord.stack

        if (not stack) and (empty is not None):
            stack.append(empty)
            return

        if (len(stack) == 1) and (unary is not None):
            x = stack[-1]
            z = unary(x)
            stack.pop()
            stack.append(z)
            return

        if len(stack) < 2:
            return

        y = stack[-2]
        x = stack[-1]

        _x_ = func(y, x)  # invites Func to raise Exception before Stack-Pop Side-Effect

        stack.pop()
        stack.pop()
        stack.append(_x_)


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# todo: Solve >>> (1 2 +) 7 /
# todo: Solve >>> 1 2 3 .


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litword.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
