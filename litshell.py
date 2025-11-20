"""
usage: from litpyfun import litshell
"""

# code reviewed by people and by Black, Flake8, Mypy-Strict, & Pylance-Standard


import os
import subprocess
import sys


def exit_after_shell(shline: str) -> None:
    """Run the Sh Line on Stdin/Stdout/Stderr and exit, but mention the Exit Code if nonzero"""

    run = subprocess.run(shline, shell=True)
    if run.returncode:
        print("+ exit", run.returncode, file=sys.stderr)

    sys.exit(run.returncode)


def exit_after_run(argv: list[str]) -> None:
    """Run the ArgV on Stdin/Stdout/Stderr and exit, but mention the Exit Code if nonzero"""

    run = subprocess.run(argv)
    if run.returncode:
        print("+ exit", run.returncode, file=sys.stderr)

    sys.exit(run.returncode)


def grep_expand_ae_i(shargs: tuple[str, ...]) -> tuple[str, ...]:
    """Tune to presume text, ignore case, and match >= 1 patterns"""

    strs = list()
    strs.append("-ai")  # -a = --text  # -i = --ignore-case
    for i, arg in enumerate(shargs):
        if arg == "--":
            strs.extend(shargs[i:])
            break
        elif arg.startswith("-"):
            strs.append(arg)
        else:
            strs.append("-e")
            strs.append(arg)

    argv = tuple(strs)
    return argv


def sys_argv_partition(default: str) -> tuple[str, ...]:
    """Drop a leading '--shfile=' Arg if present"""

    alt_sys_argv = (default, *sys.argv[1:])

    if sys.argv[1:]:
        arg1 = sys.argv[1]

        (head, sep, tail) = arg1.partition("--shfile=")
        if (not head) and sep and tail:
            basename = os.path.basename(tail)

            shverb = basename
            shargs = tuple(sys.argv[2:])

            alt_sys_argv = (shverb, *shargs)

    return alt_sys_argv


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/litshell.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
