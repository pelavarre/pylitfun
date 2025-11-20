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
    print(file=sys.stderr)
    sys.exit(130)

sys.exit(run.returncode)
