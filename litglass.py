#!/usr/bin/env python3

r"""
usage: litglass.py [-h] [-f] [--seed SEED] [--egg EGG]

loop Input back to Output, to Screen from Touch/ Mouse/ Key

options:
  -h, --help   show this help message and exit
  -f, --force  ask fewer questions (like do run slow self-test's)
  --seed SEED  a chosen seed for pseudorandom choices (like to replay a game)
  --egg EGG    a hint of how to behave, such as 'repr' or 'sigint'

quirks:
  talks with the Terminal at Stderr (with /dev/stderr, not with /dev/tty)
  quits when given ⌃C

examples:
  ./litglass.py --  # runs with defaults
  ./litglass.py --egg=enter  # launches into loop back with no setup
  ./litglass.py --egg=exit  # quits after loop back with no teardown
  ./litglass.py --egg=help  # surfaces like two dozen easter eggs planted here
  ./litglass.py --egg=scrollback  # scrolls into scrollback then launch in alt screen
  ./litglass.py --egg=yolo  # runs with defaults, but more explicitly so
"""

# ./litglass.py --egg=logging  # writes log lines into ./__pycache__/litglass.log

# ./litglass.py --egg=clickarrows  # to loopback the ⌥-Click Arrows as they come in
# ./litglass.py --egg=clickruns  # to loopback the ⌥-Click Arrows as run-length compressed
# ./litglass.py --egg=sigint  # for ⌃C to raise KeyboardInterrupt

# ./litglass.py --egg=assert  # to assert False before doing much
# ./litglass.py --egg=byteloop  # loop back without adding latencies
# ./litglass.py --egg=color-picker  # to launch our Color Picker Game
# ./litglass.py --egg=echoes  # to echo the Control Sequences as they run
# ./litglass.py --egg=keycaps  # to launch our keyboard-viewer of keycaps
# ./litglass.py --egg=repr  # to loop the Repr, not the Str
# ./litglass.py --egg=squares  # to launch our Squares Game

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import __main__
import argparse
import bdb
import collections
import collections.abc  # .collections.abc is not .abc
import dataclasses
import datetime as dt
import difflib
import functools
import itertools
import logging
import math
import os
import pdb
import random
import re
import select
import shlex
import signal
import string
import sys
import termios
import textwrap
import time
import traceback
import tty
import types
import typing
import unicodedata  # of a .unicodedata.unidata_version for friends of 웃 襾 ¤


_: object  # blocks Mypy from narrowing the Datatype of '_ =' at first mention

if not __debug__:
    raise NotImplementedError([__debug__])  # because 'python3 better than python3 -O'


default_eq_None = None  # spells out 'default=None' where Python forbids that

logger = logging.getLogger(__name__)


#
# Choose a personality
#


_os_environ_get_cloud_shell_ = os.environ.get("CLOUD_SHELL", "")


@dataclasses.dataclass(order=True)  # , frozen=True)
class Flags:
    """Choose a personality"""

    # Always truthy:  flags.yolo

    yolo: bool = True  # placeholder, means almost nothing

    # Chosen for you or by --egg:  flags.apple, flags.google, flags.terminal

    apple: bool = sys.platform == "darwin"
    google: bool = bool(_os_environ_get_cloud_shell_)
    terminal: bool = os.environ.get("TERM_PROGRAM", "") == "Apple_Terminal"

    mobile: bool = False  # truthy for < 30x30 Columns x Rows discovered

    # todo: barefoot:  #  for when Rows not-hidden beneath a Southern Keyboard
    # todo: portrait:  #  for when lots more Rows than Columns
    # todo: landscape:  #  for when lots more Columns than Row
    # todo: darkmode:  #  for when low low Luminance as uncolored backlight
    # todo: lightmode:  #  for when high high Luminance as uncolored backlight

    #
    # Chosen by big tech --egg, or not
    #
    #   flags.enter, flags._exit_, flags.logging, flags.scrollback
    #

    enter: bool = False  # launch loop back with no setup
    _exit_: bool = False  # quit loop back with no teardown
    logging: bool = False  # write log lines into ./__pycache__/litglass.log
    scrollback: bool = False  # launch below Scrollback

    #
    # Chosen by small tech --egg, or not
    #
    #   flags.clickarrows, flags.clickruns, flags.sigint
    #

    clickarrows: bool = False  # loop back the ⌥-Click Arrows as they arrive
    clickruns: bool = False  # loop back the ⌥-Click Arrows as run-length compressed
    darkmode: bool = False  # for low low Luminance as uncolored backlight
    lightmode: bool = False  # for high high Luminance as uncolored backlight
    sigint: bool = False  # for ⌃C to raise KeyboardInterrupt, for ⏎ to say ⌃J not ⌃M

    #
    # Chosen by game --egg, or not
    #
    #   flags._assert_, flags.byteloop, flags.color_picker, flags.echoes, flags.keycaps,
    #   flags._repr_, flags.squares
    #

    _assert_: bool = False  # assert False before doing much
    byteloop: bool = False  # loop back without adding latencies
    color_picker: bool = False  # show Color choices and tweak them
    echoes: bool = False  # echo the Control Sequences as they loopback
    keycaps: bool = False  # launch our Keyboard-Viewer of Leycaps
    _repr_: bool = False  # loop the Repr, not the Str
    squares: bool = False  # launch our Squares Game

    @property
    def games(self) -> int:
        """Count the Games Chosen"""

        games = 0

        games += self._assert_
        games += self.byteloop
        games += self.color_picker
        games += self.echoes
        games += self.keycaps
        games += self._repr_
        games += self.squares

        if games > 1:
            print(
                "Choose at most one of:"
                "  assert, byteloop, color-picker, echoes, keycaps, repr, squares",
                file=sys.stderr,
            )
            sys.exit(2)  # exits 2 for bad Args

        return games


flags = Flags()

# flags.sigint = True


MAX_ARROW_KEY_JAM_2 = 2  # takes Key Jams larger than Double Arrow as ⌥-Click's


#
# Run from the Shell, but tell uncaught Exceptions to launch the Py Repl
#


def main() -> None:
    """Run from the Shell, but tell uncaught Exceptions to launch the Py Repl"""

    try:
        try_main()
    except BaseException:  # KeyboardInterrupt  # SystemExit
        excepthook(*sys.exc_info())


def try_main() -> None:
    """Run from the Shell, but tell uncaught Exceptions to launch the Py Repl"""

    naive = dt.datetime.now()

    parser = arg_doc_to_parser(__main__.__doc__ or "")
    ns = shell_args_take_in(args=sys.argv[1:], parser=parser)

    if flags.logging:  # writes into:  tail -F __pycache__/litglass.log
        logging_resume()

    seed = shell_args_take_in_seed(ns.seed, naive=naive)

    with Loopbacker(seed) as lbr:
        logger_info_replay(seed, naive=naive)

        if flags._assert_:
            assert False, "Asserting False before doing much"

        cpg = ColorPickerGame(lbr)
        kcg = KeycapsGame(lbr)
        sqg = SquaresGame(lbr)

        if flags.byteloop:
            lbr.lbr_run_byteloop()
        elif flags.color_picker:
            cpg.cp_run_awhile()
        elif flags.keycaps:
            kcg.kc_run_awhile()
        elif flags.squares:
            sqg.sq_run_awhile()
        else:
            lbr.lbr_run_awhile()


def logging_resume() -> None:
    """Open up a new Logging Session at our .logger"""

    os.makedirs("__pycache__", exist_ok=True)

    logging.basicConfig(
        filename="__pycache__/litglass.log",  # appends, doesn't restart
        level=logging.INFO,  # .INFO and above
        format="%(message)s",  # omits '%(levelname)s:%(name)s:'
    )

    logger.info("")
    logger.info("")
    logger.info("launched")
    logger.info("")

    #
    # default Python .logging
    #
    #       drops many .INFO, .DEBUG, .NOTSET as < 30 .WARNING - # secretly, silently, uncountably
    #       tags many lines at left with like 'INFO:__main__:'
    #


def arg_doc_to_parser(doc: str) -> ArgDocParser:
    """Declare the Positional Arguments & Options"""

    parser = ArgDocParser(doc, add_help=True)

    force_help = "ask fewer questions (like do run slow self-test's)"
    seed_help = "a chosen seed for pseudorandom choices (like to replay a game)"
    egg_help = "a hint of how to behave, such as 'repr' or 'sigint'"

    parser.add_argument("-f", "--force", action="count", help=force_help)
    parser.add_argument("--seed", dest="seed", help=seed_help)
    parser.add_argument("--egg", dest="eggs", metavar="EGG", action="append", help=egg_help)

    return parser


def shell_args_take_in(args: list[str], parser: ArgDocParser) -> argparse.Namespace:
    """Take in the Shell Command-Line Args"""

    ns = parser.parse_args_if(args)  # often prints help & exits zero
    print_usage = parser.parser.print_usage

    ns_keys = list(vars(ns).keys())
    assert ns_keys == ["force", "seed", "eggs"], (ns_keys, ns, args)

    shell_args_take_in_eggs(ns.eggs, print_usage=print_usage)

    games = flags.games
    if games:
        flags.logging = True

    if ns.force:
        _try_lit_glass_()

    return ns


def shell_args_take_in_eggs(eggs: list[str] | None, print_usage: typing.Callable[[], None]) -> None:
    """Take in the Shell --egg=EGG's"""

    hints = eggs or list()

    # Find the Eggs

    dash_dash_eggs = list(vars(flags).keys())

    # Choose some Eggs or none

    corrections = 0
    attr_list = list()
    for hint in hints:
        splits = hint.split(",")
        for split in splits:  # to one egg from several joined across comma separators
            casefold = split.casefold()  # to folded case from unfolded case
            strip = casefold.strip("_")  # to plain word from enclosed in skid marks
            replace = strip.replace("-", "_")  # to skidded from snake case

            matches = list(_ for _ in dash_dash_eggs if _.strip("_").startswith(replace))
            if len(matches) != 1:

                s = sorted(_.strip("_") for _ in dash_dash_eggs)
                if len(matches) > 1:
                    s = sorted(matches)

                print_usage()
                print(f"don't choose {split!r}, do choose from {s}", file=sys.stderr)
                sys.exit(2)  # exits 2 for bad Arg

            copies = list(_ for _ in dash_dash_eggs if _.strip("_") == split)
            if copies != matches:
                corrections += 1

            attr = matches[-1]
            setattr(flags, attr, True)

            attr_list.append(attr)

    if corrections:
        print(f"+ litglass.py --egg={','.join(attr_list)}")


def shell_args_take_in_seed(seed: str | None, naive: dt.datetime) -> str:
    """Take in the last Shell --seed=SEED"""

    strftime = naive.strftime("%Y-%m-%d %H:%M:%S")
    if not seed:
        return strftime

    if re.fullmatch(r"[0-9]+(:[0-9]+)?(:[0-9]+)?", string=seed):

        splits = seed.split(":")

        ints = tuple(int(_) for _ in splits)
        if len(splits) == 1:
            ints = (naive.hour, ints[0], 0)  # --seed=MM
        elif len(splits) == 2:
            ints = (ints[0], ints[1], 0)  # --seed=HH:MM
        else:
            assert len(splits) == 3, (splits, ints)

        t = naive.replace(hour=ints[0], minute=ints[1], second=ints[2])
        strftime = t.strftime("%Y-%m-%d %H:%M:%S")

        return strftime

    return seed


def logger_info_replay(seed: str, naive: dt.datetime) -> None:
    """Log restarting/ starting from --seed=SEED"""

    t = dt.datetime.fromisoformat(seed)
    strftime = t.strftime("%Y-%m-%d %H:%M:%S")

    shargs = list()

    sharg = seed_to_sharg_near_naive(seed, naive=naive)
    shargs.append(sharg)
    shargs.append(f"--seed={strftime!r}")

    d = dict(vars(flags))

    items = sorted(_ for _ in d.items() if _[-1])
    if items[1:]:
        del d["yolo"]
        items = sorted(_ for _ in d.items() if _[-1])

    for option, value in items:
        _option_ = option.replace("_", "-")
        if value:
            shargs.append(f"--egg={_option_}")

    join = " ".join(shargs)
    logger.info(f"python3 litglass.py {join}")


def seed_to_sharg_near_naive(seed: str, naive: dt.datetime) -> str:
    """Quote back one Shell --seed=SEED"""

    t = dt.datetime.fromisoformat(seed)

    if (t.year, t.month, t.day) != (naive.year, naive.month, naive.day):
        sharg = "--seed=" + shlex.quote(seed)
        return sharg

    if t.second:
        sharg = t.strftime("--seed=%H:%M:%S")  # '--seed=19:42:56'
        return sharg

    if t.hour != naive.hour:
        sharg = t.strftime("--seed=%H:%M")  # '--seed=19:42'
        return sharg

    sharg = t.strftime(f"--seed={t.minute}")  # '--seed=9'
    return sharg


def _try_lit_glass_() -> None:
    """Run slow and quick Self-Test's of this Module"""

    _try_chop_()
    _try_key_byte_frame_()
    _try_unicode_source_texts_()


#
# Play for --egg=color-picker
#


class ColorPickerGame:
    """Play for --egg=color-picker"""

    loopbacker: Loopbacker

    game_yx: tuple[int, ...]

    red: int  # 0..5
    green: int  # 0..5
    blue: int  # 0..5

    focus_int: int  # 0, 1, or 2

    def __init__(self, loopbacker: Loopbacker) -> None:

        self.loopbacker = loopbacker

        self.game_yx = tuple()

        self.red = 2
        self.green = 3
        self.blue = 2

        self.focus_int = 1  # 1 is middle

    def cp_run_awhile(self) -> None:
        """Trace Key Releases till ⌃C"""

        lbr = self.loopbacker

        sw = lbr.screen_writer
        kr = lbr.keyboard_reader

        assert ord("C") ^ 0x40 == ord("\003")  # ⌃C

        # Place & draw the Gameboard, scrolling if need be

        (h, w, y, x) = kr.sample_hwyx()
        self.game_yx = (y, x)  # replaces

        self.cp_game_draw()

        # Run till Quit

        quitting = False
        while not quitting:

            # Read Input

            kr.kbhit(timeout=None)
            frames = kr.read_byte_frames()

            # Eval Input and print Output

            self.cp_step_once(frames)

            # Quit at ⌃C

            if b"\003" in frames:
                quitting = True
                break

        sw.print()

    def cp_game_draw(self) -> None:
        """Draw the Gameboard, scrolling if need be"""

        lbr = self.loopbacker
        sw = lbr.screen_writer

        game_yx = self.game_yx

        r = self.red
        g = self.green
        b = self.blue

        focus_int = self.focus_int

        assert CUF_X == "\033[" "{}" "C"
        assert SGR_PS == "\033[" "{}" "m"

        dent = 4 * " "

        # Find the present Color

        ps = 0o20 + (r * 36) + (g * 6) + b

        # Place the board

        (y, x) = game_yx
        sw.write_control(f"\033[{y};{x}H")

        # Draw the Board

        sw.print()
        sw.print()  # twice

        ns = 3 * len("5 ") * " "
        i = focus_int * len("5 ")
        j = i + len("5 ")

        gap = len("rgb color ") * " "
        n = ns[:i] + "↑ " + ns[j:]
        s = ns[:i] + "↓ " + ns[j:]

        sw.print(dent + gap + n + dent)
        sw.print()
        sw.print(dent + f"rgb color {r} {g} {b} is {ps=}" + dent)
        sw.print()
        sw.print(dent + gap + s + dent)

        sw.print()
        sw.print()  # twice

        sw.write_control(f"\033[38;5;{ps}m")

        for _ in range(3):

            sw.write_printable(dent)  # todo7: split controls from printables
            sw.write_printable("█")
            sw.write_control("\033[2C")
            sw.write_printable("██")
            sw.write_control("\033[2C")
            sw.write_printable("███")
            sw.write_control("\033[2C")
            sw.write_printable("██")
            sw.write_control("\033[2C")
            sw.write_printable("█")
            sw.write_printable(dent)
            sw.write_some_controls(["\r", "\n"])

            # sw.print(dent + "███  ██  █  █  ██  ███" + dent)

        sw.write_control("\033[m")

        sw.print()

        # Draw the Chat

        sw.print("Press ⌃C")
        sw.print()

    def cp_step_once(self, frames: tuple[bytes, ...]) -> None:
        """Eval Input and print Output"""

        lbr = self.loopbacker
        kd = lbr.keyboard_decoder

        # Take all plain unmarked classic Arrows here, and nothing else

        note_to_self = True
        for frame in frames:
            kseqs = kd.bytes_to_kseqs_if(frame)
            kseq = kseqs[0] if kseqs else ""
            if kseq not in ("←", "↑", "→", "↓"):
                note_to_self = False
                break

        if note_to_self:
            for frame in frames:
                self.cp_step_one_arrow_once(frame)
            self.cp_game_draw()
            return

        # Else fall back onto the enclosing Loopbacker

        lbr.lbr_step_once(frames)

    def cp_step_one_arrow_once(self, frame: bytes) -> None:
        """Eval one Arrow in the Frame"""

        r = self.red
        g = self.green
        b = self.blue

        focus_int = self.focus_int

        lbr = self.loopbacker
        kd = lbr.keyboard_decoder
        kseqs = kd.bytes_to_kseqs_if(frame)
        kseq = kseqs[0] if kseqs else ""

        assert kseq in ("←", "↑", "→", "↓"), (kseq,)

        if kseq == "←":
            self.focus_int = (focus_int - 1) % 3
        elif kseq == "→":
            self.focus_int = (focus_int + 1) % 3
        else:
            diff = -1 if (kseq == "↓") else 1
            if focus_int == 0:
                self.red = min(max(0, r + diff), 5)
            elif focus_int == 1:
                self.green = min(max(0, g + diff), 5)
            else:
                self.blue = min(max(0, b + diff), 5)


#
# Play for --egg=keycaps
#


