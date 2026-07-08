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

import builtins
import os
import shlex
import subprocess
import sys
import traceback

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


def main() -> None:
    """Launch a Python Chat"""

    ps1 = LitWordSysPs1(">>> ")

    sys.ps1 = ps1
    sys.displayhook = sys_displayhook
    os.environ["PYTHONINSPECT"] = str(True)


def _exec_(pytext: str) -> None:
    """Read, Eval, Print Repr, Loop across the Lines of the Text in order"""

    ps1 = LitWordSysPs1(">>> ")

    pylines = pytext.splitlines()
    for pyline in pylines:
        str(ps1)  # calls as if printing prompt before reading input
        value = eval(pyline)
        repr(value)  # calls as if printing repr


#
# Reconstruct a Shell Input Line from how Python calls its pieces after parsing it
#


class LitWord:
    """Reconstruct a Shell Input Line from how Python calls its pieces after parsing it"""

    argv: list[str] = list()
    marks = ""

    def __init__(self, name: str) -> None:
        self.name = name

    #
    # Catch a "-" or "+" Unary Operator as a Mark on the left of a Word
    #

    def __pos__(self) -> LitWord:
        marks = LitWord.marks
        LitWord.marks = "+" + marks
        return self

    def __neg__(self) -> LitWord:
        marks = LitWord.marks
        LitWord.marks = "-" + marks
        return self

    #
    # Give a "-" Binary Operator as a second "-" Mark
    # Give a "+" Binary Operator as an empty "" Mark
    #

    def __add__(self, other: object) -> LitWord:
        self._binop_(mark="", other=other)  # mark="", not mark="+"
        return self

    def __radd__(self, _: object) -> LitWord:
        return self

    def __rsub__(self, _: object) -> LitWord:
        return self

    def __sub__(self, other: object) -> LitWord:
        self._binop_(mark="-", other=other)
        return self

    def _binop_(self, mark: str, other: object) -> None:

        argv = LitWord.argv

        if isinstance(other, LitWord):
            word = mark + LitWord.marks + other.name
            LitWord.marks = ""
        else:
            word = mark + str(other)  # str.__str__, not str.__repr__, in particular

        argv.append(word)

    #
    # Reconstruct & run the Shell Input Line, when the Py Repl calls Repr
    #

    def __repr__(self) -> str:
        """Reconstruct & run the Shell Input Line, when the Py Repl calls Repr"""

        _shline_, _argv_ = self._take_shline_argv_()
        assert _shline_, (_shline_,)
        assert _argv_, (_argv_,)

        sys.stdout.flush()
        print("+", _shline_, file=sys.stderr)
        sys.stderr.flush()

        try:
            subprocess.run(_argv_)
        except Exception as exc:
            texts = traceback.format_exception(exc, limit=0)  # colorize=sys.stderr.isatty(
            print(texts[0].rstrip())

        sys.stdout.flush()
        print("+", file=sys.stderr)
        sys.stderr.flush()

        r = object.__repr__(self)
        return r

    def _take_shline_argv_(self) -> tuple[str, list[str]]:
        """Reconstruct the Shell ArgV, after the Py Repl finishes parsing it & calling pieces"""

        name = self.name

        argv = LitWord.argv
        marks = LitWord.marks

        # Form the Shell ArgV

        _argv_ = list(argv)

        _argv_[0:0] = [name]
        if marks:
            _argv_ += [marks]  # warps marks on the Shell Verb out to the far end of line

        if _argv_[0][:1] in "-+":  # never tries to call a Shell Verb started by "+" or "-"
            _argv_[0:0] = ["echo"]

        # Split a "---" Triple Dash that may have come from Python joining 3 "-" Single Dashes

        for i, arg in enumerate(_argv_):
            if i and arg.startswith("--"):
                if arg == "--":  # stops searching when the Dash Options end
                    break
                if arg.startswith("---"):
                    _argv_[i : i + 1] = ["--", arg.removeprefix("--")]
                    break

        # Form the Shell Line (like to trace it)

        _shline_ = ""
        for arg in _argv_:
            if _shline_:
                _shline_ += " "
            _shline_ += shlex.quote(arg)

        # Succeed

        return (_shline_, _argv_)


class LitWordSysPs1:
    """Restart the Shell Line when the Py Repl calls for $PS1"""

    def __init__(self, ps1: str) -> None:
        self.ps1 = ps1

    def __str__(self) -> str:
        LitWord.argv.clear()
        LitWord.marks = ""
        return self.ps1


assert sys.displayhook is sys.__displayhook__, (sys.displayhook, sys.__displayhook__)


def sys_displayhook(value: object) -> None:
    """Run as a Sys DisplayHook but see None as the Repr of 1 or more LitWord's"""

    hooking = False
    if isinstance(value, LitWord):
        hooking = True
    elif isinstance(value, tuple):
        if value and all(isinstance(v, LitWord) for v in value):
            hooking = True

    if hooking:
        repr(value)  # calls as if printing repr
        setattr(builtins, "_", value)  # stores as if running sys.__displayhook__
        return

        # note: __builtins__ vs builtins work differently for main script vs imported py files

    sys.__displayhook__(value)  # falls back to the Stock Py Repl for every other Value


#
# Define a Button for each ASCII Letter, plus some Shell Verbs
#


MODULE = sys.modules[__name__]


# awk = LitWord("awk")
bash = LitWord("bash")
cal = LitWord("cal")
cat = LitWord("cat")
clear = LitWord("clear")
# cd = LitWord("cd")  # todo: build in verbs to call in place of subprocess.run
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
if sys.platform == "linux":
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
if sys.platform == "darwin":
    sw_vers = LitWord("sw_vers")
tail = LitWord("tail")
# time = LitWord("time")  # todo: vs Shell 'time'
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
