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


Apple = "\uf8ff"  # Apple  occupies U+F8FF = last of U+E000 .. U+F8FF Private Use Area (PUA)

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
    i_term_app: bool = os.environ.get("TERM_PROGRAM", "") == "iTerm.app"
    ghostty: bool = os.environ.get("TERM_PROGRAM", "") == "ghostty"

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
    color_picker: bool = False  # show Color Choices and tweak them
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

    lg = LitGlass()

    try:
        lg.try_main()
    except BaseException:  # KeyboardInterrupt  # SystemExit
        # TerminalBoss.selves[-1].__exit__()  # todo6:
        excepthook(*sys.exc_info())


class LitGlass:
    """Run from the Shell, but tell uncaught Exceptions to launch the Py Repl"""

    def try_main(self) -> None:
        """Run from the Shell, but tell uncaught Exceptions to launch the Py Repl"""

        naive = dt.datetime.now()

        parser = self.arg_doc_to_parser(__main__.__doc__ or "")
        ns = self.shell_args_take_in(args=sys.argv[1:], parser=parser)

        if flags.logging:  # writes into:  tail -F __pycache__/litglass.log
            self.logging_resume()

        if ns.force:
            self.try_lit_glass()

        seed = self.shell_args_take_in_seed(ns.seed, naive=naive)

        with TerminalBoss(seed) as tb:
            self.logger_info_replay(seed, naive=naive)

            if flags._assert_:
                assert False, "Asserting False before doing much"

            cpg = ColorPickerGame(tb)
            kcg = KeycapsGame(tb)
            sqg = SquaresGame(tb)

            if flags.byteloop:
                tb.tb_run_byteloop()
            elif flags.color_picker:
                cpg.cp_run_awhile()
            elif flags.keycaps:
                kcg.kc_run_awhile()
            elif flags.squares:
                sqg.sq_run_awhile()
            else:
                tb.tb_run_awhile()

    def logging_resume(self) -> None:
        """Open up a new Logging Session at our .logger"""

        os.makedirs("__pycache__", exist_ok=True)

        logging.basicConfig(
            filename="__pycache__/litglass.log",  # appends, doesn't restart
            level=logging.INFO,  # .INFO and above
            format="%(message)s",  # omits '%(levelname)s:%(name)s:'
        )

        logger_print("")
        logger_print("")
        logger_print("launched")
        logger_print("")

        #
        # default Python .logging
        #
        #       drops many .INFO, .DEBUG, .NOTSET as < 30 .WARNING - # secretly, silently, uncountably
        #       tags many lines at left with like 'INFO:__main__:'
        #

    def arg_doc_to_parser(self, doc: str) -> ArgDocParser:
        """Declare the Positional Arguments & Options"""

        parser = ArgDocParser(doc, add_help=True)

        force_help = "ask fewer questions (like do run slow self-test's)"
        seed_help = "a chosen seed for pseudorandom choices (like to replay a game)"
        egg_help = "a hint of how to behave, such as 'repr' or 'sigint'"

        parser.add_argument("-f", "--force", action="count", help=force_help)
        parser.add_argument("--seed", dest="seed", help=seed_help)
        parser.add_argument("--egg", dest="eggs", metavar="EGG", action="append", help=egg_help)

        return parser

    def shell_args_take_in(self, args: list[str], parser: ArgDocParser) -> argparse.Namespace:
        """Take in the Shell Command-Line Args"""

        ns = parser.parse_args_if(args)  # often prints help & exits zero
        print_usage = parser.parser.print_usage

        ns_keys = list(vars(ns).keys())
        assert ns_keys == ["force", "seed", "eggs"], (ns_keys, ns, args)

        self.shell_args_take_in_eggs(ns.eggs, print_usage=print_usage)

        games = flags.games
        if games or ns.force:
            flags.logging = True

        return ns

    def shell_args_take_in_eggs(
        self, eggs: list[str] | None, print_usage: typing.Callable[[], None]
    ) -> None:
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

        # todo9: is -f to --force a correction worth printing?

    def shell_args_take_in_seed(self, seed: str | None, naive: dt.datetime) -> str:
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

    def logger_info_replay(self, seed: str, naive: dt.datetime) -> None:
        """Log restarting/ starting from --seed=SEED"""

        t = dt.datetime.fromisoformat(seed)
        strftime = t.strftime("%Y-%m-%d %H:%M:%S")

        shargs = list()

        sharg = self.seed_to_sharg_near_naive(seed, naive=naive)
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
        logger_print("")
        logger_print(f"python3 litglass.py {join}")

    def seed_to_sharg_near_naive(self, seed: str, naive: dt.datetime) -> str:
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

    def try_lit_glass(self) -> None:
        """Run slow and quick Self-Test's of this Module"""

        t0 = time.time()

        _try_chop_()
        _try_keyboard_decoder_()
        _try_key_byte_frame_()
        _try_unicode_source_texts_()

        t1 = time.time()
        t1t0 = t1 - t0
        logger_print(f"spent {chop(t1t0)}s on self-test")


#
# Play for --egg=color-picker
#