class KeycapsGame:
    """Play for --egg=keycaps"""

    loopbacker: Loopbacker
    game_yx: tuple[int, ...]
    shifters: str  # todo: dump/ load Keycaps Games
    scrollables: list[str]  # Rows printed

    MAX_SCROLLABLES_3 = 3

    # Lay out 6 Rows per Keyboard  # todo: measure how high, don't guess

    PlainKeyboard = r"""
        ⎋    F1 F2 F3 F4 F5 F6 F7 F8 F9 F10 F11 F12 <>
        `   1  2  3  4  5  6  7  8  9  0   -   =     ⌫
        ⇥    q  w  e  r  t  y  u  i  o  p   [   ]      \
        ⇪     a  s  d  f  g  h  j  k  l   ;   '        ⏎
        ⇧      z  x  c  v  b  n  m   ,  .  /           ⇧
        Fn  ⌃  ⌥  ⌘   Spacebar    ⌘   ⌥          ← ↑ → ↓
    """

    Unprintables = "⎋ ⇥ ⌫ ⏎ ← ↑ → ↓"
    Unprintables = "".join(Unprintables.split())

    ShiftedKeyboard = r"""
        ⎋    F1 F2 F3 F4 F5 F6 F7 F8 F9 F10 F11 F12 <>
        ~   !  @  #  $  %  ^  &  *  (  )   _   +     ⌫
        ⇥    Q  W  E  R  T  Y  U  I  O  P   {   }      |
        ⇪     A  S  D  F  G  H  J  K  L   :   "        ⏎
        ⇧      Z  X  C  V  B  N  M   <  >  ?           ⇧
        Fn  ⌃  ⌥  ⌘   Spacebar    ⌘   ⌥            ← →
    """

    # . 123456789 123456789 123456789 123456789 12345678

    #

    def __init__(self, loopbacker: Loopbacker) -> None:

        self.loopbacker = loopbacker
        self.game_yx = tuple()
        self.shifters = ""  # none of ⎋ ⌃ ⌥ ⇧
        self.scrollables = list()

    def kc_run_awhile(self) -> None:
        """Trace Key Releases till ⌃C"""

        lbr = self.loopbacker

        sw = lbr.screen_writer
        kr = lbr.keyboard_reader

        assert ord("C") ^ 0x40 == ord("\003")  # ⌃C

        # Draw the Gameboard, scrolling if need be

        game_yx = self.kc_game_draw()
        self.game_yx = game_yx  # replaces

        # Run till Quit

        quitting = False
        while not quitting:

            # Read Input

            kr.kbhit(timeout=None)
            frames = kr.read_byte_frames()

            # Eval Input and print Output

            self.kc_step_once(frames)

            # Quit at ⌃C

            if b"\003" in frames:
                quitting = True
                break

        sw.print()

        # todo9: --egg=keycaps: toggle back out of @@@@@@@@@ or @@ or @
        # todo9: --egg=keycaps: take mouse hits to the Keyboard viewed

    def kc_game_draw(self) -> tuple[int, int]:
        """Draw the Gameboard, scrolling if need be"""

        lbr = self.loopbacker
        kr = lbr.keyboard_reader

        shifters = self.shifters
        assert shifters in ("", "⇧"), (shifters,)

        lbr = self.loopbacker
        sw = lbr.screen_writer

        assert EL_PS == "\033[" "{}" "K"

        # Scroll to make Rows in the South, if need be, like after:  seq 987

        sep = 1  # 1 in the North, 1 in the South, 1 between Board & Hello, 1 between Hello & Chat
        high = sep + 6 + sep + 1 + sep + 3 + sep  # todo: measure how high, don't guess
        wide = 4 + 48 + 4  # todo: measure how wide, don't guess

        n = high - 1  # 1 Southernmost comes free by Convention
        sw.write_some_controls(n * ["\n"])
        sw.write_some_controls(n * ["\033[A"])

        # Place the Gameboard

        (h, w, y, x) = kr.sample_hwyx()

        assert h >= high, (h, high)  # todo: negotiate Height more gracefully
        assert w >= wide, (w, wide)  # todo: negotiate Width more gracefully

        # Form the Rows of the Gameboards

        keyboard = self.ShiftedKeyboard if (shifters == "⇧") else self.PlainKeyboard

        dent = 4 * " "
        dedent = textwrap.dedent(keyboard).strip()
        splitlines = dedent.splitlines()

        # Print each Row

        sw.print()
        for line in splitlines:

            printable = dent + line + dent
            if shifters == "⇧":
                printable = printable.replace("F1 F2 F3 F4", "<> <> <> <>")

            if shifters != "⇧":
                sw.write_printable(printable)
            else:

                splits = printable.split("⇧")
                for index, split in enumerate(splits):
                    if index:
                        sw.write_control("\033[7m")  # ⎋[7M style-reverse
                        sw.write_printable("⇧")
                        sw.write_control("\033[m")  # ⎋[M style-plain
                    sw.write_printable(split)

                # todo: can we more simply code this idea of highlighting the ⇧ Shift Lock?

            sw.write_control("\033[K")

            sw.write_some_controls(["\r", "\n"])

        # Print a Trailer in the far Southeast

        sw.print()
        sw.print("Press ⌃C")
        sw.print()

        # Succeed

        return (y, x)

        # todo: .kc_game_draw well onto larger & smaller Screens

    def kc_step_once(self, frames: tuple[bytes, ...]) -> None:
        """Eval Input and print Output"""

        lbr = self.loopbacker
        sw = lbr.screen_writer

        kr = lbr.keyboard_reader
        kd = lbr.keyboard_decoder

        assert ord("C") ^ 0x40 == ord("\003")  # ⌃C
        assert unicodedata.name("¤").title() == "Currency Sign".title()

        # Eval each Input Frame

        unhit_kseqs: list[object] = list()

        (h, w, y, x) = kr.sample_hwyx()

        for frame in frames:
            kseqs = kd.bytes_to_kseqs_if(frame)

            if not kseqs:
                unhit_kseqs.append([frame, kseqs])
            else:
                self.kc_switch_tab_if(kseqs)
                self.kc_press_keys_if(kseqs, unhit_kseqs)

        sw.write_control(f"\033[{y};{x}H")  # row-column-leap ⎋[⇧H

        if unhit_kseqs:
            if frames != (b"\003",):
                self.kc_print(unhit_kseqs, "Keycap not found", frames)

    def kc_print(self, *args: object) -> None:

        lbr = self.loopbacker  # todo9: layer KeycapsGame over TerminalBoss?
        kr = lbr.keyboard_reader
        sw = lbr.screen_writer

        scrollables = self.scrollables

        assert KeycapsGame.MAX_SCROLLABLES_3 == 3

        printable = " ".join(str(_) for _ in args)

        (y, x) = (kr.row_y, kr.column_x)

        yn = y + 1
        if len(scrollables) >= 3:
            yn = y

            y3 = y - 3
            scrollable = scrollables.pop(0)

            sw.write_control(f"\033[{y3};{x}H")  # row-column-leap ⎋[⇧H
            sw.write_control("\033[M")  # rows-delete ⎋[⇧M

            sw.write_control("\033[H")  # row-column-leap ⎋[⇧H
            sw.write_control("\033[L")  # rows-insert ⎋[⇧L
            sw.write_printable(scrollable)  # todo9: .kc_print wider than screen
            sw.write_control("\033[K")  # row-tail-erase ⎋[⇧K

            sw.write_control("\033[32100H")  # row-column-leap ⎋[⇧H
            sw.write_control("\n")

            sw.write_control(f"\033[{y - 1};{x}H")  # row-column-leap ⎋[⇧H
            sw.write_control("\033[L")  # rows-insert ⎋[⇧L

        sw.write_printable(printable)  # todo9: .kc_print wider than screen
        sw.write_control("\033[K")  # row-tail-erase ⎋[⇧K

        scrollables.append(printable)
        sw.write_control(f"\033[{yn};{x}H")  # row-column-leap ⎋[⇧H

    def kc_switch_tab_if(self, kseqs: tuple[str, ...]) -> None:
        """Switch to next Keyboard View when a Key is struck out there"""

        kseqs_join = "".join(kseqs)
        kseq = kseqs[0]

        lbr = self.loopbacker
        game_yx = self.game_yx
        shifters = self.shifters

        sw = lbr.screen_writer
        (game_y, game_x) = game_yx

        # Don't switch Tabs for ⌃ Control and ⌥ Option Keys  # todo9: --egg=keycaps: do

        if any((_ in kseq) for _ in "⌃⌥"):
            return

        # Change Keyboard Choice, or don't

        kseqs_shifters = shifters

        if not shifters:

            if "⇧" in kseq:
                kseqs_shifters = "⇧"

        else:

            assert shifters == "⇧", (shifters,)
            if kseq in string.ascii_uppercase:
                kseqs_shifters = ""
            elif kseq in ("↑", "↓"):  # could be ⇧↑ ⇧↓
                assert "⇧" in kseqs_join, (kseqs_join, kseq)
            elif "⇧" not in kseqs_join:
                kseqs_shifters = ""

        # Switch Tabs when Keyboard Choice changes

        if kseqs_shifters == shifters:
            return

        shifters = kseqs_shifters
        self.shifters = shifters

        sw.write_control(f"\033[{game_y};{game_x}H")  # row-column-leap ⎋[⇧H
        self.kc_game_draw()

    def kc_press_keys_if(self, kseqs: tuple[str, ...], unhit_kseqs: list[object]) -> None:
        """Wipe out each Keycap when pressed"""

        assert kseqs, (kseqs,)

        lbr = self.loopbacker
        game_yx = self.game_yx
        shifters = self.shifters

        sw = lbr.screen_writer
        (game_y, game_x) = game_yx

        # Form the Rows of the Gameboards

        keyboard = self.ShiftedKeyboard if (shifters == "⇧") else self.PlainKeyboard

        dent = 4 * " "
        dedent = textwrap.dedent(keyboard).strip()
        splitlines = dedent.splitlines()

        removesuffix = str_removesuffix(dedent, suffix=splitlines[-1])

        # Visit each Keycap

        kseq = kseqs[0]

        cap = kseq
        if kseq == "␢":
            cap = "Spacebar"
        elif flags.sigint and (kseq == "⌃J"):
            cap = "⏎"
        elif kseq in tuple(string.ascii_uppercase):
            cap = kseq.lower()
        elif kseq.startswith("⇧"):
            cap = str_removeprefix(kseq, prefix="⇧")

        # Wipe out each Keycap when pressed

        cap_is_esc = cap == "⎋"
        cap_is_fn = cap.startswith("F") and str_removeprefix(cap, prefix="F")

        suffix_kseqs = ("␢", "←", "↑", "→", "↓", "⇧←", "⇧→")
        hittable = dedent if kseq in suffix_kseqs else removesuffix
        find = -1 if (cap_is_esc or cap_is_fn) else len(splitlines[0])

        hits = 0
        while True:

            start = find + 1
            find = hittable.find(cap, start)
            if find < 0:
                break

            hits += 1

            found_lines = dedent[: find + 1].splitlines()
            assert found_lines, (found_lines, find, cap)

            # Leap to this found Keycap

            y = game_y + len(found_lines)
            x = game_x + len(dent) + len(found_lines[-1]) - 1

            sw.write_control(f"\033[{y};{x}H")  # row-column-leap ⎋[⇧H

            # Wipe out this Keycap

            width = len(cap)  # width 1 except for len('Spacebar')

            sw.write_control("\033[1m")  # ⎋[1M style-bold
            sw.write_printable(width * "¤")
            sw.write_control("\033[m")  # ⎋[M style-plain

            # Wipe out only "F1" and not the "F1" in "F12", etc

            if cap_is_fn:
                break

        if not hits:
            unhit_kseqs.append([cap, kseqs])

    # todo9: --egg=keycaps: restart in each Keyboard viewed
    # todo9: --egg=keycaps: save/ load progress in each Keyboard viewed
    # todo9: --egg=keycaps: celebrate near to winning, and celebrate winning


#
# Play for --egg=squares
#


class SquaresGame:
    """Play for --egg=squares"""

    loopbacker: Loopbacker

    by_y_by_x: dict[int, dict[int, str]]
    y_high: int  # H W positive after initial zero
    x_wide: int

    game_yx: tuple[int, ...]

    strikes: int

    Squares = "🟥 🟨 🟩 🟦 🟪"
    Squares = "".join(Squares.split())

    def __init__(self, loopbacker: Loopbacker) -> None:

        self.loopbacker = loopbacker
        self.by_y_by_x = dict()
        self.y_high = 0
        self.x_wide = 0
        self.game_yx = tuple()
        self.strikes = 0

    def sq_run_awhile(self) -> None:
        """Run till Quit"""

        lbr = self.loopbacker

        sw = lbr.screen_writer
        kr = lbr.keyboard_reader

        assert ord("C") ^ 0x40 == ord("\003")  # ⌃C

        # Draw the Gameboard

        (h, w, y, x) = kr.sample_hwyx()
        self.game_yx = (y, x)  # replaces

        self.sq_game_form()
        self.sq_game_draw()

        # Run till Quit

        while True:
            logger.info("")
            logger.info("...")

            # Read Input

            kr.kbhit(timeout=None)
            frames = kr.read_byte_frames()

            # Eval Input and print Output

            self.sq_steps_because_frames(frames)

            # Quit at can't move

            if not self.sq_find_moves():
                break

            # Quit at ⌃C

            if b"\003" in frames:
                break

        sw.write_control("\033[2A")
        sw.write_printable("🏆")
        sw.write_control("\033[K")
        sw.write_some_controls(["\r", "\n"])

        sw.print()
        sw.print()  # twice

        # todo4: bias the Row from above to reward Column Shuffle of middle
        # todo4: bias the Column from above to reward Row Shuffle of middle

        # todo4: ⇥ autoruns Shuffles till one is about to work, then stops there

        # todo4: seq 99 && @ --seed='2025-12-08 08:01:46' --egg=squares

    def sq_game_form(self) -> None:
        """Fill the Board with Tiles"""

        lbr = self.loopbacker
        r = lbr.random_random

        by_y_by_x = self.by_y_by_x

        squares = SquaresGame.Squares

        #

        h = len(squares)
        w = len(squares)

        self.y_high = h
        self.x_wide = w

        #

        for y in range(h):

            by_x: dict[int, str] = dict()
            by_y_by_x[y] = by_x

            for x in range(w):
                t = r.choice(squares)
                by_x[x] = t

    def sq_game_draw(self) -> None:
        """Draw the Gameboard, scrolling if need be"""

        # Enter

        by_y_by_x = self.by_y_by_x
        game_yx = self.game_yx

        lbr = self.loopbacker
        sw = lbr.screen_writer

        squares = SquaresGame.Squares
        dent = 4 * " "

        # Place the Gameboard

        (y, x) = game_yx
        sw.write_control(f"\033[{y};{x}H")  # row-column-leap ⎋[⇧H

        # Draw the Northern Border

        sw.print()
        sw.print()  # twice

        # Draw the Board itself, between its West and East Borders

        h = len(squares)
        for y in range(h):
            by_x = by_y_by_x[y]
            y_text = "".join(by_x.values())
            sw.write_printable(dent + y_text + dent)
            sw.write_some_controls(["\r", "\n"])

        # Draw the Southern Decor and the Southern Border

        sw.print(dent + "  ↓    ↓  " + dent)

        sw.print()
        sw.print()  # twice

        # Draw the Chat

        sw.print("Press ⌃C")  # todo5: overwrite with "Press Spacebar"
        sw.print()

        # todo6: find the ⌥-click on the board

        # todo7: rotate gravity to match arrow, and drag perpendicular to gravity

    def sq_steps_because_frames(self, frames: tuple[bytes, ...]) -> None:
        """Eval Frames of Input and print Output"""

        boxes = tuple(BytesBox(_) for _ in frames)
        for box in boxes:
            self.sq_step_because_box(box)

    def sq_step_because_box(self, box: BytesBox) -> bool:
        """Eval 1 Box of Input and print Output"""

        f = KeyByteFrame(box.data)
        (marks, ints) = f.to_csi_marks_ints_if()

        # Take some and not all of Tap, Mouse Release/ Press, Key Release

        if box.text == " ":  # takes ␢ Spacebar
            pass
        elif marks == b"<M":  # takes Mouse Press
            return True  # and discards it
        elif marks == b"<m":  # takes Mouse Release
            pass
        else:
            return False

        # Find and draw Collisions

        east_bars = self.sq_find_east_bars()
        south_poles = self.sq_find_south_poles()

        if east_bars or south_poles:
            self.sq_empty_east_bars(east_bars)
            self.sq_empty_south_poles(south_poles)
            self.strikes = 0
            self.sq_game_draw()
            return True

        # Across the South, fall from the North

        falls = self.sq_fall_south_into_empty_cells()

        if falls:
            self.strikes = 0
            self.sq_game_draw()
            return True

            # todo5: move all the 3 square arrows where they point
            # todo6: game trophies of first finding each kind of move

        # Shuffle Columns or Rows

        self.strikes += 1
        if self.strikes <= 3:
            self.sq_rows_shuffle()  # todo7: only while gravity pulls South
        else:
            self.strikes = 0
            self.sq_columns_shuffle()

        self.sq_game_draw()

        return True

    def sq_find_east_bars(self) -> list[tuple[int, int, int]]:
        """Search each Row to find >= 3 Tiles together"""

        by_y_by_x = self.by_y_by_x
        y_high = self.y_high
        x_wide = self.x_wide

        east_bars = list()

        for y in range(0, y_high):
            for x in range(0, x_wide):
                by_x = by_y_by_x[y]
                t = by_x[x]

                if t == "⬜":
                    continue

                east = "".join(by_x[_] for _ in range(x, x_wide))
                wide = len(east) - len(east.lstrip(t))
                if wide >= 3:
                    east_bar = (y, x, wide)
                    east_bars.append(east_bar)

                    logger.info(str([y, x, wide, (wide * t), "East Bar"]))

                    assert x_wide <= 5, (x_wide, wide, east_bar)
                    break

        return east_bars

    def sq_find_south_poles(self) -> list[tuple[int, int, int]]:
        """Search each Column to find >= 3 Tiles together"""

        by_y_by_x = self.by_y_by_x
        y_high = self.y_high
        x_wide = self.x_wide

        south_poles = list()

        for x in range(0, x_wide):
            for y in range(0, y_high):
                by_x = by_y_by_x[y]
                t = by_x[x]

                if t == "⬜":
                    continue

                south = "".join(by_y_by_x[_][x] for _ in range(y, y_high))
                high = len(south) - len(south.lstrip(t))
                if high >= 3:
                    south_pole = (y, x, high)
                    south_poles.append(south_pole)

                    logger.info(str([y, x, high, (high * t), "South Pole"]))

                    assert y_high <= 5, (y_high, high, south_pole)
                    break

        return south_poles

    def sq_empty_east_bars(self, east_bars: list[tuple[int, int, int]]) -> None:
        """Erase each Cell of each East Bar"""

        by_y_by_x = self.by_y_by_x

        for east_bar in east_bars:
            (y, x, wide) = east_bar
            by_x = by_y_by_x[y]
            for xw in range(x, x + wide):

                by_x[xw] = "⬜"  # todo5: Darkmode

    def sq_empty_south_poles(self, south_poles: list[tuple[int, int, int]]) -> None:
        """Erase each Cell of each South Pole"""

        by_y_by_x = self.by_y_by_x

        for south_pole in south_poles:
            (y, x, high) = south_pole
            for ys in range(y, y + high):
                by_x = by_y_by_x[ys]

                by_x[x] = "⬜"  # todo5: Darkmode

    def sq_fall_south_into_empty_cells(self) -> int:
        """Across the South, fall from the North"""

        lbr = self.loopbacker
        r = lbr.random_random

        by_y_by_x = self.by_y_by_x
        y_high = self.y_high
        x_wide = self.x_wide

        squares = SquaresGame.Squares

        # Walk from South to North to find each Empty Cell

        falls_by_y_by_x: dict[int, dict[int, str]] = dict()

        falls = 0
        for ys in reversed(range(y_high)):
            yn = ys - 1
            yn_by_x = dict() if (yn < 0) else by_y_by_x[yn]

            # Walk always from West to East, even though East to West would work just as well

            ys_falls: dict[int, str] = dict()
            falls_by_y_by_x[ys] = ys_falls

            for x in range(0, x_wide):
                ys_by_x = by_y_by_x[ys]

                ts = ys_by_x[x]
                if ts != "⬜":
                    ys_falls[x] = "⬜"
                    continue

                # Pull from Above, else from the Void

                tn = r.choice(squares) if (yn < 0) else yn_by_x[x]
                ys_falls[x] = tn

                ys_by_x[x] = tn
                yn_by_x[x] = "⬜"

                falls += 1

        # Log the Falls, but from North to South

        for ys in range(y_high):
            ys_falls = falls_by_y_by_x[ys]
            ys_text = "".join(ys_falls.values())

            if "⬜" in ys_text:
                if ys_text.rstrip("⬜"):
                    logger.info(str([ys, ys_text, "Falls"]))

        # Succeed, or fail

        return falls

    def sq_columns_shuffle(self) -> None:
        """Shuffle the Columns"""

        lbr = self.loopbacker
        r = lbr.random_random

        by_y_by_x = self.by_y_by_x
        y_high = self.y_high
        x_wide = self.x_wide

        x_list = list(range(x_wide))

        t_list = list()
        for x in x_list:
            for y in range(y_high):
                by_x = by_y_by_x[y]
                t = by_x[x]
                t_list.append(t)

        x2_list = list(x_list)
        while x2_list == x_list:
            logger.info("columns_shuffle")
            r.shuffle(x2_list)

        for x2 in x2_list:
            for y in range(y_high):
                by_x2 = by_y_by_x[y]
                by_x2[x2] = t_list.pop(0)

    def sq_rows_shuffle(self) -> None:
        """Shuffle the Rows"""

        lbr = self.loopbacker
        r = lbr.random_random

        by_y_by_x = self.by_y_by_x
        y_high = self.y_high
        x_wide = self.x_wide

        y_list = list(range(y_high))

        t_list = list()
        for y in y_list:
            for x in range(x_wide):
                by_x = by_y_by_x[y]
                t = by_x[x]
                t_list.append(t)

        y2_list = list(y_list)
        while y2_list == y_list:
            logger.info("rows_shuffle")
            r.shuffle(y2_list)

        for y2 in y2_list:
            for x in range(x_wide):
                by2_x = by_y_by_x[y2]
                by2_x[x] = t_list.pop(0)

    def sq_find_moves(self) -> bool:
        """Say if progress is possible"""

        by_y_by_x = self.by_y_by_x
        y_high = self.y_high
        x_wide = self.x_wide

        # Search all Column Shuffles to pick out >= 3 in a Row

        for y in range(y_high):
            by_x = by_y_by_x[y]
            y_cells = list(by_x[x] for x in range(x_wide))
            count_by_cell = collections.Counter(y_cells)

            hope = max(count_by_cell.values())
            if hope >= 3:
                return True

        # Search all Row Shuffles to pick out >= 3 in a Column

        for x in range(x_wide):
            x_cells = list(by_y_by_x[y][x] for y in range(y_high))
            count_by_cell = collections.Counter(x_cells)

            hope = max(count_by_cell.values())
            if hope >= 3:
                return True

        # Search all Cells to pick out a Fall of Cells in progress

        for y in range(y_high):
            for x in range(x_wide):
                cell = by_y_by_x[y][x]
                if cell == "⬜":
                    return True

        # Else give up

        return False

    # todo: more Squares, less Squares, colorable
    # todo: colorable single-wide █ ██ Full-Block U+2588
    # todo: colorable double-wide ⬤ Black-Large-Circle U+2B24


