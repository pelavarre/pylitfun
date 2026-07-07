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

    for i, s in _decimal_int_chop_to_eng_i_o_:
        _s_ = decimal_int_chop_to_eng(i)
        assert _s_ == s, (_s_, s)

    print("litdecimal.py: passed supercalifragilistically", file=sys.stderr)


#
# Amp up Import Decimal
#


def decimal_int_chop_to_eng(n: int) -> str:
    """Chop down to 3 Digits at a Multiple-of-Three Exponent"""

    ctx = decimal.Context(prec=3, rounding=decimal.ROUND_DOWN)  # the Towards-Zero kind of "Down"
    D = ctx.create_decimal

    i = int(repr(n))  # raises ValueError when a Float breaks our ': int' contract
    clip = D(i).to_eng_string().lower().replace("e+", "e")

    return clip  # int(float(clip)) is equal to (n) or less than and near (n)
    # '0'  # '1'  # '1.00e3'  # '987' # '9.87e3'  # '98.7e3'  # '987e3'
    # as if repr of int, int, float, int, float, float, float  # and '987e3' can mean 0x9_87E3

    # 'def decimal_int_chop_to_eng' last modified for py2def.py on 2026-07-05 or later


_decimal_int_chop_to_eng_i_o_: tuple[tuple[int, str], ...] = (
    (0, "0"),
    (1, "1"),
    (42, "42"),
    (999, "999"),
    (1000, "1.00e3"),
    (9876, "9.87e3"),
    (98765, "98.7e3"),
    (987654, "987e3"),
)


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/litdecimal.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
