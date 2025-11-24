"""
usage: from pylitfun import litshell
"""

# code reviewed by people and by Black, Flake8, Mypy-Strict, & Pylance-Standard


import os
import sys


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


def sys_argv_patch_shverb_if(default: str) -> tuple[str, ...]:
    """Replace the ArgV 0 with the '--shfile=' Shell Arg if present as ArgV 1"""

    shverb = default
    alt_sys_argv = (shverb, *sys.argv[1:])

    if sys.argv[1:]:
        argv1 = sys.argv[1]

        (head, sep, tail) = argv1.partition("--shfile=")
        if (not head) and sep and tail:
            basename = os.path.basename(tail)

            shverb = basename
            shargs = tuple(sys.argv[2:])

            alt_sys_argv = (shverb, *shargs)

    assert alt_sys_argv[0] == shverb, (alt_sys_argv, shverb)

    return alt_sys_argv


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/litshell.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