#
# Loop Input back to Output, to Screen from Touch/ Mouse/ Key
#


class Loopbacker:
    """Loop Input back to Output, to Screen from Touch/ Mouse/ Key"""

    terminal_boss: TerminalBoss
    screen_writer: ScreenWriter
    keyboard_reader: KeyboardReader

    keyboard_decoder: KeyboardDecoder
    screen_change_order: ScreenChangeOrder

    seed: str
    random_random: random.Random

    #
    # Init, enter, and exit
    #

    def __init__(self, seed: str) -> None:

        assert DSR5 == "\033[" "5n"

        #

        tb = TerminalBoss()
        kr = tb.keyboard_reader
        sw = tb.screen_writer

        kd = KeyboardDecoder()

        dsr5 = BytesBox(b"\033[5n")
        sco = ScreenChangeOrder()
        sco.grow_order(dsr5, yx=(kr.row_y, kr.column_x))

        r = random.Random(seed)

        #

        self.terminal_boss = tb
        self.screen_writer = sw
        self.keyboard_reader = kr

        self.keyboard_decoder = kd
        self.screen_change_order = sco
        self.seed = seed
        self.random_random = r

        # todo: limit fanout of pretending ⎋[5N came as last Input before Launch

    def __enter__(self) -> Loopbacker:

        tb = self.terminal_boss
        sw = self.screen_writer
        kr = self.keyboard_reader

        assert SM_PS and SU_Y

        tb.__enter__()

        if flags.scrollback or ((not flags.enter) and (not flags._exit_)):

            (h, w, y, x) = kr.sample_hwyx()

            if flags.games:
                if (h * w) < (30 * 30):
                    flags.mobile = True

            if flags.games:
                luminance = 0.5
                # luminance = kr.sample_luminance()
                if (luminance < -0.75) or (luminance > 0.75):
                    flags.lightmode = True
                elif (luminance >= -0.25) and (luminance <= 0.25):
                    flags.darkmode = True

            if flags.scrollback:
                if y > 1:
                    sw.write_control(f"\033[{y - 1}S")  # ⎋[⇧S south-rows-insert
                if (not flags.enter) and (not flags._exit_):
                    sw.write_control("\033[?1049h")  # alt-screen ⎋[⇧?1049H

        if flags.mobile:
            if not flags.enter:
                sw.write_control("\033[?1006;1000h")  # sgr-mouse-take

            # sw.write_control("\033[?2004h")  # paste-wrap  # todo8:

        return self

    def __exit__(self, *args: object) -> None:

        tb = self.terminal_boss
        sw = self.screen_writer
        kr = self.keyboard_reader

        assert SM_PS and RM_PS and SGR_PS and DECSCUSR_PS

        if not flags.enter:
            if flags.mobile:
                sw.write_control("\033[?1006;1000l")  # mouse-give

        # if not flags.enter:  # todo8:

        #     sw.write_control("\033[?2004l")  # paste-unwrap ⎋[?2004L

        if not flags._exit_:

            sw.write_control("\033[m")  # plain ⎋[M vs other ⎋[ M
            sw.write_control("\033[ q")  # cursor-unstyled ⎋[␢Q vs other ⎋[ Q
            sw.write_control("\033[4l")  # replacing ⎋[4L vs ⎋[4H
            sw.write_control("\033[?25h")  # cursor-show ⎋[⇧?25H vs ⎋[?25L

            (h, w, y, x) = kr.sample_hwyx()
            sw.write_control("\033[?1049l")  # main-screen ⎋[⇧?1049L vs ⎋[⇧?1049H
            sw.write_control(f"\033[{y};{x}H")  # row-column-leap ⎋[⇧H

        tb.__exit__(*args)

    #
    # Run awhile
    #

    def lbr_run_byteloop(self) -> None:
        """Loop back without adding latencies"""

        tb = self.terminal_boss
        sw = self.screen_writer

        assert ord("C") ^ 0x40 == ord("\003")  # ⌃C

        sw.write_printable("Press ⌃C")
        while True:
            data = tb.read_one_byte()
            tb.write_some_bytes(data)
            if data == b"\r":  # rounds up ⌘V of \r to \r\n
                tb.write_some_bytes(b"\n")
            if data == b"\003":
                break

    def lbr_run_awhile(self) -> None:
        """Loop Input back to Output, to Screen from Touch/ Mouse/ Key"""

        sw = self.screen_writer
        kr = self.keyboard_reader

        assert ord("C") ^ 0x40 == ord("\003")  # ⌃C

        assert CUU_Y == "\033[" "{}" "A"
        assert CUP_Y_X == "\033[" "{};{}H"
        assert ED_PS == "\033[" "{}" "J"
        assert _MAX_PN_32100_ == 32100

        # Draw the Gameboard

        if flags._repr_:
            sw.print("Press ⌃C")
            sw.write_some_controls(2 * ["\t"])
        else:
            sw.write_printable("Press ⌃C ")

        # Run till Quit

        quitting = False
        while not quitting:

            # Read Input

            t0 = time.time()

            kr.kbhit(timeout=None)
            frames = kr.read_byte_frames()

            t1 = time.time()
            t1t0 = t1 - t0

            # Eval Input and print Output

            logger.info("")
            logger.info(f"{frames=}")
            if flags._repr_:
                self.lbr_print_repr_frame_per_row(frames, t1t0=t1t0)
            else:
                self.lbr_step_once(frames)

            # Quit at ⌃C

            if b"\003" in frames:
                quitting = True
                break

        if not flags._exit_:
            sw.write_control("\033[32100H")  # cursor-unstyled ⎋[32100⇧H
            sw.write_control("\033[2A")  # 2 ↑ ⎋[2⇧A
            sw.write_control("\033[J")  # after-erase ⎋[⇧J  # simpler than ⎋[0⇧J
            sw.print("bye for now")

    def lbr_step_once(self, frames: tuple[bytes, ...]) -> None:
        """Collect Input Frames over time as a Screen Change Order"""

        sw = self.screen_writer
        kr = self.keyboard_reader
        sco = self.screen_change_order

        # Take in each Frame

        boxes = tuple(BytesBox(_) for _ in frames)

        clearing_screen_order = False
        for box_index, box in enumerate(boxes):
            data = box.data
            text = box.text

            assert data, (data,)

            if not text:
                self.lbr_write_frame_echo(data)
                continue

            (y, x) = (kr.row_y, kr.column_x)

            # Take in the Frame by itself, while Order incomplete

            sco.grow_order(box, yx=(kr.row_y, kr.column_x))

            if not (sco.forceful_order or sco.intricate_order):

                if flags.echoes:
                    self.lbr_write_frame_echo(data)
                    sw.write_control(f"\033[{y};{x}H")

                self.lbr_box_step_once(box, intricate_order=False)

                continue

                # todo9: Delete the repeat-count when not-echo'ing the Key Byte Frame

            compilation = sco.compile_order()
            (row_y, column_x, strong, factor, sco_box) = compilation

            if not sco_box:
                self.lbr_write_frame_echo(data)
                break

            # Run this Order as completed by this Frame

            self.lbr_sco_step_once(data, compilation=compilation)

            sco.yx = tuple()
            f = sco.key_byte_frame
            f.clear_frame()  # reruns Factor for remaining Frames

            if boxes[box_index:][1:]:
                _ = kr.sample_hwyx()

            clearing_screen_order = True

        if clearing_screen_order:
            sco.clear_order()

    def lbr_sco_step_once(
        self, data: bytes, compilation: tuple[int, int, int, int, BytesBox]
    ) -> None:
        """Run this Order as completed by this Frame"""

        (row_y, column_x, strong, factor, sco_box) = compilation
        sco_data = sco_box.data
        sco_text = sco_box.text

        sw = self.screen_writer
        kr = self.keyboard_reader
        sco = self.screen_change_order

        assert sco.forceful_order or sco.intricate_order, (sco,)

        # Write the Frame and grow the Order

        if sco_box.nearly_printable and (not strong):

            sw.write_printable(sco_text)

        elif factor < -1:  # echoes without writing

            self.lbr_write_frame_echo(data)

        elif factor == -1:  # echoes and greatly details

            frames = tuple([sco_data])

            t1 = time.time()
            t1t0 = t1 - sco.time_time

            self.lbr_write_frame_echo(data)

            sw.write_printable(" ")
            self.lbr_print_repr_frame_per_row(frames, t1t0=t1t0)

        elif factor == 0:  # echoes and leaps and writes

            self.lbr_write_frame_echo("⌃m".encode() if (data == b"\r") else data)  # ⌃M

            sw.write_control(f"\033[{row_y};{column_x}H")
            kr.row_y = row_y
            kr.column_x = column_x

            if sco_box.nearly_printable:
                sw.write_printable(sco_text)
            else:
                sw.write_control(sco_text)

        else:  # echoes and cooks and leaps and writes

            if sco.intricate_order or flags.echoes:
                self.lbr_write_frame_echo(data)

            sw.write_control(f"\033[{row_y};{column_x}H")
            kr.row_y = row_y
            kr.column_x = column_x

            for _ in range(factor):
                self.lbr_box_step_once(sco_box, intricate_order=sco.intricate_order)

    #
    # Loop back a single Frame of decodable Input Bytes,
    # having arrived all together or else slowly intricately built as a Screen Change Order
    #

    def lbr_box_step_once(self, box: BytesBox, intricate_order: bool) -> None:
        """Loop back the Decode of the Frame, else echo it"""

        data = box.data
        text = box.text

        sw = self.screen_writer

        kd = self.keyboard_decoder
        echo = kd.frame_to_echo(data)
        assert echo.isprintable(), (echo,)

        assert _NorthArrow_ and _SouthArrow_ and _EastArrow_ and _WestArrow_
        assert _NorthwestArrow_ and _NortheastArrow_ and _SoutheastArrow_ and _SouthwestArrow_

        # If Frame is Printable

        if box.nearly_printable:
            sw.write_printable(text)
            return

        # If Frame has Keycaps

        if self.lbr_decode_kseqs_step_once_if(box, intricate_order=intricate_order):
            return

        # Loop back a few Esc Byte Sequences unchanged

        loopable_controls = ("\0337", "\0338", "\033D", "\033E", "\033M")
        if text in loopable_controls:
            sw.write_control(text)
            return

        # Block the heavy hammer of ⎋C and the complex hammer of ⎋L

        if text == "\033c":  # ⎋C to ⎋[⇧H ⎋[2⇧J ⎋[3⇧J screen/ scrollback erase
            sw.write_some_controls(["\033[H", "\033[2J", "\033[3J"])
            return

            # does work:  macOS ⌘K
            # does work:  seq 987 && printf '\e[H''\e[2J''\e[3J'
            # not so much:  seq 987 && printf '\e[3J''\e[H''\e[2J'
            # lots of Shell 'clear' get this wrong, including Oct/2024 Sequoia macOS 15

        if text == "\033l":  # ⎋L terminal-confuse to ⎋[⇧H row-column-leap
            sw.write_control("\033[H")
            return

        # Leap the Cursor to the ⌥-Click  # todo9: also ⎋[⇧M Click Releases

        f = KeyByteFrame(data)
        (marks, ints) = f.to_csi_marks_ints_if()

        if (marks == b"<m") and (len(ints) == 3):
            (b, x, y) = ints  # todo: bounds check on Click Release
            sw.write_control(f"\033[{y};{x}H")
            sw.write_printable("@")  # '@' to make ⌥-Click's visible
            return

        # Leap the Cursor to the 8-way ↖↗↘↙ Compass Arrows

        controls_by_marks = {
            "↖".encode(): ["\033[A", "\033[D", "\033[D"],
            "↗".encode(): ["\033[A", "\033[C", "\033[C"],
            "↘".encode(): ["\033[B", "\033[C", "\033[C"],
            "↙".encode(): ["\033[B", "\033[D", "\033[D"],
        }

        if marks in controls_by_marks.keys():
            controls = controls_by_marks[marks]
            sw.write_some_controls(controls)
            return

        # Show a brief loud Repr of any Unknown Encode arriving as Input

        bouncing = not intricate_order

        if flags.clickruns:
            if marks in (b"A", b"B", b"C", b"D"):
                if len(ints) == 1:

                    bouncing = False

                    # todo9: solve .clickruns Frames as fully as not, across Wrapped Lines

        if bouncing:

            if echo != "⌃C":  # presumes ⌃C don't want this Echo here
                sw.write_printable("<" + echo + ">")  # <⌃Y>

            return

        # Loop back well-known Csi & Osc Byte Sequences

        if self.lbr_csi_osc_step_once_if(box):
            return

        # Else echo vertically down southward

        self.lbr_write_echo_southward(echo)

    def lbr_write_echo_southward(self, echo: str) -> None:

        sw = self.screen_writer
        kr = self.keyboard_reader

        for e in echo:

            sw.write_printable(e)
            if kr.row_y >= kr.y_high:
                sw.write_control("\n")

            kr.row_y = min(kr.y_high, kr.row_y + 1)
            sw.write_control(f"\033[{kr.row_y};{kr.column_x}H")

    def lbr_decode_kseqs_step_once_if(self, box: BytesBox, intricate_order: bool) -> bool:
        """Loop back the Keycaps of the Frame, else return False"""

        data = box.data
        text = box.text

        kr = self.keyboard_reader
        kd = self.keyboard_decoder

        kseqs = kd.bytes_to_kseqs_if(data)
        if not kseqs:
            return False

        kseq = kseqs[0]  # only search for the first Keycap

        sw = self.screen_writer
        kd = self.keyboard_decoder

        # Echo ⎋ Esc and ⎋⎋ Esc Esc as such

        if kseq in ("⎋", "⎋⎋"):
            sw.write_printable(kseq)
            return True

        # Loop back a few Key Chord Byte Sequences unchanged

        loopable_kseqs = ("⌃G", "⌃H", "⇥", "⌃K", "⇧⇥")
        if kseq in loopable_kseqs:
            sw.write_control(text)  # ⌃I for ⇥, ⎋[⇧Z for ⇧⇥, etc
            return True

        # Loop back ⌃J encoding of ⏎ Return as ⌃J ⎋[ ⇧G column-leap

        if kseq == "⌃J":
            if not flags.sigint:
                sw.write_control(text)  # ⌃J for ⌃J
            else:
                x = kr.column_x
                sw.write_some_controls(["\n", f"\033[{x}G"])  # "\n" lands as "\r\n"
            return True

        # Loop back ⌃M encoding of ⏎ Return as CR LF

        if kseq == "⏎":
            sw.write_some_controls(["\r", "\n"])
            return True

        # Loop back ⌃⇧? ⌫ as Delete

        if kseq == "⌫":
            sw.write_some_controls(["\033[D", "\033[P"])
            return True

        # Loop back as Arrow, no matter the shifting Keys

        join = str(kseqs)
        if not intricate_order:

            arrows = tuple(_ for _ in ("←", "↑", "→", "↓") if _ in join)
            if len(arrows) == 1:
                arrow = arrows[-1]
                assert arrow in ("←", "↑", "→", "↓"), (arrow, join)

                arrow_control = kd.decode_by_kseq[arrow]
                sw.write_control(arrow_control)
                if (arrow in ("←", "→")) and flags.echoes:
                    sw.write_control(arrow_control)

                return True

        # Else don't loop back here

        return False

    def lbr_csi_osc_step_once_if(self, box: BytesBox) -> bool:
        """Loop back well-known Csi & Osc Byte Sequences"""

        control = box.text
        f = KeyByteFrame(box.data)

        head = bytes(f.head)
        neck = bytes(f.neck)
        backtail = bytes(f.backtail)

        sw = self.screen_writer

        assert CSI == "\033["
        assert OSC == "\033]"

        # Loop back well-known Csi Byte Sequences

        if head == b"\033[M" and (not backtail):
            assert not neck, (neck, head, backtail, f)
            sw.write_control(control)
            return True

        if head == b"\033[":
            if len(backtail) == 1:

                if backtail in b"@" b"ABCDEFGHIJKLM" b"P" b"ST" b"Z" b"d" b"f" b"h" b"lm" b"q":
                    sw.write_control(control)  # no limits on .marks and .ints
                    return True

                if backtail in b"nt":
                    sw.write_control(control)  # no limits on .marks and .ints
                    return True

            # Emulate Columns Insert/ Delete by Csi

            if self._screen_columns_insert_delete_if_(f):
                return True

            # todo: Accept only the Csi understood by our Class ScreenWriter

        # Loop back well-known Osc Byte Sequences

        osc_necks = [b"", b"10;?", b"11;?", b"12;?", b"12", b"112"]
        if flags.google:
            osc_necks.remove(b"12")  # crashes 6/Dec/2025 Google Cloud Terminals

        if head == b"\033]":
            if backtail in (b"\007", b"\033\134"):
                if neck in osc_necks:  # .neck == f"{Ps};{Pt}".encode()
                    sw.write_control(control)
                    return True

                    # Osc 10;⇧? sends for Color ⎋]10;RGB⇧:{r}/{g}/{b}⌃G
                    # Osc 11;⇧? sends for Backlight ⎋]11;RGB⇧:{r}/{g}/{b}⌃G
                    # Osc 12;⇧? and Osc 112;⇧? change and revert Cursor Color

                    # Osc without Ps without Pt does almost no harm

            # todo: Accept only the Osc understood by our Class ScreenWriter

        return False

    def _screen_columns_insert_delete_if_(self, f: KeyByteFrame) -> bool:
        """Emulate Columns Insert/ Delete by Csi"""

        sw = self.screen_writer

        kr = self.keyboard_reader
        row_y = kr.row_y
        y_high = kr.y_high

        #

        (marks, ints) = f.to_csi_marks_ints_if()
        if marks not in (b"'}", b"'~"):
            return False

        if len(ints) > 1:
            return False

        #

        deleting = [b"'}", b"'~"].index(marks)

        pn_int = ints[-1] if ints else PN1
        pn = pn_int  # accepts pn = 0

        #

        assert ICH_X == "\033[" "{}" "@"
        assert VPA_Y == "\033[" "{}" "d"
        assert DECDC_X == "\033[" "{}" "'~"
        assert DECIC_X == "\033[" "{}" "'}}"  # speaking of ⎋[ '}

        #

        for y in range(Y1, y_high + 1):
            sw.write_control(f"\033[{y}d")
            sw.write_control(f"\033[{pn}P" if deleting else f"\033[{pn}@")
        sw.write_control(f"\033[{row_y}d")

        return True

        # macOS Terminal & macOS iTerm2 & Google Cloud Shell lack ⎋['⇧} cols-insert

    #
    # Form Repr's of Frames of Input Bytes
    #

    def lbr_write_frame_echo(self, frame: bytes) -> None:
        """Show a brief Repr of one Frame"""

        sw = self.screen_writer
        kd = self.keyboard_decoder

        echo = kd.frame_to_echo(frame)
        sw.write_printable(echo)

    def lbr_print_repr_frame_per_row(self, frames: tuple[bytes, ...], t1t0: float) -> None:
        """Print the Repr of each Frame, but mark the Frames as framed together"""

        sw = self.screen_writer
        kr = self.keyboard_reader

        assert CUP_Y_X == "\033[" "{};{}H"

        frame_t1t0 = t1t0
        (y, x) = (kr.row_y, kr.column_x)

        for frame_index in range(len(frames)):

            self.lbr_print_one_repr_frame(frames, frame_index=frame_index, t1t0=frame_t1t0)

            frame_t1t0 = 0e0
            y += 1  # todo: 'row_y > y_high' happens here  # todo: update Y X shadow

            sw.write_control("\n")
            sw.write_control(f"\033[{y};{x}H")

    def lbr_print_one_repr_frame(
        self, frames: tuple[bytes, ...], frame_index: int, t1t0: float
    ) -> None:
        """Write the Repr of one Frame, but mark the Frames as framed together"""

        frame = frames[frame_index]

        box = BytesBox(frame)
        text = box.text

        sw = self.screen_writer
        kd = self.keyboard_decoder

        # Choose which Keycaps to put out front

        kseqs = kd.bytes_to_kseqs_if(frame)

        alt_kseqs = kseqs
        if kseqs:
            if (frame == b"`") and frames[1:]:
                alt_kseqs = tuple(reversed(kseqs))  # ('⌥⇧`', '`') 0 `

        # Choose which details to print

        printables: list[object] = list()

        if alt_kseqs:
            printables.append(alt_kseqs[0])

        if not box.nearly_printable:
            printables.append(repr(frame))
        else:
            if text == " ":
                printables.append(repr(text))
            else:
                printables.append(text)

        printables.append(chop(1000 * t1t0))

        if alt_kseqs[1:]:
            printables.append(alt_kseqs[1:])

        if frames[1:]:
            printables.append(frame_index)

        # Print the chosen details

        join = " ".join(str(_) for _ in printables)
        sw.write_printable(join)

        self.t = time.time()

        #
        # Quadruple Key Jam
        #
        #   → b'\x1b[C' 192 ('⌥⇧→',) 0
        #   ← b'\x1b[D' 0 ('⌥⇧←',) 1
        #   ↓ b'\x1b[B' 0 ('⌥↓', '⇧↓', '⌥⇧↓') 2
        #   ↑ b'\x1b[A' 0 ('⌥↑', '⇧↑', '⌥⇧↑') 3
        #


