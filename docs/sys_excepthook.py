#!/usr/bin/env python3

"""
usage: sys_excepthook.py --

slowly show much of how the macOS Copy-Paste Clipboard decodes and encodes bytes

examples:
  sys_excepthook.py
  sys_excepthook.py --  # raises AssertionError except when given Shell Args
"""

from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import bdb
import datetime as dt
import pdb
import signal
import sys
import time
import traceback
import types

# import zoneinfo

# Pacific = zoneinfo.ZoneInfo("America/Los_Angeles")
# PacificLaunch = dt.datetime.now(Pacific)

Launch = dt.datetime.now()


def main() -> None:
    """Run from the Shell, but tell uncaught Exceptions to launch the Py Repl"""

    # sys.excepthook = sys_excepthook_func  # catches SystemExit, KeyboardInterrupt, etc
    # try_main()

    try:

        try_main()

    except Exception, KeyboardInterrupt:  # BrokenPipeError # never SystemExit

        # PacificQuit = dt.datetime.now(Pacific)
        # print(PacificQuit, PacificQuit - PacificLaunch)

        Quit = dt.datetime.now()
        print(Quit, Quit - Launch)

        sys_excepthook_func(*sys.exc_info())  # launches pdb.pm()


def try_main() -> None:

    print("Hello, Sys ExceptHook World!")

    time.sleep(0.321)

    assert sys.argv[1:], (sys.argv,)


#
# Amp up Import Traceback
#

assert sys.__stderr__ is not None  # refuses to run headless
with_stderr = sys.stderr

assert int(0x80 + signal.SIGINT) == 130  # discloses the Nonzero Exit Code for after ⌃C SigInt


def sys_excepthook_func(  # last modified for py2def.py on 2026-07-03 or later
    exc_type: type[BaseException] | None,  # aka .type
    exc_value: BaseException | None,  # aka .exc_obj aka .value
    exc_traceback: types.TracebackType | None,  # aka .exc_tb aka .traceback aka .tb
) -> None:
    """Tell an Uncaught Exception to launch the Py Repl, as if a Breakpoint were at the Raise"""

    # Do nothing after a SystemExit

    if exc_type is SystemExit:
        return

        # consciously no traceback.print_exception
        # happens without sys.flags.interactive when not called via sys.excepthook

    # Quit loudly for KeyboardInterrupt

    if exc_type is KeyboardInterrupt:
        pass

    # Quit quietly, early now, if BdbQuit

    if exc_type is bdb.BdbQuit:
        with_stderr.write("BdbQuit\n")
        sys.exit(130)  # 0x80 + signal.SIGINT  # same as for KeyboardInterrupt

    # Print the usual 'Traceback (most recent call last):', & Traceback, & Assert

    print(file=with_stderr)
    print(file=with_stderr)  # twice

    traceback.print_exception(exc_type, value=exc_value, tb=exc_traceback, file=with_stderr)

    print(file=with_stderr)
    print(file=with_stderr)  # twice

    # Launch the Post-Mortem Debugger

    if exc_value is not None:
        if not hasattr(sys, "last_exc"):
            setattr(sys, "last_exc", exc_value)  # ducks out of confusing pdb.pm()

            # todo: figure out when .last_exc is and isn't initted for us

    if exc_traceback is not None:
        if not hasattr(sys, "last_traceback"):
            setattr(sys, "last_traceback", exc_traceback)  # ducks out of confusing pdb.pm()

            # todo: figure out when .last_traceback is and isn't initted for us

    print(">" ">" "> pdb.pm()", file=with_stderr)  # (3 * ">") spelled unlike a Git Conflict
    pdb.pm()  # launches the Py Repl of The Post-Mortem Debugger


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/sys_excepthook.py
# copied from:  git clone https://github.com/pelavarre/litpython.git