class ColorPickerGame:
    """Play for --egg=color-picker"""

    terminal_boss: TerminalBoss

    game_yx: tuple[int, ...]

    red: int  # 0..5
    green: int  # 0..5
    blue: int  # 0..5

    focus_int: int  # 0, 1, or 2

    def __init__(self, terminal_boss: TerminalBoss) -> None:

        self.terminal_boss = terminal_boss

        self.game_yx = tuple()

        self.red = 2
        self.green = 3
        self.blue = 2

        self.focus_int = 1  # 1 is middle

    def cp_run_awhile(self) -> None:
        """Trace Key Releases till ⌃C"""

        tb = self.terminal_boss

        sw = tb.screen_writer
        kr = tb.keyboard_reader

        # Place & draw the Gameboard, scrolling if need be

        assert not self.game_yx, (self.game_yx,)
        game_yx = self.cp_game_draw(first=True)
        assert game_yx, (game_yx,)

        self.game_yx = game_yx  # replaces

        # Run till Quit

        while not tb.quitting:

            # Read Input

            kr.kbhit(timeout=None)
            frames = tb.tb_read_byte_frames()

            # Eval Input and print Output

            self.cp_step_once(frames)

        sw.print()

    def cp_game_draw(self, first: bool) -> tuple[int, ...]:
        """Draw the Gameboard, scrolling if need be"""

        tb = self.terminal_boss
        sw = tb.screen_writer
        kr = tb.keyboard_reader

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

        if game_yx:
            (y, x) = game_yx
            sw.write_control(f"\033[{y};{x}H")

        # Form the Board

        ns = 3 * len("5 ") * " "
        i = focus_int * len("5 ")
        j = i + len("5 ")

        gap = len("rgb color ") * " "
        n = ns[:i] + "↑ " + ns[j:]
        s = ns[:i] + "↓ " + ns[j:]

        y_high = 0

        # Draw above the Board

        sw.write_control("\033[39m")  # todo3: checkpoint & revert ⎋[M

        sw.print()
        sw.print()  # twice

        sw.print(dent + gap + n + dent)
        sw.print()
        sw.print(dent + f"rgb color {r} {g} {b} is {ps=}" + dent)
        sw.print()
        sw.print(dent + gap + s + dent)

        sw.print()
        sw.print()  # twice

        y_high += 2 + 5 + 2

        # Draw the Board per se

        sw.write_control(f"\033[38;5;{ps}m")

        for _ in range(3):
            sep = "\033[2C"
            text = dent + "█" + sep + "██" + sep + "███" + sep + "██" + sep + "█" + dent + "\r\n"
            sw.write_text(text)

        y_high += 3

        # Draw below the Board

        sw.write_control("\033[39m")

        sw.print()

        sw.print("Press ⌃C")
        sw.print()

        y_high += 1 + 2

        # Place the Board

        if first:
            (h, w, y, x) = kr.sample_hwyx()
            y -= y_high
            game_yx = (y, x)  # replaces

        # Revert to TerminalBoss Cursor, but change which Color it draws

        sw.write_control(f"\033[38;5;{ps}m")

        if not first:
            (ya, xa) = (kr.row_y, kr.column_x)
            sw.write_control(f"\033[{ya};{xa}H")

        return game_yx

        # todo: call ScreenWriter Def's to checkpoint & revert Color, Backlight, Cursor
        # todo: Cursor Position as tuple[int, int], or as tuple[int, ..], or as int & int

    def cp_step_once(self, frames: tuple[bytes, ...]) -> None:
        """Eval Input and print Output"""

        tb = self.terminal_boss
        kd = tb.keyboard_decoder

        # Take all plain unmarked classic Arrows here, and nothing else

        note_to_self = True
        for frame in frames:
            echoes = kd.bytes_to_echoes_if(frame)
            echo = echoes[0] if echoes else ""
            if echo not in ("←", "↑", "→", "↓"):
                note_to_self = False
                break

        if note_to_self:
            for frame in frames:
                self.cp_step_one_arrow_once(frame)
            self.cp_game_draw(first=False)
            return

        # Else fall back onto the enclosing TerminalBoss

        tb.tb_step_once(frames)

    def cp_step_one_arrow_once(self, frame: bytes) -> None:
        """Eval one Arrow in the Frame"""

        r = self.red
        g = self.green
        b = self.blue

        focus_int = self.focus_int

        tb = self.terminal_boss
        kd = tb.keyboard_decoder
        echoes = kd.bytes_to_echoes_if(frame)
        echo = echoes[0] if echoes else ""

        assert echo in ("←", "↑", "→", "↓"), (echo,)

        if echo == "←":
            self.focus_int = (focus_int - 1) % 3
        elif echo == "→":
            self.focus_int = (focus_int + 1) % 3
        else:
            diff = -1 if (echo == "↓") else 1
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

    terminal_boss: TerminalBoss
    game_yx: tuple[int, ...]  # Northwest Corner of the Gameboard
    chat_yx: tuple[int, ...]  # Just below the Southwest Corner of the Gameboard
    scrollables: list[str]  # Rows of Messages

    wipeouts_by_shifters: dict[str, list[str]]

    shifters: str
    tangible_keyboard: str
    wipeouts: list[str]  # Key Caps found and wiped, not yet found again and restored

    kc_echo_index: int  # distinguish one input from the next

    MAX_SCROLLABLES_1 = 1

    # Lay out 6 Rows per Keyboard  # todo: measure how high, don't guess

    PlainKeyboard = r"""
        ⎋    F1 F2 F3 F4 F5 F6 F7 F8 F9 F10 F11 F12 <>
        `   1  2  3  4  5  6  7  8  9  0   -   =     ⌫
        ⇥    q  w  e  r  t  y  u  i  o  p   [   ]    \
        ⇪     a  s  d  f  g  h  j  k  l   ;   '      ⏎
        ⇧      z  x  c  v  b  n  m   ,  .  /         ⇧
        Fn  ⌃  ⌥  ⌘   Spacebar    ⌘   ⌥        ← ↑ → ↓
                                                ↖ ↗ ↘ ↙
    """

    ShiftedKeyboard = r"""
        ⎋    F1 F2 F3 F4 F5 F6 F7 F8 F9 F10 F11 F12 <>
        ~   !  @  #  $  %  ^  &  *  (  )   _   +     ⌫
        ⇥    Q  W  E  R  T  Y  U  I  O  P   {   }    |
        ⇪     A  S  D  F  G  H  J  K  L   :   "      ⏎
        ⇧      Z  X  C  V  B  N  M   <  >  ?         ⇧
        Fn  ⌃  ⌥  ⌘   Spacebar    ⌘   ⌥        ← ↑ → ↓
                                                ↖ ↗ ↘ ↙
    """

    # . 123456789 123456789 123456789 123456789 12345678

    #

    def __init__(self, terminal_boss: TerminalBoss) -> None:

        # Form 1 Wipeout Set per Shifting Key Chord

        shifter_by_index = "⎋ ⌃ ⌥ ⇧ Fn".split()
        n = len(shifter_by_index)

        d: dict[str, list[str]] = dict()
        for bitsum in range(2**n):
            _shifters_ = ""
            for i in range(n):
                if bitsum & (1 << i):
                    _shifters_ += shifter_by_index[i]  # ordered conventionally

            d[_shifters_] = list()  # ['']  # ['⎋']  # ['⎋⌃']  # ['⌥']  # ...

        wipeouts_by_shifters = d

        # Init the Fields

        shifters = ""  # none of ⎋ ⌃ ⌥ ⇧

        self.terminal_boss = terminal_boss
        self.game_yx = tuple()
        self.chat_yx = tuple()
        self.scrollables = list()

        self.wipeouts_by_shifters = wipeouts_by_shifters

        self.shifters = shifters
        self.tangible_keyboard = self.kc_tangible_keyboard()
        self.wipeouts = wipeouts_by_shifters[shifters]

        self.kc_echo_index = 0

    def kc_run_awhile(self) -> None:
        """Trace Key Releases till ⌃C"""

        tb = self.terminal_boss

        sw = tb.screen_writer
        kr = tb.keyboard_reader

        # Draw the Gameboard, scrolling if need be

        sw.write_control("\033[?25l")

        game_yx = self.kc_game_draw()
        self.game_yx = game_yx  # replaces

        (h, w, y, x) = kr.sample_hwyx()
        self.chat_yx = (y, x)  # replaces

        # Run till Quit

        while not tb.quitting:

            # Read Input

            kr.kbhit(timeout=None)
            frames = tb.tb_read_byte_frames()

            # Eval Input and print Output

            self.kc_step_once(frames)

        sw.print()

        # todo9: --egg=keycaps: toggle back out of @@@@@@@@@ or @@ or @
        # todo9: --egg=keycaps: take mouse hits to the Keyboard viewed

    def kc_game_draw(self) -> tuple[int, int]:
        """Draw the Gameboard, scrolling if need be"""

        tb = self.terminal_boss
        kr = tb.keyboard_reader

        shifters = self.shifters
        tangible_keyboard = self.tangible_keyboard

        tb = self.terminal_boss
        sw = tb.screen_writer

        assert EL_PS == "\033[" "{}" "K"

        # Schedule tests of ⎋ and ⌃ ⌥ ⇧
        #
        #   todo: make a way to say ⌃⌥⇧ and ⌃⌥ Apple macOS Terminals have no distinct Key Chords
        #
        #   todo: never speak of ⌃⌥⇧ reversed ⇧⌥⌃|⇧⌥|⇧⌃|⌥⌃
        #   todo: never speak of ⌃⌥⇧ shuffled ⌃⇧⌥|⌥⌃⇧|⇧⌃⌥
        #   todo: never speak of ⇧`|⇧-|⇧=|⇧\[|⇧\]|⇧\\|⇧;|⇧'|⇧,|⇧\.|⇧/
        #

        tested_shifters = [""] + "⎋ ⎋⌃ ⎋⌃⇧ ⎋⇧".split() + "⌃ ⌥ ⇧ ⌃⌥ ⌃⇧ ⌥⇧ ⌃⌥⇧".split()
        assert shifters in tested_shifters, (shifters, tested_shifters)

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

        enter = "\033[7m"  # ⎋[7m reverse
        exit = "\033[27m"  # ⎋[27m reverse-not

        exit_caps = self.kc_exit_caps()

        keyboard = tangible_keyboard
        for cap in exit_caps:
            repl = enter + cap + exit
            # assert keyboard.count(cap) == 1, (keyboard.count(cap), cap, shifters)  # todo0:
            keyboard = keyboard.replace(cap, repl)

        dent = 4 * " "
        splitlines = keyboard.splitlines()

        # Print each Row

        sw.print()
        for line in splitlines:
            text = dent + line + dent

            sw.write_text(text)
            sw.write_control("\033[K")
            sw.write_some_controls(["\r", "\n"])

        # Print a Trailer in the far Southeast

        sw.write_control("\033[K")
        sw.write_some_controls(["\r", "\n"])

        sw.print(r"Press ⌃C or ⌃\ or ⌃⇧| or ⌃⌥⇧|")
        sw.print()

        # Succeed

        return (y, x)

        # todo: .kc_game_draw well onto larger & smaller Screens

    def kc_exit_caps(self) -> tuple[str, ...]:
        """Find the Key Caps that will quit the Game"""

        shifters = self.shifters

        exit_caps: tuple[str, ...] = tuple()
        if shifters == "⌃":
            exit_caps = ("C", "\\")
            if flags.i_term_app or flags.ghostty:
                exit_caps = ("4", "C", "\\")
        elif shifters == "⌃⌥":
            exit_caps = ("C", "\\")
        elif shifters == "⌃⇧":
            if flags.i_term_app:
                exit_caps = ("C", "|")
            elif flags.ghostty:
                exit_caps = ("$",)
            else:
                exit_caps = ("|",)
        elif shifters == "⌃⌥⇧":
            exit_caps = ("C", "|")

        return exit_caps

    def kc_tangible_keyboard(self) -> str:
        """Draw a Keyboard but blank out its intangible Key Caps"""

        shifters = self.shifters

        # Add Key Caps

        keyboard = self.ShiftedKeyboard
        if "⇧" not in shifters:
            keyboard = self.PlainKeyboard
            if shifters:
                keyboard = keyboard.upper()
                keyboard = keyboard.replace("Spacebar".upper(), "Spacebar")

        keyboard = textwrap.dedent(keyboard).strip()

        # Drop Key Caps

        tangible_keyboard = self._kc_blank_the_intangible_keys_(keyboard)

        # Succeed

        return tangible_keyboard

    def _kc_blank_the_intangible_keys_(self, keyboard: str) -> str:
        """Blank out the intangible Key Caps"""

        tb = self.terminal_boss
        kd = tb.keyboard_decoder
        decode_by_echo = kd.decode_by_echo

        shifters = self.shifters

        echoes = keyboard.split()
        for echo in echoes:
            echo_plus = shifters + ("␢" if (echo == "Spacebar") else echo.upper())

            tangible = False
            if echo_plus in decode_by_echo.keys():
                decode = decode_by_echo[echo_plus]
                if decode:

                    tangible = True
                    (_shifters_, _cap_) = kd.echo_split_shifters_cap(echo_plus)
                    if (_shifters_ != shifters) or (not _cap_):
                        if echo != shifters:

                            tangible = False

            if not tangible:
                if (echo == "⎋") or (echo not in tuple(shifters)):

                    repl = len(echo) * " "
                    if (echo == "⌥") and ("⎋" in shifters):
                        repl = "⎋"

                    count_eq_1 = 1
                    keyboard = keyboard.replace(echo, repl, count_eq_1)

        return keyboard

    def kc_step_once(self, frames: tuple[bytes, ...]) -> None:
        """Eval Input and print Output"""

        tb = self.terminal_boss
        sw = tb.screen_writer
        kr = tb.keyboard_reader
        kd = tb.keyboard_decoder

        wipeouts_by_shifters = self.wipeouts_by_shifters

        assert ord("C") ^ 0x40 == ord("\003")  # ⌃C
        assert ord("\\") ^ 0x40 == ord("\034")  # ⌃\

        assert unicodedata.name("¤").title() == "Currency Sign".title()

        # Eval each Input Frame

        unhit_kseqs: list[object] = list()

        (h, w, y, x) = kr.sample_hwyx()

        for frame in frames:
            echoes = kd.bytes_to_echoes_if(frame)

            # Strike the Key Caps from which the Bytes may have come

            if echoes:

                finds = self.kc_press_keys_if(echoes, unhit_kseqs)
                if not finds:
                    unhit_kseqs.clear()
                    if not tb.quitting:
                        self.kc_switch_tab(echoes)
                        finds = self.kc_press_keys_if(echoes, unhit_kseqs)

                # s = "s" if finds[1:] else ""
                # logger_print(f"{frame!r} {echoes} toggled {finds} Key Cap{s}")

            # Switch to the Keyboard Tab named by Paste

            else:

                shifters = ""
                if len(frames) == 1:  # todo: Shifters pasted as multiple Frames
                    frame = frames[-1]
                    text = frame.decode()  # todo: UnicodeDecodeError from Paste
                    if text in wipeouts_by_shifters.keys():
                        shifters = text

                if not shifters:
                    logger_print(f"{frame!r}  # dropped because defined on no keyboard")
                    continue

                self.kc_switch_tab(echoes=(shifters,))

            # Trace the Bytes taken in

            echoes = kd.bytes_to_echoes_if(frame)
            join = " ".join(_.replace(" ", "") for _ in echoes)
            if not echoes:
                join = kd.bytes_to_one_main_echo(frame)

            self.kc_print(frame, " " + join + " ", self.kc_echo_index)
            self.kc_echo_index += 1

            y = kr.row_y

        sw.write_control(f"\033[{y};{x}H")  # row-column-leap ⎋[⇧H

        if unhit_kseqs:
            if frames == (b"\003",):  # ⌃C
                pass
            elif frames == (b"\034",):  # ⌃\
                pass
            else:
                self.kc_print(unhit_kseqs, "not found", frames)

        # todo1: Take up the ⎋[ U and ⎋[ ~ Key Codes from iTerm2 & Ghostty
        # todo1: Test & grow the nearly unreachable ⌃⌥ Keyboard
        # todo2: Shuffle the Byte Trace Panel up above the Panel of Press ⌃C etc

        # todo2: Test KeyCaps vs Bracketed Paste, not only vs Unbracketed Paste

    def kc_print(self, *args: object) -> None:

        chat_yx = self.chat_yx

        tb = self.terminal_boss  # todo9: layer KeycapsGame over KeyboardScreenIOWrapper?
        kr = tb.keyboard_reader
        sw = tb.screen_writer

        scrollables = self.scrollables

        printable = " ".join(str(_) for _ in args)

        (y, x) = chat_yx
        y += len(scrollables)

        assert KeycapsGame.MAX_SCROLLABLES_1 == 1
        n = 1

        if len(scrollables) >= n:
            yn = y - n

            scrollable = scrollables.pop(0)

            sw.write_control(f"\033[{yn};{x}H")  # row-column-leap ⎋[⇧H
            sw.write_control("\033[M")  # rows-delete ⎋[⇧M

            sw.write_control("\033[H")  # row-column-leap ⎋[⇧H
            sw.write_control("\033[L")  # rows-insert ⎋[⇧L
            sw.write_printable(scrollable)  # todo9: .kc_print wider than screen
            sw.write_control("\033[K")  # row-tail-erase ⎋[⇧K

            sw.write_control("\033[32100H")  # row-column-leap ⎋[⇧H
            sw.write_control("\n")  # south-rows-insert

            y = kr.row_y = yn + n - 1

            sw.write_control(f"\033[{y};{x}H")  # row-column-leap ⎋[⇧H
            sw.write_control("\033[L")  # rows-insert ⎋[⇧L

        sw.write_control(f"\033[{y};{x}H")  # row-column-leap ⎋[⇧H
        sw.write_printable(printable)  # todo9: .kc_print wider than screen
        sw.write_control("\033[K")  # row-tail-erase ⎋[⇧K
        sw.write_some_controls(["\r", "\n"])

        kr.row_y = y + 1

        scrollables.append(printable)

    def kc_switch_tab(self, echoes: tuple[str, ...]) -> None:
        """Switch to next Keyboard View when a Key is struck out there"""

        tb = self.terminal_boss
        kd = tb.keyboard_decoder
        sw = tb.screen_writer

        game_yx = self.game_yx
        shifters = self.shifters
        wipeouts = self.wipeouts
        wipeouts_by_shifters = self.wipeouts_by_shifters

        (game_y, game_x) = game_yx
        assert wipeouts is wipeouts_by_shifters[shifters]

        # Switch Tabs

        assert echoes, (echoes,)

        echo = echoes[0]

        (_shifters_, _cap_) = kd.echo_split_shifters_cap(echo)
        logger_print(f"{_shifters_=} {echoes=}  # kc_switch_tab_if")

        self.shifters = _shifters_  # replaces
        self.tangible_keyboard = self.kc_tangible_keyboard()

        # Replay Wipeouts

        wipeouts = self.wipeouts_by_shifters[_shifters_]  # replaces
        self.wipeouts = wipeouts

        sw.write_control(f"\033[{game_y};{game_x}H")  # row-column-leap ⎋[⇧H
        self.kc_game_draw()

        caps = list(wipeouts)
        wipeouts.clear()
        for cap in caps:
            self.kc_wipeout_else_restore(cap)
        assert wipeouts == caps, (wipeouts, caps)

    def kc_press_keys_if(  # noqa C901 too complex (27  # todo0:
        self, echoes: tuple[str, ...], unhit_kseqs: list[object]
    ) -> list[str]:
        """Wipe out each Key Cap when pressed"""

        tb = self.terminal_boss
        kd = tb.keyboard_decoder

        tangible_keyboard = self.tangible_keyboard

        assert echoes, (echoes,)

        findables = list()
        shifters = self.shifters
        for echo in echoes:
            (_shifters_, _cap_) = kd.echo_split_shifters_cap(echo)

            findable = _cap_ if _shifters_ else _cap_.lower()
            if _cap_ == "␢":
                findable = "Spacebar"

            if _shifters_ != shifters:
                pass  # logger_print(f"{_cap_!r} {echo!r}  # dropped for {_shifters_!r} vs {shifters!r}")
            elif findable not in tangible_keyboard:
                logger_print(f"{_cap_!r} {echo!r} {findable!r}  # dropped for not found")
            else:
                findables.append(findable)

        distinct_findables = list(collections.Counter(findables).keys())

        finds = list()
        for findable in distinct_findables:
            hits = self.kc_wipeout_else_restore(findable)
            finds += hits * [findable]
            if not hits:
                logger_print(f"{findable!r}  # dropped for not hit")  # todo: never happens?

        if not finds:
            unhit_kseqs.extend(echoes)

        return finds

    def kc_wipeout_else_restore(self, findable: str) -> int:
        """Wipe out each Key Cap, or restore, when found"""

        tb = self.terminal_boss
        game_yx = self.game_yx

        keyboard = self.tangible_keyboard
        wipeouts = self.wipeouts

        sw = tb.screen_writer
        (game_y, game_x) = game_yx

        # Form the Rows of the Gameboards

        dent = 4 * " "

        find = -1

        hits = 0
        while True:

            start = find + 1
            find = keyboard.find(findable, start)
            if find < 0:
                break

            hits += 1

            found_lines = keyboard[: find + 1].splitlines()
            assert found_lines, (found_lines, find, findable)

            # Leap to this found Key Cap

            y = game_y + len(found_lines)
            x = game_x + len(dent) + len(found_lines[-1]) - 1

            sw.write_control(f"\033[{y};{x}H")  # row-column-leap ⎋[⇧H

            # Restore this Key Cap later, else wipe it out to begin with

            if findable in wipeouts:
                wipeouts.remove(findable)

                sw.write_printable(findable)

            else:
                wipeouts.append(findable)

                width = len(findable)  # 1  # len("Spacebar")  # len("F12")

                sw.write_control("\033[1m")  # ⎋[1M style-bold
                sw.write_printable(width * "¤")
                sw.write_control("\033[m")  # ⎋[M style-plain

            # Flip once and done  # Don't find "a" in Spacebar, etc

            break

        return hits

    # todo9: --egg=keycaps: restart in each Keyboard viewed
    # todo9: --egg=keycaps: save/ load progress in each Keyboard viewed
    # todo9: --egg=keycaps: celebrate near to winning, and celebrate winning