@dataclasses.dataclass(order=True)  # , frozen=True)
class ScreenChangeOrder:
    """Hold some Text, or one Control Sequence"""

    time_time: float

    yx: tuple[int, ...]

    early_mark: str  # ''  # '\025' ⌃U
    int_literal: str  # ''  # '0x42'  # '9'
    late_mark: str  # ''  # '\025' ⌃U

    key_byte_frame: KeyByteFrame
    intricate_order: bool  # says if .key_byte_frame grown from multiple Inputs

    #
    # Define Init, Bool, Str, & Clear
    #

    def __init__(self) -> None:

        self.key_byte_frame = KeyByteFrame(b"")
        self.clear_order()

    def clear_order(self) -> None:

        self.time_time = time.time()

        self.yx = tuple()

        self.early_mark = ""
        self.int_literal = ""
        self.late_mark = ""

        f = self.key_byte_frame
        f.clear_frame()

        self.intricate_order = False

    def __bool__(self) -> bool:

        truthy = self != ScreenChangeOrder()
        return truthy

    @property
    def forceful_order(self) -> bool:
        forceful = bool(self.early_mark or self.int_literal or self.late_mark)
        return forceful

    def __str__(self) -> str:

        early_mark = self.early_mark
        int_literal = self.int_literal
        late_mark = self.late_mark

        intricate_order = self.intricate_order

        f = self.key_byte_frame
        data = f.to_frame_bytes()

        em = repr(early_mark)[1:-1]
        lm = repr(late_mark)[1:-1]

        s = f"{em} {int_literal} {lm} {intricate_order} {data!r}"  # no .forceful_order

        return s

        # '\x15' '0' '\x15' b'\x1b[A'

    #
    # Say what to do and where
    #

    def compile_order(self) -> tuple[int, int, int, int, BytesBox]:
        """Say where to run, what to run, and if strongly told to run it other than once"""

        yx = self.yx

        early_mark = self.early_mark
        int_literal = self.int_literal
        late_mark = self.late_mark

        f = self.key_byte_frame

        assert DL_Y == "\033[" "{}M"
        assert _CLICK3_ == "\033[M"

        # Say where to run

        (row_y, column_x) = yx

        # Say how strongly marked the Factor is, if marked at all

        strong = len(early_mark + late_mark)

        # Take an Int Literal as is, not changed by more or less ⌃U marks next door

        if not int_literal:
            factor = 4 ** len(early_mark)  # per Emacs
        else:
            try:
                base = 0
                factor = int(int_literal, base)  # maybe negative or zero
            except ValueError:
                factor = -1 if (int_literal == "-") else 1

        # Quit now to grow some more, else fall through with a whole Frame

        f.tilt_to_close_frame()  # like stop staying open to accept b x y into ⎋[⇧M{b}{x}{y}

        data = f.to_frame_bytes()
        if not f.closed:
            if not f.printable:
                data = b""

        box = BytesBox(data)

        # Succeed

        return (row_y, column_x, strong, factor, box)

    #
    # Add on a next Input, else restart
    #

    def grow_order(self, box: BytesBox, yx: tuple[int, int]) -> None:
        """Add on a next Input, else restart"""

        data = box.data
        text = box.text

        assert data, (data,)

        f = self.key_byte_frame
        assert _FactorMark_ == "\025"

        # Take Input after a Text Frame or Closed Frame as a new Order

        if f.printable or f.closed:
            self.clear_order()

        # Place Output over top of first Input

        if not self.yx:
            self.yx = yx

        # Pick Self apart AFTER our last .clear_order

        early_mark = self.early_mark
        int_literal = self.int_literal
        late_mark = self.late_mark

        # Take ⌃U as a thing to count in itself at first
        # Take one extra ⌃U later to end and strengthen the .int_literal

        if text == "\025":  # ⌃U

            if (early_mark and late_mark) or f:

                self.clear_order()
                self.early_mark = text

            else:

                if not early_mark:
                    self.early_mark = text
                elif not int_literal:
                    self.early_mark += text
                else:
                    self.late_mark = text

            return

        # Start or grow an Int Literal

        lit_plus = int_literal + text

        if not late_mark:
            if not text.isspace():
                if not f:

                    try:

                        x = lit_plus + "0"
                        base_eq_0 = 0
                        _ = int(x, base_eq_0)

                        self.int_literal = lit_plus
                        return

                    except ValueError:

                        pass

        # Grow the Frame

        with_bool_f = bool(f)
        extras = f.take_data_if(data)
        if not extras:
            if with_bool_f:
                self.intricate_order = True

            return

        # Else start over  # like when reached by ⎋ [ ' 2

        self.clear_order()

        # todo9: Accept the shifting Symbols of ⎋ ⌃ ⌥ ⇧ ⌘ Fn into the Screen Change Order


#
# Talk with one KeyboardReader and one ScreenWriter
#


class TerminalBoss:
    """Talk with one KeyboardReader and one ScreenWriter"""

    selves: list[TerminalBoss] = list()

    stdio: typing.TextIO
    fileno: int
    tcgetattr: list[int | list[bytes | int]]  # replaced by .__enter__

    screen_writer: ScreenWriter
    keyboard_reader: KeyboardReader

    def __init__(self) -> None:

        TerminalBoss.selves.append(self)

        stdio = sys.__stderr__
        assert stdio is not None  # refuses to run headless

        fileno = stdio.fileno()

        sw = ScreenWriter(self)
        kr = KeyboardReader(self)

        self.stdio = stdio
        self.fileno = fileno
        self.tcgetattr = list()  # replaced by .__enter__

        self.screen_writer = sw
        self.keyboard_reader = kr

    @staticmethod
    def _breakpoint_() -> None:
        """Exit for just long enough to breakpoint then re-enter"""

        tb = TerminalBoss.selves[-1]
        tb.__exit__()

        breakpoint()  # Pdb likes:  where, up, down, tb = None, continue
        pass  # Pdb likes:  where, up, down, tb = None, continue

        if tb:
            tb.__enter__()

        # TerminalBoss._breakpoint_()

    def __enter__(self) -> TerminalBoss:
        r"""Stop line-buffering Input, stop taking \n Output as \r\n, etc"""

        stdio = self.stdio
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        # Enter once

        if tcgetattr:
            return self

        # Flush Output, drain Input, and change Input Mode

        stdio.flush()  # before 'tty.setraw' of TerminalStudio.__enter__

        with_tcgetattr = termios.tcgetattr(fileno)
        assert with_tcgetattr, (with_tcgetattr,)

        self.tcgetattr = with_tcgetattr  # replaces

        # Stop line-buffering Input, stop replacing \n Output with \r\n, etc

        if not flags.sigint:
            tty.setraw(fileno, when=termios.TCSADRAIN)
        else:
            tty.setcbreak(fileno, when=termios.TCSADRAIN)

        # Succeed

        return self

        # todo: try termios.TCSAFLUSH to discard Input while entering

    def __exit__(self, *args: object) -> None:
        r"""Restart line-buffering Input, restart taking \n Output as \r\n, etc"""

        kr = self.keyboard_reader

        stdio = self.stdio
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        # Exit once

        if not tcgetattr:
            return

        # Mention Input Bytes buffered and lost by an early Exit

        reads_ahead = kr.reads_ahead
        if reads_ahead:
            logger.info(f"{reads_ahead=} {fileno=}")

        # Flush Output, drain Input, and change Input Mode

        stdio.flush()  # before 'termios.tcsetattr' of TerminalStudio.__exit__

        fd = fileno
        when = termios.TCSADRAIN
        attributes = tcgetattr
        termios.tcsetattr(fd, when, attributes)

        self.tcgetattr = list()  # replaces

        # todo: try termios.TCSAFLUSH to discard Input while exiting

    def write_some_bytes(self, data: bytes) -> None:
        """Write zero or more Bytes"""

        # logger.info(f"{data=}")

        fileno = self.fileno
        fd = fileno
        os.write(fd, data)  # maybe empty

    def read_one_byte(self) -> bytes:
        """Read one Byte"""

        fileno = self.fileno

        fd = fileno
        length = 1
        read = os.read(fd, length)

        assert len(read) == 1, (read,)  # todo: test os.read returns empty

        return read

        # way far away from KeyboardReader.read_bytes and .read_byte_frames

    def stdio_select_select(self, timeout: float | None) -> bool:
        """Block till next Input Byte, else till Timeout, else till forever"""

        stdio = self.stdio
        fileno = self.fileno

        assert self.tcgetattr, (self.tcgetattr,)

        stdio.flush()  # before select.select of .stdio_select_select
        (r, w, x) = select.select([fileno], [], [], timeout)

        hit = fileno in r

        return hit

        # a la msvcrt.kbhit


class ScreenWriter:
    """Write Lines of Output to the Terminal Screen"""

    terminal_boss: TerminalBoss

    def __init__(self, terminal_boss: TerminalBoss) -> None:
        self.terminal_boss = terminal_boss

    def print(self, *args: object) -> None:
        """Answer the question of 'what is print?' here lately"""

        printable = " ".join(str(_) for _ in args)

        self.write_printable(printable)  # may raise UnicodeEncodeError
        self.write_some_controls(["\r", "\n"])

        # todo: one 'def print' per project is exactly enough?

    def write_printable(self, text: str) -> None:
        """Write the Byte Encodings of Printable Text without adding a Line-Break"""

        printable = text  # alias
        assert printable.replace("", "-").isprintable(), (printable,)

        assert CUF_X == "\033[" "{}" "C"
        assert CUB_X == "\033[" "{}" "D"

        # Trust the Terminal to write well

        if not flags.google:
            self._write_encode_(printable)
            return

        # Else trust the Terminal to write all but Fullwidth & Wide well

        eaws_set = set(unicodedata.east_asian_width(_) for _ in printable)
        if "Fullwidth"[0] not in eaws_set:
            if "Wide"[0] not in eaws_set:
                self._write_encode_(printable)
                return

        # Else trust the Terminal to write well, except to stop the Cursor at X + 1, not at X + 2

        for t in text:
            self._write_encode_(t)
            eaw = unicodedata.east_asian_width(t)
            if eaw in ("Fullwidth"[0], "Wide"[0]):
                self.write_control("\033[C")
                if not _os_environ_get_cloud_shell_:  # separate from .flags.google
                    self.write_control("\033[D")

        # "Ambiguous"[0]  # ¡ ¤ § ® Ø ß ± ¶ ↖ ↗ ↘ ↙ € Ω Ⅷ 
        # "Narrow"[:2]  # ¢ and £ and the Printable US Ascii
        # "Neutral"[0]  # © « µ » ñ

        # "Halfwidth"[0]  # Hangul, Katakana, & Halfwidth ￭ ￮
        # "Fullwidth"[0]  # ０ ９ Ａ Ｚ ￥ ￦  # U+3000 Ideographic Space
        # "Wide"[0]  # ☕ ☰ ♿ 🌅 🌐 💾 💿 🔍 🔰 😃 🛼

        # also Wide are ♿ ⚪⚫ ⬛⬜ 🔰 🔴🔵 😃 🛼 🟠🟡🟢🟣🟤 🟥🟦🟧🟨🟩🟪🟫

        # todo: shrink the distribution of '.replace("", "-").isprintable'

    def write_some_controls(self, texts: typing.Iterable[str]) -> None:
        """Write the Byte Encodings of >= 0 Unprintable Control Texts"""

        controls = texts  # alias

        for control in controls:
            self.write_control(control)

        # may write zero controls

    def write_control(self, text: str) -> None:
        """Write the Byte Encodings of one Unprintable Control Text"""

        control = text  # alias

        if not control:
            return

        assert not control.isprintable(), (control,)

        data = control.encode()
        f = KeyByteFrame(data)  # may raise UnicodeEncodeError
        f.tilt_to_close_frame()  # like stop staying open to accept b x y into ⎋[⇧M{b}{x}{y}
        assert (not f.printable) and f.closed, (data, f)

        self._write_encode_(control)

        # todo: can the assert is-control idea be spoken lots more simply?

    def _write_encode_(self, text: str) -> None:
        """Write the Byte Encodings of Text without adding a Line-Break"""

        # logger.info(f"{text=}")  # printable or control or a mix of both

        tb = self.terminal_boss
        data = text.encode()  # may raise UnicodeEncodeError
        tb.write_some_bytes(data)


Y1 = 1  # min Y of Terminal Cursor
X1 = 1  # min X of Terminal Cursor


PS0 = 0  # default Csi Ps = 0 for some

PN1 = 1  # default Csi Pn = 1 for others
_MAX_PN_32100_ = 32100  # max Csi Pn = 32100 exceeds the x_wide x y_high of most Terminal Screens


