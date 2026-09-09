#!/usr/bin/env python3

"""
usage: g.py ..., or |g.py ...

run the colocated litpygit.py in place of g.py, or run the |grep.py in place of |g.py

quirks:
  without pipelike stdin, calls litpygit.py [--help] [--make-bin] SHFILE [SHWORD ...]
  with pipelike stdin, calls |grep.py SHFILE [SHWORD ...]
  test results found by calling with SHWORD but without a SHFILE of 'pylitgit/g' don't much matter

examples:
  g.py  # litpygit.py
  echo |g.py  # grep.py
  g.py <requirements.txt  # grep.py
  g.py </dev/null  # litpygit.py
  cat <(g.py)  # litpygit.py
  cat <(g.py) |cat -  # litpygit.py, no matter that Zsh infers </dev/null
"""

import os
import signal
import stat
import subprocess
import sys

#


ifstat = os.fstat(sys.stdin.fileno())
os_devnull_rdev = os.stat(os.devnull).st_rdev
inull = stat.S_ISCHR(ifstat.st_mode) and (ifstat.st_rdev == os_devnull_rdev)
ipipelike = (not sys.stdin.isatty()) and (not inull)  # lets 'cat <(g.py) |' work at Zsh

shverb = "grep.py" if ipipelike else "litpygit.py"
argv0 = os.path.join(os.path.dirname(__file__), shverb)

argv = list(sys.argv)
argv[0] = argv0


assert int(0x80 + signal.SIGINT) == 130
pass_fds = tuple(int(_) for _ in os.listdir("/dev/fd"))
try:
    run = subprocess.run(argv, pass_fds=pass_fds)
except KeyboardInterrupt:
    if sys.platform == "darwin":
        print(file=sys.stderr)  # after "^" and "C" printed without a "\r\n"
    sys.exit(130)

    # subprocess.run raises KeyboardInterrupt even when the called Python does catch & exit
    # Linux Shells print a "\r\n" after Python exits after catching a KeyboardInterrupt


sys.exit(run.returncode)


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/pylitgit/g.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