#
# Play for --egg=squares
#


class SquaresGame:
    """Play for --egg=squares"""

    terminal_boss: TerminalBoss

    by_y_by_x: dict[int, dict[int, str]]
    y_high: int  # H W positive after initial zero
    x_wide: int

    game_yx: tuple[int, ...]

    steps: int
    strikes: int
    row_strikes: int

    Squares = "🟥 🟨 🟩 🟦 🟪"
    Squares = "".join(Squares.split())

    def __init__(self, terminal_boss: TerminalBoss) -> None:

        self.terminal_boss = terminal_boss
        self.by_y_by_x = dict()
        self.y_high = 0
        self.x_wide = 0
        self.game_yx = tuple()

        self.steps = 0
        self.strikes = 0
        self.row_strikes = 0

    def sq_logger_info_reprs(self, *args: object) -> None:
        """Send the Repr's as Logger Info, but led by Step Count"""

        steps = self.steps
        logger_print(steps, *args)

    def sq_run_awhile(self) -> None:
        """Run till Quit"""

        tb = self.terminal_boss

        sw = tb.screen_writer
        kr = tb.keyboard_reader

        # Draw the Gameboard

        (h, w, y, x) = kr.sample_hwyx()
        self.game_yx = (y, x)  # replaces

        self.sq_game_form()
        while not self.sq_find_moves():
            self.sq_logger_info_reprs("form again")
            self.sq_game_form()

        self.sq_game_draw()

        # Run till Quit  # 13:44:20 13:56:57.721291861

        min_steps = 5e6 + 1  # passed in 13m at --seed='2025-12-13 10:34:03'
        min_steps = -1  # last wins

        max_strikes = 0

        self.steps -= 1

        winning = False
        while not tb.quitting:
            self.steps += 1

            # Read or fabricate Input

            if self.steps > min_steps:
                kr.kbhit(timeout=None)
                kbhit = True
            else:
                kbhit = kr.kbhit(timeout=0)
                if kbhit:
                    min_steps = self.steps

            frames: tuple[bytes, ...] = (b" ",)
            if kbhit:
                frames = tb.tb_read_byte_frames()

            # Eval Input and print Output

            boxes = tuple(BytesBox(_) for _ in frames)
            for box in boxes:
                self.sq_step_because_box(box)

            # Count the widest span of shuffles without collisions

            if self.strikes > max_strikes:
                max_strikes = self.strikes
                self.sq_logger_info_reprs(max_strikes)

            # Quit at can't move

            if not self.sq_find_moves():  # todo8: never True
                self.sq_logger_info_reprs("quit at no moves")
                winning = True
                tb.quitting = True

        self.sq_logger_info_reprs(f"quit at {max_strikes=}")

        if winning:  # todo8: never True
            sw.write_control("\033[2A")
            sw.write_control("\033[K")
            sw.write_printable("🏆")
            sw.print()
            sw.print()  # twice

        sw.print()  # thrice

        # todo5: Squares ⇥ autoruns Shuffles till what
        # todo5: Squares ⇥ autoruns Shuffles till just before one works

    def sq_game_form(self) -> None:
        """Fill the Board with Tiles"""

        tb = self.terminal_boss
        r = tb.random_random

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

        tb = self.terminal_boss
        sw = tb.screen_writer

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
            if flags.darkmode:
                y_text = y_text.replace("⬜", "⬛")

            sw.write_printable(dent + y_text + dent)
            sw.write_some_controls(["\r", "\n"])

        # Draw the Southern Decor and the Southern Border

        sw.print(dent + "  ↓    ↓  " + dent)

        sw.print()
        sw.print()  # twice

        # Draw the Chat

        sw.print("Press ⌃C")  # todo5: overwrite with "Press Spacebar"
        sw.print()

        # todo5: have the ⌥-click on the board flip tiles through colors
        # todo5: rotate gravity to match arrow, and drag perpendicular to gravity

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
            self.row_strikes = 0
            self.sq_game_draw()
            return True

        # Across the South, fall from the North

        falls = self.sq_fall_south_into_empty_cells()

        if falls:
            self.strikes = 0
            self.row_strikes = 0
            self.sq_game_draw()
            return True

            # todo5: move all the 3 square arrows where they point
            # todo5: game trophies of first finding each kind of move

        # Shuffle Columns or Rows

        self.strikes += 1

        self.row_strikes += 1
        if self.row_strikes <= 3:
            self.sq_rows_shuffle()  # todo5: only while gravity pulls South
        else:
            self.row_strikes = 0
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

                    self.sq_logger_info_reprs(y, x, wide, (wide * t), "east bar")

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

                    self.sq_logger_info_reprs(y, x, high, (high * t), "south pole")

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

                by_x[xw] = "⬜"

    def sq_empty_south_poles(self, south_poles: list[tuple[int, int, int]]) -> None:
        """Erase each Cell of each South Pole"""

        by_y_by_x = self.by_y_by_x

        for south_pole in south_poles:
            (y, x, high) = south_pole
            for ys in range(y, y + high):
                by_x = by_y_by_x[ys]

                by_x[x] = "⬜"

    def sq_fall_south_into_empty_cells(self) -> int:
        """Across the South, fall from the North"""

        by_y_by_x = self.by_y_by_x
        y_high = self.y_high
        x_wide = self.x_wide

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

                tn = self.sq_y_x_choice(ys, x=x) if (yn < 0) else yn_by_x[x]
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
                    self.sq_logger_info_reprs(ys, ys_text, "falls")

        # Succeed, or fail

        return falls

    def _sq_y_x_choice_(self, y: int, x: int) -> str:
        """Choose pseudo randomly to show sticking points"""

        assert y == 0, (y, x)

        tb = self.terminal_boss
        r = tb.random_random

        squares = SquaresGame.Squares

        # Pull down pseudo random Choices

        self.sq_logger_info_reprs(y, x, "random choice")
        tn = r.choice(squares)

        return tn

    def sq_y_x_choice(self, y: int, x: int) -> str:
        """Choose less randomly to run for longer"""

        assert y == 0, (y, x)

        tb = self.terminal_boss
        r = tb.random_random

        by_y_by_x = self.by_y_by_x
        y_high = self.y_high
        x_wide = self.x_wide

        squares = SquaresGame.Squares

        # Pull down pseudo random Choices till stuck

        if self.sq_find_shuffle_moves():
            self.sq_logger_info_reprs(y, x, "random choice")
            tn = r.choice(squares)
            return tn

        choices = list()

        # Look down the Column to focus in the Row where the Choice could land

        x_cells = list()
        for ys in range(y_high):
            ys_by_x = by_y_by_x[ys]
            yt = ys_by_x[x]
            x_cells.append(yt)

        count_by_yt = collections.Counter(x_cells)
        yt_fuzz = count_by_yt["⬜"]
        assert yt_fuzz >= 1, (yt_fuzz, x_cells)

        yf = yt_fuzz - 1

        # Bias for the two-of-a-kind Color in this Column, if it exists

        for yt, count in count_by_yt.items():
            if yt == "⬜":
                continue

            assert count < 3, (count, yt)  # because not .sq_find_shuffle_moves
            if (count + (yt_fuzz - 1)) >= 2:
                choices.append(yt)

        # Bias for the two-of-a-kind Color in that Row, if it exists

        yf_by_x = by_y_by_x[yf]
        yf_cells = list(yf_by_x[_] for _ in range(x_wide))

        count_by_xt = collections.Counter(yf_cells)
        xt_fuzz = count_by_xt["⬜"]

        for xt, count in count_by_xt.items():
            if xt == "⬜":
                continue

            assert count < 3, (count, xt)  # because not .sq_find_shuffle_moves
            if (count + (max(xt_fuzz, 1) - 1)) >= 2:
                choices.append(xt)

        # Pull down random choices when all choices unstick us

        if (xt_fuzz > 3) or (yt_fuzz > 3) or (not choices):
            self.sq_logger_info_reprs(y, x, "all choices")
            tn = r.choice(squares)
            return tn

        # Choose so as to keep us moving

        choices = sorted(set(choices))
        self.sq_logger_info_reprs(y, x, choices, "biased choices")

        tn = r.choice(choices)

        return tn

        # todo9: a mathematically sound .sq_y_x_choice

    def sq_columns_shuffle(self) -> None:
        """Shuffle the Columns"""

        tb = self.terminal_boss
        r = tb.random_random

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
            self.sq_logger_info_reprs("columns shuffle")
            r.shuffle(x2_list)

        for x2 in x2_list:
            for y in range(y_high):
                by_x2 = by_y_by_x[y]
                by_x2[x2] = t_list.pop(0)

        # todo5: push just 1 column to the westmost, but tile by tile

    def sq_rows_shuffle(self) -> None:
        """Shuffle the Rows"""

        tb = self.terminal_boss
        r = tb.random_random

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
            self.sq_logger_info_reprs("rows shuffle")
            r.shuffle(y2_list)

        for y2 in y2_list:
            for x in range(x_wide):
                by2_x = by_y_by_x[y2]
                by2_x[x] = t_list.pop(0)

        # todo5: push just 1 row to the northmost but tile by tile

    def sq_find_moves(self) -> bool:
        """Say if progress is possible"""

        by_y_by_x = self.by_y_by_x
        y_high = self.y_high
        x_wide = self.x_wide

        # Search all Shuffles to pick out >= 3 together

        if self.sq_find_shuffle_moves():
            return True

        # Search all Cells to pick out a Fall of Cells in progress

        for y in range(y_high):
            for x in range(x_wide):
                cell = by_y_by_x[y][x]
                if cell == "⬜":
                    return True

        # Else give up

        return False

    def sq_find_shuffle_moves(self) -> bool:
        """Say if progress is possible"""

        by_y_by_x = self.by_y_by_x
        y_high = self.y_high
        x_wide = self.x_wide

        # Search all Column Shuffles to pick out >= 3 in a Row

        for y in range(y_high):
            by_x = by_y_by_x[y]
            y_cells = list(by_x[x] for x in range(x_wide))

            filled_y_cells = list(_ for _ in y_cells if _ != "⬜")
            if filled_y_cells:
                count_by_tx = collections.Counter(filled_y_cells)

                hope = max(count_by_tx.values())
                if hope >= 3:
                    return True

        # Search all Row Shuffles to pick out >= 3 in a Column

        for x in range(x_wide):
            x_cells = list(by_y_by_x[y][x] for y in range(y_high))

            filled_x_cells = list(_ for _ in x_cells if _ != "⬜")
            if filled_x_cells:
                count_by_ty = collections.Counter(filled_x_cells)

                hope = max(count_by_ty.values())
                if hope >= 3:
                    return True

        # Else give up

        return False

    # todo: more Squares, less Squares, colorable
    # todo: colorable single-wide █ ██ Full-Block U+2588
    # todo: colorable double-wide ⬤ Black-Large-Circle U+2B24


#
# Edit Screen per Change Orders received from Touch/ Mouse/ Key Release/ Press
#


