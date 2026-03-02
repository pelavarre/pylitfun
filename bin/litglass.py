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
# ./litglass.py --egg=rubik  # to launch our Rubik's Cube Game
# ./litglass.py --egg=squares  # to launch our Squares Game

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

# import time
# t0 = time.time()

import __main__
import argparse
import ast
import bdb
import collections
import collections.abc  # .collections.abc is not .abc & collections.abc.Callable is not typing.Callable
import dataclasses
import datetime as dt
import difflib
import functools
import itertools
import logging
import math
import os
import pathlib
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

# t1 = time.time()
# print(t1 - t0)  # ~50ms for 30 Imports at 3/Jan/2026
# sys.exit(2)


_: object  # blocks Mypy from narrowing the Datatype of '_ =' at first mention

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 than python3 -O'


ImportStamp = dt.datetime.now().astimezone()


AppleLogo = "\uf8ff"  # Apple  occupies U+F8FF = last of U+E000 .. U+F8FF Private Use Area (PUA)

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
    #   flags._repr_, flags.rubik, flags.squares
    #

    _assert_: bool = False  # assert False before doing much
    byteloop: bool = False  # loop back without adding latencies
    color_picker: bool = False  # show Color Choices and tweak them
    echoes: bool = False  # echo the Control Sequences as they loopback
    keycaps: bool = False  # launch our Keyboard-Viewer of Leycaps
    _repr_: bool = False  # loop the Repr, not the Str
    rubik: bool = False  # launch our Rubik's Cube Game
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
        games += self.rubik
        games += self.squares

        if games > 1:
            print(
                "Choose at most one of:"
                "  assert, byteloop, color-picker, echoes, keycaps, repr, rubik, squares",
                file=sys.stderr,
            )
            sys.exit(2)  # exits 2 for bad args

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
            rkg = RubikGame(tb)
            sqg = SquaresGame(tb)

            now = dt.datetime.now().astimezone()
            boss = (now - MainStamp).total_seconds()
            boss_clip = clip_metric(boss)
            logger.info("%s", f"and spent {boss_clip}s to launch TerminalBoss")

            if flags.byteloop:
                tb.tb_run_byteloop()
            elif flags.color_picker:
                cpg.cp_run_awhile()
            elif flags.keycaps:
                kcg.kc_run_awhile()
            elif flags.rubik:
                rkg.rk_run_awhile()
            elif flags.squares:
                sqg.sq_run_awhile()
            else:
                tb.tb_run_awhile()

            # todo1: logger_print vs logger.info

    def logging_resume(self) -> None:
        """Open up a new Logging Session at our .logger"""

        pathname = "__pycache__/litglass.log"
        os.makedirs("__pycache__", exist_ok=True)
        logging.basicConfig(
            filename=pathname,  # appends, doesn't restart
            level=logging.INFO,  # .INFO and above
            format="%(message)s",  # omits '%(levelname)s:%(name)s:'
        )

        path = pathlib.Path(pathname)
        if not path.is_file():

            logger_print("")
            logger_print("")
            logger_print("launched")
            logger_print("")

        else:
            stat = path.stat()
            mtime = stat.st_mtime

            # naive = dt.datetime.fromtimestamp(mtime)
            # aware = naive.astimezone()

            # now = dt.datetime.now().astimezone()

            # _import_ = (ImportStamp - aware).total_seconds()
            # import_clip = clip_metric(_import_)

            # _main_ = (MainStamp - aware).total_seconds()
            # main_clip = clip_metric(_main_)

            # launch = (now - aware).total_seconds()
            # launch_clip = clip_metric(launch)

            t = time.time() - mtime

            logger_print("")
            logger_print("")
            logger_print(f"launched and spent {clip_metric(t)}s since {mtime=}")
            # logger_print(f"{mtime=}")
            # logger_print(f"{globals().get("t0")=}")
            # logger_print(f"{import_clip=}")
            # logger_print(f"{main_clip=}")
            # logger_print(f"{launch_clip=}")
            # logger_print(f"{time.time()=}")

        # todo2: why "⌃\'" in place of "⌃'" in our logs
        logger_print(repr("⌃'"), repr('⌃⇧"'), "overly escaped : -(")  # todo3

        logger_print("")

        #
        # default Python .logging
        #
        #       drops many .INFO, .DEBUG, .NOTSET as < 30 .WARNING - # secretly, silently, uncountably
        #       tags many lines at left with like 'INFO:__main__:'
        #

    def arg_doc_to_parser(self, doc: str) -> ArgDocParser:
        """Declare the Options & Positional Arguments"""

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
        self, eggs: list[str] | None, print_usage: collections.abc.Callable[[], None]
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
                    sys.exit(2)  # exits 2 for bad args

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

        _try_clip_()

        _try_keyboard_decoder_()
        _try_key_byte_frame_()
        _try_unicode_source_texts_()

        t1 = time.time()
        t1t0 = t1 - t0
        if t1t0 > 250e-6:
            logger_print(f"spent {clip_metric(t1t0)}s on self-test")


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

        dent4 = 4 * " "

        # Find the present Color

        ps = 0o20 + (r * 36) + (g * 6) + b

        # Place the board

        if game_yx:
            y, x = game_yx
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

        sw.print(dent4 + gap + n + dent4)
        sw.print()
        sw.print(dent4 + f"rgb color {r} {g} {b} is {ps=}" + dent4)
        sw.print()
        sw.print(dent4 + gap + s + dent4)

        sw.print()
        sw.print()  # twice

        y_high += 2 + 5 + 2

        # Draw the Board per se

        sw.write_control(f"\033[38;5;{ps}m")

        for _ in range(3):
            sep = "\033[2C"
            text = dent4 + "█" + sep + "██" + sep + "███" + sep + "██" + sep + "█" + dent4 + "\r\n"
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
            h, w, y, x = kr.sample_hwyx()
            y -= y_high
            game_yx = (y, x)  # replaces

        # Revert to TerminalBoss Cursor, but change which Color it draws

        sw.write_control(f"\033[38;5;{ps}m")

        if not first:
            ya, xa = (kr.row_y, kr.column_x)
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

    tangible_keyboard: str

    shifts: str
    wipeouts_by_shifts: dict[str, list[str]]
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

        self.terminal_boss = terminal_boss
        self.game_yx = tuple()
        self.chat_yx = tuple()
        self.scrollables = list()

        self.tangible_keyboard = ""  # mostly unneeded

        shifts = ""  # none of ⎋ ⌃ ⌥ ⇧
        self.shifts = shifts

        self.wipeouts_by_shifts = dict((_, list()) for _ in KeyboardDecoder.ShortcutShifts)
        self.wipeouts = self.wipeouts_by_shifts[shifts]

        self.kc_echo_index = 0

        tangible_keyboard = self.kc_tangible_keyboard()
        self.tangible_keyboard = tangible_keyboard

    def kc_run_awhile(self) -> None:
        """Trace Key Releases till ⌃C"""

        tb = self.terminal_boss

        sw = tb.screen_writer
        kr = tb.keyboard_reader

        paste_shifts = KeyboardDecoder.FamiliarShifts
        if flags.ghostty:
            paste_shifts = tuple(_ for _ in KeyboardDecoder.FamiliarShifts if "⌥" not in _)

        join = " ".join((_ if _ else "''") for _ in paste_shifts)

        sw.print()
        sw.print(r"Paste your choice of", join)
        sw.print()

        # Draw the Gameboard, scrolling if need be

        sw.write_control("\033[?25l")

        game_yx = self.kc_game_draw()
        self.game_yx = game_yx  # replaces

        h, w, y, x = kr.sample_hwyx()
        self.chat_yx = (y, x)  # replaces

        # Run till Quit

        now = dt.datetime.now().astimezone()
        kc = (now - MainStamp).total_seconds()
        kc_clip = clip_metric(kc)
        logger.info("%s", f"and spent {kc_clip}s to launch KeycapsGame")

        while not tb.quitting:

            # Read Input

            kr.kbhit(timeout=None)
            frames = tb.tb_read_byte_frames()

            # Eval Input and print Output

            self.kc_step_once(frames)

        sw.print()

        # todo1: logger_print vs logger.info

        # todo9: --egg=keycaps: toggle back out of @@@@@@@@@ or @@ or @
        # todo9: --egg=keycaps: take mouse hits to the Keyboard viewed

    def kc_step_once(self, frames: tuple[bytes, ...]) -> None:
        """Eval Input and print Output"""

        tb = self.terminal_boss
        sw = tb.screen_writer
        kr = tb.keyboard_reader
        kd = tb.keyboard_decoder

        wipeouts_by_shifts = self.wipeouts_by_shifts

        twelve_fn_meta_control_p = KeyboardDecoder.TwelveFnMetaControlP

        assert ord("C") ^ 0x40 == ord("\003")  # ⌃C
        assert ord("\\") ^ 0x40 == ord("\034")  # ⌃\

        assert unicodedata.name("¤").title() == "Currency Sign".title()

        # Eval each Input Frame

        unhit_kseqs: list[object] = list()

        h, w, y, x = kr.sample_hwyx()

        for frame in frames:
            echoes = kd.bytes_to_echoes_if(frame)

            # Strike the Key Caps from which the Bytes may have come

            if echoes:

                finds = self.kc_press_keys_if(echoes, unhit_kseqs)
                if not finds:
                    unhit_kseqs.clear()
                    if not tb.quitting:
                        self.kc_switch_tab(echoes)
                        self.kc_press_keys_if(echoes, unhit_kseqs)

            # Switch to the Keyboard Tab named by Paste

            else:

                shifts = self.shifts
                if len(frames) == 1:  # todo: Shifts pasted as multiple Frames
                    frame = frames[-1]

                    text = frame.decode()  # todo: UnicodeDecodeError from Paste
                    key = text.replace("//", "").strip().strip('"').strip("'")
                    if key in wipeouts_by_shifts.keys():
                        shifts = key

                if shifts != self.shifts:
                    self.kc_switch_tab(echoes=(shifts,))

            # Trace the Bytes taken in

            echoes = kd.bytes_to_echoes_if(frame)
            join = " ".join(_.replace(" ", "") for _ in echoes)
            if not echoes:
                join = kd.bytes_to_one_main_echo(frame)
            if frame == b"\033\020":
                assert join.split() == twelve_fn_meta_control_p.split()
                join = "⎋⌃P ⎋⌃⇧P ⎋⇧F1 ... ⎋⌃... ⎋⌃⇧... ⎋⌃⇧F12"

            str_shifts = str(self.shifts) if self.shifts else "''"
            self.kc_print(str_shifts, " " + str(frame), " " + join + " ", self.kc_echo_index)
            self.kc_echo_index += 1

            y = kr.row_y

        sw.write_control(f"\033[{y};{x}H")  # row-column-leap ⎋[⇧H

        if unhit_kseqs:
            if frames == (b"\003",):  # ⌃C
                pass
            elif frames == (b"\034",):  # ⌃\
                pass
            else:
                self.kc_print(unhit_kseqs, frames, "not found")

        # todo9: Shuffle the Byte Trace Panel up above the Panel of Press ⌃C etc, or don't

        # todo2: Test KeyCaps vs Bracketed Paste, not only vs Unbracketed Paste

    def kc_game_draw(self) -> tuple[int, int]:
        """Draw the Gameboard, scrolling if need be"""

        tb = self.terminal_boss
        kr = tb.keyboard_reader
        kd = tb.keyboard_decoder
        sw = tb.screen_writer

        echoes_by_decode = kd.echoes_by_decode

        shifts = self.shifts
        assert shifts in KeyboardDecoder.ShortcutShifts, (shifts,)
        tangible_keyboard = self.tangible_keyboard

        assert EL_PS == "\033[" "{}" "K"

        # Scroll to make Rows in the South, if need be, like after:  seq 987

        sep = 1  # 1 in the North, 1 in the South, 1 between Board & Hello, 1 between Hello & Chat
        high = sep + 6 + sep + 1 + sep + 3 + sep  # todo: measure how high, don't guess
        wide = 4 + 48 + 4  # todo: measure how wide, don't guess

        n = high - 1  # 1 Southernmost comes free by Convention
        sw.write_some_controls(n * ["\n"])
        sw.write_some_controls(n * ["\033[A"])

        # Place the Gameboard

        h, w, y, x = kr.sample_hwyx()

        assert h >= high, (h, high)  # todo: negotiate Height more gracefully
        assert w >= wide, (w, wide)  # todo: negotiate Width more gracefully

        # Form the Rows of the Gameboards

        enter = "\033[7m"  # ⎋[7m reverse
        exit = "\033[27m"  # ⎋[27m reverse-not

        exit_caps = self.kc_exit_caps()

        text = tangible_keyboard
        for cap in exit_caps:
            render = cap
            repl = enter + render + exit

            regex = r"( |\n|^)(" + re.escape(render) + r")( |\n|$)"  # todo2: merge 4 copies
            matches = list(re.finditer(regex, string=text))
            assert len(matches) == 1, (matches, regex, render)
            m = matches[-1]
            assert m.group(2) == render

            index = m.start() + len(m.group(1))
            text = text[:index] + repl + text[index + len(render) :]

        dent4 = 4 * " "
        splitlines = text.splitlines()

        # Print each Row

        sw.print()
        for line in splitlines:
            text = dent4 + line + dent4

            sw.write_text(text)
            sw.write_control("\033[K")
            sw.write_some_controls(["\r", "\n"])

        # Print a Trailer in the far Southeast

        echoes = echoes_by_decode["\003"] + echoes_by_decode["\034"]
        join = " or ".join(sorted(echoes))

        sw.write_control("\033[K")
        sw.write_some_controls(["\r", "\n"])

        sw.print(r"Press", join, "to quit")  # Press ⌃C or ⌃\ or ... to quit
        sw.print()

        # Succeed

        return (y, x)

        # todo: .kc_game_draw well onto larger & smaller Screens

        # todo: say which Keyboards have no distinct Echoes - ⌃⌥⇧ Terminal, ⌃⌥ Terminal, and what?
        # todo: never speak of ⌃⌥⇧ reversed ⇧⌥⌃|⇧⌥|⇧⌃|⌥⌃ or shuffled ⌃⇧⌥|⌥⌃⇧|⇧⌃⌥
        # todo: never speak of ⌃⌥⇧ downshifted ⇧`|⇧-|⇧=|⇧\[|⇧\]|⇧\\|⇧;|⇧'|⇧,|⇧\.|⇧/
        # todo: never speak of ↑← ↑→ ↓→ ↓← reversed ←↑|→↑|→↓|←↓, except as part of ←↑→↓

    def kc_exit_caps(self) -> tuple[str, ...]:
        """Find the Key Caps that will quit the Game"""

        shifts = self.shifts

        exit_caps: tuple[str, ...] = tuple()
        if shifts == "⌃":
            exit_caps = ("C", "\\")
            if flags.i_term_app or flags.ghostty or flags.google:
                exit_caps = ("4", "C", "\\")
        elif shifts == "⌃⌥":
            exit_caps = ("C", "\\")
        elif shifts == "⌃⇧":
            if flags.i_term_app:
                exit_caps = ("C", "|")
            elif flags.ghostty:
                exit_caps = ("$",)
            else:
                exit_caps = ("|",)
        elif shifts == "⌃⌥⇧":
            exit_caps = ("C", "|")

        return exit_caps

    def kc_tangible_keyboard(self) -> str:
        """Draw a Keyboard but blank out its intangible Key Caps"""

        shifts = self.shifts

        # Add Key Caps

        keyboard = self.ShiftedKeyboard
        if "⇧" not in shifts:
            keyboard = self.PlainKeyboard
            if shifts:
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

        shifts = self.shifts

        echoes = keyboard.split()
        for echo in echoes:
            echo_plus = shifts + ("␢" if (echo == "Spacebar") else echo.upper())
            echo_plus_key = (shifts + "F5") if (echo == "Fn") else echo_plus  # todo1: Fn if any Fn

            tangible = False
            if echo_plus_key in decode_by_echo.keys():
                decode = decode_by_echo[echo_plus_key]
                assert decode, (decode, echo_plus_key)

                tangible = True  # todo: why split the .echo_plus that we joined?
                _shifts_, _cap_ = kd.echo_split_shifts_cap(echo_plus)
                if (_shifts_ != shifts) or (not _cap_):
                    if echo != shifts:

                        tangible = False

            if not tangible:
                if (echo == "⎋") or (echo not in tuple(shifts)):
                    render = echo

                    repl = len(echo) * " "
                    if (echo == "⌥") and ("⎋" in shifts):
                        repl = "⎋"

                    regex = r"( |\n|^)(" + re.escape(render) + r")( |\n|$)"  # todo2: merge 4 copies
                    matches = list(re.finditer(regex, string=keyboard))
                    assert matches, (matches, regex, render)
                    for m in matches[:1]:
                        assert m.group(2) == render

                        index = m.start() + len(m.group(1))
                        keyboard = keyboard[:index] + repl + keyboard[index + len(render) :]

        return keyboard

    def kc_print(self, *args: object) -> None:

        chat_yx = self.chat_yx

        tb = self.terminal_boss  # todo9: layer KeycapsGame over KeyboardScreenIOWrapper?
        kr = tb.keyboard_reader
        sw = tb.screen_writer

        x_wide = kr.x_wide

        scrollables = self.scrollables

        join = " ".join(str(_) for _ in args)
        logger_print("kc_print", join)

        printable = join
        widest = x_wide - 1
        if len(join) > widest:
            i0 = widest - 10 - len(" ... ")
            printable = join[:i0] + " ... " + join[-10:]

            # todo8: solve for Screens less wide than 10 Columns

        y, x = chat_yx
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
        shifts = self.shifts
        wipeouts = self.wipeouts
        wipeouts_by_shifts = self.wipeouts_by_shifts

        game_y, game_x = game_yx
        assert wipeouts is wipeouts_by_shifts[shifts]

        # Switch Tabs

        assert echoes, (echoes,)

        echo = echoes[0]
        _shifts_, _cap_ = kd.echo_split_shifts_cap(echo) if echo else ("", "")
        if echo == "⎋":
            _shifts_ = "⎋"  # takes "⎋" as a Shifts Key, not as a Cap

        logger_print(f"{_shifts_=} {echoes=}  # kc_switch_tab")

        self.shifts = _shifts_  # replaces
        tangible_keyboard = self.kc_tangible_keyboard()
        self.tangible_keyboard = tangible_keyboard

        # Replay Wipeouts

        wipeouts = self.wipeouts_by_shifts[_shifts_]  # replaces
        self.wipeouts = wipeouts

        sw.write_control(f"\033[{game_y};{game_x}H")  # row-column-leap ⎋[⇧H
        self.kc_game_draw()

        renders = list(wipeouts)
        wipeouts.clear()

        for render in renders:
            regex = r"( |\n|^)(" + re.escape(render) + r")( |\n|$)"  # todo2: merge 4 copies
            matches = list(re.finditer(regex, string=tangible_keyboard))
            assert len(matches) == 1, (matches, regex, render)
            m = matches[-1]
            assert m.group(2) == render

            self.kc_wipeout_else_restore(m)

        assert wipeouts == renders, (wipeouts, renders)

    def kc_press_keys_if(self, echoes: tuple[str, ...], unhit_kseqs: list[object]) -> int:
        """Wipe out each Key Cap when pressed"""

        tb = self.terminal_boss
        kd = tb.keyboard_decoder

        tangible_keyboard = self.tangible_keyboard

        assert echoes, (echoes,)

        renders: list[str] = list()
        matches: list[re.Match[str]] = list()

        shifts = self.shifts
        for echo in echoes:
            _shifts_, _cap_ = kd.echo_split_shifts_cap(echo)

            # Search only once for each rendering of a Key Cap

            render = _cap_
            if (not _shifts_) and (not _cap_[1:]):
                render = _cap_.lower()
            if _cap_ == "␢":
                render = "Spacebar"

            # Remember where found

            regex = r"( |\n|^)(" + re.escape(render) + r")( |\n|$)"  # todo2: merge 4 copies
            more_matches = list(re.finditer(regex, string=tangible_keyboard))
            m: re.Match[str] | None = None
            if more_matches:
                assert len(more_matches) == 1, (matches, regex, render)
                m = more_matches[-1]
                assert m.group(2) == render

            if _shifts_ != shifts:
                pass  # logger_print(f"{_cap_!r} {echo!r}  # dropped for {_shifts_!r} vs {shifts!r}")
            elif not m:
                logger_print(f"{_cap_!r} {echo!r} {render!r} {echoes}  # dropped for not found")
            elif render in renders:
                continue
            else:
                renders.append(render)
                matches.append(m)

        for m in matches:
            self.kc_wipeout_else_restore(m)

        if not matches:
            unhit_kseqs.extend(echoes)

        return len(matches)

    def kc_wipeout_else_restore(self, m: re.Match[str]) -> None:
        """Wipe out each Key Cap, or restore, when found"""

        render = m.group(2)

        tb = self.terminal_boss
        game_yx = self.game_yx

        tangible_keyboard = self.tangible_keyboard
        wipeouts = self.wipeouts

        sw = tb.screen_writer
        game_y, game_x = game_yx

        # Form the Rows of the Gameboards

        find = m.start() + len(m.group(1))
        find_plus = find + 1

        found_lines = tangible_keyboard[:find_plus].splitlines()
        assert found_lines, (found_lines, find_plus, render)

        # Leap to this found Key Cap

        dent4 = 4 * " "

        y = game_y + len(found_lines)
        x = game_x + len(dent4) + len(found_lines[-1]) - 1

        sw.write_control(f"\033[{y};{x}H")  # row-column-leap ⎋[⇧H

        # Restore this Key Cap later, else wipe it out to begin with

        if render in wipeouts:
            wipeouts.remove(render)

            sw.write_printable(render)

        else:
            wipeouts.append(render)

            width = len(render)  # 1  # len("Spacebar")  # len("F12")

            sw.write_control("\033[1m")  # ⎋[1M style-bold
            sw.write_printable(width * "¤")
            sw.write_control("\033[m")  # ⎋[M style-plain

    # todo9: --egg=keycaps: restart in each Keyboard viewed
    # todo9: --egg=keycaps: save/ load progress in each Keyboard viewed
    # todo9: --egg=keycaps: celebrate near to winning, and celebrate winning

    #
    # Our Fn is for F1..F12 only, we don't test
    #
    #   Fn B, G, I J K L, O P, R S T U V W X Y Z
    #   Fn ⇧ B C, G H I J K L, N O P Q R S T U V W X Y Z
    #   Fn ⌃ A B, D E, G H I J K L M N O P Q, S T U V W X Y Z
    #   Fn ⌃ R has a sideband with Fn ⌃ F C Fn ⌃ when first struck, but comes through thereafter
    #
    #   iTerm2 agrees, Ghostty agrees
    #
    #   Google Cloud Shell adds Fn D E F M, Fn ⇧ D E F M, Fn ⌃ C F, and has no sideband on its Fn ⌃ R
    #


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

        h, w, y, x = kr.sample_hwyx()
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
        dent4 = 4 * " "

        # Place the Gameboard

        y, x = game_yx
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

            sw.write_printable(dent4 + y_text + dent4)
            sw.write_some_controls(["\r", "\n"])

        # Draw the Southern Decor and the Southern Border

        sw.print(dent4 + "  ↓    ↓  " + dent4)

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
        marks, ints = f.to_csi_marks_ints_if()

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
            y, x, wide = east_bar
            by_x = by_y_by_x[y]
            for xw in range(x, x + wide):

                by_x[xw] = "⬜"

    def sq_empty_south_poles(self, south_poles: list[tuple[int, int, int]]) -> None:
        """Erase each Cell of each South Pole"""

        by_y_by_x = self.by_y_by_x

        for south_pole in south_poles:
            y, x, high = south_pole
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
# Play for --egg=rubik
#


