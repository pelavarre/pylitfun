#!/usr/bin/env python3

"""
usage: grep.py [--shfile=SHFILE] SHWORD [SHWORD ...]

call Grep but as |grep -ai -e ... -e ...

positional arguments:
  SHWORD           option or positional argument of Grep

options:
  --help           show this help message and exit (-h is for Grep, not for Grep·Py)
  --shfile SHFILE  which Grep Alias to decode

quirks:
  tunes to presume text, ignore case, and match >= 1 patterns (like for 2025, in place of 1973)

examples:
  cat bin/*.py |g -nw def print
  cat bin/*.py |grep.py --shfile=$HOME/bin/g -nw def print
  cat bin/*.py |grep -ai -nw -e def -e print
"""

# code reviewed by people and by Black, Flake8, Mypy-Strict, & Pylance-Standard


import shlex
import subprocess
import sys

from pylitfun import litshell

if not __debug__:
    raise NotImplementedError([__debug__])  # because 'python3 better than python3 -O'


shargv = litshell.sys_argv_patch_shverb_if(default="g")
if shargv[0] != "g":
    raise NotImplementedError(shargv)


if not sys.argv[2:]:
    print("usage: |grep.py SHWORD [SHWORD ...]", file=sys.stderr)
    sys.exit(2)  # exits 2 for bad args


argv = list()
argv.append("grep")
argv.extend(litshell.grep_expand_ae_i(tuple(sys.argv[2:])))

join = shlex.join(argv)
print("|" + join, file=sys.stderr)


run = subprocess.run(argv)
if run.returncode:
    print("+ exit", run.returncode, file=sys.stderr)

sys.exit(run.returncode)


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/grep.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