class TerminalBoss:
    """Edit Screen per Change Orders received from Touch/ Mouse/ Key Release/ Press"""

    selves: list[TerminalBoss] = list()

    keyboard_screen_i_o_wrapper: KeyboardScreenIOWrapper
    screen_writer: ScreenWriter
    keyboard_reader: KeyboardReader

    keyboard_decoder: KeyboardDecoder
    screen_change_order: ScreenChangeOrder

    seed: str
    random_random: random.Random

    quitting: bool

    #
    # Init, enter, and exit
    #

    def __init__(self, seed: str) -> None:

        TerminalBoss.selves.append(self)

        assert DSR5 == "\033[" "5n"

        #

        ks = KeyboardScreenIOWrapper()
        kr = ks.keyboard_reader
        sw = ks.screen_writer

        kd = KeyboardDecoder()

        dsr5 = BytesBox(b"\033[5n")
        order = ScreenChangeOrder()
        order.grow_order(dsr5, yx=(kr.row_y, kr.column_x))

        r = random.Random(seed)

        #

        self.keyboard_screen_i_o_wrapper = ks
        self.screen_writer = sw
        self.keyboard_reader = kr

        self.keyboard_decoder = kd
        self.screen_change_order = order
        self.seed = seed
        self.random_random = r

        self.quitting = False

        # todo: limit fanout of pretending ⎋[5N came as last Input before Launch

    def __enter__(self) -> TerminalBoss:

        ks = self.keyboard_screen_i_o_wrapper
        sw = self.screen_writer
        kr = self.keyboard_reader

        assert SM_PS and SU_Y

        ks.__enter__()

        if flags.scrollback or ((not flags.enter) and (not flags._exit_)):

            (h, w, y, x) = kr.sample_hwyx()

            if flags.games:
                if (h * w) < (30 * 30):
                    flags.mobile = True

            if flags.games:
                (dark, light) = kr.guess_dark_light()
                if (not dark) and (not light):
                    dark = flags.google  # todo9: discover don't guess Google Cloud Shell Darkmode
                flags.darkmode |= dark
                flags.lightmode |= light

            if flags.scrollback:
                if y > 1:
                    sw.write_control(f"\033[{y - 1}S")  # ⎋[⇧S south-rows-insert
                if (not flags.enter) and (not flags._exit_):
                    sw.write_control("\033[?1049h")  # alt-screen ⎋[⇧?1049H

        if flags.mobile:
            if not flags.enter:
                sw.write_control("\033[?1006;1000h")  # sgr-mouse-take

            # sw.write_control("\033[?2004h")  # paste-wrap  # todo6:

        return self

    def __exit__(self, *args: object) -> None:

        ks = self.keyboard_screen_i_o_wrapper
        sw = self.screen_writer
        kr = self.keyboard_reader

        assert SM_PS and RM_PS and SGR_PS and DECSCUSR_PS

        if not flags.enter:
            if flags.mobile:
                sw.write_control("\033[?1006;1000l")  # mouse-give

        # if not flags.enter:  # todo6:
        #     sw.write_control("\033[?2004l")  # paste-unwrap ⎋[?2004L  # todo6:

        if not flags._exit_:

            sw.write_control("\033[m")  # plain ⎋[M vs other ⎋[ M
            sw.write_control("\033[ q")  # cursor-unstyled ⎋[␢Q vs other ⎋[ Q
            sw.write_control("\033[4l")  # replacing ⎋[4L vs ⎋[4H
            sw.write_control("\033[?25h")  # cursor-show ⎋[⇧?25H vs ⎋[?25L

            (h, w, y, x) = kr.sample_hwyx()
            sw.write_control("\033[?1049l")  # main-screen ⎋[⇧?1049L vs ⎋[⇧?1049H
            sw.write_control(f"\033[{y};{x}H")  # row-column-leap ⎋[⇧H

        ks.__exit__(*args)

    #
    # Run awhile
    #

    def tb_run_byteloop(self) -> None:
        """Loop back without adding latencies"""

        ks = self.keyboard_screen_i_o_wrapper
        sw = self.screen_writer

        assert ord("C") ^ 0x40 == ord("\003")  # ⌃C
        assert ord("\\") ^ 0x40 == ord("\034")  # ⌃\

        sw.print("Press ⌃C")
        while True:
            data = ks.read_one_byte()
            ks.write_some_bytes(data)
            if data == b"\r":  # rounds up ⌘V of \r to \r\n
                ks.write_some_bytes(b"\n")
            if data in (b"\003", b"\034"):
                break

    def tb_run_awhile(self) -> None:
        """Loop Input back to Output, to Screen from Touch/ Mouse/ Key"""

        sw = self.screen_writer
        kr = self.keyboard_reader

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

        while not self.quitting:

            # Read Input

            t0 = time.time()

            kr.kbhit(timeout=None)
            frames = self.tb_read_byte_frames()

            t1 = time.time()
            t1t0 = t1 - t0

            # Eval Input and print Output

            logger_print("")
            logger_print(f"{frames=}")

            if flags._repr_:
                self.tb_print_repr_frame_per_row(frames, t1t0=t1t0)
                continue

            self.tb_step_once(frames)

        if not flags._exit_:

            if flags._repr_:
                sw.write_control("\r")
                return

            sw.write_control("\033[32100H")  # cursor-unstyled ⎋[32100⇧H
            sw.write_control("\033[3A")  # 3 ↑ ⎋[3⇧A
            sw.write_control("\033[J")  # after-erase ⎋[⇧J  # simpler than ⎋[0⇧J
            sw.print("bye for now ...")

    def tb_read_byte_frames(self) -> tuple[bytes, ...]:
        """Read one Frame at a time, and help the Caller quit"""

        assert ord("C") ^ 0x40 == ord("\003")  # ⌃C
        assert ord("\\") ^ 0x40 == ord("\034")  # ⌃\

        kr = self.keyboard_reader
        frames = kr.read_byte_frames()

        if b"\003" in frames:
            self.quitting = True
        elif b"\034" in frames:
            self.quitting = True

        return frames

    def tb_step_once(self, frames: tuple[bytes, ...]) -> None:
        """Collect Input Frames over time as a Screen Change Order"""

        sw = self.screen_writer
        kr = self.keyboard_reader
        order = self.screen_change_order

        # Take in each Frame

        boxes = tuple(BytesBox(_) for _ in frames)
        boxes_yx = (kr.row_y, kr.column_x) if boxes[1:] else tuple()

        clearing_screen_order = False
        for box_index, box in enumerate(boxes):
            data = box.data
            text = box.text

            assert data, (data,)

            if not text:
                self.tb_write_frame_echo(data)
                continue

            (y, x) = (kr.row_y, kr.column_x)

            # Take in the Frame by itself, while Order incomplete

            order.grow_order(box, yx=(kr.row_y, kr.column_x))

            if not (order.forceful_order or order.intricate_order):

                if flags.echoes:
                    self.tb_write_frame_echo(data)
                    sw.write_control(f"\033[{y};{x}H")

                self.tb_box_step_once(box, intricate_order=False, boxes_yx=boxes_yx)

                continue

                # todo9: Delete the .factor repeat-count when not-echo'ing the Key Byte Frame

            if not order.compile_order():
                self.tb_write_frame_echo(data)
                break

            # Run this Order as completed by this Frame

            self.tb_order_step_once(data, order=order, boxes_yx=boxes_yx)

            order.yx = tuple()
            f = order.key_byte_frame
            f.clear_frame()  # reruns Factor for remaining Frames

            if boxes[box_index:][1:]:
                _ = kr.sample_hwyx()

            clearing_screen_order = True

        if clearing_screen_order:
            order.clear_order()

    def tb_order_step_once(
        self, data: bytes, order: ScreenChangeOrder, boxes_yx: tuple[int, ...]
    ) -> None:
        """Run this Order as completed by this Frame"""

        yx = order.yx
        (row_y, column_x) = yx

        strong = order.strong
        factor = order.factor

        order_box = order.box
        order_data = order_box.data
        order_text = order_box.text

        ks = self.keyboard_screen_i_o_wrapper
        sw = self.screen_writer
        kr = self.keyboard_reader
        order = self.screen_change_order

        assert order.forceful_order or order.intricate_order, (order,)

        # Write the Frame and grow the Order

        if (not strong) and order_box.nearly_printable:

            sw.write_printable(order_text)

        elif (not strong) and (order_text in ("\r", "\177")):  # ⏎ ⌫

            assert not order.intricate_order, (strong, order_text, data, order)
            self.tb_box_step_once(
                order_box, intricate_order=order.intricate_order, boxes_yx=boxes_yx
            )

        elif factor < -1:  # echoes without writing

            self.tb_write_frame_echo(data)

        elif factor == -1:  # echoes and greatly details

            frames = tuple([order_data])

            t1 = time.time()
            t1t0 = t1 - order.time_time

            self.tb_write_frame_echo(data)

            sw.write_printable(" ")
            self.tb_print_repr_frame_per_row(frames, t1t0=t1t0)

        elif factor == 0:  # echoes and leaps and writes

            self.tb_write_frame_echo("⌃m".encode() if (data == b"\r") else data)  # ⌃M

            sw.write_control(f"\033[{row_y};{column_x}H")
            kr.row_y = row_y
            kr.column_x = column_x

            ks.write_some_bytes(order_data)  # todo8: notice back to ScreenWriter for mirroring?

        else:  # echoes and cooks and leaps and writes

            if order.intricate_order or flags.echoes:
                self.tb_write_frame_echo(data)

            sw.write_control(f"\033[{row_y};{column_x}H")
            kr.row_y = row_y
            kr.column_x = column_x

            for _ in range(factor):
                self.tb_box_step_once(
                    order_box, intricate_order=order.intricate_order, boxes_yx=boxes_yx
                )

    #
    # Loop back a single Frame of decodable Input Bytes,
    # having arrived all together or else slowly intricately built as a Screen Change Order
    #

    def tb_box_step_once(
        self, box: BytesBox, intricate_order: bool, boxes_yx: tuple[int, ...]
    ) -> None:
        """Loop back the Decode of the Frame, else echo it"""

        data = box.data
        text = box.text

        sw = self.screen_writer
        kd = self.keyboard_decoder

        echo = kd.bytes_to_one_main_echo(data)
        assert echo.isprintable(), (echo,)

        assert ord("C") ^ 0x40 == ord("\003")  # ⌃C

        # If Frame is Printable

        if box.nearly_printable:
            sw.write_printable(text)
            return

        # If Frame has Key Caps

        if self.tb_echoes_step_once_if(box, intricate_order=intricate_order, boxes_yx=boxes_yx):
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

        # Show a brief loud Repr of any Unknown Encode arriving as Input

        bouncing = not intricate_order

        if flags.clickruns:
            if marks in (b"A", b"B", b"C", b"D"):
                if len(ints) == 1:

                    bouncing = False

                    # todo9: solve .clickruns Frames as fully as not, across Wrapped Lines

        if bouncing:
            sw.write_printable("<" + echo + ">")  # <⌃C>  # <⌃\>
            return

        # Loop back well-known Csi & Osc Byte Sequences

        if self.tb_csi_osc_step_once_if(box):
            return

        # Else echo vertically down southward

        self.tb_write_echo_southward(echo)

    def tb_write_echo_southward(self, echo: str) -> None:

        sw = self.screen_writer
        kr = self.keyboard_reader

        for e in echo:

            sw.write_printable(e)
            if kr.row_y >= kr.y_high:
                sw.write_control("\n")

            kr.row_y = min(kr.y_high, kr.row_y + 1)
            sw.write_control(f"\033[{kr.row_y};{kr.column_x}H")

    def tb_echoes_step_once_if(
        self, box: BytesBox, intricate_order: bool, boxes_yx: tuple[int, ...]
    ) -> bool:
        """Loop back the Key Caps of the Frame, else return False"""

        data = box.data
        text = box.text

        kr = self.keyboard_reader
        kd = self.keyboard_decoder

        echoes = kd.bytes_to_echoes_if(data)
        if not echoes:
            return False

        echo = echoes[0]  # only search for the first Key Cap

        sw = self.screen_writer
        kd = self.keyboard_decoder

        assert CUF_X == "\033[" "{}" "C"

        # Echo ⎋ Esc and ⎋⎋ Esc Esc as such

        if echo in ("⎋", "⎋⎋"):
            sw.write_printable(echo)
            return True

        # Loop back a few Key Chord Byte Sequences unchanged

        loopable_kseqs = ("⌃G", "⌃H", "⇥", "⌃K", "⇧⇥")
        if echo in loopable_kseqs:
            sw.write_control(text)  # ⌃I for ⇥, ⎋[⇧Z for ⇧⇥, etc
            return True

        # Loop back ⌃J encoding of ⏎ Return as ⌃J ⎋[ ⇧G column-leap

        if echo == "⌃J":
            if not flags.sigint:
                sw.write_control(text)  # ⌃J for ⌃J
            else:
                x = kr.column_x
                sw.write_some_controls(["\n", f"\033[{x}G"])  # "\n" lands as "\r\n"
            return True

        # Loop back ⌃M encoding of ⏎ Return as CR LF

        if echo == "⏎":

            sw.write_some_controls(["\r", "\n"])

            if boxes_yx:  # vertically pastes multiple Frames of Input
                (y, x) = boxes_yx
                if x > X1:
                    sw.write_control(f"\033[{x - X1}C")

            return True

        # Loop back ⌃⇧? ⌫ as Delete

        if echo == "⌫":
            sw.write_some_controls(["\033[D", "\033[P"])
            return True

        # Loop back as a Cardinal Arrow, no matter the shifting Keys

        join = str(echoes)
        if not intricate_order:

            arrows = tuple(_ for _ in ("←", "↑", "→", "↓") if _ in join)
            if len(arrows) == 1:
                arrow = arrows[-1]
                assert arrow in ("←", "↑", "→", "↓"), (arrow, join)

                arrow_control = kd.decode_by_echo[arrow]
                sw.write_control(arrow_control)

                if (arrow in ("←", "→")) and flags.echoes:
                    sw.write_control(arrow_control)  # double wide while echoed

                return True

        # Loop back as an Intercardinal Arrow

        if not intricate_order:
            if echo in ("↖", "↗", "↘", "↙"):
                arrow_control = kd.decode_by_echo[echo]
                sw.write_control(arrow_control)
                return True

        # Else don't loop back here  # so likely come out echoed at .bouncing

        return False

    def tb_csi_osc_step_once_if(self, box: BytesBox) -> bool:
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

            diagonal_tails = ("↖".encode(), "↗".encode(), "↘".encode(), "↙".encode())
            if backtail in diagonal_tails:
                sw.write_control(control)  # no limits on .marks and .ints
                return True

            elif backtail in (b"'}", b"'~"):

                sw.write_control(control)  # no limits on .marks and .ints
                return True

            elif len(backtail) == 1:

                if backtail in b"@" b"ABCDEFGHIJKLM" b"P" b"ST" b"Z" b"d" b"f" b"h" b"lm" b"q":
                    sw.write_control(control)  # no limits on .marks and .ints
                    return True

                if backtail in b"nt":
                    sw.write_control(control)  # no limits on .marks and .ints
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

    #
    # Form Repr's of Frames of Input Bytes
    #

    def tb_write_frame_echo(self, frame: bytes) -> None:
        """Show a brief Repr of one Frame"""

        sw = self.screen_writer
        kd = self.keyboard_decoder

        echo = kd.bytes_to_one_main_echo(frame)
        sw.write_printable(echo)

    def tb_print_repr_frame_per_row(self, frames: tuple[bytes, ...], t1t0: float) -> None:
        """Print the Repr of each Frame, but mark the Frames as framed together"""

        sw = self.screen_writer
        kr = self.keyboard_reader

        assert CUP_Y_X == "\033[" "{};{}H"

        frame_t1t0 = t1t0
        (y, x) = (kr.row_y, kr.column_x)

        for frame_index in range(len(frames)):

            self.tb_print_one_repr_frame(frames, frame_index=frame_index, t1t0=frame_t1t0)

            frame_t1t0 = 0e0
            y += 1  # todo: 'row_y > y_high' happens here  # todo: update Y X shadow

            sw.write_control("\n")
            sw.write_control(f"\033[{y};{x}H")

    def tb_print_one_repr_frame(
        self, frames: tuple[bytes, ...], frame_index: int, t1t0: float
    ) -> None:
        """Write the Repr of one Frame, but mark the Frames as framed together"""

        frame = frames[frame_index]

        box = BytesBox(frame)
        text = box.text

        sw = self.screen_writer
        kd = self.keyboard_decoder

        # Choose which Key Caps to put out front

        echoes = kd.bytes_to_echoes_if(frame)

        alt_kseqs = echoes
        if echoes:
            if (frame == b"`") and frames[1:]:
                alt_kseqs = tuple(reversed(echoes))  # ('⌥⇧~', '`') 0 `

        # Choose which details to print

        joinables: list[object] = list()

        if alt_kseqs:
            joinables.append(alt_kseqs[0])

        if not box.nearly_printable:
            joinables.append(repr(frame))
        else:
            if text == " ":
                joinables.append(repr(text))
            else:
                joinables.append(text)

        joinables.append(chop(1000 * t1t0))

        if alt_kseqs[1:]:
            joinables.append(alt_kseqs[1:])

        if frames[1:]:
            joinables.append(frame_index)

        # Print the chosen details

        join = " ".join(str(_) for _ in joinables)
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

    strong: bool
    factor: int
    box: BytesBox

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

        self.strong = False
        self.factor = 1
        self.box = BytesBox(b"")

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
    # Add on a next Input, else restart  # todo6: Accept ⎋⌃⌥⇧F Key Caps
    #

    def grow_order(self, box: BytesBox, yx: tuple[int, int]) -> None:
        """Add on a next Input, else restart"""

        data = box.data
        text = box.text

        assert data, (data,)

        f = self.key_byte_frame
        assert _FactorMark_ == "\025"

        # Take Input after a Text Frame or Closed Frame as a new Order

        if f.encodes or f.closed:
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
    # Say what to do and where
    #

    def compile_order(self) -> bool:
        """Say where to run, what to run, and if strongly told to run it other than once"""

        early_mark = self.early_mark
        int_literal = self.int_literal
        late_mark = self.late_mark

        f = self.key_byte_frame

        assert DL_Y == "\033[" "{}M"
        assert _CLICK3_ == "\033[M"

        # Say how strongly marked the Factor is, if marked at all

        strong = bool(early_mark + late_mark)

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
        box = BytesBox(data)

        if not f.closed:
            if not f.encodes:
                return False

        # Succeed

        strong_str = "demand" if strong else "suggest"
        logger_print(f"{strong_str} {factor} {box.data=}")

        self.strong = strong  # replaces
        self.factor = factor  # replaces
        self.box = box  # replaces

        return True