class RubikGame:
    """Play for --egg=rubik"""

    terminal_boss: TerminalBoss
    game_yx: tuple[int, ...]

    FACES_6 = 6

    Y_HIGH_PER_FACE_3 = 3
    X_WIDE_PER_FACE_3 = 3

    by_f_by_y_by_x: list[list[list[int]]]  # [face][row][column] = color

    ANSI_PS_BY_COLOR = [
        0o20 + 4 * 36 + 4 * 6 + 4,  # '#444' Off-White = 188  # Center
        0o20 + 0 * 36 + 3 * 6 + 0,  # '#030' Green = 34  # North
        0o20 + 5 * 36 + 0 * 6 + 0,  # '#500' Red = 196  # West
        0o20 + 0 * 36 + 0 * 6 + 4,  # '#004' Blue = 20  # East
        0o20 + 5 * 36 + 5 * 6 + 0,  # '#550' Yellow = 226  # South
        0o20 + 5 * 36 + 3 * 6 + 0,  # '#530' Orange = 214  # Far South
    ]

    def __init__(self, terminal_boss: TerminalBoss) -> None:

        self.terminal_boss = terminal_boss
        self.game_yx = tuple()

        rows = RubikGame.Y_HIGH_PER_FACE_3
        columns = RubikGame.X_WIDE_PER_FACE_3

        by_f_by_y_by_x = list()
        for f in range(RubikGame.FACES_6):
            # Start with a solved cube: each face has its own color
            color = f
            face = [[color for _ in range(columns)] for _ in range(rows)]
            by_f_by_y_by_x.append(face)

        self.by_f_by_y_by_x = by_f_by_y_by_x

    def rk_run_awhile(self) -> None:
        """Run till Quit"""

        tb = self.terminal_boss

        sw = tb.screen_writer
        kr = tb.keyboard_reader

        # Draw the Gameboard

        h, w, y, x = kr.sample_hwyx()
        self.game_yx = (y, x)

        self.rk_game_draw()

        # Run till Quit

        while not tb.quitting:

            # Read Input

            kr.kbhit(timeout=None)
            frames = tb.tb_read_byte_frames()

            # Eval Input and print Output

            self.rk_step_once(frames)

        sw.print()

    def rk_game_draw(self) -> None:
        """Draw the Rubik's Cube as a 2D unfolding in tee cross shape"""

        tb = self.terminal_boss
        sw = tb.screen_writer
        game_yx = self.game_yx

        y_high_per_face_3 = RubikGame.Y_HIGH_PER_FACE_3

        dent4 = 4 * " "
        dent6 = 6 * " "

        # Place the Gameboard

        y, x = game_yx
        sw.write_control(f"\033[{y};{x}H")

        sw.print()
        sw.print()

        # Number the Faces

        North = 1
        WestCenterEast = (2, 0, 3)
        South = 4
        FarSouth = 5

        # Draw the North Face, centered

        for face_y in range(y_high_per_face_3):
            f = North
            line = dent4 + dent6 + self.rk_render_face(f, face_y=face_y) + dent4
            logger_print(f"North face_y={face_y}: {line!r}")
            sw.write_text(line)
            sw.write_some_controls(["\r", "\n"])

        # Draw the Wide Row

        for face_y in range(y_high_per_face_3):
            line = dent4
            for f in WestCenterEast:
                line += self.rk_render_face(f, face_y=face_y)
            line += dent4
            logger_print(f"WestCenterEast face_y={face_y}: {line!r}")
            sw.write_text(line)
            sw.write_some_controls(["\r", "\n"])

        # Draw the South and FarSouth Faces, centered

        for face_y in range(y_high_per_face_3):
            f = South
            line = dent4 + dent6 + self.rk_render_face(4, face_y=face_y) + dent4
            logger_print(f"South face_y={face_y}: {line!r}")
            sw.write_text(line)
            sw.write_some_controls(["\r", "\n"])

        for face_y in range(y_high_per_face_3):
            f = FarSouth
            line = dent4 + dent6 + self.rk_render_face(5, face_y=face_y) + dent4
            logger_print(f"FarSouth face_y={face_y}: {line!r}")
            sw.write_text(line)
            sw.write_some_controls(["\r", "\n"])

        sw.print()
        sw.print("↑/↓: rotate Center face (0)")
        sw.print("←: rotate West face (2)")
        sw.print("→: rotate East face (3)")
        sw.print("Spacebar: scramble cube")
        sw.print("Press ⌃C to quit")
        sw.print()

        #
        #    1      # North
        #  2 0 3    # West Center East
        #    4      # South
        #    5      # Far South
        #

    def rk_render_face(self, face_idx: int, face_y: int) -> str:
        """Render one Row of a Rubik Face with Ansi #555 Colors"""

        by_f_by_y_by_x = self.by_f_by_y_by_x

        ansi_ps_by_color = RubikGame.ANSI_PS_BY_COLOR
        x_wide_per_face_3 = RubikGame.X_WIDE_PER_FACE_3

        face = by_f_by_y_by_x[face_idx]

        z = "█"

        result = ""
        for face_x in range(x_wide_per_face_3):
            color = face[face_y][face_x]
            ansi_ps = ansi_ps_by_color[color]

            result += f"\033[38;5;{ansi_ps}m" + z + z + "\033[m"

        return result

    def rk_step_once(self, frames: tuple[bytes, ...]) -> None:
        """Eval Input and print Output"""

        tb = self.terminal_boss
        kd = tb.keyboard_decoder

        # Check if all frames are arrows or space
        note_to_self = True
        for frame in frames:
            echoes = kd.bytes_to_echoes_if(frame)
            echo = echoes[0] if echoes else ""
            if echo not in ("←", "↑", "→", "↓", "␢"):
                note_to_self = False
                break

        if note_to_self:
            for frame in frames:
                self.rk_step_one_key_once(frame)
            self.rk_game_draw()
            return

        # Else fall back onto the enclosing TerminalBoss

        tb.tb_step_once(frames)

    def rk_step_one_key_once(self, frame: bytes) -> None:
        """Eval one Arrow or Space in the Frame"""

        tb = self.terminal_boss
        kd = tb.keyboard_decoder
        echoes = kd.bytes_to_echoes_if(frame)
        echo = echoes[0] if echoes else ""

        assert echo in ("←", "↑", "→", "↓", "␢"), (echo,)

        logger_print(f"rk_step_one_key_once: echo={echo!r}")

        # Space = scramble
        if echo == "␢":
            logger_print("  -> scrambling")
            self.rk_scramble()
            return

        # Arrow keys rotate faces:
        # ↑/↓ = Center face (0)
        # ←/→ = Center face (0)
        if echo == "↑":
            logger_print("  -> rotate Center face (0) clockwise")
            self.rk_rotate_face_clockwise(0)
        elif echo == "↓":
            logger_print("  -> rotate Center face (0) counterclockwise")
            self.rk_rotate_face_counterclockwise(0)
        elif echo == "→":
            logger_print("  -> rotate East face (3) clockwise")
            self.rk_rotate_face_clockwise(3)
        elif echo == "←":
            logger_print("  -> rotate West face (2) clockwise")
            self.rk_rotate_face_clockwise(2)

    def rk_rotate_face_clockwise(self, face_idx: int) -> None:
        """Rotate a face 90 degrees clockwise with full Rubik's Cube mechanics"""

        # Face layout:
        #      1 (North)
        #   2  0  3 (West, Center, East)
        #      4 (South)
        #      5 (FarSouth)

        face = self.by_f_by_y_by_x[face_idx]
        logger_print(f"  Before rotate CW face {face_idx}: {face}")

        # Rotate the face itself 90 degrees clockwise
        # New[row][col] = Old[2-col][row]
        new_face = [[0 for _ in range(3)] for _ in range(3)]
        for row in range(3):
            for col in range(3):
                new_face[row][col] = face[2 - col][row]

        self.by_f_by_y_by_x[face_idx] = new_face

        # Rotate adjacent edges based on which face is being rotated
        self.rk_rotate_edges_clockwise(face_idx)

        logger_print(f"  After rotate CW face {face_idx}: {self.by_f_by_y_by_x[face_idx]}")

    def rk_rotate_face_counterclockwise(self, face_idx: int) -> None:
        """Rotate a face 90 degrees counterclockwise with full Rubik's Cube mechanics"""

        face = self.by_f_by_y_by_x[face_idx]
        logger_print(f"  Before rotate CCW face {face_idx}: {face}")

        # Rotate the face itself 90 degrees counterclockwise
        # New[row][col] = Old[col][2-row]
        new_face = [[0 for _ in range(3)] for _ in range(3)]
        for row in range(3):
            for col in range(3):
                new_face[row][col] = face[col][2 - row]

        self.by_f_by_y_by_x[face_idx] = new_face

        # Rotate adjacent edges (3 clockwise = 1 counterclockwise)
        self.rk_rotate_edges_clockwise(face_idx)
        self.rk_rotate_edges_clockwise(face_idx)
        self.rk_rotate_edges_clockwise(face_idx)

        logger_print(f"  After rotate CCW face {face_idx}: {self.by_f_by_y_by_x[face_idx]}")

    def rk_rotate_edges_clockwise(self, face_idx: int) -> None:
        """Rotate the edges of adjacent faces when rotating a face clockwise"""

        # Face indices:
        # 0=Center, 1=North, 2=West, 3=East, 4=South, 5=FarSouth

        cube = self.by_f_by_y_by_x

        if face_idx == 0:  # Center face
            # Save North bottom row
            temp = [cube[1][2][0], cube[1][2][1], cube[1][2][2]]
            # North bottom <- West right column (reversed)
            cube[1][2][0] = cube[2][2][2]
            cube[1][2][1] = cube[2][1][2]
            cube[1][2][2] = cube[2][0][2]
            # West right column <- South top row
            cube[2][0][2] = cube[4][0][0]
            cube[2][1][2] = cube[4][0][1]
            cube[2][2][2] = cube[4][0][2]
            # South top row <- East left column (reversed)
            cube[4][0][0] = cube[3][2][0]
            cube[4][0][1] = cube[3][1][0]
            cube[4][0][2] = cube[3][0][0]
            # East left column <- temp (North bottom)
            cube[3][0][0] = temp[0]
            cube[3][1][0] = temp[1]
            cube[3][2][0] = temp[2]

        elif face_idx == 1:  # North face
            # Save Center top row
            temp = [cube[0][0][0], cube[0][0][1], cube[0][0][2]]
            # Center top <- West top row
            cube[0][0][0] = cube[2][0][0]
            cube[0][0][1] = cube[2][0][1]
            cube[0][0][2] = cube[2][0][2]
            # West top <- FarSouth top row (reversed)
            cube[2][0][0] = cube[5][0][2]
            cube[2][0][1] = cube[5][0][1]
            cube[2][0][2] = cube[5][0][0]
            # FarSouth top <- East top row
            cube[5][0][0] = cube[3][0][0]
            cube[5][0][1] = cube[3][0][1]
            cube[5][0][2] = cube[3][0][2]
            # East top <- temp (Center top)
            cube[3][0][0] = temp[0]
            cube[3][0][1] = temp[1]
            cube[3][0][2] = temp[2]

        elif face_idx == 2:  # West face
            # Save North left column
            temp = [cube[1][0][0], cube[1][1][0], cube[1][2][0]]
            # North left <- FarSouth left column
            cube[1][0][0] = cube[5][0][0]
            cube[1][1][0] = cube[5][1][0]
            cube[1][2][0] = cube[5][2][0]
            # FarSouth left <- South left column
            cube[5][0][0] = cube[4][0][0]
            cube[5][1][0] = cube[4][1][0]
            cube[5][2][0] = cube[4][2][0]
            # South left <- Center left column
            cube[4][0][0] = cube[0][0][0]
            cube[4][1][0] = cube[0][1][0]
            cube[4][2][0] = cube[0][2][0]
            # Center left <- temp (North left)
            cube[0][0][0] = temp[0]
            cube[0][1][0] = temp[1]
            cube[0][2][0] = temp[2]

        elif face_idx == 3:  # East face
            # Save North right column
            temp = [cube[1][0][2], cube[1][1][2], cube[1][2][2]]
            # North right <- Center right column
            cube[1][0][2] = cube[0][0][2]
            cube[1][1][2] = cube[0][1][2]
            cube[1][2][2] = cube[0][2][2]
            # Center right <- South right column
            cube[0][0][2] = cube[4][0][2]
            cube[0][1][2] = cube[4][1][2]
            cube[0][2][2] = cube[4][2][2]
            # South right <- FarSouth right column
            cube[4][0][2] = cube[5][0][2]
            cube[4][1][2] = cube[5][1][2]
            cube[4][2][2] = cube[5][2][2]
            # FarSouth right <- temp (North right)
            cube[5][0][2] = temp[0]
            cube[5][1][2] = temp[1]
            cube[5][2][2] = temp[2]

        elif face_idx == 4:  # South face
            # Save Center bottom row
            temp = [cube[0][2][0], cube[0][2][1], cube[0][2][2]]
            # Center bottom <- East bottom row
            cube[0][2][0] = cube[3][2][0]
            cube[0][2][1] = cube[3][2][1]
            cube[0][2][2] = cube[3][2][2]
            # East bottom <- FarSouth bottom row (reversed)
            cube[3][2][0] = cube[5][2][2]
            cube[3][2][1] = cube[5][2][1]
            cube[3][2][2] = cube[5][2][0]
            # FarSouth bottom <- West bottom row
            cube[5][2][0] = cube[2][2][0]
            cube[5][2][1] = cube[2][2][1]
            cube[5][2][2] = cube[2][2][2]
            # West bottom <- temp (Center bottom)
            cube[2][2][0] = temp[0]
            cube[2][2][1] = temp[1]
            cube[2][2][2] = temp[2]

        elif face_idx == 5:  # FarSouth face
            # Save West middle row
            temp = [cube[2][1][0], cube[2][1][1], cube[2][1][2]]
            # West middle <- South bottom row (reversed)
            cube[2][1][0] = cube[4][2][2]
            cube[2][1][1] = cube[4][2][1]
            cube[2][1][2] = cube[4][2][0]
            # South bottom <- East middle row
            cube[4][2][0] = cube[3][1][0]
            cube[4][2][1] = cube[3][1][1]
            cube[4][2][2] = cube[3][1][2]
            # East middle <- North bottom row (reversed)
            cube[3][1][0] = cube[1][2][2]
            cube[3][1][1] = cube[1][2][1]
            cube[3][1][2] = cube[1][2][0]
            # North bottom <- temp (West middle)
            cube[1][2][0] = temp[0]
            cube[1][2][1] = temp[1]
            cube[1][2][2] = temp[2]

    def rk_scramble(self) -> None:
        """Scramble the cube with random rotations"""

        tb = self.terminal_boss
        r = tb.random_random

        # Do 20 random rotations
        for _ in range(20):
            face_idx = r.randint(0, 5)
            if r.choice([True, False]):
                self.rk_rotate_face_clockwise(face_idx)
            else:
                self.rk_rotate_face_counterclockwise(face_idx)


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

        ks = self.keyboard_screen_i_o_wrapper
        sw = self.screen_writer
        kr = self.keyboard_reader

        assert SM_PS and SU_Y

        ks.__enter__()

        if flags.scrollback or ((not flags.enter) and (not flags._exit_)):

            h, w, y, x = kr.sample_hwyx()

            if flags.games:
                if (h * w) < (30 * 30):
                    flags.mobile = True

            if flags.games:
                dark, light = kr.guess_dark_light()
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

    def __exit__(self, *exc_info: object) -> None:

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

            h, w, y, x = kr.sample_hwyx()
            sw.write_control("\033[?1049l")  # main-screen ⎋[⇧?1049L vs ⎋[⇧?1049H
            sw.write_control(f"\033[{y};{x}H")  # row-column-leap ⎋[⇧H

        ks.__exit__(*exc_info)

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

            y, x = (kr.row_y, kr.column_x)

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
        row_y, column_x = yx

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
        marks, ints = f.to_csi_marks_ints_if()

        if (marks == b"<m") and (len(ints) == 3):
            b, x, y = ints  # todo: bounds check on Click Release
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
        """Write the Echo vertically, southward, so it stands out"""

        assert len(echo.split()) == 1, (len(echo.split()), echo)

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
                y, x = boxes_yx
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
        y, x = (kr.row_y, kr.column_x)

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

        joinables.append(clip_metric(1000 * t1t0))

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
        assert printable.replace(AppleLogo, "-").isprintable(), (printable,)

        assert CUF_X == "\033[" "{}" "C"
        assert CUB_X == "\033[" "{}" "D"
        assert AppleLogo == "\uf8ff"

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

        #
        # Results at unicodedata.east_asian_width
        #
        #   "Ambiguous"[0]  # ¡ ¤ § ® ± ¶ Ø ß and € Ω Ⅷ  and ← ↑ → ↓ ↖ ↗ ↘ ↙ 
        #   "Narrow"[:2]  # ¢ and £ and the Printable US Ascii
        #   "Neutral"[0]  # © « µ » ñ
        #
        #   "Halfwidth"[0]  # Hangul, Katakana, & Halfwidth ￭ ￮
        #   "Fullwidth"[0]  # ０ ９ Ａ Ｚ ￥ ￦  # U+3000 Ideographic Space
        #   "Wide"[0]  # ☕ ☰ ♿ 🌅 🌐 💾 💿 🔍 🔰 😃 🛼
        #
        #   also Wide are ♿ ⚪⚫ ⬛⬜ 🔰 🔴🔵 😃 🛼 🟠🟡🟢🟣🟤 🟥🟦🟧🟨🟩🟪🟫
        #

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

        marks, ints = f.to_csi_marks_ints_if()

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

        start, end = self._read_click_release_frame_and_after_()
        assert start or end, (start, end)

        if start:
            frame_list.append(start)

        data = end
        while data:
            start, end = self._bytes_split_frame_(data)
            assert (start + end) == data, (start, end, data)
            assert start, (start, end, data)

            frame_list.append(start)
            data = end

        frames = tuple(frame_list)
        assert frames, (frames,)

        frames = self._frames_compress_if_(frames)

        return frames

        # todo3: add undo arrow for late intercardinal arrows at << 80ms

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

        arrowheads, end = self._bytes_split_arrowheads_(data)
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

            # todo8: discuss ⌥` ⌥` codes as early ` vs ⌥` ⌥` o as ` ò but ⌥` ⌥` P as ` ⌥⇧~ P

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
            reads, rgb = self._bytes_split_osc_rgb_ints_(reads_endswith_rgb, osc=osc)

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
                r, g, b = rgb
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
        h, w, y, x = (self.y_high, self.x_wide, self.row_y, self.column_x)

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

        hwyx, reads = self._read_hwyx_bytes_()
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

        yx, reads = self._read_yx_bytes_()
        y, x = yx

        # Sample H W just after the last Input Byte arrives

        fd = fileno
        w, h = os.get_terminal_size(fd)  # Columns x Lines
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
    #   ⌥` sends b"``" as 1 Burst of 2 Seven-Bit US Ascii Chars
    #


