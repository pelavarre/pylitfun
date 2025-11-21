#!/usr/bin/env python3

import signal
import subprocess
import sys

assert int(0x80 + signal.SIGINT) == 130

shverb = "git.py" if sys.stdin.isatty() else "grep.py"
sys.argv[0] = shverb

try:
    run = subprocess.run(sys.argv)
except KeyboardInterrupt:
    print(file=sys.stderr)  # after "^" and "C" printed without a "\r\n"
    sys.exit(130)

    # subprocess.run raises KeyboardInterrupt even when the called Python does catch & exit
    # some Linux Shells print a "\r\n" after Python exits after catching a KeyboardInterrupt

sys.exit(run.returncode)