class ScreenWriter:
    """Write Lines of Output to the Terminal Screen"""

    keyboard_screen_i_o_wrapper: KeyboardScreenIOWrapper

    def __init__(self, keyboard_screen_i_o_wrapper: KeyboardScreenIOWrapper) -> None:
        self.keyboard_screen_i_o_wrapper = keyboard_screen_i_o_wrapper

    def print(self, *args: object) -> None:
        """Answer the question of 'what is print?' here lately"""

        printable = " ".join(str(_) for _ in args)

        self.write_printable(printable)  # may raise UnicodeEncodeError
        self.write_some_controls(["\r", "\n"])

        # todo: one 'def print' per project is exactly enough?

    def write_text(self, text: str) -> None:
        """Write the Characters of a Text, after splitting it into Controls and Printables"""

        frame = KeyByteFrame(b"")

        encode = text.encode()  # may raise UnicodeEncodeError

        ba = bytearray()
        ba.extend(encode)

        ba.extend(b".")  # runs with one extra at the end
        while ba:
            code = ba.pop(0)

            if ba:
                byte = bytes([code])
                extras = frame.take_one_byte_if(byte)
                ba[0:0] = extras

            if frame.closed or not ba:
                encodes = frame.encodes
                box_text = encodes.decode()
                if box_text:
                    self.write_printable(box_text)
                else:
                    control = frame.to_frame_bytes()
                    self.write_control(control.decode())
                frame.clear_frame()

        # todo: one 'def write_text' per project is exactly enough?

    def write_printable(self, text: str) -> None:
        """Write the Byte Encodings of Printable Text without adding a Line-Break"""

        ks = self.keyboard_screen_i_o_wrapper

        printable = text  # alias
        assert printable.replace(Apple, "-").isprintable(), (printable,)

        assert CUF_X == "\033[" "{}" "C"
        assert CUB_X == "\033[" "{}" "D"
        assert Apple == "\uf8ff"

        # Trust the Terminal to write well

        if not flags.google:
            ks.write_text_encode(printable)
            return

        # Else trust the Terminal to write all but Fullwidth & Wide well

        eaws_set = set(unicodedata.east_asian_width(_) for _ in printable)
        if "Fullwidth"[0] not in eaws_set:
            if "Wide"[0] not in eaws_set:
                ks.write_text_encode(printable)
                return

        # Else trust the Terminal to write well, except to stop the Cursor at X + 1, not at X + 2

        for t in text:
            ks.write_text_encode(t)
            eaw = unicodedata.east_asian_width(t)
            if eaw in ("Fullwidth"[0], "Wide"[0]):
                if _os_environ_get_cloud_shell_:  # separate from .flags.google
                    self.write_control("\033[C")

                    # todo8: double-wide chars in the far East and far Southeast

        # "Ambiguous"[0]  # ¡ ¤ § ® Ø ß ± ¶ ↖ ↗ ↘ ↙ € Ω Ⅷ 
        # "Narrow"[:2]  # ¢ and £ and the Printable US Ascii
        # "Neutral"[0]  # © « µ » ñ

        # "Halfwidth"[0]  # Hangul, Katakana, & Halfwidth ￭ ￮
        # "Fullwidth"[0]  # ０ ９ Ａ Ｚ ￥ ￦  # U+3000 Ideographic Space
        # "Wide"[0]  # ☕ ☰ ♿ 🌅 🌐 💾 💿 🔍 🔰 😃 🛼

        # also Wide are ♿ ⚪⚫ ⬛⬜ 🔰 🔴🔵 😃 🛼 🟠🟡🟢🟣🟤 🟥🟦🟧🟨🟩🟪🟫

        # todo: every mention of  in Source makes Code Patches difficult to send across platforms

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

        #

        assert _NorthArrow_ and _SouthArrow_ and _EastArrow_ and _WestArrow_
        assert _NorthwestArrow_ and _NortheastArrow_ and _SoutheastArrow_ and _SouthwestArrow_

        #

        assert not control.isprintable(), (control,)

        data = control.encode()  # todo: speak this assert is-control idea lots more simply?
        f = KeyByteFrame(data)  # may raise UnicodeEncodeError
        f.tilt_to_close_frame()  # like stop staying open to accept b x y into ⎋[⇧M{b}{x}{y}
        assert (not f.encodes) and f.closed, (data, f)

        #

        (marks, ints) = f.to_csi_marks_ints_if()

        if marks == f.backtail:
            if f.backtail == b"'}":
                self.columns_insert(ints[:1])
                return
            if f.backtail == b"'~":
                self.columns_delete(ints[:1])
                return

        #

        controls_by_marks = {  # not yet standard
            "↖".encode(): ["\033[A", "\033[D", "\033[D"],
            "↗".encode(): ["\033[A", "\033[C", "\033[C"],
            "↘".encode(): ["\033[B", "\033[C", "\033[C"],
            "↙".encode(): ["\033[B", "\033[D", "\033[D"],
        }

        if marks in controls_by_marks.keys():
            controls = controls_by_marks[marks]
            for control in controls:
                self.write_control_through(control)
            return

        #

        self.write_control_through(control)

    def columns_delete(self, ints: tuple[int, ...]) -> None:
        """Delete Columns of the Screen"""

        pn_int = ints[-1] if ints else PN1
        pn = pn_int  # accepts pn = 0

        #

        ks = self.keyboard_screen_i_o_wrapper
        kr = ks.keyboard_reader
        row_y = kr.row_y
        y_high = kr.y_high

        #

        assert DCH_X == "\033[" "{}" "P"
        assert VPA_Y == "\033[" "{}" "d"
        assert DECDC_X == "\033[" "{}" "'~"

        #

        for y in range(Y1, y_high + 1):
            self.write_control_through(f"\033[{y}d")
            self.write_control_through(f"\033[{pn}P")
        self.write_control_through(f"\033[{row_y}d")

        # macOS Terminal & macOS iTerm2 & Google Cloud Shell lack ⎋['⇧~ cols-delete

    def columns_insert(self, ints: tuple[int, ...]) -> None:
        """Insert Columns of the Screen & fill with Backlight or not"""

        pn_int = ints[-1] if ints else PN1
        pn = pn_int  # accepts pn = 0

        #

        ks = self.keyboard_screen_i_o_wrapper
        kr = ks.keyboard_reader
        row_y = kr.row_y
        y_high = kr.y_high

        #

        assert ICH_X == "\033[" "{}" "@"
        assert VPA_Y == "\033[" "{}" "d"
        assert DECIC_X == "\033[" "{}" "'}}"  # speaking of ⎋[ '}

        #

        for y in range(Y1, y_high + 1):
            self.write_control_through(f"\033[{y}d")
            self.write_control_through(f"\033[{pn}@")
        self.write_control_through(f"\033[{row_y}d")

        # macOS Terminal & macOS iTerm2 & Google Cloud Shell lack ⎋['⇧} cols-insert

    def write_control_through(self, text: str) -> None:
        """Write the Byte Encodings of one Unprintable Control Text"""

        ks = self.keyboard_screen_i_o_wrapper
        ks.write_text_encode(text)


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

