r"""
usage: python3 bin/...

run as if Python first found a /pylitfun/ Dir in the Dirs above this File

examples:
  cd pylitfun/
  python3 -m pdb bin/litshell.py
    import pylitfun
    print(pylitfun.__file__)
"""

# code reviewed by people and by Black, Flake8, Mypy-Strict, & Pylance-Standard


import os
import sys


# Start searching where we are

if "PWD" in os.environ.keys():
    PWD = os.environ["PWD"]  # commonly an Abs Path, but often not a Real Path
else:
    MODULE = sys.modules[__name__]

    FILENAME = MODULE.__file__
    assert FILENAME, (FILENAME, MODULE, __name__)
    DIRNAME = os.path.dirname(FILENAME)  # commonly an Abs Real Path

    PWD = DIRNAME


# Search the Paths above to find a /pylitfun/ to import in place of this File

WD = PWD
while True:
    assert WD, (WD, PWD)

    PATHNAME = os.path.join(WD, "pylitfun")  # often missing from Abs Paths above
    if os.path.isdir(PATHNAME):  # if is Dir or SymLink-to-Dir
        break

    WD = os.path.dirname(WD)  # step back up through SymLink-to-Dir or through Dir
    assert WD != "/", (WD, PWD)


# Change the Py Sys Path to place the Found Dir ahead of all others

if sys.path:
    assert sys.path[0] != WD, (sys.path[0], WD, sys.path)

sys_path_before = list(sys.path)
sys.path.insert(0, WD)

del sys.modules[__name__]


# Retry the Import of PyLitFun

if True:
    import pylitfun

    sys.path[::] = sys_path_before

    # the enclosing If-True ducks Flake8:  E402 module level import not at top of file


# Promise the Linters we do nothing more with PyLitFun here

_ = pylitfun