ICH_X = "\033[" "{}" "@"  # Csi 04/00 [Insert] Cursor Horizontal [Pn] [Columns]

CUU_Y = "\033[" "{}" "A"  # Csi 04/01 Cursor Up [Pn] [Rows]
CUF_X = "\033[" "{}" "C"  # Csi 04/03 Cursor Forward [Pn] [Columns]
CUB_X = "\033[" "{}" "D"  # Csi 04/04 Cursor Backward [Pn] [Columns]
CUP_Y_X = "\033[" "{};{}H"  # Csi 04/08 [Choose] Cursor Position [Y and X]
ED_PS = "\033[" "{}" "J"  # CSI 04/10 Erase in Display  # 0 Tail # 1 Head # 2 Rows # 3 Scrollback
EL_PS = "\033[" "{}" "K"  # CSI 04/11 Erase in Line [Row]  # 0 Tail # 1 Head # 2 Row
IL_Y = "\033[" "{}" "L"  # Csi 04/12 Insert Line [Row]
_CLICK3_ = "\033[M"  # ⎋[⇧M{b}{x}{y} Click Press/ Release
DL_Y = "\033[" "{}M"  # Csi 04/13 Delete Line [Row]
SU_Y = "\033[" "{}S"  # CSI 05/03 Scroll Up [Into Scrollback]

VPA_Y = "\033[" "{}" "d"  # Csi 06/04 Vertical Position Absolute [Row]

DECIC_X = "\033[" "{}" "'}}"  # Csi 07/13 [DEC] Insert Column [Pn]
DECDC_X = "\033[" "{}" "'~"  # Csi 07/14 [DEC] Delete Column [Pn]


SM_PS = "\033[" "{}" "h"  # CSI 06/08 4 Set Mode
RM_PS = "\033[" "{}" "l"  # CSI 06/12 4 Reset Mode
SGR_PS = "\033[" "{}" "m"  # CSI 06/13 Select Graphic Rendition [Text Style]
DSR_PS = "\033[" "{}n"  # Csi 06/14 [Request] Device Status Report [Ps]
DECSCUSR_PS = "\033[" "{}" " q"  # CSI 06/15 [DEC] Set Cursor Style [Ps]  # Two Byte Backtail

DSR5 = "\033[" "5n"  # DSR_PS Ps 5 for DSR0
DSR6 = "\033[" "6n"  # DSR_PS Ps 6 for CPR_Y_X

# ⎋[4H inserting  ⎋[4L replacing  ⎋[⇧?2004H paste-wrap  ⎋[⇧?2004L paste-unwrap
# ⎋[?25H cursor-show  ⎋[?25L -hide  ⎋[6 Q -bar  ⎋[4 Q -skid  ⎋[ Q -unstyled

# ⎋[1M bold  ⎋[4M underline  ⎋[7M reverse/inverse  ⎋[103M backlight yellow
# ⎋[31M red  ⎋[32M green  ⎋[34M blue  ⎋[38;5;130M orange  ⎋[48;5;130M same back
# ⎋[M plain  ⎋[⇧?1049H screen-alt  ⎋[⇧?1049L screen-main

# ⎋[5N send for reply ⎋[0N
# ⎋[6N send for reply ⎋[{y};{x}⇧R  ⎋[18T send for reply ⎋[8;{rows};{columns}T
# ⎋]11;⇧?⌃G send for {r}/{g}/{b}  # 11 Backlight  # 10 Color

# <!-- todo: Say more of Osc Ps 12 112, esp Ps 12 crashes of Terminal Tabs at Google Cloud Shell -->


class KeyboardReader:
    """Read Frames of Input from the Terminal Keyboard"""

    terminal_boss: TerminalBoss

    y_high: int  # H W positive after initial zero
    x_wide: int

    row_y: int  # Y X positive after initial zero
    column_x: int

    reads_ahead: bytearray

    def __init__(self, terminal_boss: TerminalBoss) -> None:

        self.terminal_boss = terminal_boss

        self.row_y = 0
        self.column_x = 0
        self.y_high = 0
        self.x_wide = 0

        self.reads_ahead = bytearray()

    #
    # Split the Input Bytes of a Cursor Position Report into >= 1 Frames,
    # and update the H W Y X of this KeyboardReader
    #

    def read_byte_frames(self) -> tuple[bytes, ...]:
        """Read one Frame at a time, and help the Client ignore H W Y X"""

        frame_list = list()

        (start, end) = self._read_click_release_frame_and_after_()
        assert start or end, (start, end)

        if start:
            frame_list.append(start)

        data = end
        while data:
            (start, end) = self._bytes_split_frame_(data)
            assert (start + end) == data, (start, end, data)
            assert start, (start, end, data)

            frame_list.append(start)
            data = end

        frames = tuple(frame_list)
        assert frames, (frames,)

        frames = self._frames_compress_if_(frames)

        return frames

        # todo: keep 'def read_byte_frames' paired up with 'def kbhit'
        # way far away from TerminalBoss.read_one_byte

    def _frames_compress_if_(self, frames: tuple[bytes, ...]) -> tuple[bytes, ...]:
        """Collapse two Frames to one, or don't"""

        assert _NorthArrow_ and _SouthArrow_ and _EastArrow_ and _WestArrow_
        assert _NorthwestArrow_ and _NortheastArrow_ and _SoutheastArrow_ and _SouthwestArrow_

        # Convert a Double Key Jam of actual 4-way ←↑→↓ Arrows into 8-way ↖↗↘↙ Compass Arrows

        classic_arrow_encodings = (b"\033[A", b"\033[B", b"\033[C", b"\033[D")

        if len(frames) == 2:
            if all((_ in classic_arrow_encodings) for _ in frames):
                backtails = b"".join(sorted(_[-1:] for _ in frames))

                if backtails == b"AD":  # _NorthArrow_ _WestArrow_
                    return ("\033[↖".encode(),)
                elif backtails == b"AC":  # _NorthArrow_ _EastArrow_
                    return ("\033[↗".encode(),)
                elif backtails == b"BC":  # _SouthArrow_ _EastArrow_
                    return ("\033[↘".encode(),)
                elif backtails == b"BD":  # _SouthArrow_ _WestArrow_
                    return ("\033[↙".encode(),)

                # ⎋ [ ↖ ↗ ↘ ↙  # not yet standard

        # Else make no change

        return frames

    def _read_click_release_frame_and_after_(self) -> tuple[bytes, bytes]:
        """Read Bytes, but split off a leading ⌥-Click if present"""

        data = self.read_bytes()
        assert data, (data,)

        (arrowheads, end) = self._bytes_split_arrowheads_(data)
        assert arrowheads or end, (arrowheads, end, data)

        frame = b""
        if arrowheads:
            frame = self._arrowheads_to_frame_(arrowheads)
            assert frame, (frame, arrowheads)

        return (frame, end)

    def _bytes_split_arrowheads_(self, data: bytes) -> tuple[str, bytes]:
        """Split a Burst of Arrows into a Head of Arrows and a Tail of Bytes"""

        marks: list[str] = list()

        assert ClassicArrows == ("\033[A", "\033[B", "\033[C", "\033[D")

        if len(data) <= (MAX_ARROW_KEY_JAM_2 * 3):
            return ("", data)

        end = b""
        for i in range(0, len(data), 3):
            few = data[i:][:3]  # spans of 3 bytes, but maybe short at end

            if few not in (b"\033[A", b"\033[B", b"\033[C", b"\033[D"):
                end = data[i:]
                break

            ord_mark = few[-1]
            mark = chr(ord_mark)  # the Csi Final Byte

            assert mark in ("A", "B", "C", "D"), (mark, few)
            marks.append(mark)

        if flags.clickruns and marks:

            runs = b"".join(
                b"\033[%d%b" % (len(list(g)), k.encode()) for k, g in itertools.groupby(marks)
            )

            alt_data = runs + end
            return ("", alt_data)

        arrowheads = "".join(marks)
        return (arrowheads, end)

    def _arrowheads_to_frame_(self, arrowheads: str) -> bytes:
        """Convert a Burst of Arrows into a ⌥-Click Release"""

        y = self.row_y
        x = self.column_x
        h = self.y_high
        w = self.x_wide

        assert _NorthArrow_ and _SouthArrow_ and _EastArrow_ and _WestArrow_

        o = (y, x, h, w, arrowheads)

        for a in arrowheads:

            if x > w:
                x -= w
                y += 1

            if a == "A":  # 'A' Arrowhead of ⎋[⇧A _NorthArrow_

                y -= 1

            elif a == "B":  # 'B' Arrowhead of ⎋[⇧B _SouthArrow_

                y += 1

            elif a == "C":  # 'C' Arrowhead of ⎋[⇧C _EastArrow_

                x += 1

            else:
                assert a == "D", (a,)  # 'D' Arrowhead of ⎋[⇧D _WestArrow_

                x -= 1
                if x < X1:
                    x += w
                    y -= 1

            if len(arrowheads) <= 3:  # takes Arrow Key Mash as ⌥-Click Release
                y = min(max(Y1, y), h)
                x = min(max(X1, x), w)
                continue

            assert Y1 <= y <= h, (y, x, h, w, o)
            assert X1 <= x <= (w + 1), (y, x, h, w, o)

        if x > w:
            logger.info(f"{h=} {w=} {y=} {x=}  # x > w")
            x -= 1
            assert X1 <= x <= w, (y, x, h, w, o)

        f = int("0b01000", base=0)  # f = 0b⌃⌥⇧00
        data = f"\033[<{f};{x};{y}m".encode()

        return data  # lower 'm' for Release

    def _bytes_split_frame_(self, data: bytes) -> tuple[bytes, bytes]:
        """Split one Frame off the Start of the Bytes"""

        assert KeyboardDecoder.OptionAccents == ("`", "´", "¨", "ˆ", "˜")
        assert KeyboardDecoder.OptionGraveGrave == "``"

        if not data:
            return (data, b"")

        text = KeyByteFrame.bytes_decode_if(data)

        # Accept the b"``" as the Frame of ⌥⇧`

        if len(text) == 2:
            if text == "``":  # ⌥⇧` `
                start = data
                end = b""
                return (start, end)

            # Split the ⌥ Accents arriving together with an Unaccented Decode

            accents = ("`", "´", "¨", "ˆ", "˜")  # ⌥⇧` ⌥⇧E ⌥⇧U ⌥⇧I ⌥⇧N
            if text[0] in accents:
                start = text[0].encode()
                end = text[1:].encode()
                return (start, end)

        # Split one Text or Control Frame off the Start of the Bytes

        end = b""

        f = KeyByteFrame(b"")
        for i in range(len(data)):
            one_byte = data[i:][:1]
            some_bytes = data[i:][1:]

            extras = f.take_one_byte_if(one_byte)
            if extras:
                assert f.closed, (f.closed, extras, one_byte, f)
                end = extras + some_bytes
                break

            if f.closed:
                end = some_bytes
                break

        start = f.to_frame_bytes()
        assert (start + end) == data, (start, end, data)

        return (start, end)

    #
    # Frame the Input Bytes that share a Cursor Position Report,
    # and update the H W Y X of this KeyboardReader
    #

    def kbhit(self, timeout: float | None = None) -> None:
        """Block till next Input Byte, else till Timeout, else till forever"""

        reads_ahead = self.reads_ahead
        if reads_ahead:
            return

        tb = self.terminal_boss
        tb.stdio_select_select(timeout=timeout)  # a la msvcrt.kbhit

        # todo: one 'def kbhit' per project is exactly enough?
        # todo: keep 'def kbhit' paired up with 'def read_bytes' and 'def read_byte_frames'

    def sample_luminance(self) -> float:
        """Choose Darkmode & Lightmode by Backlight else by Color"""

        tb = self.terminal_boss
        sw = tb.screen_writer
        reads_ahead = self.reads_ahead

        # Sends ⎋]10;⇧?⌃G for reply ⎋]10;RGB⇧:{r}/{g}/{b}\007 for 10, 11, and 12

        for osc in (10, 11, 12):  # 10 Color  # 11 Backlight  # 12 Cursor

            dsr5 = "\033[5n"
            sw.write_control(dsr5)

            osc_control = f"\033]{osc};?\007"
            sw.write_control(osc_control)

            reads_endswith_rgb = self.read_bytes()
            (reads, rgb) = self._bytes_split_osc_rgb_ints_(reads_endswith_rgb, osc=osc)

            if rgb:
                rep_rgb = "(" + ", ".join(f"0x{_:04X}" for _ in rgb) + ")"
                logger.info(f"{osc=} rgb={rep_rgb}")

            if reads:
                m = re.search(rb"\033\[0n$", string=reads)
                if m:
                    logger.info(f"took {m.group(0)!r}")  # for Dsr 0 before Osc 10 11 12

                    n = len(m.group(0))
                    reads = reads[:-n]

            if reads:
                logger.info(f"{reads=} {osc_control=}")
                reads_ahead.extend(reads)

        # Succeed

        return 0.0

    def _bytes_split_osc_rgb_ints_(self, data: bytes, osc: int) -> tuple[bytes, tuple[int, ...]]:
        """Split the Osc Byte Sequence off the end"""

        encode = str(osc).encode()
        m = re.search(
            rb"\033]" + encode + rb";rgb:([0-9a-f]+)/([0-9a-f]+)/([0-9a-f]+)(\007|\033\134)$",
            string=data,
        )

        startswith = data
        int_list = list()

        if m:
            logger.info(f"took {m.group(0)!r}")  # for Osc 10 11 12

            n = len(m.group(0))
            startswith = data[:-n]

            for g in range(1, 3 + 1):
                i = int(m.group(g), base=0x10)
                assert 0 <= i <= 0xFFFF, (i, m.group(g), data)
                int_list.append(i)

        return (startswith, tuple(int_list))

    def sample_hwyx(self) -> tuple[int, int, int, int]:
        """Take a fresh sample of Width x Height and Y X Cursor Position of this Terminal"""

        tb = self.terminal_boss
        sw = tb.screen_writer
        reads_ahead = self.reads_ahead

        assert DSR0 == "\033[" "0n"
        assert DSR5 == "\033[" "5n"

        sw.write_control("\033[5n")  # sends ⎋[5N for reply ⎋[0N
        dsr0_bytes = self.read_bytes()
        (h, w, y, x) = (self.y_high, self.x_wide, self.row_y, self.column_x)

        dsr0 = b"\033[0n"
        assert dsr0_bytes.endswith(dsr0), (dsr0_bytes, dsr0)
        # logger.info(f"took {dsr0}")

        n = len(dsr0)
        reads = dsr0_bytes[:-n]

        if reads:
            logger.info(f"{reads=} {dsr0=}")
            reads_ahead.extend(reads)

        # Move this KeyboardReader to this fresh H W Y X

        self._store_h_w_y_x_(h, w=w, y=y, x=x)

        # Succeed

        return (h, w, y, x)

    def read_bytes(self) -> bytes:
        """Take Input Bytes from Cache, else from Terminal"""

        # Take all the Input Bytes from Cache at once

        reads_ahead = self.reads_ahead
        if reads_ahead:
            logger.info(f"{reads_ahead=}")

            reads = bytes(reads_ahead)
            reads_ahead.clear()

            return reads

        # Else take a Cursor Position Frame of Input Bytes from Terminal

        (hwyx, reads) = self._read_hwyx_bytes_()
        self._store_h_w_y_x_(*hwyx)

        return reads

        # todo: keep 'def read_bytes' paired up with 'def kbhit'
        # way far away from TerminalBoss.read_one_byte

        # todo: one 'def read_bytes' per project is exactly enough?

    def _store_h_w_y_x_(self, h: int, w: int, y: int, x: int) -> None:
        """Limit & store the Height Width Y X of this Terminal"""

        assert h >= 5, (h,)  # todo: test of Terminals smaller than macOS Terminals
        assert w >= 20, (w,)  # todo: test of 9 Columns x 2 Rows at macOS iTerm2

        self.y_high = h
        self.x_wide = w

        assert Y1 <= y <= h, (y, h)
        assert X1 <= x <= w, (x, w)

        self.row_y = y
        self.column_x = x

    def _read_hwyx_bytes_(self) -> tuple[tuple[int, int, int, int], bytes]:
        """Read the Input Bytes and their Y X, then add their H W"""

        tb = self.terminal_boss
        fileno = tb.fileno

        # Read one Byte, then send for Y X Cursor Position, then block till it comes

        (yx, reads) = self._read_yx_bytes_()
        (y, x) = yx

        # Sample H W just after the last Input Byte arrives

        fd = fileno
        (w, h) = os.get_terminal_size(fd)
        if (h, w) != (self.y_high, self.x_wide):
            logger.info(f"took ⎋[8;{h};{w}T")

        # Succeed

        hwyx = (h, w, y, x)

        return (hwyx, reads)

    def _read_yx_bytes_(self) -> tuple[tuple[int, int], bytes]:
        """Read 1 Byte, send for Cursor Y X Position, & read Available Bytes till the Report"""

        tb = self.terminal_boss
        sw = tb.screen_writer

        assert _NorthArrow_ and _SouthArrow_ and _EastArrow_ and _WestArrow_
        assert DSR6 == "\033[" "6n"
        assert CPR_Y_X == "\033[" "{};{}R"

        tb.write_some_bytes(b"\033[6n")  # ⎋[6n send for reply Y X
        tb.stdio_select_select(timeout=0e0)  # flushes and blocks after .write_some_bytes

        row_y = -1
        column_x = -1
        ba = bytearray()

        flags_lazy_kbhits = False  # truthy to show more messy things
        while True:

            read = tb.read_one_byte()
            ba.extend(read)

            if flags.clickarrows:
                sm = re.search(rb"(\033\[[ABCD])$", string=ba)  # ⎋[⇧A ⎋[⇧B ⎋[⇧C ⎋[⇧D
                if sm:
                    logger.info(f"took {sm.group(0)!r}")  # for flags.clickarrows
                    n = len(sm.group(0))

                    control = sm.group(0).decode()
                    del ba[-n:]

                    sw.write_control(control)
                    continue

                    # todo8: wrap the --egg=clickarrows ⎋[⇧C ⎋[⇧D across screen edges

            if row_y < Y1:
                sm = re.search(rb"\033\[([0-9]+);([0-9]+)R$", string=ba)  # ⎋[{y};{x}⇧R
                if not sm:
                    continue

                n = len(sm.group(0))
                row_y = int(sm.group(1))
                column_x = int(sm.group(2))

                del ba[-n:]
                if (row_y, column_x) != (self.row_y, self.column_x):
                    logger.info(f"took ⎋[{row_y};{column_x}⇧R")

                assert row_y >= Y1, (row_y, column_x, ba)
                assert column_x >= X1, (row_y, column_x, ba)

                if not ba:  # eats first ⎋[ ⇧R, when ⎋[6N written before Def Entry
                    continue  # doesn't eat second ⎋[ ⇧R, because .row_y >= Y1 by then

                if flags_lazy_kbhits:
                    break

                    # Arrow Key Bursts split apart into frames if .flags_lazy_kbhits
                    # Double Key Jams still often recur despite .flags_lazy_kbhits

            if not tb.stdio_select_select(timeout=0e0):  # blocks
                break

        yx = (row_y, column_x)  # taken from first, when more left in .ba
        reads = bytes(ba)

        if len(ba) < 20:
            headtail = bytes(ba)
            # logger.info(f"ba={headtail!r} y={row_y} x={column_x}")
            _ = headtail
        else:
            head = bytes(ba[:10])
            tail = bytes(ba[-10:])
            _ = head, tail
            # logger.info(f"[:10]={head!r} [-10:]={tail!r} y={row_y} x={column_x}")

        return (yx, reads)

        # ⌥-Click sends D A B C in the sense of D's, then A's or B's, then C's;
        # except across a Wrapped Line it can even send like D B C B C, and A D A D A,
        # and A D A D C, and so on and on

    #  ⎋[200⇧~ .. ⎋[201⇧~ arrive together from ⎋[ ⇧?2004H Bracketed Paste

    #
    # at macOS Terminal
    #
    #   mashing the ← ↑ → ↓ Arrow Keys sends 1..3 Arrows
    #   ⌥-Click sends 1..X Burst of 1..Y Arrows each
    #   ⌥` sends b"``" sometimes together, sometimes separately
    #

    #
    # at macOS iTerm2
    #
    #   mashing the ← ↑ → ↓ Arrow Keys sends 1..2 Arrows
    #   ⌥-Click sends 1 Burst of 1..Y Arrows
    #   ⌥` sends b"``" as 1 Burst of 2 Seven-Bit US-Ascii Chars
    #


