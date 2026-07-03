#!/usr/bin/env python3

"""
usage: litdecimal.py --

show how we chop ints down to 3 digits at a multiple-of-three exponent

examples:
  litdecimal.py --  # runs tests
"""

from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import decimal
import sys

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


def main() -> None:
    """Run from the Shell"""

    # import litsys
    # sys.excepthook = litsys.sys_excepthook

    int_chop_to_eng(0)  # 'better called without check than untested'
    int_chop_to_eng(1)
    int_chop_to_eng(1000)
    int_chop_to_eng(9876)
    int_chop_to_eng(98765)
    int_chop_to_eng(987654)

    print("litdecimal.py: passed supercalifragilistically", file=sys.stderr)


#
# Amp up Import Decimal
#


def int_chop_to_eng(n: int) -> str:
    """Chop down to 3 Digits at a Multiple-of-Three Exponent"""

    ctx = decimal.Context(prec=3, rounding=decimal.ROUND_DOWN)  # the Towards-Zero kind of "Down"
    D = ctx.create_decimal

    clip = D(n).to_eng_string().lower()

    return clip

    # '0'  # '1'  # '1.00e+3'  # '987' # '9.87e+3'  # '98.7e+3'  # '987e+3'

    # 'def int_chop_to_eng' last modified for py2def.py on 2026-07-04 or later


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/litdecimal.py
# copied from:  git clone https://github.com/pelavarre/litpython.git
