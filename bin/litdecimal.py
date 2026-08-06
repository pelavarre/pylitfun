#!/usr/bin/env python3

"""
usage: litdecimal.py --

show how we chop ints down to 3 digits at a multiple-of-three exponent

examples:
  bin/litdecimal.py --  # runs tests
"""

from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import decimal
import sys

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


def main() -> None:
    """Run from the Shell"""

    # import litsys
    # sys.excepthook = litsys.sys_excepthook_pdb_pm

    for i, s in _decimal_int_chop_to_eng_i_o_:
        _s_ = decimal_int_chop_to_eng(i)
        assert _s_ == s, (_s_, s)

    print("litdecimal.py: passed supercalifragilistically", file=sys.stderr)


#
# Amp up Import Decimal
#


def _(n: int) -> str:
    ctx = decimal.Context(prec=3, rounding=decimal.ROUND_DOWN)
    D = ctx.create_decimal
    i = int(repr(n))
    clip = D(i).to_eng_string().lower().replace("e+", "e")
    return clip

    # when coded without docstring and without comments


def decimal_int_chop_to_eng(n: int) -> str:
    """Rep the exact Int, else chop down to 3 Digits at an explicit Multiple-of-Three Exponent"""

    ctx = decimal.Context(prec=3, rounding=decimal.ROUND_DOWN)  # the towards-zero kind of "Down"
    D = ctx.create_decimal

    i = int(repr(n))  # raises ValueError when a Float breaks our ': int' contract
    clip = D(i).to_eng_string().lower().replace("e+", "e")

    return clip  # int(float(clip)) == n, or near to n but a little closer to zero

    # '-9.99e3'  # '-2'  # '0'  # '1'  # '987'  # '1.00e3'  # '9.87e3'  # '98.7e3'  # '987e3'
    # as if repr of float, int, int, int, int, float, float, float, float
    # with the unsigned 'e' standing in place of the int digits we did chop off

    # Python's hex int("987e3", 0x10) == 0x9_87E3 does nearly collide with our '987e3' lacking '.'
    # Python Floats overflow out beyond '179e306', but we correctly clip '180 * 10**306' and above

    # 'def decimal_int_chop_to_eng' last modified for py2def.py on 2026-07-31 or later


_decimal_int_chop_to_eng_i_o_: tuple[tuple[int, str], ...] = (
    (-9999, "-9.99e3"),  # not '-1e+04'
    (-2, "-2"),
    (0, "0"),  # not '0e0'  # not '0.0'
    (1, "1"),
    (42, "42"),
    (288, "288"),  # not '2.9e+02'
    (999, "999"),  # not '1e+03'
    (1000, "1.00e3"),
    (3652, "3.65e3"),
    (9876, "9.87e3"),
    (98765, "98.7e3"),
    (104999, "104e3"),  # not '1.05e+05'
    (987654, "987e3"),  # not '9.88e+05'
)


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/litdecimal.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
