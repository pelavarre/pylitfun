#!/usr/bin/env python3

"""
usage: litsys.py --

show how we tell uncaught exceptions to launch the py repl, as if a breakpoint were at the raise

examples:
  litsys.py
  litsys.py --  # raises AssertionError except when given Shell Args
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

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


# Pacific = zoneinfo.ZoneInfo("America/Los_Angeles")
# PacificLaunch = dt.datetime.now(Pacific)

Launch = dt.datetime.now()


def main() -> None:
    """Run from the Shell, but tell uncaught Exceptions to launch the Py Repl"""

    # sys.excepthook = sys_excepthook_pdb_pm  # catches SystemExit, KeyboardInterrupt, etc
    # try_main()

    try:

        try_main()

    except (Exception, KeyboardInterrupt):  # BrokenPipeError # never SystemExit

        # PacificQuit = dt.datetime.now(Pacific)
        # launch, _quit_ = PacificLaunch, PacificQuit

        Quit = dt.datetime.now()
        launch, _quit_ = Launch, Quit
        print(str(_quit_ - launch), "Quit='" + str(_quit_) + "'", "launch='" + str(launch) + "'")

        sys_excepthook_pdb_pm(*sys.exc_info())  # launches pdb.pm()

    except SystemExit:
        pass  # because 'return' shouts less than 'sys.exit' does, when run by 'python3 -i'


def try_main() -> None:

    print("Hello, Sys ExceptHook World!")

    time.sleep(0.321)

    assert sys.argv[1:], (sys.argv,)

    sys.exit()


#
# Amp up Import Traceback
#


assert sys.__stderr__ is not None  # refuses to run headless
with_stderr = sys.stderr

assert int(0x80 + signal.SIGINT) == 130  # discloses the Nonzero Exit Code for after ⌃C SigInt


def sys_excepthook_pdb_pm(
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

    # 'def sys_excepthook_pdb_pm' last modified for py2def.py on 2026-07-09 or later


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litsys.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
