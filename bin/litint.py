#!/usr/bin/env python3

"""
usage: litint.py --

show how we chop ints down to 3 digits at a multiple-of-three exponent

examples:
  bin/litint.py --  # runs tests
  from litint import decimal_int_chop_to_eng as ichop
"""

from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import decimal
import sys

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


def main() -> None:
    """Run from the Shell"""

    _self_test_()


#
# Amp up Import BuiltIns
#


def repr_int_chop_to_eng(n: int) -> str:
    """Rep the exact Int, else chop down to 3 Digits at an explicit Multiple-of-Three Exponent"""

    i = int(repr(n))  # raises ValueError when a Float breaks our ': int' contract
    s = repr(i)  # '-120789'
    _, dash, digits = s.rpartition("-")  # ('', '-', '120789')

    sci = len(digits) - 1  # 5
    eng = 3 * (sci // 3)  # 3

    assert eng in (sci, sci - 1, sci - 2), (eng, sci, digits, n)

    clip = s
    if eng:

        assert len(digits) >= 4, (len(digits), eng, sci, digits, n)
        assert 1 <= (len(digits) - eng) <= 3, (len(digits), eng, sci, digits, n)

        precise = digits[:-eng] + "." + digits[-eng:]  # '120.789'
        nearby = precise[:4]  # '120.'  # significand, mantissa, multiplier  # with a dot included
        worthy = nearby.rstrip(".")  # '120' # drops a single trailing '.'

        assert "." in nearby, (nearby, precise, eng, sci, digits, n)

        clip = dash + worthy + "e" + str(eng)  # '-120e3' as a way of saying -120*10**3

    if -(2**53) < i < 2**53:
        aif = abs(int(float(clip)))
        assert aif <= abs(i), (aif, abs(i), i, n)

    return clip

    # raises ValueError above n = 10**4300 - 1

    # '-9.99e3'  # '-2'  # '0'  # '1'  # '987'  # '1.00e3'  # '9.87e3'  # '98.7e3'  # '987e3'
    # as if repr of float, int, int, int, int, float, float, float, float
    # with the unsigned 'e' standing in place of the int digits we did chop off

    # Python's hex int("987e3", 0x10) == 0x9_87E3 does nearly collide with our '987e3' lacking '.'
    # Python Floats overflow out beyond '179e306', but we correctly clip '180 * 10**306' and above

    # 'def repr_int_chop_to_eng' last modified for py2def.py on 2026-08-22 or later


#
# Amp up Import Decimal
#


def _(n: int) -> str:

    ctx = decimal.Context(prec=3, rounding=decimal.ROUND_DOWN)
    D = ctx.create_decimal

    clip = D(n).to_eng_string().lower().replace("e+", "e")

    return clip

    # when coded without docstring, without comments, and without asserts


def decimal_int_chop_to_eng(n: int) -> str:
    """Rep the exact Int, else chop down to 3 Digits at an explicit Multiple-of-Three Exponent"""

    i = int(repr(n))  # raises ValueError when a Float breaks our ': int' contract
    ctx = decimal.Context(prec=3, rounding=decimal.ROUND_DOWN)  # the towards-zero kind of "Down"
    D = ctx.create_decimal  # truncating is not ceiling, floor, half down/up, half even, nor 0 5 up

    clip = D(i).to_eng_string().lower().replace("e+", "e")

    if -(2**53) < i < 2**53:
        aif = abs(int(float(clip)))
        assert aif <= abs(i), (aif, abs(i), i, n)

    return clip  # int(float(clip)) == n, or near to n but a little closer to zero

    # raises ValueError above n = 10**4300 - 1

    # '-9.99e3'  # '-2'  # '0'  # '1'  # '987'  # '1.00e3'  # '9.87e3'  # '98.7e3'  # '987e3'
    # as if repr of float, int, int, int, int, float, float, float, float
    # with the unsigned 'e' standing in place of the int digits we did chop off

    # Python's hex int("987e3", 0x10) == 0x9_87E3 does nearly collide with our '987e3' lacking '.'
    # Python Floats overflow out beyond '179e306', but we correctly clip '180 * 10**306' and above

    # 'def decimal_int_chop_to_eng' last modified for py2def.py on 2026-08-25 or later


#
# Amp up Import Math for Decimal Metric Units and Binary Metric Units
#
#   from litint import k, M, G, T, P, E, Z, Y, R, Q
#   from litint import Ki, Mi, Gi, Ti, Pi, Ei, Zi, Yi, Ri, Qi
#


k = 10**3  # 'kMGTPEZYRQ' from https://en.wikipedia.org/wiki/Metric_prefix
M = 10**6
G = 10**9
T = 10**12
P = 10**15
E = 10**18
Z = 10**21
Y = 10**24
R = 10**27
Q = 10**30


Ki = 2**10  # "KMGTPE" + 'i' at https://physics.nist.gov/cuu/Units/binary.html
Mi = 2**20
Gi = 2**30
Ti = 2**40
Pi = 2**50
Ei = 2**60
Zi = 2**70  # "KMGTPEZYRQ" + 'i' at https://en.wikipedia.org/wiki/Binary_prefix
Yi = 2**80
Ri = 2**90
Qi = 2**100


#
# Test things around here
#


def _self_test_() -> None:
    """Test things around here"""

    # import litsys
    # sys.excepthook = litsys.sys_excepthook_pdb_pm

    for i, s in _str_by_int_.items():

        _s_ = repr_int_chop_to_eng(i)
        assert _s_ == s, (_s_, s)

        _s_ = decimal_int_chop_to_eng(i)
        assert _s_ == s, (_s_, s)

    print("litint.py: passed supercalifragilistically", file=sys.stderr)


_str_by_int_ = {
    -9999: "-9.99e3",  # not '-1e+04'
    -2: "-2",
    0: "0",  # not '0e0'  # not '0.0'
    1: "1",
    42: "42",
    288: "288",  # not '2.9e+02'
    999: "999",  # not '1.00e+03'
    1000: "1.00e3",  # not '1e+03'
    3652: "3.65e3",
    9876: "9.87e3",
    98765: "98.7e3",
    104999: "104e3",  # not '1.05e+05'
    120789: "120e3",  # not '1.21e+05'
    987654: "987e3",  # not '9.88e+05'
}


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/litint.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
