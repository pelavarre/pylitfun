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
import os
import pathlib
import shlex
import subprocess
import sys
import traceback

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


def main() -> None:
    """Launch a Python Chat"""

    sys.displayhook = sys_displayhook
    os.environ["PYTHONINSPECT"] = str(True)


def _exec_(pytext: str) -> None:  # todo: add callers of 'def _exec_'
    """Read, Eval, Print Repr, Loop across the Lines of the Text in order"""

    pylines = pytext.splitlines()
    for pyline in pylines:
        value = eval(pyline)
        repr(value)  # calls as if printing repr


#
# Reconstruct a Shell Input Line from how Python calls its pieces after parsing it
#


class LitWord:
    """Reconstruct a Shell Input Line from how Python calls its pieces after parsing it"""

    name: str
    argv: list[str]

    def __init__(self, name: str) -> None:

        self.name = name
        self.argv = list()

    def __str__(self) -> str:
        name = self.name
        return name

    def _mention_(self) -> LitWord:
        """Say which ArgV to continue, else start a new LitWord with an ArgV of Self Name"""

        argv = self.argv

        if argv:
            return self

        word = LitWord(str(self))

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

        shline = " ".join(shlex.quote(_) for _ in argv)

        sys.stdout.flush()
        print("+", shline, file=sys.stderr)
        sys.stderr.flush()

        func = self.do_chdir if argv[0] == "cd" else subprocess.run
        try:
            func(argv)
        except Exception as exc:
            texts = traceback.format_exception(exc, limit=0)  # colorize=stderr.isatty
            print(texts[0].rstrip())

        sys.stdout.flush()
        print("+", file=sys.stderr)
        sys.stderr.flush()

    #
    # Define some Unary Python Operators
    #

    def __pos__(self) -> LitWord:
        word = self._mention_()

        assert word.argv[0] == str(word), (word.argv[0], str(word))
        word.name = "+" + str(word)
        word.argv[0] = str(word)

        return word

    def __neg__(self) -> LitWord:
        word = self._mention_()

        assert word.argv[0] == str(word), (word.argv[0], str(word))
        word.name = "-" + str(word)
        word.argv[0] = str(word)

        return word

    #
    # Define some Binary Python Operators
    #

    def __add__(self, other: object) -> LitWord:
        word = self._mention_()

        argv = word.argv
        argv.append(str(other))  # consciously not:  argv.append("+" + str(other))

        return word

    def __sub__(self, other: object) -> LitWord:
        word = self._mention_()

        argv = word.argv
        argv.append("-" + str(other))

        return word

    #
    # Run in place of a Shell Command, when LitWord.__repr__ called
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


def sys_displayhook(value: object) -> None:
    """Run as a Sys DisplayHook but see None as the Repr of a LitWord, and of a Tuple[LitWord]"""

    hooking = False
    if isinstance(value, LitWord):
        hooking = True
    elif isinstance(value, tuple):
        if value and all(isinstance(v, LitWord) for v in value):
            hooking = True

            # does hook a tuple of even just one LitWord

    if hooking:
        repr(value)  # calls as if printing repr
        assert value is not None, (value,)
        setattr(builtins, "_", value)  # stores as if running sys.__displayhook__
        return

        # (__builtins__ is vars(builtins)) or (__builtins__ is builtins)

    sys.__displayhook__(value)


assert sys.displayhook is sys.__displayhook__, (sys.displayhook, sys.__displayhook__)


#
# Define a Button for each ASCII Letter, plus some Shell Verbs
#


MODULE = sys.modules[__name__]


# awk = LitWord("awk")
bash = LitWord("bash")
cal = LitWord("cal")
cat = LitWord("cat")
clear = LitWord("clear")
cd = LitWord("cd")
cp = LitWord("cp")
curl = LitWord("curl")
date = LitWord("date")  # date +'+%H:%M:%S'
# dd = LitWord("dd")
df = LitWord("df")
diff = LitWord("diff")
echo = LitWord("echo")
find = LitWord("find")
# head = LitWord("head")
hexdump = LitWord("hexdump")
# jq = LitWord("jq")
# less = LitWord("less")
ls = LitWord("ls")
if str(sys.platform) == "linux":  # mentions of 'lsb_release' raise NameError on other Platforms
    lsb_release = LitWord("lsb_release")
man = LitWord("man")  # man +date
md5sum = LitWord("md5sum")
mkdir = LitWord("mkdir")
mv = LitWord("mv")
od = LitWord("od")
_open_ = LitWord("open")
pbpaste = LitWord("pbpaste")
ps = LitWord("ps")
pwd = LitWord("pwd")
python = LitWord("python")
python3 = LitWord("python3")
screen = LitWord("screen")
script = LitWord("script")
sh = LitWord("sh")
sleep = LitWord("sleep")
sort = LitWord("sort")
ssh = LitWord("ssh")
stty = LitWord("stty")
sudo = LitWord("sudo")
if str(sys.platform) == "darwin":  # mentions of 'sw_vers' raise NameError on other Platforms
    sw_vers = LitWord("sw_vers")
tail = LitWord("tail")
# time = LitWord("time")  # todo: Python 'import time' vs Shell 'time'
touch = LitWord("touch")
tr = LitWord("tr")
uptime = LitWord("uptime")
# if sys.platform == "darwin":
#     uptime = LitWord("uptime.py")  # todo: vs Shell 'uptime --pretty'
# xargs = LitWord("xargs")
zsh = LitWord("zsh")

_ = _open_


LSs = LitWord("LSs")  # curl -k -LSs +'http://example.com'
bpru = LitWord("bpru")  # diff -bpru +a +b
color = LitWord("color")  # ls --color
hlAF = LitWord("hlAF")  # ls -hlAF -rt
pretty = LitWord("pretty")  # uptime --pretty
rt = LitWord("rt")  # bash -c +ls -d -hlAF -rt +'*'
sane = LitWord("sane")  # stty +sane
version = LitWord("version")  # python3 --version


a = LitWord("a")
b = LitWord("b")
c = LitWord("c")
d = LitWord("d")
e = LitWord("e")
f = LitWord("f")
g = LitWord("g")
h = LitWord("h")
i = LitWord("i")
j = LitWord("j")
k = LitWord("k")
setattr(MODULE, "l", LitWord("l"))
m = LitWord("m")
n = LitWord("n")
o = LitWord("o")
p = LitWord("p")
q = LitWord("q")
r = LitWord("r")
s = LitWord("s")
t = LitWord("t")
u = LitWord("u")
v = LitWord("v")
w = LitWord("w")
x = LitWord("x")
y = LitWord("y")
z = LitWord("z")


A = LitWord("A")
B = LitWord("B")
C = LitWord("C")
D = LitWord("D")
E = LitWord("E")
F = LitWord("F")
G = LitWord("G")
H = LitWord("H")
setattr(MODULE, "I", LitWord("I"))
J = LitWord("J")
K = LitWord("K")
L = LitWord("L")
M = LitWord("M")
N = LitWord("N")
setattr(MODULE, "O", LitWord("O"))
P = LitWord("P")
Q = LitWord("Q")
R = LitWord("R")
S = LitWord("S")
T = LitWord("T")
U = LitWord("U")
V = LitWord("V")
W = LitWord("W")
X = LitWord("X")
Y = LitWord("Y")
Z = LitWord("Z")


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litword.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