@dataclasses.dataclass(order=True)  # , frozen=True)
class KeyByteFrame:
    """Frame Bytes of Input, as an ⎋ Esc Sequence, else simply"""

    printable: bytearray  # b''  # Decodable Printable Text

    head: bytearray  # b''  # N * ESC  # N * ESC + CSI  # N * ESC + SS3  # OSC
    neck: bytearray  # b''  # Csi Params  # Osc Payload
    backtail: bytearray  # b''  # Csi Intermediates and Final  # Osc Terminator

    stash: bytearray  # b''  # 1..3 Bytes taken while not printable

    closed: bool

    def __init__(self, data: bytes) -> None:

        self.printable = bytearray()

        self.head = bytearray()
        self.neck = bytearray()
        self.backtail = bytearray()

        self.stash = bytearray()

        self.closed = False

        # Take the Bytes in, else raise ValueError

        for i in range(len(data)):
            kbyte = data[i:][:1]

            extras = self.take_one_byte_if(kbyte)
            if extras:
                raise ValueError(extras, kbyte, self)

    def __bool__(self) -> bool:

        truthy = self != KeyByteFrame(b"")
        return truthy

    # def __str__(self) -> str:  # todo9: add for Class KeyByteFrame

    def clear_frame(self) -> None:
        """Start again"""

        printable = self.printable
        head = self.head
        neck = self.neck
        backtail = self.backtail
        stash = self.stash

        printable.clear()
        head.clear()
        neck.clear()
        backtail.clear()
        stash.clear()

        self.closed = False

    def tilt_to_close_frame(self) -> None:
        """Transform into a Closed DL_Y without explicit Pn, if it was _CLICK3_ and no Stash"""

        printable = self.printable
        head = self.head
        neck = self.neck
        backtail = self.backtail
        stash = self.stash
        closed = self.closed

        assert _CLICK3_ == "\033[M"
        assert DL_Y == "\033[" "{}M"

        data = self.to_frame_bytes()

        if data == b"\033[M":  # takes the ⎋[⇧M DL_Y that isn't the ⎋[⇧M{b}{x}{y} _CLICK3_
            assert (not printable) and (not neck) and (not backtail), (head, self, data)
            assert head == b"\033[M", (head, self, data)

            if not stash:
                assert head == b"\033[M", (head,)
                assert not closed, (closed, self)

                del head[len(b"\033[") :]
                backtail.extend(b"M")

                self.close_frame()

                # stops staying open to accepting b x y into ⎋[⇧M{b}{x}{y}

        # todo: can the .tilt_to_close_frame idea be spoken lots more simply?

    def to_frame_bytes(self) -> bytes:
        """List the Bytes taken"""

        printable = self.printable

        head = self.head
        neck = self.neck
        backtail = self.backtail

        stash = self.stash

        join = bytes(printable + head + neck + backtail + stash)

        return join  # no matter if .closed or not

    def close_frame(self) -> None:
        """Close if not closed already"""

        stash = self.stash
        assert not stash, (stash,)

        self.closed = True

    #
    # Pick apart a Esc Csi Sequence into its Marks and Ints
    #

    def to_csi_marks_ints_if(self) -> tuple[bytes, tuple[int, ...]]:
        """Pick out the Nonnegative Int Literals of a Csi Escape Sequence"""

        printable = self.printable
        head = self.head
        neck = self.neck
        backtail = self.backtail
        stash = self.stash

        assert CSI == "\033["

        if (head != b"\033[") or printable or stash or (not backtail):
            return (b"", tuple())

        fm = re.fullmatch(rb"^([^0-9;]*)([0-9;]*)(.*)$", string=neck + backtail)
        assert fm, (fm, neck, backtail)

        marks = fm.group(1) + fm.group(3)
        ints = tuple((int(_) if _ else -1) for _ in fm.group(2).split(b";"))

        return (marks, ints)

        # (b"A", []) for "\033[A"
        # (b"H", [123, -1]) for "\033[123;H"

    #
    # Take 1 Byte in and return 0 Bytes, else return 1..4 Bytes that don't fit
    #

    def take_data_if(self, data: bytes) -> bytes:
        """Try to take X Bytes in and return 0 <= Y <= X Bytes that don't fit"""

        for index in range(len(data)):
            kbyte = data[index:][:1]
            kbytes = data[index:][1:]

            extras = self.take_one_byte_if(kbyte)
            if extras:
                extras_plus = extras + kbytes
                return extras_plus

        return b""

    def take_one_byte_if(self, data: bytes) -> bytes:
        """Take 1 Byte in and return 0 Bytes, else return 1..4 Bytes that don't fit"""

        assert len(data) == 1, (data,)
        kbyte = data

        printable = self.printable
        head = self.head
        stash = self.stash
        closed = self.closed

        assert ESC == "\033"

        assert SS3 == "\033O"
        assert CSI == "\033["
        assert _CLICK3_ == "\033[M"
        assert OSC == "\033]"

        # Bounce while Closed

        if closed:
            return kbyte

        # Hold 1..3 Bytes to decode later

        data = bytes(stash + kbyte)
        text = KeyByteFrame.bytes_decode_if(data)

        if not text:
            if KeyByteFrame.bytes_to_later_decode_if(data):
                stash.extend(kbyte)
                return b""

        assert len(text) <= 1, (len(text), text, data)

        stash.clear()

        # Take the Bytes in before the first Head, or without ever a Head

        if not head:
            extras = self._take_before_head_if_(data, text=text)
            return extras

        # Take later Bytes in differently, after starts with each kind of Head

        assert not printable, (printable,)

        dent = len(head) - len(head.lstrip(b"\033"))
        dent = (dent - 1) if dent else 0
        undented_head = head[dent:]

        if undented_head == b"\033":
            extras = self._take_after_esc_if_(data)
            return extras

        elif undented_head == b"\033O":
            extras = self._take_after_ss3_if_(data)
            return extras

        elif undented_head == b"\033[M":
            extras = self._take_after_csi_m_if_(data)
            return extras

        elif undented_head == b"\033[":
            extras = self._take_after_csi_if_(data, text=text)
            return extras

        elif undented_head == b"\033]":
            extras = self._take_after_osc_if_(data, text=text)
            return extras

        assert False, (head, head[dent:], dent, self)

    def _take_before_head_if_(self, data: bytes, text: str) -> bytes:
        """Take 1..4 more Bytes in, before any Head, else return what doesn't fit"""

        printable = self.printable
        head = self.head

        # Take 1 Decoded Printable Char, without closing the Frame

        if text:
            if text.isprintable():
                self.printable = printable + data
                return b""

        # End a Text Frame before Unprintable or Undecodable Bytes

        if printable:
            self.close_frame()
            return data

        # Take 1..4 Unprintable or Undecodable Bytes as Head

        head.extend(data)
        if head != b"\033":
            self.close_frame()

        return b""

        # takes \b \t \n \r \x7f etc

        # doesn't take bytes([0x80 | 0x0B]) as meaning b"\033\x5b" Csi ⎋[
        # doesn't take bytes([0x80 | 0x0F]) as meaning b"\033\x4f" Ss3 ⎋O
        # doesn't take bytes([0x90 | 0x0D]) as meaning b"\033\x5d" Osc ⎋]

        # despite "Table 2b - Bit combinations" "control functions of the C1 set in an 8-bit code"

    Headbook = (
        b"\033",  # ⎋ ESC
        b"\033\033",  # ⎋⎋ after
        b"\033\033O",  # ⎋⎋O is ⎋ before ⎋O
        b"\033\033[",  # ⎋⎋[ is ⎋ before ⎋[
        b"\033O",  # ⎋O SS3
        b"\033[",  # ⎋[ CSI
        b"\033[M",  # ⎋[⇧M Click Press/ Release
        b"\033]",  # ⎋ OSC
    )

    def _take_after_esc_if_(self, data: bytes) -> bytes:
        """Take 1..4 more Bytes in, after ⎋ Esc, else return what doesn't fit"""

        head = self.head

        # Take one of the ⎋ Esc Head's, without closing the Frame

        head_plus = head + data
        if head_plus in KeyByteFrame.Headbook:
            lstrip = head_plus.lstrip(b"\033")
            assert len(lstrip) <= 1, (head_plus,)

            head.extend(data)
            return b""

            # doesn't take ⇧M after \⎋ [ here

        # Take ⎋ Esc as an Emacs Meta Byte before 1..4 Bytes

        head.extend(data)
        self.close_frame()
        return b""

    def _take_after_ss3_if_(self, data: bytes) -> bytes:
        """Take 1..4 more Bytes in, after ⎋O SS3, else return what doesn't fit"""

        head = self.head

        head.extend(data)
        self.close_frame()
        return b""

    def _take_after_csi_m_if_(self, data: bytes) -> bytes:
        """Take 1..4 more Bytes in, after ⎋[⇧M, else return what doesn't fit"""

        head = self.head
        backtail = self.backtail

        # Take up to three B X Y Chars after the Head, if all printable

        head_backtail_plus = bytes(head + backtail + data)
        plus_later = KeyByteFrame.bytes_to_later_decode_if(head_backtail_plus)
        assert not plus_later, (plus_later, head, backtail, data)

        plus_decode = KeyByteFrame.bytes_decode_if(head_backtail_plus)
        if plus_decode:
            if len(plus_decode) <= 6:
                backtail.extend(data)
                if len(plus_decode) == 6:
                    self.close_frame()
                return b""

        # Take up to three B X Y Bytes after the Head without limitation

        fit = 6 - len(head + backtail)
        if fit > 0:
            backtail.extend(data[:fit])
            extra = data[fit:]
            if len(head_backtail_plus) >= 6:
                self.close_frame()
            return extra  # maybe empty

        # Close the ⎋[⇧M Frame after 6 Bytes or before

        self.close_frame()
        return data

    def _take_after_csi_if_(self, data: bytes, text: str) -> bytes:
        """Take 1..4 more Bytes in, after ⎋[ CSI, else return what doesn't fit"""

        code = ord(text)

        head = self.head
        neck = self.neck
        backtail = self.backtail

        assert _CLICK3_ == "\033[M"

        # Take the 3-Byte ⎋[⇧M Esc Head, without closing the Frame

        if (not neck) and (not backtail):
            head_plus = head + data
            if head_plus in KeyByteFrame.Headbook:
                assert head_plus == b"\033[M", (head_plus,)
                head.extend(data)
                return b""

        # Grow the ⎋[ Csi Frame with 1 Decoded Printable Char

        if text and text.isprintable():
            assert code >= 0x20, (code, text, data)

            # Grow the Neck until the Backtail starts

            if 0x30 <= code < 0x40:  # 16 Parameter Codes  # 0123456789:;<=>?

                if not backtail:
                    neck.extend(data)
                    return b""

                # Close before more Params, if Backtail has started

                self.close_frame()
                return data

            # Grow the Backtail

            if 0x20 <= code < 0x30:  # 16 Intermediate Codes  # ␢!"#$%&\'()*+,-./
                backtail.extend(data)
                return b""

            # Close after a Csi Final Code, or after Printable Unicode

            assert code >= 0x40, (code, text, data)  # 63 Final Codes  # @A Z[\\]^_`a z{|}~

            backtail.extend(data)
            self.close_frame()
            return b""

        # Close the ⎋[ Csi Frame before Unprintable or Undecodable Bytes

        self.close_frame()
        return data

    def _take_after_osc_if_(self, data: bytes, text: str) -> bytes:
        """Take 1..4 more Bytes in, after ⎋] OSC, else return what doesn't fit"""

        neck = self.neck
        backtail = self.backtail

        assert BEL == "\007"
        assert ST == "\033\134"

        # Grow the ⎋] Osc Frame with 1 Decoded Printable Char

        if not backtail:
            if text and text.isprintable():
                neck.extend(data)
                return b""

        # Close the ⎋] Osc Frame with BEL or ST

        if text == "\007":
            backtail.extend(data)
            self.close_frame()
            return b""

        if not backtail:
            if text == "\033":
                backtail.extend(data)
                return b""

        if backtail == b"\033":
            if text == "\134":
                backtail.extend(data)
                self.close_frame()
                return b""

            # todo: how should other Bytes past "\033" close an ⎋] Osc Frame?

        # Close the ⎋] Osc Frame before Unprintable or Undecodable Bytes

        self.close_frame()
        return data

    #
    # Work with Decodable and Undecodable Bytes
    #

    @staticmethod
    def bytes_decode_if(data: bytes) -> str:
        """Say if printable"""

        try:
            text = data.decode()
            return text  # returns first found
        except UnicodeDecodeError:
            pass

        return ""

    Endswiths = (b"\xbf", b"\x80\x80", b"\xbf\xbf", b"\x80\x80\x80", b"\xbf\xbf\xbf")

    @staticmethod
    def bytes_to_later_decode_if(data: bytes) -> str:
        """Say if some Bytes start 1 or more UTF-8 Encodings of Chars"""

        endswiths = KeyByteFrame.Endswiths

        for endswith in endswiths:
            data_plus = data + endswith

            try:
                text = data_plus.decode()
            except UnicodeDecodeError:
                continue

            assert len(text) >= 1, (text,)
            return text  # returns first found

        return ""

    #
    # for b"\xc2", b"\xed", b"\xe0", b"\xf4", b"\xf0", & friends
    # because =>
    #
    # "\u0000"  # b"\x00"
    # "\u007f"  # b"\x7f"
    #
    # "\u0080"  # b"\xc2\x80" accepted with b"\xc2\xbf", could be accepted as b"\xc2\x80"
    # "\u07ff"  # b"\xdf\xbf" ditto
    #
    # "\u0800"  # b"\xe0\xa0\x80" accepted with b"\xe0\xbf\xbf"
    # "\ud7ff"  # b"\xed\x9f\xbf" accepted with b"\xed\x80\x80"
    # "\ud800".."\udfff"  # rejected as b"\xed\xa0\x80" .. b"\xed\xbf\xbf" surrogates
    # "\ue000"  # b"\xee\x80\x80" accepted
    # "\uffff"  # b"\xef\xbf\xbf" accepted
    #
    # "\U00010000"  # b"\xf0\x90\x80\x80" accepted with "\xf0\xbf\xbf\xbf"
    # "\U0010ffff"  # b"\xf4\x8f\xbf\xbf" accepted with "\xf4\x80\x80\x80"
    #

    # todo: invent UTF-8'ish Encoding beyond 1..4 Bytes for Unicode Codes > 0x10_FFFF ?


BEL = "\007"  # 00/07 Bell

ESC = "\033"  # 01/11 Escape ⎋

SS3 = "\033O"  # 01/11 04/15 Single Shift Three  # ⎋O
CSI = "\033["  # 01/11 05/11 Control Sequence Introducer  # ⎋[
OSC = "\033]"  # 01/11 05/13 Operating System Command  # ⎋]

assert _CLICK3_ == "\033[M"
assert DL_Y == "\033[" "{}M"

ST = "\033\134"  # 01/11 05/12 String Terminator  # ⎋\


#
# Speak of a Byte Encoding as a Sequence of Chords of Keycaps
#


