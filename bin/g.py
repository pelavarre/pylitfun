#!/usr/bin/env python3

"""
usage: g.py ...

call git.py in place of g.py, else call |grep.py in place of |g.py
"""


import signal
import subprocess
import sys


shverb = "git.py" if sys.stdin.isatty() else "grep.py"
sys.argv[0] = shverb


assert int(0x80 + signal.SIGINT) == 130
try:
    run = subprocess.run(sys.argv)
except KeyboardInterrupt:
    if sys.platform == "darwin":
        print(file=sys.stderr)  # after "^" and "C" printed without a "\r\n"
    sys.exit(130)

    # subprocess.run raises KeyboardInterrupt even when the called Python does catch & exit
    # Linux Shells print a "\r\n" after Python exits after catching a KeyboardInterrupt


sys.exit(run.returncode)