DCH_X = "\033[" "{}" "P"  # Csi 05/00 [Delete] Cursor Horizontal [Pn] [Columns]
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

    keyboard_screen_i_o_wrapper: KeyboardScreenIOWrapper

    y_high: int  # H W positive after initial zero
    x_wide: int

    row_y: int  # Y X positive after initial zero
    column_x: int

    reads_ahead: bytearray

    def __init__(self, keyboard_screen_i_o_wrapper: KeyboardScreenIOWrapper) -> None:

        self.keyboard_screen_i_o_wrapper = keyboard_screen_i_o_wrapper

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
        # way far away from KeyboardScreenIOWrapper.read_one_byte

    def _frames_compress_if_(self, frames: tuple[bytes, ...]) -> tuple[bytes, ...]:
        """Collapse two Frames to one, or don't"""

        assert _NorthArrow_ and _SouthArrow_ and _EastArrow_ and _WestArrow_
        assert _NorthwestArrow_ and _NortheastArrow_ and _SoutheastArrow_ and _SouthwestArrow_

        # Convert a Double Key Jam of actual ←↑→↓ Cardinal Arrows to ↖↗↘↙ Intercardinal Arrows

        unshifted_encodings = (b"\033[A", b"\033[B", b"\033[C", b"\033[D")

        shifted_encodings = (b"\033[1;2A", b"\033[1;2B", b"\033[1;2C", b"\033[1;2D")
        encodings = unshifted_encodings + shifted_encodings

        if len(frames) == 2:

            m0 = all((_ in unshifted_encodings) for _ in frames)
            m1 = all((_ in encodings) for _ in frames)
            pns = "" if m0 else "1;2"

            if m0 or m1:
                backtails = b"".join(sorted(_[-1:] for _ in frames))

                if backtails == b"AD":  # _NorthArrow_ _WestArrow_
                    return (f"\033[{pns}↖".encode(),)
                elif backtails == b"AC":  # _NorthArrow_ _EastArrow_
                    return (f"\033[{pns}↗".encode(),)
                elif backtails == b"BC":  # _SouthArrow_ _EastArrow_
                    return (f"\033[{pns}↘".encode(),)
                elif backtails == b"BD":  # _SouthArrow_ _WestArrow_
                    return (f"\033[{pns}↙".encode(),)

        # Else make no change

        return frames

        # ⎋[ ↖ ↗ ↘ ↙  # ⎋[ 1 ; 2 ↖ ↗ ↘ ↙  # not yet standard

        # todo8: intercardinal arrows at Google Cloud Shell

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
            logger_print(f"{h=} {w=} {y=} {x=}  # x > w")
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

        # Accept the b"``" as the Frame of ⌥⇧~

        if len(text) == 2:
            if text == "``":  # ⌥⇧~ `
                start = data
                end = b""
                return (start, end)

            # Split the ⌥ Accents arriving together with an Unaccented Decode

            accents = ("`", "´", "¨", "ˆ", "˜")  # ⌥⇧~ ⌥⇧E ⌥⇧U ⌥⇧I ⌥⇧N
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

    def kbhit(self, timeout: float | None = None) -> bool:
        """Block till next Input Byte, else till Timeout, else till forever"""

        reads_ahead = self.reads_ahead
        if reads_ahead:
            return True

        ks = self.keyboard_screen_i_o_wrapper
        hit = ks.stdio_select_select(timeout=timeout)  # a la msvcrt.kbhit

        return hit

        # todo: one 'def kbhit' per project is exactly enough?
        # todo: keep 'def kbhit' paired up with 'def read_bytes' and 'def read_byte_frames'

    def guess_dark_light(self) -> tuple[bool, bool]:
        """Choose Darkmode or Lightmode or neither Backlight"""

        ks = self.keyboard_screen_i_o_wrapper
        sw = ks.screen_writer
        reads_ahead = self.reads_ahead

        # Sends ⎋]10;⇧?⌃G for reply ⎋]10;RGB⇧:{r}/{g}/{b}\007 for 10, 11, and 12

        rgb_by_osc = dict()
        for osc in (10, 11, 12):  # 10 Color  # 11 Backlight  # 12 Cursor

            dsr5 = "\033[5n"
            sw.write_control(dsr5)

            osc_control = f"\033]{osc};?\007"
            sw.write_control(osc_control)

            reads_endswith_rgb = self.read_bytes()
            (reads, rgb) = self._bytes_split_osc_rgb_ints_(reads_endswith_rgb, osc=osc)

            rgb_by_osc[osc] = rgb
            if rgb:
                rep_rgb = "(" + ", ".join(f"0x{_:04X}" for _ in rgb) + ")"
                logger_print(f"{osc=} rgb={rep_rgb}")

            if reads:
                m = re.search(rb"\033\[0n$", string=reads)
                if m:
                    logger_print(f"took {m.group(0)!r}")  # for Dsr 0 before Osc 10 11 12

                    n = len(m.group(0))
                    reads = reads[:-n]

            if reads:
                logger_print(f"{reads=} {osc_control=}")
                reads_ahead.extend(reads)

        # React to way low Backlight

        dark = light = False

        if 11 in rgb_by_osc.keys():
            rgb = rgb_by_osc[11]
            if rgb:
                (r, g, b) = rgb
                if (r + g + b) <= 0xFFFF:  # todo9: less simple Terminal Luminance models
                    dark = True

        # Succeed

        return (dark, light)

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
            logger_print(f"took {m.group(0)!r}")  # for Osc 10 11 12

            n = len(m.group(0))
            startswith = data[:-n]

            for g in range(1, 3 + 1):
                i = int(m.group(g), base=0x10)
                assert 0 <= i <= 0xFFFF, (i, m.group(g), data)
                int_list.append(i)

        return (startswith, tuple(int_list))

    def sample_hwyx(self) -> tuple[int, int, int, int]:
        """Take a fresh sample of Width x Height and Y X Cursor Position of this Terminal"""

        ks = self.keyboard_screen_i_o_wrapper
        sw = ks.screen_writer
        reads_ahead = self.reads_ahead

        assert DSR0 == "\033[" "0n"
        assert DSR5 == "\033[" "5n"

        sw.write_control("\033[5n")  # sends ⎋[5N for reply ⎋[0N
        dsr0_bytes = self.read_bytes()
        (h, w, y, x) = (self.y_high, self.x_wide, self.row_y, self.column_x)

        dsr0 = b"\033[0n"
        assert dsr0_bytes.endswith(dsr0), (dsr0_bytes, dsr0)

        n = len(dsr0)
        reads = dsr0_bytes[:-n]

        if reads:
            logger_print(f"{reads=} {dsr0=}")
            reads_ahead.extend(reads)

        # Move this KeyboardReader to this fresh H W Y X

        self._store_h_w_y_x_(h, w=w, y=y, x=x)

        # Succeed

        return (h, w, y, x)

        # todo2: survive iTerm2 .sample_hwyx stress of Shifted Intercardinal Arrows

    def read_bytes(self) -> bytes:
        """Take Input Bytes from Cache, else from Terminal"""

        # Take all the Input Bytes from Cache at once

        reads_ahead = self.reads_ahead
        if reads_ahead:
            logger_print(f"{reads_ahead=}")

            reads = bytes(reads_ahead)
            reads_ahead.clear()

            return reads

        # Else take a Cursor Position Frame of Input Bytes from Terminal

        (hwyx, reads) = self._read_hwyx_bytes_()
        self._store_h_w_y_x_(*hwyx)

        return reads

        # todo: keep 'def read_bytes' paired up with 'def kbhit'
        # way far away from KeyboardScreenIOWrapper.read_one_byte

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

        ks = self.keyboard_screen_i_o_wrapper
        fileno = ks.fileno

        # Read one Byte, then send for Y X Cursor Position, then block till it comes

        (yx, reads) = self._read_yx_bytes_()
        (y, x) = yx

        # Sample H W just after the last Input Byte arrives

        fd = fileno
        (w, h) = os.get_terminal_size(fd)
        if (h, w) != (self.y_high, self.x_wide):
            logger_print(f"took ⎋[8;{h};{w}T")

        # Succeed

        hwyx = (h, w, y, x)

        return (hwyx, reads)

    def _read_yx_bytes_(self) -> tuple[tuple[int, int], bytes]:
        """Read 1 Byte, send for Cursor Y X Position, & read Available Bytes till the Report"""

        ks = self.keyboard_screen_i_o_wrapper
        sw = ks.screen_writer

        assert _NorthArrow_ and _SouthArrow_ and _EastArrow_ and _WestArrow_
        assert DSR6 == "\033[" "6n"
        assert CPR_Y_X == "\033[" "{};{}R"

        ks.write_some_bytes(b"\033[6n")  # ⎋[6n send for reply Y X
        ks.stdio_select_select(timeout=0e0)  # flushes and blocks after .write_some_bytes

        row_y = -1
        column_x = -1
        ba = bytearray()

        flags_lazy_kbhits = False  # truthy to show more messy things
        while True:

            read = ks.read_one_byte()
            ba.extend(read)

            if flags.clickarrows:
                sm = re.search(rb"(\033\[[ABCD])$", string=ba)  # ⎋[⇧A ⎋[⇧B ⎋[⇧C ⎋[⇧D
                if sm:
                    logger_print(f"took {sm.group(0)!r}")  # for flags.clickarrows
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
                    logger_print(f"took ⎋[{row_y};{column_x}⇧R")

                assert row_y >= Y1, (row_y, column_x, ba)
                assert column_x >= X1, (row_y, column_x, ba)

                if not ba:  # eats first ⎋[ ⇧R, when ⎋[6N written before Def Entry
                    continue  # doesn't eat second ⎋[ ⇧R, because .row_y >= Y1 by then

                if flags_lazy_kbhits:
                    break

                    # Arrow Key Bursts split apart into frames if .flags_lazy_kbhits
                    # Double Key Jams still often recur despite .flags_lazy_kbhits

            if not ks.stdio_select_select(timeout=0e0):  # blocks
                break

        yx = (row_y, column_x)  # taken from first, when more left in .ba
        reads = bytes(ba)

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


#
# Speak of a Byte Encoding as a Sequence of Chords of Key Caps
#


def _try_keyboard_decoder_() -> None:
    """Try KeyboardDecoder things, or don't bother"""

    kd = KeyboardDecoder()

    d1 = kd.decode_by_echo
    k1 = "⌃⇧@"
    logger_print(f"{len(d1)=} [{k1!r}] = {d1.get(k1)!r}  # _try_keyboard_decoder_")

    d2 = kd.echoes_by_decode
    k2 = "⌃⇧@"
    logger_print(f"{len(d2)=} [{k2!r}] = {d2.get(k2)!r}  # _try_keyboard_decoder_")

    # todo1: measure time cost