class KeyboardDecoder:
    """Speak of a Byte Encoding as a Sequence of Chords of Keycaps"""

    selves: list[KeyboardDecoder] = list()

    decode_by_kseq: dict[str, str]
    kseqs_by_text: dict[str, tuple[str, ...]]

    def __init__(self) -> None:

        KeyboardDecoder.selves.append(self)

        self.decode_by_kseq = dict()
        self.kseqs_by_text = dict()

        self._add_basic_kseqs_()
        self._invert_decode_by_kseq_()

    #
    # Speak of a Byte Encoding as a Sequence of Chords of Keycaps
    #

    def frame_to_echo(self, data: bytes) -> str:
        """Form a brief Repr of one Input Frame"""

        assert data, (data,)

        box = BytesBox(data)
        text = box.text

        # Show Keycaps, if available as ⌫ ⇧⇥ ⇥ etc, except show ⏎ as ⌃M

        kseqs = self.bytes_to_kseqs_if(data)
        if kseqs:
            echo = kseqs[0]
            assert echo.isprintable(), (echo,)
            return echo  # ⌫  # ⇧⇥  # ⇥  # ⏎

        # Show the unquoted Repr, if not decodable

        if not text:
            echo = repr(data)[1:-1]
            assert echo.isprintable(), (echo,)
            return echo

        # Show one Keycap per Character, if decodable

        echo = ""
        for t in text:
            encode = t.encode()
            kseqs = self.bytes_to_kseqs_if(encode)
            kseq = kseqs[0] if kseqs else repr(t)[1:-1]
            echo += kseq

        assert echo.isprintable(), (echo,)
        return echo

    def bytes_to_kseqs_if(self, data: bytes) -> tuple[str, ...]:
        """Speak of a Byte Encoding as a Sequence of Chords of Keycaps"""

        text = data.decode()

        kseqs_by_text = self.kseqs_by_text

        if text in kseqs_by_text.keys():
            kseqs = kseqs_by_text.get(text, tuple())
            return kseqs

        return tuple()

    #
    # Add the Keycap Sequences for US-Ascii at MacBook
    #

    def _add_basic_kseqs_(self) -> None:
        """Add the Keycap Sequences for US-Ascii at MacBook"""

        decode_by_kseq = self.decode_by_kseq

        # Add the simplest named Keycaps: Esc, Return, Delete

        d0 = {
            #
            r"⏎": "\r",  # ⌃M
            # r"⌃⏎": "\r",  # ⌃M
            r"⇧⏎": "\r",  # ⌃M
            r"⌥⏎": "\r",  # ⌃M
            # r"⌃⇧⏎": "\r",  # ⌃M
            r"⌃⌥⏎": "\r",  # ⌃M
            r"⌥⇧⏎": "\r",  # ⌃M
            r"⌥⇧⌃⏎": "\r",  # ⌃M
            #
            r"⎋": "\033",  # ⌃[
            r"⌃⎋": "\033",  # ⌃[
            r"⇧⎋": "\033",  # ⌃[
            r"⌥⎋": "\033",  # ⌃[
            r"⌃⇧⎋": "\033",  # ⌃[
            r"⌃⌥⎋": "\033",  # ⌃[
            r"⌥⇧⎋": "\033",  # ⌃[
            r"⌥⇧⌃⎋": "\033",  # ⌃[
            #
            r"⌫": "\177",  # ⌃⇧?
            r"⌃⌫": "\177",  # ⌃⇧?
            r"⇧⌫": "\177",  # ⌃⇧?
            r"⌥⌫": "\177",  # ⌃⇧?
            r"⌃⇧⌫": "\177",  # ⌃⇧?
            r"⌃⌥⌫": "\177",  # ⌃⇧?
            r"⌥⇧⌫": "\177",  # ⌃⇧?
            r"⌥⇧⌃⌫": "\177",  # ⌃⇧?
            #
        }

        for k, v in d0.items():
            assert k not in decode_by_kseq.keys(), (k,)
            decode_by_kseq[k] = v

        # Add the forms of Spacebar and Tab

        d1 = {
            #
            r"⇥": "\t",  # ⌃I
            r"⌃⇥": "\t",  # ⌃I
            r"⇧⇥": "\033[" "Z",  # ⎋ [ ⇧Z
            r"⌥⇥": "\t",  # ⌃I
            r"⌃⇧⇥": "\033[" "Z",  # ⎋ [ ⇧Z
            r"⌃⌥⇥": "\t",  # ⌃I
            r"⌥⇧⇥": "\033[" "Z",  # ⎋ [ ⇧Z
            r"⌥⇧⌃⇥": "\033[" "Z",  # ⎋ [ ⇧Z
            #
            r"␢": "\040",  # ⌃`
            r"⌃␢": "\000",  # ⌃⇧@
            r"⇧␢": "\040",  # ⌃⇧`
            r"⌥␢": "\240",  # U+00A0 No-Break Space
            r"⌃⇧␢": "\000",  # ⌃⇧@
            r"⌃⌥␢": "\000",  # ⌃⇧@
            r"⌥⇧␢": "\240",  # U+00A0 No-Break Space
            r"⌥⇧⌃␢": "\000",  # ⌃⇧@
            #
        }

        for k, v in d1.items():
            assert k not in decode_by_kseq.keys(), (k,)
            decode_by_kseq[k] = v

        # Add the unnamed Keycaps: ⇧A..⇧Z, A..Z, 0..9, and the marks

        kseq = r"""

            ⌃⇧@  ⌃A  ⌃B  ⌃C  ⌃D  ⌃E  ⌃F  ⌃G  ⌃H  ⌃I  ⌃J  ⌃K  ⌃L  ⌃M  ⌃N  ⌃O
            ⌃P  ⌃Q  ⌃R  ⌃S  ⌃T  ⌃U  ⌃V  ⌃W  ⌃X  ⌃Y  ⌃Z  ⌃[  ⌃\  ⌃]  ⌃⇧^  ⌃-

            ⌃`  ⇧!  ⇧"  ⇧#  ⇧$  ⇧%  ⇧&  '  ⇧(  ⇧)  ⇧*  ⇧+  ,  -  .  /
            0  1  2  3  4  5  6  7  8  9  ⇧:  ;  ⇧<  =  ⇧>  ⇧?

            ⇧@  ⇧A  ⇧B  ⇧C  ⇧D  ⇧E  ⇧F  ⇧G  ⇧H  ⇧I  ⇧J  ⇧K  ⇧L  ⇧M  ⇧N  ⇧O
            ⇧P  ⇧Q  ⇧R  ⇧S  ⇧T  ⇧U  ⇧V  ⇧W  ⇧X  ⇧Y  ⇧Z  [  \  ]  ⇧^  ⇧_

            `  A  B  C  D  E  F  G  H  I  J  K  L  M  N  O
            P  Q  R  S  T  U  V  W  X  Y  Z  ⇧{  ⇧|  ⇧}  ⇧~  ⌃⇧?

        """

        code = -1
        for kcap in kseq.split():
            code += 1
            text = chr(code)

            if kcap not in ("⌃`", "⌃⇧?"):
                assert kcap not in decode_by_kseq.keys(), (kcap,)
                decode_by_kseq[kcap] = text

        # Add the aliases

        d2 = {
            r"⌃⇧_": r"⌃-",  # quicker to type ⌃-, easier to encode ⌃⇧_
            r"⌃⇧{": r"⌃[",
            r"⌃⇧|": r"⌃\ ".rstrip(),
            r"⌃⇧}": r"⌃]",
        }

        for k, v in d2.items():
            assert k not in decode_by_kseq.keys(), (k,)
            decode_by_kseq[k] = decode_by_kseq[v]

        # Add the Basic Arrows and the Double-Key-Jam Arrows

        d3 = {
            #
            r"↑": "\033[" "A",  # ⎋[⇧A
            r"↓": "\033[" "B",  # ⎋[⇧B
            r"→": "\033[" "C",  # ⎋[⇧C
            r"←": "\033[" "D",  # ⎋[⇧D
            #
            r"↖": "\033[" "↖",  # ⎋[↖    # not yet standard
            r"↗": "\033[" "↗",  # ⎋[↗
            r"↘": "\033[" "↘",  # ⎋[↘
            r"↙": "\033[" "↙",  # ⎋[↙
            #
        }

        for k, v in d3.items():
            assert k not in decode_by_kseq.keys(), (k,)
            decode_by_kseq[k] = v

        # Add the ⌥ and ⇧ Arrows  # todo8: differently at Apple vs others

        d4 = {
            r"⌥↑": d3[r"↑"],
            r"⌥↓": d3[r"↓"],
            r"⌥→": "\033" "f",  # ⎋F
            r"⌥←": "\033" "b",  # ⎋B
            #
            r"⇧↑": d3[r"↑"],
            r"⇧↓": d3[r"↓"],
            r"⇧→": "\033[" "1;2C",  # ⎋[1;2⇧C
            r"⇧←": "\033[" "1;2D",  # ⎋[1;2⇧D
            #
            r"⌥⇧↑": d3[r"↑"],
            r"⌥⇧↓": d3[r"↓"],
            r"⌥⇧→": d3[r"→"],
            r"⌥⇧←": d3[r"←"],
            #
            r"⇧Fn↑": "\033[" "5~",  # ⎋[5⇧~
            r"⇧Fn↓": "\033[" "6~",  # ⎋[6⇧~
            r"⇧Fn→": "\033[" "F",  # ⎋[⇧F
            r"⇧Fn←": "\033[" "H",  # ⎋[⇧H
        }

        for k, v in d4.items():
            assert k not in decode_by_kseq.keys(), (k,)
            decode_by_kseq[k] = v

        # Add the Fn Keys and the ⇧Fn keys

        d5 = {
            #
            r"F1": "\033O" "P",  # ⎋OP
            r"F2": "\033O" "Q",  # ⎋OQ
            r"F3": "\033O" "R",  # ⎋OR
            r"F4": "\033O" "S",  # ⎋OS
            r"F5": "\033[" "15~",  # ⎋[15⇧~
            r"F6": "\033[" "17~",  # ⎋[17⇧~
            r"F7": "\033[" "18~",  # ⎋[18⇧~
            r"F8": "\033[" "19~",  # ⎋[19⇧~
            r"F9": "\033[" "20~",  # ⎋[20⇧~
            r"F10": "\033[" "21~",  # ⎋[21⇧~
            r"F11": "\033[" "23~",  # ⎋[23⇧~  # Apple takes F11
            r"F12": "\033[" "24~",  # ⎋[24⇧~
            #
            # r"⇧F1": ...  # macOS Terminal defaults to block ⇧F1 ⇧F2 ⇧F3 ⇧F4
            # r"⇧F2": ...
            # r"⇧F3": ...
            # r"⇧F4": ...
            r"⇧F5": "\033[" "25~",  # ⎋[25⇧~
            r"⇧F6": "\033[" "26~",  # ⎋[26⇧~
            r"⇧F7": "\033[" "28~",  # ⎋[28⇧~
            r"⇧F8": "\033[" "29~",  # ⎋[29⇧~
            r"⇧F9": "\033[" "31~",  # ⎋[31⇧~
            r"⇧F10": "\033[" "32~",  # ⎋[32⇧~
            r"⇧F11": "\033[" "33~",  # ⎋[33⇧~
            r"⇧F12": "\033[" "34~",  # ⎋[34⇧~
        }

        for k, v in d5.items():
            assert k not in decode_by_kseq.keys(), (k,)
            decode_by_kseq[k] = v

        # Add more ⌃⌥⇧ Shiftings of Fn Keys

        d6 = {
            r"⌥F6": d5["F11"],
        }

        for k, v in d6.items():
            assert k not in decode_by_kseq.keys(), (k,)
            decode_by_kseq[k] = v

    #
    # Index the Keycap Sequences by their Decodes
    #

    OptionAccents = ("`", "´", "¨", "ˆ", "˜")  # ⌥⇧` ⌥⇧E ⌥⇧U ⌥⇧I ⌥⇧N
    OptionGraveGrave = "``"  # ⌥⇧` `

    def _invert_decode_by_kseq_(self) -> None:
        """Index the Keycap Sequences by their Decodes"""

        decode_by_kseq = self.decode_by_kseq
        kseqs_by_text = self.kseqs_by_text

        # Index the Sequences collected by now

        d = collections.defaultdict(list)
        for kseq, text in decode_by_kseq.items():
            d[text].append(kseq)

        # Add the ⌥ variants of Non-Blank Printable US-Ascii

        plain_printables = r"""
            -!"#$%&'()*+,-./
            0123456789:;<=>?
            @ABCDEFGHIJKLMNO
            PQRSTUVWXYZ[\]^_
            `abcdefghijklmno
            pqrstuvwxyz{|}~
        """

        assert "" == "\uf8ff"  # U+F8FF  # also tested by ._try_unicode_source_texts_

        option_printables = r"""
            ¥⁄Æ‹›ﬁ‡æ·‚°±≤–≥÷
            º¡™£¢∞§¶•ªÚ…¯≠˘¿
            €ÅıÇÎ´Ï˝ÓˆÔÒÂ˜Ø
            ∏Œ‰Íˇ¨◊„˛Á¸“«‘ﬂ—
            ¥å∫ç∂¥ƒ©˙¥∆˚¬µ¥ø
            πœ®ß†¥√∑≈¥Ω”»’¥
        """

        assert len(plain_printables) == len(option_printables)

        for plain, option in zip(plain_printables, option_printables):
            if option in ("\n", " ", "¥"):
                continue

            assert option not in plain_printables, (option,)

            kseq = "⌥" + d[plain][0]
            text = option

            assert kseq not in decode_by_kseq.keys(), (kseq,)
            decode_by_kseq[kseq] = text

            d[text].append(kseq)

            # ⌥Y comes through as the U+005C Reverse-Solidus, not U+00A5 ¥ Yen-Sign

        assert option_printables.count("¥") == 8  # ⌥␢ ⌥E ⌥I ⌥N ⌥U ⌥Y ⌥` ⌥⌫

        option_kseq_by_text = {  # upper "j́" is "J́" len 2 decode, led by plain U+004A 'J'
            # ⌥E
            "á": "⌥E A",  # ⌥⇧Y is Á is ⌥E ⇧A
            "é": "⌥E E",
            "í": "⌥E I",  # ⌥⇧S is Í is ⌥E ⇧I
            "j́": "⌥E J",  # len 2 decode, led by plain U+006A 'j'
            "ó": "⌥E O",  # ⌥⇧H is Ó is ⌥E ⇧O
            "ú": "⌥E U",
            "´": "⌥⇧E",
            # ⌥I
            "â": "⌥I A",  # ⌥⇧M is Â is ⌥I ⇧A
            "ê": "⌥I E",
            "î": "⌥I I",  # ⌥⇧D is Î is ⌥I ⇧I
            "ô": "⌥I O",  # ⌥⇧J is Ô is ⌥I ⇧O
            "û": "⌥I U",
            "ˆ": "⌥⇧I",
            # ⌥N
            "ã": "⌥N A",
            "ñ": "⌥N N",
            "õ": "⌥N O",
            "˜": "⌥⇧N",
            # ⌥U
            "ä": "⌥U A",
            "ë": "⌥U E",
            "ï": "⌥U I",  # ⌥⇧F is ï is ⌥U ⇧I
            "ö": "⌥U O",
            "ü": "⌥U U",
            "ÿ": "⌥U Y",
            "¨": "⌥⇧U",
            # ⌥`
            "à": "⌥` A",
            "è": "⌥` E",
            "ì": "⌥` I",
            "ò": "⌥` O",  # ⌥⇧L is Ò is ⌥` ⇧O
            "ù": "⌥` U",
            "``": "⌥` `",  # len 2 decode, two copies of plain U+0060 ` Grave Accent
            "`": "⌥⇧`",  # the U+0060 ` Grave Accent keycapped as ` and ⌥⇧`
        }

        for text, kseq in option_kseq_by_text.items():

            if kseq in decode_by_kseq.keys():
                assert decode_by_kseq[kseq] == text, (decode_by_kseq[kseq], text, kseq)
            else:
                decode_by_kseq[kseq] = text
                d[text].append(kseq)

            if " " in kseq:
                ks = kseq[:-1] + "⇧" + kseq[-1:]
                dc = text.upper()  # 'Á' from 'á'
                if dc != text:

                    if ks in decode_by_kseq.keys():
                        assert decode_by_kseq[ks] == dc, (decode_by_kseq[ks], dc, ks)
                    else:
                        decode_by_kseq[ks] = dc
                        d[dc].append(ks)

        # Add the "Use Option as Meta key" of macOS Terminal

        for code in range(0, 0x7F + 1):
            if code not in (0, 0x1E):  # ⎋⌃␢ and ⎋⌃⇧@ and ⎋⌃⇧^ don't
                text = chr(code)

                kseqs = tuple(d[text])
                for kseq in kseqs:
                    assert " " not in kseq, (kseq,)

                    alt_kseq = "⎋" + kseq  # '⎋␢'
                    alt_decode = "\033" + text

                    assert alt_kseq not in decode_by_kseq.keys(), (alt_kseq,)
                    decode_by_kseq[alt_kseq] = alt_decode

                    d[alt_decode].append(alt_kseq)

                    # ⎋B hides behind ⌥←, ⎋F hides behind ⌥→

        kseqs = ("⇧⇥", "↑", "↓", "→", "←")
        for kseq in kseqs:
            assert " " not in kseq, (kseq,)
            text = decode_by_kseq[kseq]

            alt_kseq = "⎋" + kseq  # '⎋␢'
            alt_decode = "\033" + text

            assert alt_kseq not in decode_by_kseq.keys(), (alt_kseq,)
            decode_by_kseq[alt_kseq] = alt_decode

            d[alt_decode].append(alt_kseq)

            # ⎋← hides behind ⎋B behind ⌥←, ⎋→ hides behind ⎋F behind ⌥→

        # Convert to immutable Tuples from mutable Lists

        for text, kseq_list in d.items():
            assert text not in kseqs_by_text, (text, kseqs_by_text[text], kseq_list)
            kseqs_by_text[text] = tuple(kseq_list)

        # no explicit mention of ÁÉÍJ́ÓÚ ÂÊÎÔÛ ÃÑÕ ÄËÏÖÜŸ ÀÈÌÒÙ


_FactorMark_ = "\025"  # 01/05 ⌃U Emacs Global-Map Universal-Argument

ClassicArrows = ("\033[A", "\033[B", "\033[C", "\033[D")

_NorthArrow_ = "\033[A"  # ←↑→↓ reordered as ↑↓→←
_SouthArrow_ = "\033[B"
_EastArrow_ = "\033[C"
_WestArrow_ = "\033[D"

CPR_Y_X = "\033[" "{};{}R"  # ⎋[y;x⇧R

DSR0 = "\033[" "0n"  # DSR_PS Ps 0

_NorthwestArrow_ = "\033[↖"  # ⎋ [ ↖↗↘↙  # not yet standard
_NortheastArrow_ = "\033[↗"
_SoutheastArrow_ = "\033[↘"
_SouthwestArrow_ = "\033[↙"


#
# Try KeyByteFrame things
#


def _try_key_byte_frame_() -> None:

    assert DL_Y == "\033[" "{}M"
    assert _CLICK3_ == "\033[M"
    assert _NorthArrow_ == "\033[A"
    assert ST == "\033\134"
    assert _NortheastArrow_ == "\033[↗"

    # Do nothing with grace & elegance

    KeyByteFrame(b"")

    # Speak well of ↑ and ⎋↑

    f = KeyByteFrame(b"\033[A")
    assert f.to_frame_bytes() == b"\033[A", (f,)
    assert f.closed, (f,)

    f = KeyByteFrame(b"\033\033[A")
    assert f.to_frame_bytes() == b"\033\033[A", (f,)
    assert f.closed, (f,)

    # Dance well with the _CLICK3_ clash into DL_Y without Pn

    f = KeyByteFrame(b"\033[M")
    assert f.to_frame_bytes() == b"\033[M", (f,)
    assert not f.closed, (f,)  # because could be ⎋[⇧M{b}{x}{y}

    f = KeyByteFrame(b"\033[Mabc")
    assert f.to_frame_bytes() == b"\033[Mabc", (f,)
    assert f.closed, (f,)

    f = KeyByteFrame(b"\033[Mab\xff")
    assert f.to_frame_bytes() == b"\033[Mab\xff", (f,)
    assert f.closed, (f,)

    # Accept 8-way Compass Arrows, not just the 4-way Most Classic Arrows

    f = KeyByteFrame("\033[↗".encode())  # not yet standard
    assert f.to_frame_bytes() == "\033[↗".encode(), (f,)
    assert f.closed, (f,)

    # Accept the ⎋\ String Terminator (ST) to close an ⎋] Osc Frame

    f = KeyByteFrame(b"\033]11;?\033\\")
    assert f.to_frame_bytes() == b"\033]11;?\033\\", (f,)
    assert f.closed, (f,)

    #
    # todo: port in more KeyByteFrame tests from ._try_key_pack_ of
    #   https://github.com/pelavarre/less-beeps/blob/1009pl/bin/less-beeps.py
    #