#
# Speak of a Byte Encoding as a Sequence of Chords of Key Caps
#


def _try_keyboard_decoder_() -> None:
    """Try KeyboardDecoder things"""

    debugging = False  # '= False' saves like 1ms
    if debugging:

        kd = KeyboardDecoder()

        decode_by_echo = kd.decode_by_echo
        echoes_by_decode = kd.echoes_by_decode

        d1 = decode_by_echo
        k1 = "⌃⇧@"
        logger_print(f"{len(d1)=} [{k1!r}] = {d1.get(k1)!r}  # _try_keyboard_decoder_")

        d2 = echoes_by_decode
        k2 = "⌃⇧@"
        logger_print(f"{len(d2)=} [{k2!r}] = {d2.get(k2)!r}  # _try_keyboard_decoder_")


class KeyboardDecoder:
    """Speak of a Byte Sequence as a Strike of Key Caps at a macBook"""

    selves: list[KeyboardDecoder] = list()

    decode_by_echo: dict[str, str]
    removals_by_echo: dict[str, str]
    echoes_by_decode: dict[str, tuple[str, ...]]

    PlainCapsWithoutFn = r"""
        ⎋
        ` 1 2 3 4 5 6 7 8 9 0 - = ⌫
        ⇥ Q W E R T Y U I O P [ ] \
        A S D F G H J K L ; ' ⏎
        Z X C V B N M , . /
        ␢ ← ↑ → ↓
    """  # Plain Caps apart from F1 .. F12 etc

    ShiftCapsWithoutFn = """
        ⎋
        ~ ! @ # $ % ^ & * ( ) _ + ⌫
        ⇥ Q W E R T Y U I O P { } |
        A S D F G H J K L : " ⏎
        Z X C V B N M < > ?
        ␢ ← ↑ → ↓
    """  # Shift Caps apart from ⇧ F1 .. ⇧ F12 etc

    ShortcutShifts: tuple[str, ...]  # ⌃ ⌥ ⇧ ⌃⌥ ⌃⇧ ⌥⇧ ⌃⌥⇧ ⎋ ⎋⌃ ⎋⇧ ⎋⌃⇧
    ShortcutShifts = ("", "⌃", "⌥", "⌃⌥", "⇧", "⌃⇧", "⌥⇧", "⌃⌥⇧", "⎋", "⎋⌃", "⎋⇧", "⎋⌃⇧")

    FamiliarShifts: tuple[str, ...]  # ⇧ ⌃ ⌥ ⌃⇧ ⌥⇧ ⌃⌥ ⌃⌥⇧ ⎋ ⎋⇧ ⎋⌃ ⎋⌃⇧
    FamiliarShifts = ("", "⇧", "⌃", "⌥", "⌃⇧", "⌥⇧", "⌃⌥", "⌃⌥⇧", "⎋", "⎋⇧", "⎋⌃", "⎋⌃⇧")

    NumberedShifts: tuple[str, ...]  # ...  1 ''  2 ⇧  3 ⌥  4 ⌥⇧  5 ⌃  6 ⌃⇧  7 ⌃⌥  8 ⌃⌥⇧  ...
    NumberedShifts = ("", "⇧", "⌥", "⌥⇧", "⌃", "⌃⇧", "⌃⌥", "⌃⌥⇧")  # when numbered as Option/Alt
    # = ("", "⇧", "⎋", "⎋⇧", "⌃", "⌃⇧", "⎋⌃", "⎋⌃⇧")  # when numbered as Meta

    assert sorted(ShortcutShifts) == sorted(FamiliarShifts)
    assert sorted(NumberedShifts) == sorted(ShortcutShifts[:8])

    OptionAccents = ("`", "´", "¨", "ˆ", "˜")  # ⌥⇧~ ⌥⇧E ⌥⇧U ⌥⇧I ⌥⇧N
    OptionGraveGrave = "``"  # ⌥` `

    def __init__(self) -> None:

        KeyboardDecoder.selves.append(self)

        self.decode_by_echo = dict()
        self.removals_by_echo = dict()
        self._form_some_keyboards_()

        self.echoes_by_decode = self._form_echoes_by_decode_()

    def _form_some_keyboards_(self) -> None:
        """Form a Keyboard for the present Terminal App only"""

        self._form_macos_keyboards_()

        if flags.terminal:
            self._form_apple_terminal_keyboards_()
        if flags.i_term_app:
            self._form_i_term_app_keyboards_()
        if flags.ghostty:
            self._form_ghostty_keyboards_()
        if flags.google:
            self._form_google_keyboards_()

        # todo2: say something about ⇧Fn⏎ sending KeyboardInterrupt at iTerm2
        # todo2: say something about Missing ⌃⇧6 and Slow Esc and Doubled ⌃B at Google Shell

    def _form_echoes_by_decode_(self) -> dict[str, tuple[str, ...]]:
        """Sort and invert our Decode_by_Echo Dict"""

        decode_by_echo = self.decode_by_echo

        familiar_shifts = KeyboardDecoder.FamiliarShifts

        def echo_to_echo_key(echo: str) -> tuple[str, ...]:
            """Sort Key Caps from least to most celebrated"""

            assert len(echo.split()) == 1, (len(echo.split()), echo)

            lstrip = echo.lstrip("⎋⌃⌥⇧")
            cap = lstrip if lstrip else echo[-1:]

            shifts = echo[: -len(cap)]
            chr_index = chr(familiar_shifts.index(shifts))

            chr_wide_cap = chr(len(cap) > 1)
            chr_len_cap = chr(len(cap))

            echo_key = (chr_wide_cap, chr_index, chr_len_cap, cap)
            return echo_key

            # ⎋⌃P ⎋⌃⇧P before ⎋⇧F2 before ⎋⇧F12, for example

        vxk = decode_by_echo

        kkxv = collections.defaultdict(list)
        for k, v in vxk.items():
            assert k and v, (k, v)
            kkxv[v].append(k)

        assert "" not in vxk.keys()

        d = dict()
        for v, kk in kkxv.items():
            assert kk, (v, kk)
            d[v] = tuple(sorted(kk, key=echo_to_echo_key))

        assert "" not in d.keys()

        return d

    def _form_macos_keyboards_(self) -> None:
        """Form the ordinary Apple macBook Keyboards of Codes sent by Caps"""

        assert AppleLogo == "\uf8ff"

        # 1 ''

        shifts = ""
        strikes = r"""
            033
            140 1 2 3 4 5 6 7 8 9 0 - = 177
            011 q w e r t y u i o p [ ] \
            a s d f g h j k l ; ' 015
            z x c v b n m , . /
            040 ⎋[⇧D ⎋[⇧A ⎋[⇧C ⎋[⇧B
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 2 ⇧

        shifts = "⇧"  # ⇧← and ⇧→ send ⎋[1;2D and ⎋[1;2C

        strikes = """
            033
            176 ! @ # $ % ^ & * ( ) _ + 177
            ⎋[⇧Z Q W E R T Y U I O P { } |
            A S D F G H J K L : " 015
            Z X C V B N M < > ?
            040 ⎋[1;2⇧D ⎋[⇧A ⎋[1;2⇧C ⎋[⇧B
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 3 ⌃

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

        # 4 ⌥

        shifts = "⌥"  # ⌥Y sends \, coded here as r""" \ """
        strikes = r"""
            033
            ¤ ¡ ™ £ ¢ ∞ § ¶ • ª º – ≠ 177
            011 œ ∑ ¤ ® † \ ¤ ¤ ø π “ ‘ «
            å ß ∂ ƒ © ˙ ∆ ˚ ¬ … æ 015
            Ω ≈ ç √ ∫ ¤ µ ≤ ≥ ÷
            302.240 ⎋B ⎋⎋[⇧A ⎋F ⎋⎋[⇧B
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 5 ⌃⇧

        shifts = "⌃⇧"
        strikes = """
            033
            ... ... 000 ... ... ... 036 ... ... ... ... 037 ... 177
            ⎋[⇧Z ... ... ... ... ... ... ... ... ... ... 033 035 034
            ... ... ... ... ... ... ... ... ... ... ... ...
            ... ... ... ... ... ... ... ... ... ...
            000 ⎋[⇧D ⎋[⇧A ⎋[⇧C ⎋[⇧B
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 6 ⌥⇧

        shifts = "⌥⇧"  # ⌥⇧K sends AppleLogo, coded here as \uf8ff
        strikes = """
            033
            140 ⁄ € ‹ › ﬁ ﬂ ‡ ° · ‚ — ± 177
            ⎋[⇧Z Œ „ ´ ‰ ˇ Á ¨ ˆ Ø ∏ ” ’ »
            Å Í Î Ï ˝ Ó Ô \uf8ff Ò Ú Æ 015
            ¸ ˛ Ç ◊ ı ˜ Â ¯ ˘ ¿
            302.240 ⎋[⇧D ⎋[⇧A ⎋[⇧C ⎋[⇧B
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 7 ⌃⌥

        shifts = "⌃⌥"
        strikes = """
            033
            140 1 2 3 4 5 6 7 8 9 0 037 = 177
            011 021 027 005 022 024 031 025 011 017 020 033 035 034
            001 023 004 006 007 010 012 013 014 ; ' 015
            032 030 003 026 002 016 015 , . /
            000 ⎋[⇧D ⎋[⇧A ⎋[⇧C ⎋[⇧B
        """
        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 8 ⌃⌥⇧

        shifts = "⌃⌥⇧"
        strikes = """
            033
            140 1 000 3 4 5 036 7 8 9 0 037 = 177
            ⎋[⇧Z 021 027 005 022 024 031 025 011 017 020 033 035 034
            001 023 004 ... 007 010 012 013 014 ; ' 015
            032 030 003 026 ... 016 015 , . /
            000 ⎋[⇧D ⎋[⇧A ⎋[⇧C ⎋[⇧B
        """
        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 9 ⎋

        shifts = "⎋"

        strikes = r"""
            ⎋⎋
            033.140 ⎋1 ⎋2 ⎋3 ⎋4 ⎋5 ⎋6 ⎋7 ⎋8 ⎋9 ⎋0 ⎋- ⎋= 033.177
            033.011 ⎋Q ⎋W ⎋E ⎋R ⎋T ⎋Y ⎋U ⎋I ⎋O ⎋P ⎋[ ⎋] ⎋\
            ⎋A ⎋S ⎋D ⎋F ⎋G ⎋H ⎋J ⎋K ⎋L ⎋; ⎋' 033.015
            ⎋Z ⎋X ⎋C ⎋V ⎋B ⎋N ⎋M ⎋, ⎋. ⎋/
            033.040 ⎋B ⎋⎋[⇧A ⎋F ⎋⎋[⇧B
        """  # ⎋B ⎋F, not ⎋⎋[⇧D ⎋⎋[⇧C

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 10 ⎋⇧  # 033.117 ⎋O stops without closing its Key Byte Frame

        shifts = "⎋⇧"
        strikes = """
            033.033
            033.176 ⎋⇧! ⎋⇧@ ⎋⇧# ⎋⇧$ ⎋⇧% ⎋⇧^ ⎋⇧& ⎋⇧* ⎋⇧( ⎋⇧) ⎋⇧_ ⎋⇧+ 033.010
            ⎋⎋[⇧Z ⎋⇧Q ⎋⇧W ⎋⇧E ⎋⇧R ⎋⇧T ⎋⇧Y ⎋⇧U ⎋⇧I ⎋⇧O ⎋⇧P ⎋⇧{ ⎋⇧} ⎋⇧|
            ⎋⇧A ⎋⇧S ⎋⇧D ⎋⇧F ⎋⇧G ⎋⇧H ⎋⇧J ⎋⇧K ⎋⇧L ⎋⇧: ⎋⇧" 033.015
            ⎋⇧Z ⎋⇧X ⎋⇧C ⎋⇧V ⎋⇧B ⎋⇧N ⎋⇧M ⎋⇧< ⎋⇧> ⎋⇧?
            033.040 ⎋⎋[⇧D ⎋⎋[⇧A ⎋⎋[⇧C ⎋⎋[⇧B
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 11 ⎋⌃

        shifts = "⎋⌃"

        strikes = """
            033.033
            033.140 ⎋1 ⎋2 ⎋3 ⎋4 ⎋5 ⎋6 ⎋7 ⎋8 ⎋9 ⎋0 033.037 ⎋= 033.010
            033.011 033.021 033.027 033.005 033.022 033.024 033.031 033.025 033.011 033.017 033.020 033.033 033.035 033.034
            033.001 033.023 033.004 033.006 033.007 033.010 033.012 033.013 033.014 ⎋; ⎋' 033.015
            033.032 033.030 033.003 033.026 033.002 033.016 033.015 ⎋, ⎋. ⎋/
            033.040 ⎋⎋[⇧D ⎋⎋[⇧A ⎋⎋[⇧C ⎋⎋[⇧B
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 12 ⎋⌃⇧

        shifts = "⎋⌃⇧"
        strikes = """
            033.033
            033.140 ⎋1 ⎋2 ⎋3 ⎋4 ⎋5 ⎋6 ⎋7 ⎋8 ⎋9 ⎋0 033.037 ⎋= 033.010
            ⎋⎋[⇧Z 033.021 033.027 033.005 033.022 033.024 033.031 033.025 033.011 033.017 033.020 033.033 033.035 033.034
            033.001 033.023 033.004 033.006 033.007 033.010 033.012 033.013 033.014 ⎋; ⎋' 033.015
            033.032 033.030 033.003 033.026 033.002 033.016 033.015 ⎋, ⎋. ⎋/
            033.040 ⎋⎋[⇧D ⎋⎋[⇧A ⎋⎋[⇧C ⎋⎋[⇧B
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

    def _form_apple_terminal_keyboards_(self) -> None:
        """Form an Apple macOS Terminal Keyboard, out of Octets"""

        # 1 ''

        self._add_ten_fn_()
        self._keyboard_add_("F12", cap_strikes="⎋[24⇧~")

        # 2 ⇧  # Sideband Bells on ⌃ F1 F2 F3 F4

        shifts = "⇧"  # ⇧← and ⇧→ send ⎋[1;2D and ⎋[1;2C

        caps = "F5 F6 F7 F8" + " " + "F9 F10 F11 F12"  # without "F1 F2 F3 F4" + " " +
        strikes = """
            ⎋[25⇧~ ⎋[26⇧~ ⎋[28⇧~ ⎋[29⇧~
            ⎋[31⇧~ ⎋[32⇧~ ⎋[33⇧~ ⎋[34⇧~
        """  # omitting ⎋[27⇧~

        self._keyboard_add_some_(caps, strikes=strikes, shifts=shifts)

        # 3 ⌃  # Sideband Bells on ⌃ F2 F3 F4 F5 F6, ⌃ F9 F10 F11 F12  # No Codes on ⌃ F7 F8

        pass

        # 4 ⌥

        shifts = "⌥"

        meta_caps = "F1 F2 F3 F4" + " " + "F5 F6 F7 F8" + " " + "F9 F10 F11 F12"
        meta_strikes = """
            ⎋[17⇧~ ⎋[18⇧~ ⎋[19⇧~ ⎋[20⇧~
            ⎋[21⇧~ ⎋[23⇧~ ⎋[24⇧~ ⎋[25⇧~
            ⎋[26⇧~ ⎋[28⇧~ ⎋[29⇧~ ⎋[31⇧~
        """  # omitting ⎋[22⇧~ ⎋[27⇧~

        self._keyboard_add_some_(meta_caps, strikes=meta_strikes, shifts=shifts)

        # 5 ⌃⇧  # Sideband Bells on ⌥⇧ F1..F6, ⌥⇧ F8..F12  # No Codes on ⌥⇧ F7
        # 6 ⌥⇧  # Sideband Bells on ⌥⇧ F1..F12
        # 7 ⌃⌥  # Sideband Bells on ⌃⌥ F1..F12
        # 8 ⌃⌥⇧  # Sideband Bells on ⌥⇧ F1..F12

        pass

        # 9 ⎋

        shifts = "⎋"
        self._keyboard_add_some_(meta_caps, strikes=meta_strikes, shifts=shifts)

        # 10 ⎋⇧

        shifts = "⎋⇧"
        self._add_twelve_fn_meta_control_p_(shifts=shifts)  # only via 'Use Option As Meta Key'

        # 11 ⎋⌃

        shifts = "⎋⌃"
        self._add_twelve_fn_meta_control_p_(shifts=shifts)  # only via 'Use Option As Meta Key'

        # 12 ⎋⌃⇧

        shifts = "⎋⌃⇧"
        self._add_twelve_fn_meta_control_p_(shifts=shifts)  # only via 'Use Option As Meta Key'

        # Terminal ⇧Fn = ⎋[ 25 26 28 29 ⇧~, ⎋[ 31 32 33 34 ⇧~,
        # no encodes of ⇧F1 ⇧F2 ⇧F3 ⇧F4 in Apple Terminal without distributing configuration

    def _form_i_term_app_keyboards_(self) -> None:
        """Form a macOS iTerm2 Keyboard, as a diff from Apple Terminal"""

        decode_by_echo = self.decode_by_echo
        plain_caps = tuple(KeyboardDecoder.PlainCapsWithoutFn.split())
        shift_caps = tuple(KeyboardDecoder.ShiftCapsWithoutFn.split())

        # 1 ''

        self._add_ten_fn_()
        self._keyboard_add_("F12", cap_strikes="⎋[24⇧~")

        # 2 ⇧

        shifts = "⇧"
        shifts_index = 2

        self._keyboard_arrow_patch_(shifts, caps="↑↓", shifts_index=shifts_index)
        self._add_twelve_fn_(shifts, f3_strike="⎋[1;2⇧R", shifts_index=shifts_index)

        # 3 ⌃  # much the same as ⌃ Ghostty, except that Ghostty patches & adds more

        shifts = "⌃"  # shifts_index = 2

        self._keyboard_patch_("⌃⌫", cap_strikes="010")  # ⌃H
        self._keyboard_remove_("⌃⇥")

        self._keyboard_add_("⌃`", cap_strikes="140")  # `
        self._keyboard_add_("⌃1", cap_strikes="061")  # 1
        self._keyboard_add_("⌃2", cap_strikes="000")  # ⌃⇧@
        self._keyboard_add_("⌃3", cap_strikes="033")  # ⌃[
        self._keyboard_add_("⌃4", cap_strikes="034")  # ⌃\
        self._keyboard_add_("⌃5", cap_strikes="035")  # ⌃]
        self._keyboard_add_("⌃6", cap_strikes="036")  # ⌃⇧^
        self._keyboard_add_("⌃7", cap_strikes="037")  # ⌃⇧_
        self._keyboard_add_("⌃8", cap_strikes="177")  # ⌫
        self._keyboard_add_("⌃9", cap_strikes="071")  # 9
        self._keyboard_add_("⌃0", cap_strikes="060")  # 0
        self._keyboard_add_("⌃=", cap_strikes="075")  # =
        self._keyboard_add_("⌃/", cap_strikes="037")  # ⌃⇧_

        self._keyboard_add_("⌃,", cap_strikes=",")  # ,
        self._keyboard_add_("⌃.", cap_strikes=".")  # .
        self._keyboard_add_("⌃;", cap_strikes=";")  # ;
        self._keyboard_add_("⌃'", cap_strikes="'")  # '

        caps = "F2 F3 F4" + " " + "F5 F6 F7" + " " + "F9 F10 F11 F12"  # F9 F10 F11 F12 as Ghostty
        strikes = """
            ⎋[1;5⇧Q ⎋[1;5⇧R ⎋[1;5⇧S
            ⎋[15;5⇧~ ⎋[17;5⇧~ ⎋[18;5⇧~
            ⎋[20;5⇧~ ⎋[21;5⇧~ ⎋[23;5⇧~ ⎋[24;5⇧~
        """  # colliding ⎋[ ⇧R  # omitting ⌃F1 ⎋[1;5⇧P, ⌃F8 ⎋[19;5⇧~  # omitting ⎋[16;5⇧~ ⎋[22;5⇧~
        self._keyboard_add_some_(caps, strikes=strikes, shifts=shifts)

        # 4 ⌥

        shifts = "⌥"
        shifts_index = 3

        self._keyboard_arrow_patch_(shifts, caps="←↑→↓", shifts_index=shifts_index)
        self._add_twelve_fn_(shifts, f3_strike="⎋[1;3⇧R", shifts_index=shifts_index)

        # 5 ⌃⇧

        shifts = "⌃⇧"
        shifts_index = 6

        for old_cap, new_cap in zip(plain_caps, shift_caps):
            new_echo = shifts + new_cap
            if new_echo not in ("⌃⇧⌫", "⌃⇧⇥", "⌃⇧@", "⌃⇧^", "⌃⇧←", "⌃⇧↑", "⌃⇧→", "⌃⇧↓"):
                old_echo = "⌃⌥" + old_cap
                decode = decode_by_echo[old_echo]

                self._keyboard_remove_if_(new_echo)
                self._keyboard_add_decode_(decode, echo=new_echo)

        self._keyboard_patch_("⌃⇧⌫", cap_strikes="010")  # ⌃H
        self._keyboard_patch_("⌃⇧?", cap_strikes="177")  # ⌫

        self._keyboard_arrow_patch_(shifts, caps="←↑→↓", shifts_index=shifts_index)
        self._add_twelve_fn_(shifts, f3_strike="⎋[1;6⇧R", shifts_index=shifts_index)

        # 6 ⌥⇧

        shifts = "⌥⇧"
        shifts_index = 4

        self._keyboard_arrow_patch_(shifts, caps="←↑→↓", shifts_index=shifts_index)
        self._add_twelve_fn_(shifts, f3_strike="⎋[1;4⇧R", shifts_index=shifts_index)

        # 7 ⌃⌥

        shifts = "⌃⌥"
        shifts_index = 7

        self._keyboard_patch_("⌃⌥␢", cap_strikes="040")  # Spacebar
        self._keyboard_arrow_patch_(shifts, caps="←↑→↓", shifts_index=shifts_index)
        self._add_twelve_fn_(shifts, f3_strike="⎋[1;7⇧R", shifts_index=shifts_index)

        # 8 ⌃⌥⇧

        shifts = "⌃⌥⇧"
        shifts_index = 8

        self._keyboard_add_("⌃⌥⇧B", cap_strikes="002")  # ⌃B
        self._keyboard_add_("⌃⌥⇧F", cap_strikes="006")  # ⌃F

        self._keyboard_arrow_patch_(shifts, caps="←↑→↓", shifts_index=shifts_index)
        self._add_twelve_fn_(shifts, f3_strike="⎋[1;8⇧R", shifts_index=shifts_index)

        # 9 ⎋
        # 11 ⎋⌃
        # 10 ⎋⇧
        # 12 ⎋⌃⇧

        pass  # todo1: remove ⎋ ⎋⌃ ⎋⇧ ⎋⌃⇧ from iTerm2, and ⌥ ⌥⇧ ⌃⌥⇧ from Ghostty

    def _form_ghostty_keyboards_(self) -> None:  # todo1: test and solve Fn at Ghostty
        """Form a macOS Ghostty Keyboard, as a diff from Apple Terminal"""

        # 1 ''

        self._add_ten_fn_()
        self._keyboard_add_("F12", cap_strikes="⎋[24⇧~")

        # 2 ⇧

        shifts = "⇧"
        shifts_index = 2

        self._keyboard_shifts_patch_("⇧⎋", octet="033", csi="~", shifts_index=shifts_index)
        self._keyboard_shifts_patch_("⇧⏎", octet="015", csi="~", shifts_index=shifts_index)

        self._keyboard_arrow_patch_("⇧", caps="↑↓", shifts_index=shifts_index)

        caps = "F1 F2 F3 F4" + " " + "F5 F6 F7 F8" + " " + "F9 F10 F11 F12"
        strikes = """
            ⎋[1;2⇧P ⎋[1;2⇧Q ⎋[13;2⇧~ ⎋[1;2⇧S
            ⎋[15;2⇧~ ⎋[17;2⇧~ ⎋[18;2⇧~ ⎋[19;2⇧~
            ⎋[20;2⇧~ ⎋[21;2⇧~ ⎋[23;2⇧~ ⎋[24;2⇧~
        """  # coding ⎋[13;2⇧~ in place of ⎋[1;2⇧R # omitting ⎋[16;2⇧~ ⎋[12;2⇧~

        self._keyboard_add_some_(caps, strikes=strikes, shifts=shifts)

        # 3 ⌃  # much the same as ⌃ iTerm2, except that Ghostty patches & adds more

        shifts = "⌃"
        shifts_index = 5

        self._keyboard_patch_("⌃⌫", cap_strikes="010")  # ⌃H
        self._keyboard_remove_("⌃⇥")

        self._keyboard_add_("⌃`", cap_strikes="140")  # `
        self._keyboard_add_("⌃1", cap_strikes="1")  # 1
        self._keyboard_add_("⌃2", cap_strikes="000")  # ⌃⇧@
        self._keyboard_add_("⌃3", cap_strikes="033")  # ⌃[
        self._keyboard_add_("⌃4", cap_strikes="034")  # ⌃\
        self._keyboard_add_("⌃5", cap_strikes="035")  # ⌃]
        self._keyboard_add_("⌃6", cap_strikes="036")  # ⌃⇧^
        self._keyboard_add_("⌃7", cap_strikes="037")  # ⌃⇧_
        self._keyboard_add_("⌃8", cap_strikes="177")  # ⌫
        self._keyboard_add_("⌃9", cap_strikes="9")  # 9
        self._keyboard_add_("⌃0", cap_strikes="0")  # 0
        self._keyboard_add_("⌃=", cap_strikes="=")  # =
        self._keyboard_add_("⌃/", cap_strikes="037")  # ⌃⇧_

        self._keyboard_shifts_add_("⌃;", octet="073", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_add_("⌃'", octet="047", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_add_("⌃,", octet="054", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_add_("⌃.", octet="056", csi="u", shifts_index=shifts_index)

        self._keyboard_shifts_patch_("⌃⎋", octet="033", csi="~", shifts_index=shifts_index)
        self._keyboard_shifts_patch_("⌃`", octet="140", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_patch_("⌃=", octet="075", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_patch_("⌃I", octet="151", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_patch_("⌃M", octet="155", csi="u", shifts_index=shifts_index)

        caps = "F9 F10 F11 F12"  # F9 F10 F11 F12 as iTerm2
        strikes = """
             ⎋[20;5⇧~ ⎋[21;5⇧~ ⎋[23;5⇧~ ⎋[24;5⇧~
        """  # omitting ⎋[22;5⇧~
        self._keyboard_add_some_(caps, strikes=strikes, shifts=shifts)

        # 4 ⌥

        pass

        # 5 ⌃⇧  # mixes in ⌃ shifts_index=5 into ⌃⇧ =6   # todo2: Ghostty bug?

        shifts = "⌃⇧"
        shifts_index = 6

        self._keyboard_shifts_patch_("⌃⇧⎋", octet="033", csi="~", shifts_index=shifts_index)
        self._keyboard_remove_("⌃⇧⇥")
        self._keyboard_patch_("⌃⇧⌫", cap_strikes="010")  # ⌃H
        self._keyboard_shifts_add_("⌃⇧⏎", octet="015", csi="~", shifts_index=shifts_index)

        self._keyboard_add_("⌃⇧!", cap_strikes="061")  # 1
        self._keyboard_shifts_patch_("⌃⇧@", octet="100", csi="u", shifts_index=5)
        self._keyboard_add_("⌃⇧#", cap_strikes="033")  # ⌃[
        self._keyboard_add_("⌃⇧$", cap_strikes="134")  # ⌃\
        self._keyboard_add_("⌃⇧%", cap_strikes="035")  # ⌃]
        self._keyboard_add_("⌃⇧&", cap_strikes="037")  # ⌃⇧_
        self._keyboard_add_("⌃⇧*", cap_strikes="177")  # ⌫
        self._keyboard_add_("⌃⇧(", cap_strikes="071")  # 9
        self._keyboard_add_("⌃⇧)", cap_strikes="060")  # 0

        for cap in string.ascii_uppercase:
            echo = f"⌃⇧{cap}"
            octet = f"{ord(cap.lower()):03o}"
            cap.lower()
            self._keyboard_shifts_add_(echo, octet=octet, csi="u", shifts_index=shifts_index)

        self._keyboard_shifts_add_("⌃⇧+", octet="075", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_patch_("⌃⇧{", octet="173", csi="u", shifts_index=5)
        self._keyboard_shifts_patch_("⌃⇧}", octet="175", csi="u", shifts_index=5)
        self._keyboard_shifts_patch_("⌃⇧|", octet="174", csi="u", shifts_index=5)
        self._keyboard_shifts_add_("⌃⇧:", octet="073", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_add_('⌃⇧"', octet="047", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_add_("⌃⇧<", octet="054", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_add_("⌃⇧>", octet="056", csi="u", shifts_index=shifts_index)
        self._keyboard_add_("⌃⇧?", cap_strikes="037")  # ⌃⇧_

        self._keyboard_arrow_patch_("⌃⇧", caps="←↑→↓", shifts_index=shifts_index)

        # 6 ⌥⇧
        # 7 ⌃⌥
        # 8 ⌃⌥⇧

        pass

        # 9 ⎋

        shifts = "⎋"
        shifts_index = 3

        self._keyboard_arrow_patch_(shifts, caps="↑↓", shifts_index=shifts_index)

        # 10 ⎋⇧

        shifts = "⎋⇧"
        shifts_index = 4

        self._keyboard_shifts_patch_("⎋⇧⎋", octet="033", csi="~", shifts_index=shifts_index)
        self._keyboard_shifts_patch_("⎋⇧⇥", octet="011", csi="~", shifts_index=shifts_index)
        self._keyboard_patch_("⎋⇧⌫", cap_strikes="033.177")  # ⎋⌫
        self._keyboard_shifts_patch_("⎋⇧⏎", octet="015", csi="~", shifts_index=shifts_index)

        self._keyboard_arrow_patch_(shifts, caps="←↑→↓", shifts_index=shifts_index)

        # 11 ⎋⌃

        shifts = "⎋⌃"
        shifts_index = 7

        self._keyboard_patch_("⎋⌃⌫", cap_strikes="033.010")  # ⌃H
        self._keyboard_remove_("⎋⌃⇥")

        self._keyboard_shifts_patch_("⎋⌃`", octet="140", csi="u", shifts_index=shifts_index)

        self._keyboard_patch_("⎋⌃1", cap_strikes="⎋1")  # ⎋ 1
        self._keyboard_patch_("⎋⌃2", cap_strikes="033.000")  # ⎋ ⌃⇧@
        self._keyboard_patch_("⎋⌃3", cap_strikes="033.033")  # ⎋ ⌃[
        self._keyboard_patch_("⎋⌃4", cap_strikes="033.034")  # ⎋ ⌃\
        self._keyboard_patch_("⎋⌃5", cap_strikes="033.035")  # ⎋ ⌃]
        self._keyboard_patch_("⎋⌃6", cap_strikes="033.036")  # ⎋ ⌃⇧^
        self._keyboard_patch_("⎋⌃7", cap_strikes="033.037")  # ⎋ ⌃⇧_
        self._keyboard_patch_("⎋⌃8", cap_strikes="033.177")  # ⎋ ⌫
        self._keyboard_patch_("⎋⌃9", cap_strikes="⎋9")  # ⎋ 9
        self._keyboard_patch_("⎋⌃0", cap_strikes="⎋0")  # ⎋ 0
        self._keyboard_patch_("⎋⌃/", cap_strikes="033.037")  # ⌃⇧_  # beeps 🙄

        self._keyboard_shifts_patch_("⎋⌃;", octet="073", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_patch_("⎋⌃'", octet="047", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_patch_("⎋⌃,", octet="054", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_patch_("⎋⌃.", octet="056", csi="u", shifts_index=shifts_index)

        self._keyboard_shifts_patch_("⎋⌃⎋", octet="033", csi="~", shifts_index=shifts_index)

        self._keyboard_shifts_patch_("⎋⌃-", octet="055", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_patch_("⎋⌃=", octet="075", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_patch_("⎋⌃I", octet="151", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_patch_("⎋⌃[", octet="133", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_patch_("⎋⌃M", octet="155", csi="u", shifts_index=shifts_index)

        self._keyboard_shifts_patch_("⎋⌃⏎", octet="015", csi="~", shifts_index=shifts_index)

        self._keyboard_patch_("⎋⌃␢", cap_strikes="033.000")  # Spacebar

        self._keyboard_arrow_patch_(shifts, caps="←↑→↓", shifts_index=shifts_index)

        # 12 ⎋⌃⇧  # mixes ⎋⌃ shifts_index=7 into ⎋⌃⇧ =8   # todo2: Ghostty bug?

        shifts = "⎋⌃⇧"
        shifts_index = 8

        self._keyboard_shifts_patch_("⎋⌃⇧⎋", octet="033", csi="~", shifts_index=shifts_index)
        self._keyboard_remove_("⎋⌃⇧⇥")

        self._keyboard_shifts_patch_("⎋⌃⇧~", octet="140", csi="u", shifts_index=shifts_index)
        self._keyboard_patch_("⎋⌃⇧@", cap_strikes="033.000")  # ⎋ ⌃⇧@
        self._keyboard_patch_("⎋⌃⇧#", cap_strikes="033.033")  # ⎋ ⎋  # ⎋ ⌃[
        self._keyboard_patch_("⎋⌃⇧$", cap_strikes="033.034")  # ⎋ ⌃\
        self._keyboard_patch_("⎋⌃⇧%", cap_strikes="033.035")  # ⎋ ⌃]
        self._keyboard_patch_("⎋⌃⇧^", cap_strikes="033.036")  # ⎋ ⌃⇧^
        self._keyboard_patch_("⎋⌃⇧&", cap_strikes="033.037")  # ⎋ ⌃⇧_
        self._keyboard_patch_("⎋⌃⇧*", cap_strikes="033.177")  # ⎋ ⌫
        self._keyboard_shifts_patch_("⎋⌃⇧+", octet="075", csi="u", shifts_index=shifts_index)
        self._keyboard_patch_("⎋⌃⇧⌫", cap_strikes="177")  # ⌫

        self._keyboard_shifts_patch_("⎋⌃⇧{", octet="173", csi="u", shifts_index=7)
        self._keyboard_shifts_patch_("⎋⌃⇧}", octet="175", csi="u", shifts_index=7)
        self._keyboard_shifts_patch_("⎋⌃⇧|", octet="174", csi="u", shifts_index=7)

        self._keyboard_shifts_patch_("⎋⌃⇧:", octet="073", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_patch_('⎋⌃⇧"', octet="047", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_patch_("⎋⌃⇧⏎", octet="015", csi="~", shifts_index=shifts_index)
        self._keyboard_shifts_patch_("⎋⌃⇧<", octet="054", csi="u", shifts_index=shifts_index)
        self._keyboard_shifts_patch_("⎋⌃⇧>", octet="056", csi="u", shifts_index=shifts_index)
        self._keyboard_patch_("⎋⌃⇧?", cap_strikes="033.037")  # ⎋ ⌃⇧_

        for cap in string.ascii_uppercase:
            echo = shifts + cap
            octet = f"{ord(cap.lower()):03o}"
            cap.lower()
            self._keyboard_shifts_patch_(echo, octet=octet, csi="u", shifts_index=shifts_index)

        self._keyboard_patch_("⎋⌃⇧␢", cap_strikes="033.000")  # Spacebar

        self._keyboard_arrow_patch_(shifts, caps="←↑→↓", shifts_index=shifts_index)

        # todo2: reject the patches that change nothing
        # todo2: look before & after the drops of whole keyboards for like ⌃⌥⇧ Google and ⌃⌥ Google
        # todo2: learn & teach the art of reaching the different keyboards without pasting

        #

    def _form_google_keyboards_(self) -> None:  # todo1: test and solve Fn at Google Cloud Shell
        """Form a Google Cloud Shell Keyboard, as a diff from Apple Terminal"""

        decode_by_echo = self.decode_by_echo

        # 1 ''

        self._add_ten_fn_()
        self._keyboard_add_("F12", cap_strikes="⎋[24⇧~")

        # 2 ⇧

        shifts = "⇧"

        self._keyboard_remove_("⇧←")
        self._keyboard_remove_("⇧↑")
        self._keyboard_remove_("⇧→")
        self._keyboard_remove_("⇧↓")

        caps = "F1 F2 F3 F4" + " " + "F5 F6 F7 F8"  # without + " " + "F9 F10 F11 F12"
        strikes = """
            ⎋[25⇧~ ⎋[26⇧~ ⎋[28⇧~ ⎋[29⇧~
            ⎋[20⇧~ ⎋[21⇧~ ⎋[22⇧~ ⎋[23⇧~
        """  # omitting ⎋[27⇧~

        self._keyboard_add_some_(caps, strikes=strikes, shifts=shifts)

        # 3 ⌃  # todo: mark which No-Code Keys do beep, such as ⌃/ vs ⌃=

        self._keyboard_patch_("⌃⌫", cap_strikes="010")  # ⌃H

        self._keyboard_add_("⌃3", cap_strikes="033")  # ⌃[
        self._keyboard_add_("⌃4", cap_strikes="034")  # ⌃\
        self._keyboard_add_("⌃5", cap_strikes="035")  # ⌃]
        self._keyboard_add_("⌃7", cap_strikes="037")  # ⌃⇧_

        self._keyboard_remove_("⌃-")
        self._keyboard_remove_("⌃⇥")
        self._keyboard_remove_("⌃B")
        self._keyboard_add_("⌃⏎", cap_strikes="015")  # ⏎
        self._keyboard_remove_("⌃M")

        # 4 ⌥

        self._keyboard_patch_("⌥Y", cap_strikes="302.245")  # ¥
        self._keyboard_patch_("⌥⌫", cap_strikes="033.177")  # ⎋ ⌫
        self._keyboard_patch_("⌥⏎", cap_strikes="033.015")  # ⎋ ⏎

        self._keyboard_patch_("⌥←", cap_strikes="⎋⎋[⇧D")  # ⎋ ⎋[⇧D
        self._keyboard_patch_("⌥↑", cap_strikes="⎋⎋[⇧A")  # ⎋ ⎋[⇧A
        self._keyboard_patch_("⌥→", cap_strikes="⎋⎋[⇧C")  # ⎋ ⎋[⇧C
        self._keyboard_patch_("⌥↓", cap_strikes="⎋⎋[⇧B")  # ⎋ ⎋[⇧B

        # 5 ⌃⇧  # not much here except ⌃⇧@ and ⌃⇧_

        self._keyboard_patch_("⌃⇧⎋", cap_strikes="033.033")  # ⎋ ⎋
        self._keyboard_patch_("⌃⇧⌫", cap_strikes="010")  # ⌃H
        self._keyboard_add_("⌃⇧⏎", cap_strikes="015")  # ⏎

        self._keyboard_remove_("⌃⇧^")
        self._keyboard_remove_("⌃⇧⇥")
        self._keyboard_remove_("⌃⇧|")
        self._keyboard_remove_("⌃⇧␢")
        self._keyboard_remove_("⌃⇧{")
        self._keyboard_remove_("⌃⇧}")

        self._keyboard_remove_("⌃⇧←")
        self._keyboard_remove_("⌃⇧↑")
        self._keyboard_remove_("⌃⇧→")
        self._keyboard_remove_("⌃⇧↓")

        # 6 ⌥⇧

        self._keyboard_remove_("⌥⇧←")
        self._keyboard_remove_("⌥⇧↑")
        self._keyboard_remove_("⌥⇧→")
        self._keyboard_remove_("⌥⇧↓")

        # 7 ⌃⌥

        echoes = list(decode_by_echo.keys())
        for echo in echoes:
            if echo.startswith("⌃⌥"):
                self._keyboard_remove_(echo)

        self._keyboard_add_("⌃⌥⎋", cap_strikes="033.033")  # ⎋ ⎋
        self._keyboard_add_("⌃⌥⌫", cap_strikes="033.010")  # ⌃H
        self._keyboard_add_("⌃⌥⏎", cap_strikes="033.015")  # ⎋ ⏎

        # 8 ⌃⌥⇧

        echoes = list(decode_by_echo.keys())
        for echo in echoes:
            if echo.startswith("⌃⌥⇧"):
                self._keyboard_remove_(echo)

        self._keyboard_add_("⌃⌥⇧⎋", cap_strikes="033.033")  # ⎋ ⎋
        self._keyboard_add_("⌃⌥⇧⌫", cap_strikes="033.010")  # ⌃H
        self._keyboard_add_("⌃⌥⇧⏎", cap_strikes="033.015")  # ⎋ ⏎
        self._keyboard_add_("⌃⌥⇧@", cap_strikes="000")  # ⌃⇧@
        self._keyboard_add_("⌃⌥⇧_", cap_strikes="037")  # ⌃⇧_

        # 9 ⎋
        # 11 ⎋⌃
        # 10 ⎋⇧
        # 12 ⎋⌃⇧

        pass  # todo: no working "Alt is Meta" found in Google Cloud Shell

        # todo2: fix the slow ⌥⎋ of Google that breaks the Key Byte Frame of b"⎋⎋"

    def _add_twelve_fn_(self, shifts: str, f3_strike: str, shifts_index: int) -> None:
        """Add the twelve Fn Keys for these Shifts in the usual way"""

        assert shifts in KeyboardDecoder.ShortcutShifts, (shifts,)
        assert 2 <= shifts_index <= 8, (shifts_index,)  # todo1: less magic

        i_term_app__f3_strike = f"⎋[1;{shifts_index}⇧R"  # colliding ⎋[ ⇧R
        ghostty__f3_strike = f"⎋[13;{shifts_index}⇧~"
        assert f3_strike in (i_term_app__f3_strike, ghostty__f3_strike), (f3_strike,)

        f3 = f3_strike
        i = shifts_index

        caps = "F1 F2 F3 F4" + " " + "F5 F6 F7 F8" + " " + "F9 F10 F11 F12"
        strikes = f"""
            ⎋[1;{i}⇧P ⎋[1;{i}⇧Q {f3} ⎋[1;{i}⇧S
            ⎋[15;{i}⇧~ ⎋[17;{i}⇧~ ⎋[18;{i}⇧~ ⎋[19;{i}⇧~
            ⎋[20;{i}⇧~ ⎋[21;{i}⇧~ ⎋[23;{i}⇧~ ⎋[24;{i}⇧~
        """  # omitting ⎋[16;...⇧~ ⎋[22;...⇧~

        self._keyboard_add_some_(caps, strikes=strikes, shifts=shifts)

    def _add_keyboard_(self, shifts: str, strikes: str) -> None:
        """Add in 1 Keyboard of Key Caps and their Strikes"""

        assert shifts in KeyboardDecoder.ShortcutShifts, (shifts,)

        strikes_split = strikes.split()
        if not strikes_split:
            return

        plain_caps = tuple(KeyboardDecoder.PlainCapsWithoutFn.split())
        shift_caps = tuple(KeyboardDecoder.ShiftCapsWithoutFn.split())

        o = (len(plain_caps), len(shift_caps), len(strikes_split))
        assert len(plain_caps) == len(shift_caps) == len(strikes_split), o

        caps = shift_caps if ("⇧" in shifts) else plain_caps
        for cap, cap_strikes in zip(caps, strikes_split):
            echo = shifts + cap
            decode = self._cap_strikes_to_decode_(cap_strikes, echo=echo)
            if decode:

                self._keyboard_add_decode_(decode, echo=echo)

    def _add_ten_fn_(self) -> None:
        """Add the first Ten F Keys, held in common across all our Unshifted Keyboards"""

        shifts = ""

        caps = "F1 F2 F3 F4" + " " + "F5 F6 F7 F8" + " " + "F9 F10"  # without " F11 F12"
        strikes = """
            ⎋⇧O⇧P ⎋⇧O⇧Q ⎋⇧O⇧R ⎋⇧O⇧S
            ⎋[15⇧~ ⎋[17⇧~ ⎋[18⇧~ ⎋[19⇧~
            ⎋[20⇧~ ⎋[21⇧~
        """  # omitting ⎋[16~  # not-colliding with ⎋[ ⇧R

        self._keyboard_add_some_(caps, strikes=strikes, shifts=shifts)

        # ⎋OP ⎋OQ ⎋OR ⎋OS  # ⎋[15~ ⎋[17~ ⎋[18~ ⎋[19~  # ⎋[20~ ⎋[21

    def _add_twelve_fn_meta_control_p_(self, shifts: str) -> None:
        """Add the Twelve F Keys at the one Decode"""

        assert shifts in KeyboardDecoder.ShortcutShifts, (shifts,)

        caps = "F1 F2 F3 F4" + " " + "F5 F6 F7 F8" + " " + "F9 F10 F11 F12"
        strikes = 12 * " 033.020"  # ⎋⌃P
        self._keyboard_add_some_(caps, strikes=strikes, shifts=shifts)

    TwelveFnMetaControlP = """
        ⎋⌃P    ⎋⌃⇧P
        ⎋⇧F1   ⎋⇧F2   ⎋⇧F3   ⎋⇧F4   ⎋⇧F5   ⎋⇧F6   ⎋⇧F7   ⎋⇧F8   ⎋⇧F9   ⎋⇧F10   ⎋⇧F11   ⎋⇧F12
        ⎋⌃F1   ⎋⌃F2   ⎋⌃F3   ⎋⌃F4   ⎋⌃F5   ⎋⌃F6   ⎋⌃F7   ⎋⌃F8   ⎋⌃F9   ⎋⌃F10   ⎋⌃F11   ⎋⌃F12
        ⎋⌃⇧F1  ⎋⌃⇧F2  ⎋⌃⇧F3  ⎋⌃⇧F4  ⎋⌃⇧F5  ⎋⌃⇧F6  ⎋⌃⇧F7  ⎋⌃⇧F8  ⎋⌃⇧F9  ⎋⌃⇧F10  ⎋⌃⇧F11  ⎋⌃⇧F12
    """  # ⎋⌃P ⎋⌃⇧P ⎋⇧F1 ... ⎋⌃... ⎋⌃⇧... ⎋⌃⇧F12

    def _cap_strikes_to_decode_(self, cap_strikes: str, echo: str) -> str:
        """Convert to Decode of Byte Encoding of Key Strike"""

        assert len(echo.split()) == 1, (len(echo.split()), echo)

        if cap_strikes in ("...", "¤"):
            return ""

        ba = bytearray()

        octets = [cap_strikes]
        if cap_strikes not in (".", "⎋."):
            octets = cap_strikes.split(".")

        for octet in octets:

            # Accept single Characters

            if len(octet) == 1:  # '€'
                t = octet
                assert t not in ("⎋⌃⌥⇧" "`~"), (octet, octets, cap_strikes, echo)
                octet_data = octet.encode()
                ba.extend(octet_data)
                continue

            # Accept single Characters escaped, no matter if shifted or not

            if octet == "⎋⎋":  # ⎋⎋
                octet_data = b"\033\033"
                ba.extend(octet_data)
                continue

            if octet.startswith("⎋") and (len(octet) == 2):  # ⎋Z  # ⎋/
                t = octet[1:]
                if t not in (string.digits + string.ascii_uppercase):
                    assert t in ("-=" "[]\\" ";'" ",./"), (t, octet, cap_strikes, echo)
                octet_data = b"\033" + t.lower().encode()
                ba.extend(octet_data)
                continue

                # rejects ⎋`

            if octet.startswith("⎋⇧") and (len(octet) == 3):  # ⎋⇧Z  # ⎋⇧?
                t = octet[2:]
                if t not in string.ascii_uppercase:
                    assert t in ("!@#$%^&*()_+" "{}|" ':"' "<>?"), (t, octet, cap_strikes, echo)
                octet_data = b"\033" + t.encode()
                ba.extend(octet_data)
                continue

                # rejects ⎋⇧~

            # Accept three Octal Digits as an Octet

            m = re.fullmatch(r"[0-7][0-7][0-7]", string=octet)
            if m:  # 177
                ba.append(int(octet, base=0o010))  # raises ValueError when > 0o377
                continue

            # Accept simple Ss3 Sequences spoken as ⎋O... ⇧...

            m = re.fullmatch(r"(⎋)⇧(O)⇧([PQRS])", string=octet)
            if m:  # ⎋⇧O⇧S
                octet_data = b"\033"
                octet_data += m.group(2).encode() + m.group(3).encode()
                ba.extend(octet_data)
                continue

            # Accept simple Csi Sequences spoken as ⎋[... ⇧..., even when preceded by one extra ⎋

            m = re.fullmatch(r"(⎋|⎋⎋)(\[)([0-9;]*)⇧([ABCDPQRSZ~])", string=octet)
            if m:  # ⎋[⇧Z  # ⎋[1;2⇧C  # ⎋⎋[⇧D  # ⎋[17⇧~
                octet_data = len(m.group(1)) * b"\033"
                octet_data += m.group(2).encode() + m.group(3).encode() + m.group(4).encode()
                ba.extend(octet_data)
                continue

            assert False, (octet, octets, cap_strikes, echo)

        decode = ba.decode()
        assert ba and decode, (ba, decode)

        return decode

        # todo3: Factor out 'def _cap_strikes_to_decode_' as its own Co/Dec Class

    def _keyboard_patch_(self, echo: str, cap_strikes: str) -> None:
        """Patch the Keyboard with a Key Cap and its Strikes"""

        assert len(echo.split()) == 1, (len(echo.split()), echo)

        self._keyboard_remove_(echo)
        self._keyboard_add_(echo, cap_strikes=cap_strikes)

    def _keyboard_add_some_(self, caps: str, strikes: str, shifts: str) -> None:
        """Add some Key Caps at Strikes to a Keyboard"""

        caps_split = caps.split()
        strikes_split = strikes.split()
        assert shifts in KeyboardDecoder.ShortcutShifts, (shifts,)

        assert len(caps_split) == len(strikes_split), (len(caps_split), len(strikes_split))
        for cap, cap_strikes in zip(caps_split, strikes_split):
            echo = shifts + cap
            self._keyboard_add_(echo, cap_strikes=cap_strikes)

    def _keyboard_add_(self, echo: str, cap_strikes: str) -> None:
        """Add a Key Cap and its Octets to a Keyboard"""

        assert len(echo.split()) == 1, (len(echo.split()), echo)

        decode = self._cap_strikes_to_decode_(cap_strikes, echo=echo)
        self._keyboard_add_decode_(decode, echo=echo)

    def _keyboard_add_decode_(self, decode: str, echo: str) -> None:
        """Add a Key Cap and its Byte Encoding to a Keyboard"""

        assert decode, (decode, echo)
        assert len(echo.split()) == 1, (len(echo.split()), echo)

        decode_by_echo = self.decode_by_echo

        assert echo not in decode_by_echo, (echo, decode_by_echo[echo])
        decode_by_echo[echo] = decode

    def _keyboard_remove_if_(self, echo: str) -> None:
        """Remove a Key Cap and its Byte Encoding from a Keyboard, if it exists"""

        assert len(echo.split()) == 1, (len(echo.split()), echo)

        decode_by_echo = self.decode_by_echo
        if echo in decode_by_echo.keys():
            self._keyboard_remove_(echo)

    def _keyboard_remove_(self, echo: str) -> None:
        """Remove a Key Cap and its Byte Encoding from a Keyboard"""

        assert len(echo.split()) == 1, (len(echo.split()), echo)

        decode_by_echo = self.decode_by_echo
        removals_by_echo = self.removals_by_echo

        assert echo not in removals_by_echo, (echo,)
        removals_by_echo[echo] = echo

        assert echo in decode_by_echo.keys(), (echo,)
        del decode_by_echo[echo]  # todo: 'del ...' vs '... = ""'

    def _keyboard_arrow_patch_(self, shifts: str, caps: str, shifts_index: int) -> None:
        """Patch the Keyboard with like 4 more or 2 more Arrow Keys, all at once"""

        assert shifts in KeyboardDecoder.ShortcutShifts, (shifts,)
        assert 2 <= shifts_index <= 8, (shifts_index,)

        upper_by_arrow = {"←": "D", "↑": "A", "→": "C", "↓": "B"}

        for cap in caps:
            echo = shifts + cap

            arrow_upper = upper_by_arrow[cap]
            cap_strikes = f"⎋[1;{shifts_index}⇧{arrow_upper}"  # ⎋[1;2⇧C

            self._keyboard_patch_(echo, cap_strikes=cap_strikes)

            # todo: patch vs add in ._keyboard_arrow_patch_

    def _keyboard_shifts_patch_(self, echo: str, octet: str, csi: str, shifts_index: int) -> None:
        """Patch the Keyboard with a Key Cap and its Strikes"""

        assert len(echo.split()) == 1, (len(echo.split()), echo)
        assert 2 <= shifts_index <= 8, (shifts_index,)

        decode = self._shifts_to_decode_(octet, csi=csi, shifts_index=shifts_index)

        self._keyboard_remove_(echo)
        self._keyboard_add_decode_(decode, echo=echo)

    def _keyboard_shifts_add_(self, echo: str, octet: str, csi: str, shifts_index: int) -> None:
        """Add a Key Cap and its Strikes to the Keyboard"""

        assert len(echo.split()) == 1, (len(echo.split()), echo)
        assert 2 <= shifts_index <= 8, (shifts_index,)

        decode = self._shifts_to_decode_(octet, csi=csi, shifts_index=shifts_index)
        self._keyboard_add_decode_(decode, echo=echo)

    def _shifts_to_decode_(self, octet: str, csi: str, shifts_index: int) -> str:
        """Form a Csi U or ⇧~ Decode from its Octet & Shifts_Index"""

        assert octet and csi, (octet, csi)
        assert 2 <= shifts_index <= 8, (shifts_index,)

        _ord_ = int(octet, base=0o010)
        if csi == "~":
            decode = f"\033[27;{shifts_index};{_ord_}" "~"
        else:
            assert csi == "u", (csi, octet, shifts_index)
            decode = f"\033[{_ord_};{shifts_index}" "u"

        return decode

        # todo: dig up docs for Csi u and for Csi ~

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

    def echo_split_shifts_cap(self, echo: str) -> tuple[str, str]:
        """Split out the Shifts at left, and add 'Fn' if Fn"""

        assert len(echo.split()) == 1, (len(echo.split()), echo)

        shifts = ""
        for t in echo:
            if t not in "⎋ ⌃ ⌥ ⇧".split():  # .t can be 'F' or 'n' but never 'Fn'
                break
            shifts += t

        cap = echo[len(shifts) :]
        if cap == "<>":
            cap = ""  # ('', '') from '<>'
        elif not cap and shifts.endswith("⎋"):
            shifts = str_removesuffix(shifts, suffix="⎋")
            cap = "⎋"  # ('', '⎋') from '⎋'

        return (shifts, cap)

        # ('', '')  # ('⇧', '⎋')  # ('⇧', 'F5')  # ('⌃⇧', '@')

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

        escapes = len(head) - len(head.lstrip(b"\033"))
        escapes = (escapes - 1) if escapes else 0
        undented_head = head[escapes:]

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

        assert False, (head, head[escapes:], escapes, self)

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

                sys.exit(2)  # exits 2 for Help Doc and/or Parser gone wrong

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

        default_eq_none = None
        with_columns_else = os.environ.get("COLUMNS", default_eq_none)  # checkpoints
        with_no_color_else = os.environ.get("NO_COLOR", default_eq_none)  # checkpoints

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
        except UnicodeDecodeError:  # common with partial .data
            return ""

    @functools.cached_property
    def nearly_printable(self) -> bool:
        """Say if the Text exactly matches the Repr minus Quotes"""

        data = self.data
        text = self.text

        assert AppleLogo == "\uf8ff"  # .isprintable says False

        if not data:
            assert not text, (data, text)
            return True

        if not text:
            return False

        printable = text.replace(AppleLogo, "-").isprintable()

        return printable


#
# Amp up Import BuiltIns Int & Float
#


Inf = float("inf")  # implicitly also defines -Inf and +Inf
NaN = float("nan")  # actually implies NaN != NaN


_clips_by_str_f_ = {  # clip_metric, clip_float, clip_int, clip_bimetric
    #
    "-Inf": ["ValueError", "-Inf", "", ""],
    "-1e999": ["ValueError", "-Inf", "", ""],
    "-1e309": ["ValueError", "-Inf", "", ""],
    "-1e308": ["ValueError", "ValueError", "ValueError", ""],
    "-1000e18": ["ValueError", "ValueError", "ValueError", ""],
    #
    "-999e18": ["-999E", "-999e18", "-999e18", ""],
    "-999e3": ["-999k", "-999e3", "-999e3", ""],
    "-999": ["-999", "-999", "-999", ""],
    "-1000": ["-1k", "-1e3", "-1e3", ""],
    "-1": ["-1", "-1", "-1", ""],
    #
    "-1e-9": ["-1n", "-1e-9", "", ""],
    "-0.001": ["-1m", "-1e-3", "", ""],
    #
    "-1e-999": ["-0", "-0e0", "0", "0"],
    "-1e-324": ["-0", "-0e0", "0", "0"],
    "-1e-323": ["ValueError", "ValueError", "", ""],
    "-1e-27": ["ValueError", "ValueError", "", ""],
    "-1e-24": ["ValueError", "ValueError", "", ""],
    "-1e-21": ["ValueError", "ValueError", "", ""],
    "-1e-18": ["ValueError", "ValueError", "", ""],
    "-1e-15": ["ValueError", "ValueError", "", ""],
    "-1e-12": ["-1p", "-1e-12", "", ""],
    #
    "-0e0": ["-0", "-0e0", "0", "0"],
    "0": ["0", "0", "0", "0"],
    "+0e0": ["0", "0", "0", "0"],
    #
    "+1e-12": ["1p", "1e-12", "", ""],
    "+1e-15": ["ValueError", "ValueError", "", ""],
    "+1e-21": ["ValueError", "ValueError", "", ""],
    "+1e-24": ["ValueError", "ValueError", "", ""],
    "+1e-27": ["ValueError", "ValueError", "", ""],
    "+1e-323": ["ValueError", "ValueError", "", ""],
    "+1e-324": ["0", "0", "0", "0"],
    "+1e-999": ["0", "0", "0", "0"],
    #
    "1e-9": ["1n", "1e-9", "", ""],
    "0.001": ["1m", "1e-3", "", ""],
    #
    "1": ["1", "1", "1", "1"],
    "999": ["999", "999", "999", "999"],
    "1000": ["1k", "1e3", "1e3", "1000"],
    "1023": ["1.02k", "1.02e3", "1.02e3", "1023"],
    "1024": ["1.02k", "1.02e3", "1.02e3", "1Ki"],
    "10239": ["10.2k", "10.2e3", "10.2e3", "9.99Ki"],
    "999e3": ["999k", "999e3", "999e3", "975Ki"],
    "999e12": ["999T", "999e12", "999e12", "908Ti"],
    #
    "999e15": ["999P", "999e15", "999e15", "ValueError"],
    "999e18": ["999E", "999e18", "999e18", "ValueError"],
    "1000e18": ["ValueError", "ValueError", "ValueError", "ValueError"],
    "1e308": ["ValueError", "ValueError", "ValueError", "ValueError"],
    "1e309": ["ValueError", "Inf", "", ""],
    "1e999": ["ValueError", "Inf", "", ""],
    "Inf": ["ValueError", "Inf", "", ""],
    #
    "NaN": ["ValueError", "NaN", "", ""],
    #
}


def clip_metric(f: float) -> str:
    """Clip the Float but give it a Metric Prefix Multiplier, not an 'e' decimal exponent"""

    metrics = "qryzafpnμm.kMGTPEZYRQ"  # https://en.wikipedia.org/wiki/Metric_prefix

    fclip = clip_float(f)

    if math.isnan(f):  # todo: raise (f, fclip) in place of (f)?
        raise ValueError(f)  # can't clip NaN
    if math.isinf(f):
        raise ValueError(f)  # can't clip Inf
    if (not f) and (math.copysign(1, f) < 0):
        return "-0"  # doesn't lose the minus sign, and doesn't speak of "e0"

    fmag, _, fexp = fclip.partition("e")
    if not fexp:
        clip = fclip
        return clip

    exp = int(fexp if fexp else "0")

    index = 10 + (exp // 3)
    metric = metrics[index]

    clip = f"{fmag}{metric}" if exp else fmag
    return clip  # -120789 --> '-120k', etc

    # raises ValueError for Floats that 2025 SI Metric Prefixes can't count out


def clip_float(f: float) -> str:
    """Find the nearest Float Literal, as small or smaller, with 1 or 2 or 3 Digits"""

    # Clip -Inf and +Inf and NaN as themselves

    if math.isnan(f):
        return "NaN"  # unsigned, not positive and not negative

    if math.isinf(f):
        absclip = "Inf"
        clip = ("-" + absclip) if (f < 0) else absclip
        return clip

    if (not f) and (math.copysign(1, f) < 0):
        return "-0e0"  # doesn't lose the minus sign  # does speak of "e0"

    # Raise ValueError if not countable by a 2022 SI Metric Prefix

    if f:
        if not (1e-27 <= abs(f) < 1000e27):  # 2022 ronto to ronna  # beyond 1991 yocto to yotta
            raise ValueError(f)  # can't clip larger than ronna, or smaller than ronto

        # "999e30": ["998Q", "998e30", "998e30", "788Qi"],  # wrong to say 998

    # Clip as Int if equal to Int, or if >= 3 Digits at left of the Decimal Point

    intf = int(f)
    if (f == intf) or (abs(intf) >= 101):  # includes -0e0, excludes 100 == 99.999999999999999
        clip = clip_int(intf)  # may raise ValueError, like at 1e21
        assert abs(float(clip)) <= abs(f), (abs(float(clip)), abs(intf), intf, f)
        return clip

    # Raise ValueError if counting as Int might round down the first 3 Digits

    assert (1000e12 + 1) != 1000e12
    assert (10e15 + 1) == 10e15

    if abs(f) < 1e-12:  # like to block 4.2e-15 -> '4e-15'
        raise ValueError(f)  # can't clip smaller than 1e-12

    # Clip as an Int multiplied by Metric Prefix below 1

    fudge = -1e-21 if (f < 0) else +1e-21  # fudge so arbitrary you could c*pyright it
    i = int((f + fudge) / 1e-15)  # 1e-12 -> '999e-15' without fudge

    if not i:
        clip = "0"  # never '-0'
        return clip

    iclip = clip_int(i)
    imag, _, iexp = iclip.partition("e")
    exp = int(iexp if iexp else "0") - 15

    clip = f"{imag}e{exp}" if exp else imag

    assert abs(float(clip)) <= abs(f), (abs(float(clip)), abs(f), f)
    return clip  # -120.789 --> '-120', etc

    # raises ValueError for Floats that 2025 SI Metric Prefixes can't count out


def clip_int(i: int) -> str:
    """Find the nearest Int Literal, as small or smaller, with 1 or 2 or 3 Digits"""

    uncountable = 1e21
    if not (-uncountable < i < uncountable):
        raise ValueError(i)  # can't clip larger than zetta

        # "-999e21": ["-998Z", "-998e21", "-998e21", "ValueError"],  # wrong to say 998

    s = str(int(i))  # '-120789'

    _, dash, digits = s.rpartition("-")  # ('', '-', '120789')
    sci = len(digits) - 1  # 5  # scientific power of ten
    eng = 3 * (sci // 3)  # 3  # engineering power of ten

    assert eng in (sci, sci - 1, sci - 2), (eng, sci, digits, i)

    if not eng:
        clip = s
        assert abs(int(float(clip))) <= abs(i), (abs(int(float(clip))), abs(i), i)
        return clip  # drops 'e0'

    assert len(digits) >= 4, (len(digits), eng, sci, digits, i)
    assert 1 <= (len(digits) - eng) <= 3, (len(digits), eng, sci, digits, i)

    precise = digits[:-eng] + "." + digits[-eng:]  # '120.789'  # significand, mantissa, multiplier
    nearby = precise[:4]  # '120.'
    worthy = nearby.rstrip("0").rstrip(".")  # '120'  # drops '.' or'.0' or '.00'

    assert "." in nearby, (nearby, precise, eng, sci, digits, i)

    clip = dash + worthy + "e" + str(eng)  # '-120e3'

    assert abs(int(float(clip))) <= abs(i), (abs(int(float(clip))), abs(i), i)
    return clip  # -120789 --> '-120e3', etc


def clip_bimetric(i: int) -> str:
    """Find the nearest binary metric literal, as small or smaller, counting out 0..1023"""

    uncountable = 0x400 * 2**40  # 1 Pi
    if i < 0:
        raise ValueError(i)  # can't count negatively many things
    if i >= uncountable:
        raise ValueError(i)  # can't count larger than pebi

    metrics = "KMGTPEZYRQ"  # https://physics.nist.gov/cuu/Units/binary.html
    bimetrics = [""] + list((_ + "i") for _ in metrics)

    multiplier = 1
    for bimetric in bimetrics:
        above = multiplier * 0x400
        if i >= above:
            multiplier = above
            continue

        fmag = i / multiplier
        assert 0 <= fmag < 0x400, (fmag, multiplier, i)

        if fmag >= 100:
            mag = str(int(fmag))  # (1024 * 1024 - 1) -> '1023Ki'
        else:
            mag = str(fmag)[:4].rstrip("0").rstrip(".")  # 10230 -> '9.99Ki'

        clip = f"{mag}{bimetric}"  # (1024 * 1024) -> '1Mi'

        return clip  # 102399 --> '99.9Ki', etc

    assert False, (i,)

    # raises ValueError for Ints that 2025 SI Metric Binary Prefixes can't count out


def _try_clip_() -> None:
    """Try Def-Clip things"""

    kvs = {"-Inf": -Inf, "Inf": Inf, "NaN": NaN}

    for str_f, wants in _clips_by_str_f_.items():

        # Form input

        i = None
        if str_f in kvs.keys():
            f = kvs[str_f]
        else:
            v = ast.literal_eval(str_f)
            f = float(v)
            unreal = math.isnan(f) or math.isinf(f)
            if not unreal:
                if int(v) == v:
                    i = int(f)

        # Try to clip

        try:
            _metric_ = clip_metric(f)
        except Exception as exc:
            _metric_ = type(exc).__name__

        try:
            _float_ = clip_float(f)
        except Exception as exc:
            _float_ = type(exc).__name__

        try:
            _int_ = "" if (i is None) else clip_int(i)
        except Exception as exc:
            _int_ = type(exc).__name__

        try:
            _bimetric_ = "" if ((i is None) or (i < 0)) else clip_bimetric(i)
        except Exception as exc:
            _bimetric_ = type(exc).__name__

        # Require the expected results

        gots = [_metric_, _float_, _int_, _bimetric_]
        assert gots == wants, (gots, wants, str_f)


#
# Amp up Import BuiltIns Str
#


def str_removeprefix(text: str, prefix: str) -> str:
    """Remove a Prefix, if present"""

    if text.startswith(prefix):
        text = text[len(prefix) :]

    return text

    # str.removeprefix exists since Oct/2020 Python 3.9


def str_removesuffix(text: str, suffix: str) -> str:
    """Remove a Suffix, if present"""

    if text.endswith(suffix):
        text = text[: -len(suffix)]

    return text

    # str.removesuffix exists since Oct/2020 Python 3.9


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
    """Try Unicode things, far beyond 7-bit US Ascii"""

    # not yet an official standard

    assert AppleLogo == "\uf8ff"  # U+F8FF  # last of U+E000 .. U+F8FF Private Use Area (PUA)

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
    # The Apple Os Copy/Paste Buffer takes in the 128 Undecodable Bytes of 0x80..0xFF as
    #
    #   ÄÅÇÉÑÖÜáàâäãåçéèêëíìîïñóòôöõúùûü†°¢£§•¶ß®¤™´¨≠
    #   ÆØ∞±≤≥¥µ∂∑∏π∫ªºΩæø¿¡¬√ƒ≈∆«»…¤ÀÃÕŒœ–—“”‘’÷◊ÿŸ⁄€
    #   ‹›ﬁﬂ‡·‚„‰ÂÊÁËÈÍÎÏÌÓÔ¤ÒÚÛÙıˆ˜¯˘˙˚¸˝˛ˇ
    #

    #
    # The Apple ⌥ Option/Alt Keys send lots of printable U+00A1 .. U+00AC, U+00AE .. U+00FF
    #
    #   ¡ ¢ £ ¥ § ¨ © ª « ¬ ® ¯ ° ± ´ µ ¶ · ¸ º » ¿
    #   ÀÁÂÃÄÅ Æ Ç ÈÉÊË ÌÍÎÏ Ñ ÒÓÔÕÖ Ø ÙÚÛÜ ß
    #   àáâãäå æ ç èéêë ìíîï ñ òóôõö ÷ ø ùúûü ÿ
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
    # and not
    #
    #   chr(0x22C5)  # "⋅"  # Dot Operator  # "⋅·" aren't two of the same Character
    #

    #
    # The Apple macBook Keyboard
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

    def __exit__(self, *exc_info: object) -> None:
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
        r, w, x = select.select([fileno], [], [], timeout)

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


MainStamp = dt.datetime.now().astimezone()

if __name__ == "__main__":
    main()


# todo's


# todo0: Serve well as the 'export EDITOR=' of Shell ⌃X⌃E


# todo1: Debug ⇧F3 of iTerm2 because ⎋[ ⇧R i/o k/s collision
# todo1: Solve iTerm2 Key Jams with ⎋[5N sent down, not written outside
# todo2: Revive passing test of buffer key input jam in sleep before launch

# todo2: Take up the Multichord Key Strikes with Shifts
# todo2: Take up the Intercardinal Arrows with Shifts


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


# 3456789_123456789_123456789_123456789 123456789_123456789_123456789_123456789 123456789_123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litglass.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
