#!/usr/bin/env python3

"""
usage: g.py ...

call git.py in place of g.py, or call |grep.py in place of |g.py

examples:
    g.py  # git.py
    echo |g.py  # grep.py
    cat <(g.py)  # git.py
    cat <(g.py) |cat -  # git.py or grep.py chosen by Shell 🙄
    cat <(</dev/tty g.py) |cat -  # git.py
"""

import os
import signal
import subprocess
import sys

shverb = "git.py" if sys.stdin.isatty() else "grep.py"  # sadly, Zsh <() turns Stdin Isatty False
sys.argv[0] = shverb


assert int(0x80 + signal.SIGINT) == 130
pass_fds = tuple(int(_) for _ in os.listdir("/dev/fd"))
try:
    run = subprocess.run(sys.argv, pass_fds=pass_fds)
except KeyboardInterrupt:
    if sys.platform == "darwin":
        print(file=sys.stderr)  # after "^" and "C" printed without a "\r\n"
    sys.exit(130)

    # subprocess.run raises KeyboardInterrupt even when the called Python does catch & exit
    # Linux Shells print a "\r\n" after Python exits after catching a KeyboardInterrupt


sys.exit(run.returncode)


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/g.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