class KeyboardDecoder:
    """Speak of a Byte Encoding as a Combination of Chords of Key Caps"""

    selves: list[KeyboardDecoder] = list()

    decode_by_echo: dict[str, str]
    echoes_by_decode: dict[str, tuple[str, ...]]

    OptionAccents = ("`", "´", "¨", "ˆ", "˜")
    OptionGraveGrave = "``"

    def __init__(self) -> None:
        """Form a Keyboard for each Terminal App"""

        KeyboardDecoder.selves.append(self)

        self.decode_by_echo = dict()
        self.echoes_by_decode = dict()

        self._form_some_keyboards_()

    def _form_some_keyboards_(self) -> None:
        """Form a Keyboard for the present Terminal App only"""  # todo: more test

        self._form_apple_terminal_keyboards_()

        if flags.i_term_app:
            self._form_i_term_app_keyboards_()

    def _form_apple_terminal_keyboards_(self) -> None:
        """Form an Apple macOS Terminal Keyboard"""

        assert Apple == "\uf8ff"

        # 1.1 ⎋

        shifts = "⎋"
        strikes = """
            033.033
            033.140 033.061 033.062 033.063 033.064 033.065 033.066 033.067 033.070 033.071 033.060 033.055 033.075 033.177
            033.011 033.161 033.167 033.145 033.162 033.164 033.171 033.165 033.151 033.157 033.160 033.133 033.135 033.134
            033.141 033.163 033.144 033.146 033.147 033.150 033.152 033.153 033.154 033.073 033.047 033.015
            033.172 033.170 033.143 033.166 033.142 033.156 033.155 033.054 033.056 033.057
            033.040 033.142 033.033.133.101 033.146 033.033.133.102
        """

        # 1.2 ⎋⌃

        shifts = "⎋⌃"
        strikes = """
            033.033
            033.140 033.061 033.062 033.063 033.064 033.065 033.066 033.067 033.070 033.071 033.060 033.037 033.075 033.010
            033.011 033.021 033.027 033.005 033.022 033.024 033.031 033.025 033.011 033.017 033.020 033.033 033.035 033.034
            033.001 033.023 033.004 033.006 033.007 033.010 033.012 033.013 033.014 033.073 033.047 033.015
            033.032 033.030 033.003 033.026 033.002 033.016 033.015 033.054 033.056 033.057
            033.040 033.033.133.104 033.033.133.101 033.033.133.103 033.033.133.102
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 1.3 ⎋⇧

        shifts = "⎋⇧"
        strikes = """
            033.033
            033.176 033.041 033.100 033.043 033.044 033.045 033.136 033.046 033.052 033.050 033.051 033.137 033.053 033.010
            033.033.133.132 033.121 033.127 033.105 033.122 033.124 033.131 033.125 033.111 033.117 033.120 033.173 033.175 033.174
            033.101 033.123 033.104 033.106 033.107 033.110 033.112 033.113 033.114 033.072 033.042 033.015
            033.132 033.130 033.103 033.126 033.102 033.116 033.115 033.074 033.076 033.077
            033.040 033.033.133.104 033.033.133.101 033.033.133.103 033.033.133.102
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 1.4 ⎋⌃⇧

        shifts = "⎋⌃⇧"
        strikes = """
            033.033
            033.140 033.061 033.062 033.063 033.064 033.065 033.066 033.067 033.070 033.071 033.060 033.037 033.075 033.010
            033.033.133.132 033.021 033.027 033.005 033.022 033.024 033.031 033.025 033.011 033.017 033.020 033.033 033.035 033.034
            033.001 033.023 033.004 033.006 033.007 033.010 033.012 033.013 033.014 033.073 033.047 033.015
            033.032 033.030 033.003 033.026 033.002 033.016 033.015 033.054 033.056 033.057
            033.040 033.033.133.104 033.033.133.101 033.033.133.103 033.033.133.102
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 2.1 ''

        shifts = ""
        strikes = """
            033
            140 061 062 063 064 065 066 067 070 071 060 055 075 177
            011 161 167 145 162 164 171 165 151 157 160 133 135 134
            141 163 144 146 147 150 152 153 154 073 047 015
            172 170 143 166 142 156 155 054 056 057
            040 033.133.104 033.133.101 033.133.103 033.133.102
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 2.2 ⌃

        shifts = "⌃"
        strikes = """
            033
            ... ... ... ... ... ... ... ... ... ... ... 037 ... 177
            011 021 027 005 022 024 031 025 011 017 020 033 035 034
            001 023 004 006 007 010 012 013 014 ... ... ...
            032 030 003 026 002 016 015 ... ... ...
            000 ... ... ... ...
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 2.3 ⌃⌥

        shifts = "⌃⌥"
        strikes = """
            033
            140 061 062 063 064 065 066 067 070 071 060 037 075 177
            011 021 027 005 022 024 031 025 011 017 020 033 035 034
            001 023 004 006 007 010 012 013 014 073 047 015
            032 030 003 026 002 016 015 054 056 057
            000 033.133.104 033.133.101 033.133.103 033.133.102
        """
        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 2.4 ⌃⌥⇧

        shifts = "⌃⌥⇧"
        strikes = """
            033
            140 061 000 063 064 065 036 067 070 071 060 037 075 177
            033.133.132 021 027 005 022 024 031 025 011 017 020 033 035 034
            001 023 004 ... 007 010 012 013 014 073 047 015
            032 030 003 026 ... 016 015 054 056 057
            000 033.133.104 033.133.101 033.133.103 033.133.102
        """
        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 2.5 ⌃⇧

        shifts = "⌃⇧"
        strikes = """
            033
            ... ... 000 ... ... ... 036 ... ... ... ... 037 ... 177
            033.133.132 ... ... ... ... ... ... ... ... ... ... 033 035 034
            ... ... ... ... ... ... ... ... ... ... ... ...
            ... ... ... ... ... ... ... ... ... ...
            000 033.133.104 033.133.101 033.133.103 033.133.102
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 2.6 ⌥

        shifts = "⌥"  # ⌥Y sends \, coded here as r""" \ """
        strikes = r"""
            033
            ¤ ¡ ™ £ ¢ ∞ § ¶ • ª º – ≠ 177
            011 œ ∑ ¤ ® † \ ¤ ¤ ø π “ ‘ «
            å ß ∂ ƒ © ˙ ∆ ˚ ¬ … æ 015
            Ω ≈ ç √ ∫ ¤ µ ≤ ≥ ÷
            302.240 033.142 033.133.101 033.146 033.133.102
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 2.7 ⌥⇧

        shifts = "⌥⇧"  # ⌥⇧K sends Apple Logo, coded here as \uf8ff
        strikes = """
            033
            ` ⁄ € ‹ › ﬁ ﬂ ‡ ° · ‚ — ± 177
            033.133.132 Œ „ ´ ‰ ˇ Á ¨ ˆ Ø ∏ ” ’ »
            Å Í Î Ï ˝ Ó Ô \uf8ff Ò Ú Æ 015
            ¸ ˛ Ç ◊ ı ˜ Â ¯ ˘ ¿
            302.240 033.133.104 033.133.101 033.133.103 033.133.102
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 2.8 ⇧

        shifts = "⇧"  # ⇧← and ⇧→ send ⎋[1;2D and ⎋[1;2C
        strikes = """
            033
            176 041 100 043 044 045 136 046 052 050 051 137 053 177
            033.133.132 121 127 105 122 124 131 125 111 117 120 173 175 174
            101 123 104 106 107 110 112 113 114 072 042 015
            132 130 103 126 102 116 115 074 076 077
            040 033.133.061.073.062.104 033.133.101 033.133.061.073.062.103 033.133.102
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

    PlainCaps = tuple(
        r"""
        ⎋
        ` 1 2 3 4 5 6 7 8 9 0 - = ⌫
        ⇥ Q W E R T Y U I O P [ ] \
        A S D F G H J K L ; ' ⏎
        Z X C V B N M , . /
        ␢ ← ↑ → ↓
    """.split()
    )

    ShiftCaps = tuple(
        """
        ⎋
        ~ ! @ # $ % ^ & * ( ) _ + ⌫
        ⇥ Q W E R T Y U I O P { } |
        A S D F G H J K L : " ⏎
        Z X C V B N M < > ?
        ␢ ← ↑ → ↓
    """.split()
    )

    def _add_keyboard_(self, shifts: str, strikes: str) -> None:

        strikes_split = strikes.split()

        if not strikes_split:
            return

        plain_caps = KeyboardDecoder.PlainCaps
        shift_caps = KeyboardDecoder.ShiftCaps

        o = (len(plain_caps), len(shift_caps), len(strikes_split))
        assert len(plain_caps) == len(shift_caps) == len(strikes_split), o

        caps = shift_caps if ("⇧" in shifts) else plain_caps
        for cap, cap_strikes in zip(caps, strikes_split):
            echo = shifts + cap
            decode = self.cap_strikes_to_decode(cap_strikes, echo=echo)
            if decode:

                self._keyboard_add_decode_(decode, echo=echo)

        # todo2: insist on conventional Shifts, at least here

    def cap_strikes_to_decode(self, cap_strikes: str, echo: str) -> str:
        """Convert to Decode of Byte Encoding of Key Strike"""

        if cap_strikes in ("...", "¤"):
            return ""

        ba = bytearray()

        octets = cap_strikes.split(".")
        for octet in octets:
            if len(octet) == 3:
                ba.append(int(octet, base=0o010))
            else:
                octet_data = octet.encode()
                ba.extend(octet_data)

        decode = ba.decode()
        assert ba and decode, (ba, decode)

        return decode

    def _keyboard_patch_(self, echo: str, cap_strikes: str) -> None:
        """Patch the Keyboard with a Key Cap and its Strikes"""

        self._keyboard_remove_(echo)
        self._keyboard_add_(echo, cap_strikes=cap_strikes)

    def _keyboard_add_(self, echo: str, cap_strikes: str) -> None:

        decode = self.cap_strikes_to_decode(cap_strikes, echo=echo)
        self._keyboard_add_decode_(decode, echo=echo)

    def _keyboard_add_decode_(self, decode: str, echo: str) -> None:
        """Add a Key Cap and its Byte Encoding to a Keyboard"""

        assert decode, (decode, echo)

        decode_by_echo = self.decode_by_echo
        echoes_by_decode = self.echoes_by_decode

        assert echo not in decode_by_echo, (echo, decode_by_echo[echo])
        decode_by_echo[echo] = decode

        if decode not in echoes_by_decode:
            echoes_by_decode[decode] = tuple()
        echoes_by_decode[decode] += (echo,)  # todo: struggling with tuple

    def _keyboard_remove_(self, echo: str) -> None:
        """Remove a Key Cap and its Byte Encoding from a Keyboard"""

        decode_by_echo = self.decode_by_echo
        echoes_by_decode = self.echoes_by_decode

        assert echo in decode_by_echo.keys(), (echo,)
        old_decode = decode_by_echo[echo]
        del decode_by_echo[echo]  # todo: 'del ...' vs '... = ""'

        assert old_decode in echoes_by_decode.keys(), (old_decode,)
        old_echoes = list(echoes_by_decode[old_decode])  # todo: struggling with tuple
        old_echoes.remove(echo)
        echoes_by_decode[old_decode] = tuple(old_echoes)

    def _form_i_term_app_keyboards_(self) -> None:
        """Form a macOS iTerm2 Keyboard"""

        decode_by_echo = self.decode_by_echo
        plain_caps = KeyboardDecoder.PlainCaps
        shift_caps = KeyboardDecoder.ShiftCaps

        # 1.1 ⎋
        # 1.2 ⎋⌃
        # 1.3 ⎋⇧
        # 1.4 ⎋⌃⇧

        pass  # todo: "Use Option as Meta key" not found in macOS iTerm2

        # 2.1 ''

        pass

        # 2.2 ⌃

        self._keyboard_patch_("⌃⌫", cap_strikes="010")  # ⌃H

        self._keyboard_remove_("⌃⇥")

        self._keyboard_add_("⌃`", cap_strikes="140")  # `
        self._keyboard_add_("⌃1", cap_strikes="061")  # 1
        self._keyboard_add_("⌃2", cap_strikes="000")  # ⌃⇧@
        self._keyboard_add_("⌃3", cap_strikes="033")  # ⌃[
        self._keyboard_add_("⌃4", cap_strikes="003")  # ⌃C
        self._keyboard_add_("⌃5", cap_strikes="035")  # ⌃]
        self._keyboard_add_("⌃6", cap_strikes="036")  # ⌃⇧^
        self._keyboard_add_("⌃7", cap_strikes="037")  # ⌃⇧_
        self._keyboard_add_("⌃8", cap_strikes="177")  # ⌫
        self._keyboard_add_("⌃9", cap_strikes="071")  # 9
        self._keyboard_add_("⌃0", cap_strikes="060")  # 0
        self._keyboard_add_("⌃=", cap_strikes="075")  # =
        self._keyboard_add_("⌃/", cap_strikes="037")  # ⌃⇧_

        # 2.3 ⌃⌥

        self._keyboard_patch_("⌃⌥␢", cap_strikes="040")  # Spacebar
        self._keyboard_arrow_patch_("⌃⌥", caps="←↑→↓", shifts_index=7)

        # 2.4 ⌃⌥⇧

        self._keyboard_arrow_patch_("⌃⌥⇧", caps="←↑→↓", shifts_index=8)

        # 2.5 ⌃⇧ # todo2: less struggle to form iTerm2 ⌃⇧ Keyboard

        for old_cap, new_cap in zip(plain_caps, shift_caps):
            old_echo = "⌃⌥" + old_cap
            new_echo = "⌃⇧" + new_cap

            decode = decode_by_echo[old_echo]
            if new_echo in decode_by_echo.keys():
                self._keyboard_remove_(new_echo)

            self._keyboard_add_decode_(decode, echo=new_echo)

        self._keyboard_remove_("⌃⇧⇥")

        self._keyboard_patch_("⌃⇧@", cap_strikes="000")  # ⌃⇧@

        self._keyboard_patch_("⌃⇧^", cap_strikes="036")  # ⌃⇧^
        self._keyboard_patch_("⌃6", cap_strikes="036")  # ⌃⇧^
        self._keyboard_patch_("⌃⌥⇧^", cap_strikes="036")  # ⌃⇧^

        self._keyboard_patch_("⌃⇧⌫", cap_strikes="010")  # ⌃H
        self._keyboard_patch_("⌃⇧?", cap_strikes="177")  # ⌫

        self._keyboard_arrow_patch_("⌃⇧", caps="←↑→↓", shifts_index=6)

        # 2.6 ⌥

        self._keyboard_arrow_patch_("⌥", caps="←↑→↓", shifts_index=3)

        # 2.7 ⌥⇧

        self._keyboard_arrow_patch_("⌥⇧", caps="←↑→↓", shifts_index=4)

        # 2.8 ⇧

        self._keyboard_arrow_patch_("⇧", caps="↑↓", shifts_index=2)

    def _keyboard_arrow_patch_(self, shifts: str, caps: str, shifts_index: int) -> None:

        octet_by_arrow = {"←": "104", "↑": "101", "→": "103", "↓": "102"}  # 'ABCD'

        for cap in caps:
            echo = shifts + cap

            arrow_octet = octet_by_arrow[cap]

            shifts_code = ord(str(shifts_index))
            shifts_octet = f"{shifts_code:03o}"

            cap_strikes = f"033.133.061.073.{shifts_octet}.{arrow_octet}"

            self._keyboard_patch_(echo, cap_strikes=cap_strikes)

            # todo: patch vs add in ._keyboard_arrow_patch_


    #
    # Speak of a Byte Encoding as a Sequence of Chords of Key Caps
    #

    def bytes_to_one_main_echo(self, data: bytes) -> str:
        """Form a brief Repr of one Input Frame"""

        assert data, (data,)

        box = BytesBox(data)
        text = box.text

        # Show Key Caps, if available as ⌫ ⇧⇥ ⇥ etc

        echoes = self.bytes_to_echoes_if(data)
        if echoes:
            echo = echoes[0]
            assert echo.isprintable(), (echo,)
            return echo  # ⌫  # ⇧⇥  # ⇥  # ⏎

        # Show the unquoted Repr, if not decodable

        if not text:
            echo = repr(data)[1:-1]
            assert echo.isprintable(), (echo,)
            return echo

        # Show one Key Cap per Character, if decodable

        echo = ""
        for t in text:
            encode = t.encode()
            echoes = self.bytes_to_echoes_if(encode)
            e = echoes[0] if echoes else repr(t)[1:-1]
            echo += e

        assert echo.isprintable(), (echo,)
        return echo

    def echo_split_shifters_cap(self, echo: str) -> tuple[str, str]:
        """Split out the Shifters at left, and add 'Fn' if Fn"""

        shifters = ""
        for t in echo:
            if t not in "⎋ ⌃ ⌥ ⇧".split():  # .t can be 'F' or 'n' but never 'Fn'
                break
            shifters += t

        cap = echo[len(shifters) :]
        if cap == "<>":
            cap = ""  # ('', '') from '<>'
        elif not cap and shifters.endswith("⎋"):
            shifters = str_removesuffix(shifters, suffix="⎋")
            cap = "⎋"  # ('', '⎋') from '⎋'
        elif cap.startswith("F") and (cap != "F"):
            shifters += "Fn"
            if cap == "Fn":
                cap = ""  # ('Fn', '') from 'Fn'

        return (shifters, cap)

        # ('', '')  # ('⇧', '⎋')  # ('Fn', '')  # ('⌃⇧', '@')  # ('⇧Fn', 'F1')

    def bytes_to_echoes_if(self, data: bytes) -> tuple[str, ...]:
        """Speak of a Byte Encoding as Sequences of Chords of Key Caps"""

        text = data.decode()

        echoes_by_decode = self.echoes_by_decode

        if text in echoes_by_decode.keys():
            echoes = echoes_by_decode.get(text, tuple())
            return echoes

            # tuple of '⎋', of '␢', of '⌥` E', of '⌥⇧⇥', of '⌃⌥⇧Fn'

        return tuple()


_FactorMark_ = "\025"  # 01/05 ⌃U Emacs Global-Map Universal-Argument

ClassicArrows = ("\033[A", "\033[B", "\033[C", "\033[D")

_NorthArrow_ = "\033[A"  # ←↑→↓ reordered as ↑↓→←
_SouthArrow_ = "\033[B"
_EastArrow_ = "\033[C"
_WestArrow_ = "\033[D"

CPR_Y_X = "\033[" "{};{}R"  # ⎋[y;x⇧R

DSR0 = "\033[" "0n"  # DSR_PS Ps 0

_NorthwestArrow_ = "\033[↖"  # ⎋[ ↖↗↘↙  # not yet standard
_NortheastArrow_ = "\033[↗"
_SoutheastArrow_ = "\033[↘"
_SouthwestArrow_ = "\033[↙"


#
# Frame Bytes of Input, as an ⎋ Esc Sequence, else simply
#


def _try_key_byte_frame_() -> None:
    """Try KeyByteFrame things"""

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

    # Accept ↖↗↘↙ Intercardinal Arrows, not just ←↑→↓ Cardinal Arrows

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


@dataclasses.dataclass(order=True)  # , frozen=True)
class KeyByteFrame:
    """Frame Bytes of Input, as an ⎋ Esc Sequence, else simply"""

    encodes: bytearray  # b''  # Decodable Printable Text

    head: bytearray  # b''  # N * ESC  # N * ESC + CSI  # N * ESC + SS3  # OSC
    neck: bytearray  # b''  # Csi Params  # Osc Payload
    backtail: bytearray  # b''  # Csi Intermediates and Final  # Osc Terminator

    stash: bytearray  # b''  # 1..3 Bytes taken while not printable

    closed: bool

    def __init__(self, data: bytes) -> None:

        self.encodes = bytearray()

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

        encodes = self.encodes
        head = self.head
        neck = self.neck
        backtail = self.backtail
        stash = self.stash

        encodes.clear()
        head.clear()
        neck.clear()
        backtail.clear()
        stash.clear()

        self.closed = False

    def tilt_to_close_frame(self) -> None:
        """Transform into a Closed DL_Y without explicit Pn, if it was _CLICK3_ and no Stash"""

        encodes = self.encodes
        head = self.head
        neck = self.neck
        backtail = self.backtail
        stash = self.stash
        closed = self.closed

        assert _CLICK3_ == "\033[M"
        assert DL_Y == "\033[" "{}M"

        data = self.to_frame_bytes()

        if data == b"\033[M":  # takes the ⎋[⇧M DL_Y that isn't the ⎋[⇧M{b}{x}{y} _CLICK3_
            assert (not encodes) and (not neck) and (not backtail), (head, self, data)
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

        encodes = self.encodes

        head = self.head
        neck = self.neck
        backtail = self.backtail

        stash = self.stash

        join = bytes(encodes + head + neck + backtail + stash)

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

        encodes = self.encodes
        head = self.head
        neck = self.neck
        backtail = self.backtail
        stash = self.stash

        assert CSI == "\033["

        if (head != b"\033[") or encodes or stash or (not backtail):
            return (b"", tuple())

        fm = re.fullmatch(rb"^([^0-9;]*)([0-9;]*)(.*)$", string=neck + backtail)
        assert fm, (fm, neck, backtail)

        marks = fm.group(1) + fm.group(3)
        ints_bytes = fm.group(2)

        ints: tuple[int, ...] = tuple()
        if ints_bytes:
            ints = tuple((int(_) if _ else -1) for _ in ints_bytes.split(b";"))

        return (marks, ints)

        # (b"A", []) for "\033[A"
        # (b"H", [123, -1]) for "\033[123;H"

        # todo9: give examples of corners of .to_csi_marks_ints_if

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

        encodes = self.encodes
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

        assert not encodes, (encodes,)

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

        encodes = self.encodes
        head = self.head

        # Take 1 Decoded Printable Char, without closing the Frame

        if text:
            if text.isprintable():
                encodes.extend(data)
                return b""

        # End a Text Frame before Unprintable or Undecodable Bytes

        if encodes:
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

            # doesn't take ⇧M after \⎋[ here

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

        assert Apple == "\uf8ff"

        if not data:
            assert not text, (data, text)
            return True

        if not text:
            return False

        printable = text.replace(Apple, "-").isprintable()

        return printable


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
# Amp up Import Logging
#


def logger_print(*args: object) -> None:
    """Send the Repr's as Logger Info, but drop the droppable quotes"""

    texts = list()
    for index, arg in enumerate(args):
        rindex = index - len(args)

        text = repr(arg)

        if isinstance(arg, str):
            q = text[:1]
            assert q in ("'", '"', text)
            assert text[:1] == text[-1:] == q, (text[:1], text[-1:], q, text)

            if (rindex == -1) or (" " not in text):
                text = text[len(q) : -len(q)]

        texts.append(text)

    join = " ".join(texts)
    logger.info(join)


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

    assert Apple == "\uf8ff"  # U+F8FF  # last of U+E000 .. U+F8FF Private Use Area (PUA)

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
    #   doesn't send its ↖ ↗ ↘ ↙ double key jams encoded as ⎋[ U+2196..U+2199 Diagonal Arrows
    #
    # June/1993 Unicode 1.1.0 gave us ↖ ↗ ↘ ↙, among its U+2190 .. U+219F Symbols And Arrows
    #

    #
    # We mention in Source Strings but run no Tests of Unicode Characters
    #
    #   U+2588 alone, U+2588 paired, U+FB01, & U+FB02
    #
    #       █ ██ ﬁ ﬂ
    #
    #   Much of U+0131 .. U+25CA
    #
    #       ıŒœŸƒˆˇ˘˙˚˛˜˝́Ωπ–—‘’‚“”„†‡•…‰‹›⁄€™←↑→↓⇥⇧⇪∂∆∏∑√∞∫≈≠≤≥⌃⌘⌥⌫⎋⏎␢◊
    #
    #   Some of U+00A1 .. U+00F8
    #
    #       ¡¢£¥§¨©ª«¬®¯°±´µ¶·¸º»¿Çßç÷ø
    #

    #
    # macOS Terminal Profiles  # see also docs/rgb-themes.py
    #
    #   Basic
    #   Clear Dark
    #   Clear Light
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
# Amp up Import Tty
#


