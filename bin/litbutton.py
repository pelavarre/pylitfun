#!/usr/bin/env python3

r"""
usage: litbutton.py [-h] [PY ...]

take python input lines begun by shell verbs as shell input lines

positional arguments:
  PY          one more line of python code to eval

options:
  -h, --help  show this help message and exit

examples:
  bin/litbutton.py --
"""

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import os
import shlex
import subprocess
import sys
import textwrap
import traceback

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


def main() -> None:
    """Launch a Python Chat, or eval each Python Line in order"""

    argv1 = sys.argv[1:]
    if argv1 and argv1[0] == "--":
        argv1 = argv1[1:]

    # Launch a Python Chat

    prompt = LitPs1Prompt(">>> ")

    pytext = textwrap.dedent("\n".join(argv1)).strip()
    if not pytext:
        sys.ps1 = prompt
        os.environ["PYTHONINSPECT"] = str(True)
        return

    # Eval each Python Line in order

    for pyline in pytext.splitlines():
        str(prompt)
        value = eval(pyline)
        repr(value)
        print(file=sys.stderr)


#
# Reconstruct a Shell Input Line from how Python calls its pieces after parsing it
#


class LitButton:
    """Reconstruct a Shell Input Line from how Python calls its pieces after parsing it"""

    argv: list[str] = list()
    marks = ""

    def __init__(self, name: str) -> None:
        self.name = name

    #
    # Catch a "-" or "+" Unary Operator as a Mark on the left of a Word
    #

    def __pos__(self) -> LitButton:
        marks = LitButton.marks
        LitButton.marks = "+" + marks
        return self

    def __neg__(self) -> LitButton:
        marks = LitButton.marks
        LitButton.marks = "-" + marks
        return self

    #
    # Give a "-" Binary Operator as a second "-" Mark
    # Give a "+" Binary Operator as an empty "" Mark
    #

    def __add__(self, other: object) -> LitButton:
        self._binop_(mark="", other=other)  # mark="", not mark="+"
        return self

    def __radd__(self, other: object) -> LitButton:
        return self

    def __rsub__(self, other: object) -> LitButton:
        return self

    def __sub__(self, other: object) -> LitButton:
        self._binop_(mark="-", other=other)
        return self

    def _binop_(self, mark: str, other: object) -> None:

        argv = LitButton.argv

        if isinstance(other, LitButton):
            word = mark + LitButton.marks + other.name
            LitButton.marks = ""
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
        print("+", end="", file=sys.stderr)
        sys.stderr.flush()

        return ""

    def _take_shline_argv_(self) -> tuple[str, list[str]]:
        """Reconstruct the Shell ArgV, after the Py Repl finishes parsing it & calling pieces"""

        name = self.name

        argv = LitButton.argv
        marks = LitButton.marks

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


class LitPs1Prompt:
    """Restart the Shell Line when the Py Repl calls for $PS1"""

    def __init__(self, ps1: str) -> None:
        self.ps1 = ps1

    def __str__(self) -> str:
        LitButton.argv.clear()
        LitButton.marks = ""
        return self.ps1


#
# Define a Button for each ASCII Letter, plus some Shell Verbs
#


MODULE = sys.modules[__name__]


# awk = LitButton("awk")
bash = LitButton("bash")
cal = LitButton("cal")
cat = LitButton("cat")
clear = LitButton("clear")
# cd = LitButton("cd")  # todo: build in verbs to call in place of subprocess.run
cp = LitButton("cp")
curl = LitButton("curl")
date = LitButton("date")  # date +'+%H:%M:%S'
# dd = LitButton("dd")
df = LitButton("df")
diff = LitButton("diff")
echo = LitButton("echo")
find = LitButton("find")
# head = LitButton("head")
hexdump = LitButton("hexdump")
# jq = LitButton("jq")
# less = LitButton("less")
ls = LitButton("ls")
if sys.platform == "linux":
    lsb_release = LitButton("lsb_release")
man = LitButton("man")  # man +date
md5sum = LitButton("md5sum")
mkdir = LitButton("mkdir")
mv = LitButton("mv")
od = LitButton("od")
_open_ = LitButton("open")
pbpaste = LitButton("pbpaste")
ps = LitButton("ps")
pwd = LitButton("pwd")
python3 = LitButton("python3")
screen = LitButton("screen")
script = LitButton("script")
sh = LitButton("sh")
sleep = LitButton("sleep")
sort = LitButton("sort")
ssh = LitButton("ssh")
stty = LitButton("stty")
sudo = LitButton("sudo")
if sys.platform == "darwin":
    sw_vers = LitButton("sw_vers")
tail = LitButton("tail")
# time = LitButton("time")  # todo: vs Shell 'time'
touch = LitButton("touch")
tr = LitButton("tr")
uptime = LitButton("uptime")
# if sys.platform == "darwin":
#     uptime = LitButton("uptime.py")  # todo: vs Shell 'uptime --pretty'
# xargs = LitButton("xargs")
zsh = LitButton("zsh")

_ = _open_


LSs = LitButton("LSs")  # curl -k -LSs +'http://example.com'
bpru = LitButton("bpru")  # diff -bpru +a +b
hlAF = LitButton("hlAF")  # ls -hlAF -rt
pretty = LitButton("pretty")  # uptime --pretty
rt = LitButton("rt")  # bash -c +ls -d -hlAF -rt +'*'
sane = LitButton("sane")  # stty +sane


a = LitButton("a")
b = LitButton("b")
c = LitButton("c")
d = LitButton("d")
e = LitButton("e")
f = LitButton("f")
g = LitButton("g")
h = LitButton("h")
i = LitButton("i")
j = LitButton("j")
k = LitButton("k")
setattr(MODULE, "l", LitButton("l"))
m = LitButton("m")
n = LitButton("n")
o = LitButton("o")
p = LitButton("p")
q = LitButton("q")
r = LitButton("r")
s = LitButton("s")
t = LitButton("t")
u = LitButton("u")
v = LitButton("v")
w = LitButton("w")
x = LitButton("x")
y = LitButton("y")
z = LitButton("z")


A = LitButton("A")
B = LitButton("B")
C = LitButton("C")
D = LitButton("D")
E = LitButton("E")
F = LitButton("F")
G = LitButton("G")
H = LitButton("H")
setattr(MODULE, "I", LitButton("I"))
J = LitButton("J")
K = LitButton("K")
L = LitButton("L")
M = LitButton("M")
N = LitButton("N")
setattr(MODULE, "O", LitButton("O"))
P = LitButton("P")
Q = LitButton("Q")
R = LitButton("R")
S = LitButton("S")
T = LitButton("T")
U = LitButton("U")
V = LitButton("V")
W = LitButton("W")
X = LitButton("X")
Y = LitButton("Y")
Z = LitButton("Z")


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litbutton.py
# copied from:  git clone https://github.com/pelavarre/litbutton.git