#
# Amp up Import ArgParse
#


_ARGPARSE_3_10_ = (3, 10)  # Oct/2021 Python 3.10, like from Ubuntu 2022


@dataclasses.dataclass(order=True)  # , frozen=True)
class ArgDocParser:
    """Scrape Prog & Description & Epilog from Doc to form an ArgParse Argument Parser"""

    doc: str  # a copy of parser.format_help()
    add_help: bool  # truthy to define '-h, --help', else not

    parser: argparse.ArgumentParser  # the inner standard ArgumentParser
    text: str  # something like the __main__.__doc__, but dedented and stripped
    closing: str  # the last Graf of the Epilog, minus its Top Line

    add_argument: collections.abc.Callable[..., object]

    def __init__(self, doc: str, add_help: bool) -> None:

        self.doc = doc
        self.add_help = add_help

        text = textwrap.dedent(doc).strip()

        prog = self._scrape_prog_(text)
        description = self._scrape_description_(text)
        epilog = self._scrape_epilog_(text, description=description)
        closing = self._scrape_closing_(epilog)

        parser = argparse.ArgumentParser(  # doesn't distinguish Closing from Epilog
            prog=prog,
            description=description,
            add_help=add_help,
            formatter_class=argparse.RawTextHelpFormatter,  # lets Lines be wide
            epilog=epilog,
        )

        self.parser = parser
        self.text = text
        self.closing = closing

        self.add_argument = parser.add_argument

        # 'add_help=False' for needs like 'cal -h', 'df -h', 'du -h', 'ls -h', etc

        # callers who need Options & Positional Arguments have to add them

    #
    # Take in the Shell Args, else print Help and exit zero or nonzero
    #

    def parse_args_if(self, args: list[str]) -> argparse.Namespace:
        """Take in the Shell Args, else print Help and exit zero or nonzero"""

        parser = self.parser
        closing = self.closing

        # Print Diffs & exit nonzero, when Arg Doc wrong

        diffs = self._diff_doc_vs_format_help_()
        if diffs:
            if sys.version_info >= _ARGPARSE_3_10_:
                print("\n".join(diffs))

                sys.exit(2)  # exits 2 for wrong Args in Help Doc

            # takes 'usage: ... [HINT ...]', rejects 'usage: ... HINT [HINT ...]'
            # takes 'options:', rejects 'optional arguments:'
            # takes '-F, --isep ISEP', rejects '-F ISEP, --isep ISEP'

        # Print Closing & exit zero, if no Shell Args

        if not args:
            print()
            print(closing)
            print()

            sys.exit(0)  # exits 0 after printing Closing

        # Drop the "--" Shell Args Separator, if present,
        # because 'ArgumentParser.parse_args()' without Pos Args wrongly rejects it

        shargs = list(args)
        if len(args) == 1:  # because ArgParse chokes if '--' Sep present without Pos Args
            if args[0] == "--":
                shargs.clear()

        # Print help lines & exit zero, else return Parsed Args

        ns = parser.parse_args(shargs)

        return ns

        # often prints help & exits zero

    #
    # Scrape out Parser, Prog, Description, Epilog, & Closing from Doc Text
    #

    def _scrape_prog_(self, text: str) -> str:
        """Pick the Prog out of the Usage Graf that starts the Doc"""

        lines = text.splitlines()
        prog = lines[0].split()[1]  # second Word of first Line  # 'prog' from 'usage: prog'

        return prog

    def _scrape_description_(self, text: str) -> str:
        """Take the first Line of the Graf after the Usage Graf as the Description"""

        lines = text.splitlines()

        firstlines = list(_ for _ in lines if _ and (_ == _.lstrip()))
        docline = firstlines[1]  # first Line of second Graf

        description = docline
        if self._docline_is_skippable_(docline):
            description = "just do it"

        return description

    def _scrape_epilog_(self, text: str, description: str) -> str:
        """Take up the Lines past Usage, Positional Arguments, & Options, as the Epilog"""

        lines = text.splitlines()

        epilog = ""
        for index, line in enumerate(lines):
            if self._docline_is_skippable_(line) or (line == description):
                continue

            epilog = "\n".join(lines[index:])
            break

        return epilog  # maybe empty

    def _docline_is_skippable_(self, docline: str) -> bool:
        """Guess when a Doc Line can't be the first Line of the Epilog"""

        strip = docline.rstrip()

        skippable = not strip
        skippable = skippable or strip.startswith(" ")  # includes .startswith("  ")
        skippable = skippable or strip.startswith("usage")
        skippable = skippable or strip.startswith("positional arguments")
        skippable = skippable or strip.startswith("options")  # ignores "optional arguments"

        return skippable

    def _scrape_closing_(self, epilog: str) -> str:
        """Pick out the last Graf of the Epilog, minus its Top Line"""

        lines = epilog.splitlines()

        indices = list(_ for _ in range(len(lines)) if lines[_])  # drops empty Lines
        indices = list(_ for _ in indices if not lines[_].startswith(" "))  # finds top Lines

        closing = ""
        if indices:
            index = indices[-1] + 1

            join = "\n".join(lines[index:])  # last Graf, minus its Top Line
            dedent = textwrap.dedent(join)
            closing = dedent.strip()

        return closing  # maybe empty

    #
    # Form Diffs from Help Doc to Parser Format_Help
    #

    def _diff_doc_vs_format_help_(self) -> list[str]:
        """Form Diffs from Help Doc to Parser Format_Help"""

        text = self.text
        parser = self.parser

        # Say where the Help Doc came from

        a = text.splitlines()

        basename = os.path.split(__file__)[-1]
        fromfile = "{} --help".format(basename)

        # Fetch the Parser Doc from a fitting virtual Terminal
        # Fetch from a Black Terminal of 89 columns, not from the current Terminal Width
        # Fetch from later Python of "options:", not earlier Python of "optional arguments:"

        with_columns_else = os.environ.get("COLUMNS", default_eq_None)  # checkpoints
        with_no_color_else = os.environ.get("NO_COLOR", default_eq_None)  # checkpoints

        os.environ["COLUMNS"] = str(89)  # adds or replaces
        os.environ["NO_COLOR"] = "True"  # adds or replaces

        try:

            b_text = parser.format_help()

        finally:

            if with_no_color_else is None:
                del os.environ["NO_COLOR"]  # removes
            else:
                os.environ["NO_COLOR"] = with_no_color_else  # reverts

            if with_columns_else is None:
                del os.environ["COLUMNS"]  # removes
            else:
                os.environ["COLUMNS"] = with_columns_else  # reverts

        b = b_text.splitlines()

        tofile = "ArgumentParser(...)"

        # Form >= 0 Diffs from Help Doc to Parser Format_Help,
        # but ask for lineterm="", for else the '---' '+++' '@@' Diff Control Lines end with '\n'

        diffs = list(difflib.unified_diff(a=a, b=b, fromfile=fromfile, tofile=tofile, lineterm=""))

        # Succeed

        return diffs

        # .parser.format_help defaults to color its texts, since Oct/2025 Python 3.14


#
# Amp up Import BuiltIns Bytes
#


@dataclasses.dataclass(order=True, frozen=True)
class BytesBox:

    data: bytes

    def __bool__(self) -> bool:
        return bool(self.data)

    @functools.cached_property
    def text(self) -> str:
        """The Text Decode of the Bytes, if decodable, else an Empty Str"""

        try:
            text = self.data.decode()
            return text
        except UnicodeDecodeError:
            return ""

    @functools.cached_property
    def nearly_printable(self) -> bool:
        """Say if the Text exactly matches the Repr minus Quotes"""

        data = self.data
        text = self.text

        if not data:
            assert not text, (data, text)
            return True

        if not text:
            return False

        printable = text.replace("", "-").isprintable()

        return printable

        # todo: shrink the distribution of '.replace("", "-").isprintable'


#
# Amp up Import BuiltIns Float
#


def chop(f: float) -> str:
    """Find a nonzero Float Literal closer to zero with <= 3 Digits"""

    if not f:
        lit = "-0e0" if (math.copysign(1e0, f) < 0e0) else "0"
        return lit

    s = ("-" + _chop_nonnegative_(-f)) if (f < 0) else _chop_nonnegative_(f)

    return s

    # never says '0' except to mean Float +0e0 and Int 0
    # values your ink & time properly, by never saying '.' nor '.0' nor '.00' nor 'e+0'


def _chop_nonnegative_(f: float) -> str:
    """Find a nonnegative nonzero Float Literal closer to zero with <= 3 Digits"""

    assert f > 0, (f,)

    # Form the Scientific Notation

    sci = int(math.floor(math.log10(f)))
    mag = f / (10**sci)
    assert 1 <= mag < 10, (mag, f)

    # Choose a Floor, in the way of Engineering Notation

    triple = str(int(100 * mag))  # 100 == 10 ** 2
    assert "100" <= triple <= "999", (triple, mag, sci, f)

    eng = 3 * (sci // 3)  # ..., -6, -3, 0, 3, 6, ...
    span = 1 + sci - eng
    assert 1 <= span <= 3, (span, triple, mag, eng, sci, f)

    # Stand on the chosen Floor, but never say '.' nor '.0' nor '.00'

    dotted = triple[:span] + "." + triple[span:]
    dotted = dotted.rstrip("0").rstrip(".")  # lacks '.' if had only '.' or'.0' or '.00'

    # And never say 'e0' either

    lit = str_removesuffix(f"{dotted}e{eng}", suffix="e0")  # may lack both '.' and 'e'

    # But never wander far

    float_lit = float(lit)

    diff = f - float_lit
    precision = 10 ** (eng - 3 + span)
    assert diff < precision, (f, sci, mag, triple, eng, span, dotted, lit, diff, precision)

    return lit

    # Python math.trunc is a round towards zero, but can be zero, and leaps to the int ceil/ floor


def _try_chop_() -> None:

    pairs = [
        (0, "0"),
        (0e0, "0"),
        (-0e0, "-0e0"),
        #
        (1e-4, "100e-6"),
        (1e-3, "1e-3"),
        (1.2e-3, "1.2e-3"),
        (9.876e-3, "9.87e-3"),  # not '9.88e-3'
        (1e-2, "10e-3"),
        (1e-1, "100e-3"),
        #
        (1e0, "1"),
        (1e1, "10"),
        (1.2e1, "12"),
        (9.876e1, "98.7"),  # not '98.8'
        (1e2, "100"),
        (1.23e2, "123"),
        #
        (1e3, "1e3"),
        #
    ]

    for f, lit in pairs:

        chop_f = chop(f)
        assert chop_f == lit, (chop_f, lit, f"{f:.2e}", f)

        if f:
            chop_minus_f = chop(-f)
            assert chop_minus_f == (f"-{lit}"), (chop_f, lit, f"{f:.2e}", f)


#
# Amp up Import BuiltIns Str
#


def str_removeprefix(text: str, prefix: str) -> str:
    """Remove a Prefix, if present"""

    if text.startswith(prefix):
        text = text[len(prefix) :]

    return text


def str_removesuffix(text: str, suffix: str) -> str:
    """Remove a Suffix, if present"""

    if text.endswith(suffix):
        text = text[: -len(suffix)]

    return text


#
# Amp up Import Traceback
#


assert sys.__stderr__ is not None  # refuses to run headless
with_stderr = sys.stderr


assert int(0x80 + signal.SIGINT) == 130  # discloses the Nonzero Exit Code for after ⌃C SigInt


def excepthook(  # ) -> ...:
    exc_type: type[BaseException] | None,  # aka .type
    exc_value: BaseException | None,  # aka .exc_obj aka .value
    exc_traceback: types.TracebackType | None,  # aka .exc_tb aka .traceback aka .tb
) -> None:
    """Run at Process Exit"""

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

            # todo: figure out when this does and doesn't happen

    if exc_traceback is not None:
        if not hasattr(sys, "last_traceback"):
            setattr(sys, "last_traceback", exc_traceback)  # ducks out of confusing pdb.pm()

            # todo: figure out when this does and doesn't happen

    print(">" ">" "> pdb.pm()", file=with_stderr)  # (3 * ">") spelled unlike a Git Conflict
    pdb.pm()


#
# Amp up Import UnicodeData
#
# P=litglass.py && cat $P |python3 -c 'import sys; print(repr("".join(sorted(set(sys.stdin.read())))))'
#


def _try_unicode_source_texts_() -> None:
    """Explicitly don't limit our Source Text to US-Ascii"""

    # not yet an official standard

    assert "" == "\uf8ff"  # U+F8FF  # last of U+E000 .. U+F8FF Private Use Area (PUA)

    # 2 Comic Colors from Apr/2008 Unicode 5.1

    assert unicodedata.name("⬛").title() == "Black Large Square"  # U+2B1B  # 000 16
    assert unicodedata.name("⬜").title() == "White Large Square"  # U+2B1C  # 444 188

    # 7 Comic Colors from Mar/2019 Unicode 12.0

    assert unicodedata.name("🟥").title() == "Large Red Square"  # U+1F7E5  # 500 196
    assert unicodedata.name("🟦").title() == "Large Blue Square"  # U+1F7E6  # 015 27
    assert unicodedata.name("🟨").title() == "Large Yellow Square"  # U+1F7E8  # 430 178
    assert unicodedata.name("🟩").title() == "Large Green Square"  # U+1F7E9  # 020 28
    assert unicodedata.name("🟪").title() == "Large Purple Square"  # U+1F7EA  # 205 93
    assert unicodedata.name("🟧").title() == "Large Orange Square"  # U+1F7EB  # 520 208
    assert unicodedata.name("🟫").title() == "Large Brown Square"  # U+1F7EB  # 100 52

    #
    # The Apple ⌥ Option/Alt Keys send lots of printable U+00A1 .. U+00FF
    #
    #   ÀÁÂÃÄÅ Æ ÈÉÊË ÌÍÎÏ Ñ ÒÓÔÕÖ Ø ÙÚÛÜ àáâãäå æ èéêë ìíîï ñ òóôõö ùúûü ÿ
    #
    # but not
    #
    #   chr(0x00A4)  # "¤"  # Currency Sign
    #   chr(0x00A6)  # "¦"  # Broken Bar
    #
    #   chr(0x00B2)  # "²"  # Superscript Two
    #   chr(0x00B3)  # "³"  # Superscript Three
    #   chr(0x00B9)  # "¹"  # Superscript One
    #   chr(0x00BC)  # "¼"  # Vulgar Fraction One Quarter
    #   chr(0x00BD)  # "½"  # Vulgar Fraction One Half
    #   chr(0x00BE)  # "¾"  # Vulgar Fraction Three Quarters
    #
    #   chr(0x00D0)  # "Ð"  # Latin Capital Letter Eth
    #   chr(0x00D7)  # "×"  # Multiplication Sign
    #   chr(0x00DD)  # "Ý"  # Latin Capital Letter Y With Acute
    #   chr(0x00DE)  # "Þ"  # Latin Capital Letter Thorn
    #
    #   chr(0x00F0)  # "ð"  # Latin Small Letter Eth
    #   chr(0x00FD)  # "ý"  # Latin Small Letter Y With Acute
    #   chr(0x00FE)  # "þ"  # Latin Small Letter Thorn
    #

    #
    # The Apple MacBook Keyboard
    #
    #   does send its ← ↑ → ↓ keys classically encoded as ⎋[⇧D ⎋[⇧A ⎋[⇧C ⎋[⇧B
    #   doesn't send its ↖ ↗ ↘ ↙ double key jams encoded as ⎋ [ U+2196..U+2199 Diagonal Arrows
    #
    # June/1993 Unicode 1.1.0 gave us ↖ ↗ ↘ ↙, among its U+2190 .. U+219F Symbols And Arrows
    #

    #
    # We run no Tests of Unicode U+2588, U+FB01, & U+FB02, not here in 2025
    #
    #   █ ██ ﬁ ﬂ
    #
    # We run no Tests of Unicode U+0131 .. U+25CA
    #
    #   ıŒœŸƒˆˇ˘˙˚˛˜˝́Ωπ–—‘’‚“”„†‡•…‰‹›⁄€™←↑→↓⇥⇧⇪∂∆∏∑√∞∫≈≠≤≥⌃⌘⌥⌫⎋⏎␢◊
    #
    # We run no Tests of Unicode U+00A1 .. U+00F8
    #
    #   ¡¢£¥§¨©ª«¬®¯°±´µ¶·¸º»¿Çßç÷ø
    #

    #
    # macOS Terminal Themes  # todo5: survey Color & Highlight via Osc 10 11
    #
    #   Basic
    #   Grass
    #   Homebrew
    #   Man Page
    #   Novel
    #   Ocean
    #   Pro
    #   Red Sands
    #   Silver Aerogel
    #   Solid Colors
    #


#
# Cite some Terminal Escape & Control Sequence Docs
#


_ = """  # our top choices

    https://unicode.org/charts/PDF/U0000.pdf
    https://unicode.org/charts/PDF/U0080.pdf

    https://en.wikipedia.org/wiki/ANSI_escape_code
    https://jvns.ca/blog/2025/03/07/escape-code-standards

    https://invisible-island.net/xterm/ctlseqs/ctlseqs.html

    https://www.ecma-international.org/publications-and-standards/standards/ecma-48
        /wp-content/uploads/ECMA-48_5th_edition_june_1991.pdf

"""

_ = """  # more breadth found via https://jvns.ca/blog/2025/03/07/escape-code-standards

    https://github.com/tmux/tmux/blob/master/tools/ansicode.txt  <= close to h/t jvns.ca
    https://man7.org/linux/man-pages/man4/console_codes.4.html
    https://sw.kovidgoyal.net/kitty/keyboard-protocol
    https://vt100.net/docs/vt100-ug/chapter3.html

    https://iterm2.com/feature-reporting
    https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
    https://github.com/Alhadis/OSC8-Adoption?tab=readme-ov-file

"""

_ = """  # more famous Python Imports to run in place of our Code here

    curses — Terminal handling for character-cell displays
    https://docs.python.org/3/library/curses.html for 'import curses'

    tkinter — Python interface to Tcl/Tk
    https://docs.python.org/3/library/tkinter.html

    turtle — Turtle graphics
    https://docs.python.org/3/library/turtle.html for 'import turtle'

"""


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# todo8: drop Keycaps specific to macOS Terminal, when elsewhere
# todo8: add iTerm2 Keycaps
# todo8: add Google Cloud Shell Keycaps


# todo9: take bracketed-paste as print vertically
# todo9: take unbracketed-paste as print vertically to left of rightmost tracked chars


# todo9: --egg=keycaps: add Keycaps of 8 at ⌃ ⌥ ⇧ including the Fn, 8 more at ⎋
# todo9: --egg=resize to fit the Terminal to the Gameboard and vice versa

# todo9: pick apart text key jams and unbracketed text paste

# todo9: show settings
# todo9: place input echoes on the side
# todo9: vs scroll while echo of ScreenChangeOrder's in the far Southeast


# 3456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/litglass.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