class KeyboardScreenIOWrapper:
    """Talk with one KeyboardReader and one ScreenWriter"""

    selves: list[KeyboardScreenIOWrapper] = list()

    stdio: typing.TextIO  # sys.__stderr__  # todo: try open("/dev/tty", "r+")
    fileno: int  # 2
    tcgetattr: list[int | list[bytes | int]]  # replaced by .__enter__

    screen_writer: ScreenWriter
    keyboard_reader: KeyboardReader

    def __init__(self) -> None:

        KeyboardScreenIOWrapper.selves.append(self)

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

        ks = KeyboardScreenIOWrapper.selves[-1]
        ks.__exit__()

        breakpoint()  # Pdb likes:  where, up, down, ks = None, continue
        pass  # Pdb likes:  where, up, down, ks = None, continue

        if ks:
            ks.__enter__()

        # KeyboardScreenIOWrapper._breakpoint_()

    def __enter__(self) -> KeyboardScreenIOWrapper:
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
            logger_print(f"{reads_ahead=} {fileno=}")

        # Flush Output, drain Input, and change Input Mode

        stdio.flush()  # before 'termios.tcsetattr' of TerminalStudio.__exit__

        fd = fileno
        when = termios.TCSADRAIN
        attributes = tcgetattr
        termios.tcsetattr(fd, when, attributes)

        self.tcgetattr = list()  # replaces

        # todo: try termios.TCSAFLUSH to discard Input while exiting

    def write_text_encode(self, text: str) -> None:
        """Write a Text, encoded as Bytes"""

        data = text.encode()  # may raise UnicodeEncodeError
        self.write_some_bytes(data)

    def write_some_bytes(self, data: bytes) -> None:
        """Write zero or more Bytes"""

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


# todo0: Take up the many many 2 ** (⎋ ⌃ ⇧) Letter Keys of Ghostty


# todo0: Fork the KeyboardDecoder
# todo0: Write out the test results in order, with ¤ for Chords that send no Bytes
# todo0: Diff each vs Terminal and mention the Ghostty ⎋⌃/ Bell

# todo0: Name the Terminal Results, for copy-editing into the rest


# todo1: Take up the Fn Keys
# todo1: Draw the F11 as can't be reached, except indirectly via ⌥⇧F6 etc


# todo2: Revive passing test of buffer key input jam in sleep before launch
# todo2: Solve iTerm2 Key Jams with ⎋[5N sent down, not written outside
# todo2: Take up the Multichord Key Strikes with Shifter Keys
# todo2: Take up the Intercardinal Arrows with Shifter Keys


# todo3: Sort the Echoes of each Encode by (⎋ ⌃ ⌥ ⇧ Fn)

# todo4: Switch keyboards to random choice of elsewheres
# todo4: Speak missed Keys as sourcelines to add

# todo5: emulate macOS Terminal Writes at Google Cloud Shell OR vice versa
# todo5: deletes while backlight, color filling from eastmost mirrored character write

# todo6: take ⎋ or ⎋⎋ more as itself, don't force it into starting an Intricate Key Chord Sequence
# todo6: Alt + Number ⌥1⌥2⌥3 key cap
# todo6: <> could make button <F12> <⌥1⌥2⌥3>
# todo6: revisit 'pm Tue 16/Dec' experiments in echo-in-place of Key Caps such as F12 and ⌥6⌥5

# todo8: take bracketed-paste as print vertically

# todo9: --egg=resize to fit the Terminal to the Gameboard and vice versa
# todo9: pick apart text key jams and unbracketed text paste

# todo9: show settings
# todo9: place input echoes on the side
# todo9: vs scroll while echo of ScreenChangeOrder's in the far Southeast


# 3456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/litglass.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
