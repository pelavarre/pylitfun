#!/usr/bin/env python3

r"""
usage: litglass.py [-h] [-f] [--egg EGG]

loop Input back to Output, to Screen from Touch/ Mouse/ Key

options:
  -h, --help   show this help message and exit
  -f, --force  ask fewer questions (like do run slow self-test's)
  --egg EGG    a hint of how to behave, such as 'repr' or 'sigint'

quirks:
  talks with the Terminal at Stderr (with /dev/stderr, not with /dev/tty)
  quits when given ⌃C

examples:
  ./litglass.py --  # to run with defaults
  ./litglass.py --egg=enter  # to launch loop back with no setup
  ./litglass.py --egg=exit  # to quit loop back with no teardown
  ./litglass.py --egg=scroll  # to scroll into scrollback then launch in alt screen
"""

# ./litglass.py --egg=Keycaps  # to launch our keyboard-viewer of keycaps
# ./litglass.py --egg=Repr  # to loop the Repr, not the Str
# ./litglass.py --egg=SigInt  # for ⌃C to raise KeyboardInterrupt

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import __main__
import argparse
import bdb
import collections
import collections.abc  # .collections.abc is not .abc
import dataclasses
import difflib
import os
import pdb
import re
import select
import signal
import sys
import termios
import textwrap
import tty
import types
import typing

# import unicodedata  # of a .unicodedata.unidata_version for friends of 웃 襾 ¤


_: object  # blocks Mypy from narrowing the Datatype of '_ =' at first mention

if not __debug__:
    raise NotImplementedError([__debug__])  # because 'python3 better than python3 -O'


default_eq_None = None  # spells out 'default=None' where Python forbids that


#
# Choose a personality
#


@dataclasses.dataclass(order=True)  # , frozen=True)
class Flags:
    """Choose a personality"""

    apple: bool = sys.platform == "darwin"  # flags.apple
    google: bool = bool(os.environ.get("CLOUD_SHELL", ""))  # flags.google
    terminal: bool = os.environ.get("TERM_PROGRAM", "") == "Apple_Terminal"  # flags.terminal

    enter: bool = False  # --egg=enter  # flags.enter to launch loop back with no setup
    _exit_: bool = False  # --egg=exit  # flags._exit_ to quit loop back with no teardown
    scroll: bool = False  # --egg=scroll  # flags.scroll to launch below Scrollback

    keycaps: bool = False  # --egg=Keycaps  # flags.keycaps to launch our keyboard-viewer of keycaps
    _repr_: bool = False  # --egg=Repr  # flags._repr_ to loop the Repr, not the Str
    sigint: bool = False  # --egg=Sigint  # flags.sigint for ⌃C to raise KeyboardInterrupt


flags = Flags()

# flags.sigint = True


#
# Run from the Shell, but tell uncaught Exceptions to launch the Py Repl
#


def main() -> None:
    """Run from the Shell, but tell uncaught Exceptions to launch the Py Repl"""

    sys.excepthook = excepthook

    parser = arg_doc_to_parser(__main__.__doc__ or "")
    shell_args_take_in(args=sys.argv[1:], parser=parser)

    with Loopbacker() as lbr:
        kv = KeyboardViewer(lbr)

        if flags.keycaps:
            kv.trace_key_releases_till()
        else:
            lbr.loop_back_till()


def arg_doc_to_parser(doc: str) -> ArgDocParser:
    """Declare the Positional Arguments & Options"""

    parser = ArgDocParser(doc, add_help=True)

    egg_help = "a hint of how to behave, such as 'repr' or 'sigint'"
    force_help = "ask fewer questions (like do run slow self-test's)"

    parser.add_argument("-f", "--force", action="count", help=force_help)
    parser.add_argument("--egg", dest="eggs", metavar="EGG", action="append", help=egg_help)

    return parser


def shell_args_take_in(args: list[str], parser: ArgDocParser) -> argparse.Namespace:
    """Take in the Shell Command-Line Args"""

    ns = parser.parse_args_if(args)  # often prints help & exits zero

    ns_keys = list(vars(ns).keys())
    assert ns_keys == ["force", "eggs"], (ns_keys, ns, args)

    celebrated_eggs = ["enter", "exit", "keycaps", "repr", "scroll", "sigint"]

    ns_eggs = ns.eggs or list()
    for egg_arg in ns_eggs:
        eggs = egg_arg.split(",")
        for egg in eggs:
            casefold = egg.casefold()

            assert len(celebrated_eggs) == 6

            if "enter".startswith(casefold) and not "exit".startswith(casefold):
                flags.enter = True
            elif "exit".startswith(casefold) and not "enter".startswith(casefold):
                flags._exit_ = True
            elif "keycaps".startswith(casefold) and not "".startswith(casefold):
                flags.keycaps = True
            elif "repr".startswith(casefold) and not "".startswith(casefold):
                flags._repr_ = True
            elif "scroll".startswith(casefold) and not "sigint".startswith(casefold):
                flags.scroll = True
            elif "sigint".startswith(casefold) and not "scroll".startswith(casefold):
                flags.sigint = True

            else:
                parser.parser.print_usage()
                print(f"don't choose {egg!r}, do choose from {celebrated_eggs}", file=sys.stderr)
                sys.exit(2)  # exits 2 for bad Arg

    sum = flags.keycaps + flags._repr_
    assert sum <= 1, (dict(_ for _ in vars(flags).items() if _[-1]),)

    if ns.force:
        _try_lit_glass_()

    return ns


def _try_lit_glass_() -> None:
    """Run slow and quick Self-Test's of this Module"""

    _try_unicode_source_texts_()

    _try_key_byte_frame_()


#
#
#


class KeyboardViewer:  # as if 'class KeyCaps' for --egg=keycaps

    Keyboard = r"""
        ⎋    F1 F2 F3 F4 F5 F6 F7 F8 F9 F10 F11 F12 <>
        `~  1! 2@ 3# 4$ 5% 6^ 7& 8* 9( 0)  -_  =+    ⌫
        ⇧⇥   qQ wW eE rR tT yY uU iI oO pP  [{  ]}    \|
        ⇪     aA sS dD fF gG hH jJ kK lL  ;:  '"       ⏎
        ⇧      zZ xX cC vV bB nN mM  ,< .> /?          ⇧
        Fn  ⌃  ⌥  ⌘   Spacebar    ⌘   ⌥        ⇧← ↑ ⇧→ ↓
    """

    Plains = r"` 1234567890-= qwertyuiop[]\ asdfghjkl;' zxcvbnm,./"
    Plains = "".join(Plains.split())

    Shifteds = r'~ !@#$%^&*()_+ QWERTYUIOP{}| ASDFGHJKL:" ZXCVBNM<>?'
    Shifteds = "".join(Shifteds.split())

    def __init__(self, loopbacker: Loopbacker) -> None:
        self.loopbacker = loopbacker

    def trace_key_releases_till(self) -> None:
        """Trace Key Releases till ⌃C"""

        lbr = self.loopbacker

        tb = lbr.terminal_boss
        sw = lbr.screen_writer
        kr = lbr.keyboard_reader

        assert ord("C") ^ 0x40 == ord("\003")

        # Draw the Gameboard

        shifters = ""  # none of ⎋ ⌃ ⌥ ⇧
        shifters = "⇧"
        self.gameboard_draw(shifters)

        # Run till Quit

        quitting = False
        while not quitting:

            # Read Input

            tb.kbhit(timeout=None)
            frames = kr.read_byte_frames()

            # Eval Input & print Output

            self.frames_write_keycaps_reply(frames, shifters)

            # Quit at ⌃C

            if b"\003" in frames:
                quitting = True
                break

        sw.print()

        # todo1: solve ⇪⇥
        # todo1: solve ← ↑ → ↓
        # todo1: toggle back out of @@@@@@@@@ or @@ or @
        # todo1: take mouse hits

    def gameboard_draw(self, shifters: str) -> None:
        """Draw the Gameboard"""

        assert shifters in ("", "⇧"), (shifters,)
        sw = self.loopbacker.screen_writer

        if not shifters:
            s = KeyboardViewer.Shifteds
            trans = str.maketrans(s, len(s) * " ")
        else:
            assert shifters == "⇧", (shifters,)  # todo1: add ⎋ ⌃ ⌥ ⇧
            s = KeyboardViewer.Plains
            trans = str.maketrans(s, len(s) * "⇧")

        dent = 4 * " "
        dedent = textwrap.dedent(KeyboardViewer.Keyboard).strip()
        splitlines = dedent.splitlines()

        sw.print()

        for index, line in enumerate(splitlines):
            rindex = index - len(splitlines)

            text = dent + line
            if index and (rindex != -1):
                text = text.translate(trans)
                if shifters != "⇧":
                    text = text.replace("⇪⇥", "⇥ ")
                    text = text.replace("⇧← ↑ ⇧→ ↓", "  ← ↑ → ↓")

            sw.print(text)

        sw.print()
        sw.print("Press ⌃C")

    def frames_write_keycaps_reply(self, frames: tuple[bytes, ...], shifters: str) -> None:

        lbr = self.loopbacker

        sw = lbr.screen_writer
        kr = lbr.keyboard_reader
        kd = lbr.keyboard_decoder

        #

        dent = 4 * " "
        dedent = textwrap.dedent(KeyboardViewer.Keyboard).strip()
        splitlines = dedent.splitlines()
        removesuffix = dedent.removesuffix(splitlines[-1])

        plains_set = set(KeyboardViewer.Plains)
        shifteds_set = set(KeyboardViewer.Shifteds)

        #

        row_y = kr.row_y
        column_x = kr.column_x

        unhit_kseqs = list()
        for frame in frames:
            kseqs = kd.bytes_to_kseqs_if(frame)
            if not kseqs:
                continue

            # Visit each Keycap

            for kseq in kseqs[:1]:  # todo: so outdent this loop body

                plain = kseq[-1]
                lower = plain.lower()
                upper = plain.upper()

                cap = kseq
                if kseq == "␢":
                    cap = "Spacebar"
                elif kseq in ("⇧⇥", "⇧←", "⇧→"):
                    cap = plain
                elif plain in shifteds_set:
                    if (lower in plains_set) or (upper in shifteds_set):
                        cap = upper  # find 'Q' for Q or for ⇧Q

                # Wipe out each Keycap when pressed

                suffix_kseqs = ("␢", "←", "↑", "→", "↓", "⇧←", "⇧→")
                hittable = dedent if kseq in suffix_kseqs else removesuffix
                find = len(splitlines[0]) if cap != "⎋" else -1

                hits = 0
                while True:

                    start = find + 1
                    find = hittable.find(cap, start)
                    if find < 0:
                        break

                    hits += 1

                    n = len(splitlines)
                    y = row_y - 3 - n
                    x = X1 + len(dent)

                    found = dedent[: find + 1].splitlines()
                    assert found, (found, find, cap)

                    y += len(found)
                    x += len(found[-1]) - 1

                    if cap in ("⎋", "⌫", "⏎", "↑", "↓"):
                        width = len(cap)
                    else:
                        width = len(shifters) + len(cap)
                        x -= len(shifters)

                    sw.write_one_control(f"\033[{y};{x}H")  # row-column-leap ⎋[⇧H
                    sw.write_printable(width * "@")

                if not hits:
                    unhit_kseqs.append([cap, kseq])

        sw.write_one_control(f"\033[{row_y};{column_x}H")  # row-column-leap ⎋[⇧H

        if unhit_kseqs:
            sw.print(unhit_kseqs, "not found")


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

    def __init__(self) -> None:

        tb = TerminalBoss()
        kr = tb.keyboard_reader
        sw = tb.screen_writer

        kd = KeyboardDecoder()

        sco = ScreenChangeOrder()

        self.terminal_boss = tb
        self.screen_writer = sw
        self.keyboard_reader = kr

        self.keyboard_decoder = kd
        self.screen_change_order = sco

    def __enter__(self) -> Loopbacker:

        tb = self.terminal_boss
        sw = self.screen_writer
        kr = self.keyboard_reader

        assert DSR6 == "\033[" "6n"

        tb.__enter__()

        if not flags.enter:
            sw.write_one_control("\033[?2004h")  # paste-wrap

        if flags.scroll:

            sw.write_one_control("\033[6n")  # todo9: more automagic Cursor Y X Reads
            kr.read_bytes()

            y = kr.row_y
            if y > 1:
                sw.write_one_control(f"\033[{y - 1}S")  # ⎋[⇧S south-rows-insert

            sw.write_one_control("\033[?1049h")  # alt-screen ⎋[⇧?1049H

        return self

    def __exit__(self, *args: object) -> None:

        tb = self.terminal_boss
        sw = self.screen_writer
        kr = self.keyboard_reader

        assert DSR6 == "\033[" "6n"

        if not flags.enter:

            sw.write_one_control("\033[?2004l")  # paste-unwrap ⎋[?2004L

        if not flags._exit_:

            sw.write_one_control("\033[m")  # plain ⎋[M vs other ⎋[ M
            sw.write_one_control("\033[ q")  # cursor-unstyled ⎋[␢Q vs other ⎋[ Q
            sw.write_one_control("\033[4l")  # replacing ⎋[4L vs ⎋[4H
            sw.write_one_control("\033[?25h")  # cursor-show ⎋[⇧?25H vs ⎋[?25L

            sw.write_one_control("\033[6n")  # todo9: more automagic Cursor Y X Reads
            kr.read_bytes()
            sw.write_one_control("\033[?1049l")  # main-screen ⎋[⇧?1049L vs ⎋[⇧?1049H
            sw.write_one_control(f"\033[{kr.row_y};{kr.column_x}H")  # row-column-leap ⎋[⇧H

        tb.__exit__(*args)

    def loop_back_till(self) -> None:
        """Loop Input back to Output, to Screen from Touch/ Mouse/ Key"""

        tb = self.terminal_boss
        sw = self.screen_writer
        kr = self.keyboard_reader

        assert ord("C") ^ 0x40 == ord("\003")
        assert CUU_Y == "\033[" "{}" "A"
        assert CUP_Y_X == "\033[" "{};{}H"
        assert ED_PS == "\033[" "{}" "J"
        assert _MAX_PN_32100_ == 32100

        if not flags._repr_:
            sw.print("Press ⌃C ", end="")
        else:
            sw.print("Press ⌃C")
            sw.write_some_controls("\t", "\t")

        quitting = False
        while not quitting:

            # Read Input

            tb.kbhit(timeout=None)
            frames = kr.read_byte_frames()

            # Eval Input & print Output

            if not flags._repr_:
                self.some_frames_loop_back(frames)
            else:
                self.some_frames_print_repr(frames)

            # Quit at ⌃C

            if b"\003" in frames:
                quitting = True
                break

        if not flags._exit_:
            sw.write_one_control("\033[32100H")  # cursor-unstyled ⎋[32100⇧H
            sw.write_one_control("\033[A")  # 1 ↑ ⎋[⇧A
            sw.write_one_control("\033[J")  # after-erase ⎋[⇧J  # simpler than ⎋[0⇧J

    def some_frames_loop_back(self, frames: tuple[bytes, ...]) -> None:
        """Collect Input Frames over time as a Screen Change Order"""

        sw = self.screen_writer
        kr = self.keyboard_reader
        sco = self.screen_change_order

        # Take in each Frame

        for frame in frames:
            try:
                kdecode = frame.decode()
            except UnicodeDecodeError:
                kdecode = ""

            if not kdecode:
                self.frame_write_echo(frame)
                continue

            # Take in the Frame by itself, while order incomplete

            sco.take_decode(kdecode, yx=(kr.row_y, kr.column_x))

            if not (sco.forceful or sco.intricate):
                self.kdecode_cook_and_loop_back(kdecode, intricate=False)
                continue

            (row_y, column_x, strong, factor, slow_kencode) = sco.compile_order()

            if not slow_kencode:
                self.frame_write_echo(frame)
                continue

            # Run the Order, after all of it arrives

            slow_kdecode = slow_kencode.decode()
            slow_isprintable = slow_kdecode.isprintable()

            if slow_isprintable and (not strong):
                sw.write_printable(kdecode)
                sco.clear_order()
                continue

            if factor < -1:  # echoes without writing
                self.frame_write_echo(frame)

            elif factor == -1:  # echoes and greatly details
                self.frame_write_echo(frame)
                sw.write_printable(" ")
                self.some_frames_print_repr(tuple([slow_kencode]))

            elif factor == 0:  # echoes and leaps and writes
                self.frame_write_echo("⌃m".encode() if (frame == b"\r") else frame)  # ⌃M
                sw.write_one_control(f"\033[{row_y};{column_x}H")
                if slow_isprintable:
                    sw.write_printable(slow_kdecode)
                else:
                    sw.write_one_control(slow_kdecode)

            else:  # echoes and cooks and leaps and writes
                self.frame_write_echo(frame)
                sw.write_one_control(f"\033[{row_y};{column_x}H")
                kr.row_y = row_y
                kr.column_x = column_x
                for _ in range(factor):
                    self.kdecode_cook_and_loop_back(slow_kdecode, intricate=sco.intricate)

            sco.clear_order()

    def kdecode_cook_and_loop_back(self, decode: str, intricate: bool) -> None:
        """Interpret the Decode of the Frame, else echo it"""

        sw = self.screen_writer
        kr = self.keyboard_reader
        kd = self.keyboard_decoder

        frame = decode.encode()
        echo = kd.frame_to_echo(frame)
        assert echo.isprintable(), (echo,)

        # If Frame is Printable

        if decode.isprintable():
            sw.write_printable(decode)
            return

        # If Frame has Keycaps

        if self.kseqs_cook_and_loop_back(decode=decode, intricate=intricate):
            return

        # Loop back a few Esc Byte Sequences unchanged

        loopable_decodes = ("\0337", "\0338", "\033D", "\033E", "\033M")
        if decode in loopable_decodes:
            sw.write_one_control(decode)
            return

        # Block the heavy hammer of ⎋C and the complex hammer of ⎋L

        if decode == "\033C":  # ⎋C to ⎋[3⇧J ⎋[⇧H ⎋[2⇧J screen-erase
            self.frame_write_echo(b"\033[3J" b"\033[H" b"\033[2J")
            return

        if decode == "\033L":  # ⎋L to ⎋[⇧H
            self.frame_write_echo(b"\033[H")
            return

        # Leap the Cursor to the ⌥-Click  # todo9: also ⎋[⇧M Click Releases

        kbf = KeyByteFrame(frame)
        (marks, ints) = kbf.to_csi_marks_ints_if()

        if (marks == b"<m") and (len(ints) == 3):
            (b, x, y) = ints  # todo: bounds check on Click Release
            sw.write_one_control(f"\033[{y};{x}H")
            sw.write_printable("@")  # '@' to make ⌥-Click's visible
            return

        # Show a brief Repr of other Encodes

        if not intricate:
            sw.write_printable(echo)
            return

        # But do forward well-known Csi & Osc Byte Sequences arriving as multiple Frames

        if self.csi_osc_cook_and_loop_back(decode=decode):
            return

        # Echo a blocked Sequence vertically

        for e in echo:
            sw.write_printable(e)
            kr.row_y = min(kr.y_high, kr.row_y + 1)
            sw.write_one_control(f"\033[{kr.row_y};{kr.column_x}H")

    def csi_osc_cook_and_loop_back(self, decode: str) -> bool:

        frame = decode.encode()
        kbf = KeyByteFrame(frame)

        sw = self.screen_writer

        if decode.startswith("\033["):

            if decode[-1] in "@" "ABCDEFGHIJKLM" "P" "ST" "Z" "d" "f" "h" "lm" "q":
                sw.write_one_control(decode)
                return True

            if decode[-1] in "nt":
                sw.write_one_control(decode)
                return True

            # Emulate Columns Insert/ Delete by Csi

            if decode[-2:] in ("'}", "'~"):
                (marks, ints) = kbf.to_csi_marks_ints_if()
                if marks in (b"'}", b"'~"):
                    if len(ints) <= 1:
                        self.screen_columns_insert_delete(marks, ints=ints)
                        return True

            # todo: Accept only the Csi understood by our Class ScreenWriter

        if decode.startswith("\033]"):
            if decode in ("\033]11;?\007", "\033]11;?\033\134"):
                sw.write_one_control(decode)  # ⎋]11;⇧?⌃G call for ⎋]11;RGB⇧:{r}/{g}/{b}⌃G
                return True

            # todo: Accept only the Osc understood by our Class ScreenWriter

        return False

    def kseqs_cook_and_loop_back(self, decode: str, intricate: bool) -> bool:
        """Interpret the Keycaps of the Frame, else return False"""

        kd = self.keyboard_decoder

        frame = decode.encode()
        kseqs = kd.bytes_to_kseqs_if(frame)
        if not kseqs:
            return False

        kseq = kseqs[0]  # only search for the first Keycap

        sw = self.screen_writer
        kd = self.keyboard_decoder

        # Echo ⎋ Esc as such  # todo9: Accept the ⌃ ⌥ ⇧ Fn Shifting Keys into sco.kbf

        if kseq in ("⎋", "⎋⎋"):
            sw.write_printable(kseq)
            return True

        # Loop back a few Key Chord Byte Sequences unchanged

        loopable_kseqs = ("⌃G", "⌃H", "⇥", "⌃J", "⌃K", "⇧⇥")
        if kseq in loopable_kseqs:
            sw.write_one_control(decode)  # ⎋[⇧Z for ⇧⇥, etc
            return True

        # Loop back ⌃M ⏎ Return as CR LF

        if kseq == "⏎":
            sw.write_some_controls("\r", "\n")
            return True

        # Loop back ⌃⇧? ⌫ as Delete

        if kseq == "⌫":
            sw.write_some_controls("\033[D", "\033[P")
            return True

        # Loop back as Arrow, no matter the shifting Keys

        join = str(kseqs)
        if not intricate:

            arrows = tuple(_ for _ in ("←", "↑", "→", "↓") if _ in join)
            if len(arrows) == 1:
                arrow = arrows[-1]
                arrow_control = kd.decode_by_kseq[arrow]
                sw.write_one_control(arrow_control)
                return True

        return False

    def screen_columns_insert_delete(self, marks: bytes, ints: tuple[int, ...]) -> None:
        """Emulate Columns Insert/ Delete by Csi"""

        assert marks in [b"'}", b"'~"], (marks,)
        assert len(ints) <= 1, (ints,)

        deleting = [b"'}", b"'~"].index(marks)

        pn_int = ints[-1] if ints else PN1
        pn = pn_int  # accepts pn = 0

        #

        sw = self.screen_writer

        kr = self.keyboard_reader
        row_y = kr.row_y
        y_high = kr.y_high

        #

        assert ICH_X == "\033[" "{}" "@"
        assert VPA_Y == "\033[" "{}" "d"
        assert DECDC_X == "\033[" "{}" "'~"
        assert DECIC_X == "\033[" "{}" "'}}"  # speaking of ⎋[ '}

        #

        for y in range(Y1, y_high + 1):
            sw.write_one_control(f"\033[{y}d")
            sw.write_one_control(f"\033[{pn}P" if deleting else f"\033[{pn}@")
        sw.write_one_control(f"\033[{row_y}d")

        # Apple & Google lack ⎋['⇧} cols-insert

    def frame_write_echo(self, frame: bytes) -> None:
        """Show a brief Repr of one Frame"""

        sw = self.screen_writer
        kd = self.keyboard_decoder

        echo = kd.frame_to_echo(frame)
        sw.write_printable(echo)

    def some_frames_print_repr(self, frames: tuple[bytes, ...]) -> None:
        """Print the Repr of each Frame, but mark the Frames as framed together"""

        sw = self.screen_writer
        kr = self.keyboard_reader

        assert CUP_Y_X == "\033[" "{};{}H"

        (y, x) = (kr.row_y, kr.column_x)
        for frame_index, frame in enumerate(frames):
            self.frames_write_one_repr(frames, frame_index=frame_index)

            y += 1  # todo: 'row_y > y_high' happens here  # todo: update Y X shadow
            sw.write_one_control("\n")
            sw.write_one_control(f"\033[{y};{x}H")

    def frames_write_one_repr(self, frames: tuple[bytes, ...], frame_index: int) -> None:
        """Write the Repr of one Frame, but mark the Frames as framed together"""

        frame = frames[frame_index]

        try:
            decode = frame.decode()
        except UnicodeDecodeError:
            decode = ""

        sw = self.screen_writer
        kd = self.keyboard_decoder

        # Choose the details

        printables: list[object] = list()

        kseqs = kd.bytes_to_kseqs_if(frame)
        if kseqs:
            if (frame == b"`") and frames[1:]:
                printables.append(tuple(reversed(kseqs)))  # ('⌥⇧`', '`') 0 `
            else:
                printables.append(kseqs)

        if frames[1:]:
            printables.append(frame_index)

        if decode and decode.isprintable():
            printables.append(decode)
        else:
            printables.append(repr(frame))

        # Write the chosen details

        text = " ".join(str(_) for _ in printables)
        sw.write_printable(text)


@dataclasses.dataclass(order=True)  # , frozen=True)
class ScreenChangeOrder:
    """Hold some Text, or one Control Sequence"""

    yx: tuple[int, ...]

    early_mark: str  # ''  # '\025' ⌃U
    int_literal: str  # ''  # '0x42'  # '9'
    late_mark: str  # ''  # '\025' ⌃U

    key_byte_frame: KeyByteFrame
    intricate: bool  # says if .key_byte_frame grown from multiple Inputs

    #
    # Define Init, Bool, Str, & Clear
    #

    def __init__(self) -> None:

        self.key_byte_frame = KeyByteFrame(b"")
        self.clear_order()

    def clear_order(self) -> None:

        kbf = self.key_byte_frame

        self.yx = tuple()

        self.early_mark = ""
        self.int_literal = ""
        self.late_mark = ""

        kbf.clear_frame()
        self.intricate = False

    def __bool__(self) -> bool:

        truthy = self != ScreenChangeOrder()
        return truthy

    @property
    def forceful(self) -> bool:
        forceful = bool(self.early_mark or self.int_literal or self.late_mark)
        return forceful

    def __str__(self) -> str:

        early_mark = self.early_mark
        int_literal = self.int_literal
        late_mark = self.late_mark

        intricate = self.intricate

        kbf = self.key_byte_frame
        kencode = kbf.to_frame_bytes()

        em = repr(early_mark)[1:-1]
        lm = repr(late_mark)[1:-1]

        s = f"{em} {int_literal} {lm} {intricate} {kencode!r}"  # no .forceful

        return s

        # '\x15' '0' '\x15' b'\x1b[A'

    #
    # Say what to do and where
    #

    def compile_order(self) -> tuple[int, int, int, int, bytes]:
        """Say where to run, what to run, and if strongly told to run it other than once"""

        yx = self.yx

        early_mark = self.early_mark
        int_literal = self.int_literal
        late_mark = self.late_mark

        kbf = self.key_byte_frame

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

        kbf.tilt_to_close_frame()  # like stop staying open to accept b x y into ⎋[⇧M{b}{x}{y}

        kencode = kbf.to_frame_bytes()
        if not kbf.closed:
            if not kbf.printable:
                kencode = b""

        # Succeed

        return (row_y, column_x, strong, factor, kencode)

    #
    # Add on a next Input, else restart
    #

    def take_decode(self, decode: str, yx: tuple[int, int]) -> None:
        """Add on a next Input, else restart"""

        assert decode, (decode,)
        encode = decode.encode()

        kbf = self.key_byte_frame
        assert _FACTOR_MARK_ == "\025"

        # Take Input after a Text Frame or Closed Frame as a new Order

        if kbf.printable or kbf.closed:
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

        if decode == "\025":  # ⌃U

            if (early_mark and late_mark) or kbf:
                self.clear_order()
                self.early_mark = decode
                return

            if not early_mark:
                self.early_mark = decode
            elif not int_literal:
                self.early_mark += decode
            else:
                self.late_mark = decode

            return

        # Start or grow an Int Literal

        lit_plus = int_literal + decode

        if not late_mark:
            if not decode.isspace():
                if not kbf:

                    if not ScreenChangeOrder.is_int_value_error(lit_plus + "0"):
                        self.int_literal = lit_plus
                        return

        # Grow the Frame

        with_bool_kbf = bool(kbf)
        extras = kbf.take_kencode_if(encode)
        if not extras:
            if with_bool_kbf:
                self.intricate = True

            return

        # Else secretly silently start over  # like when reached by ⎋ [ ' 2

        self.clear_order()

    @staticmethod
    def is_int_value_error(x: str) -> bool:
        """Say if is Int Literal"""

        base_eq_0 = 0

        try:
            _ = int(x, base_eq_0)
            return False
        except ValueError:
            return True


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

        stdio = self.stdio
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        # Exit once

        if not tcgetattr:
            return

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

    def kbhit(self, timeout: float | None) -> bool:
        """Block till next Input Byte, else till Timeout, else till forever"""

        stdio = self.stdio
        fileno = self.fileno

        assert self.tcgetattr, (self.tcgetattr,)

        stdio.flush()  # before select.select of .kbhit
        (r, w, x) = select.select([fileno], [], [], timeout)

        hit = fileno in r

        return hit

        # a la msvcrt.kbhit


class ScreenWriter:
    """Write Lines of Output to the Terminal Screen"""

    terminal_boss: TerminalBoss

    def __init__(self, terminal_boss: TerminalBoss) -> None:
        self.terminal_boss = terminal_boss

    def print(self, *args: object, end: str | None = "\r\n") -> None:
        """Answer the question of 'what is print?' here lately"""

        text = " ".join(str(_) for _ in args)

        end_str = "" if (end is None) else end
        if end_str:
            assert not end_str.isprintable(), (end_str,)

            # todo: tighter contract than the merely standard 'def print'

        self.write_printable(text)  # may raise UnicodeEncodeError
        self.write_some_controls(*end_str)  # may raise UnicodeEncodeError

        # todo: one 'def print' per project is exactly enough?

        # .end=None here puns with .end="", same as it does in Python's .print

        # presumes writes of arbitrary bytes will go to 'tb.write_some_bytes'
        # does 'may raise UnicodeEncodeError' on purpose

    def write_printable(self, text: str) -> None:
        """Write the Byte Encodings of Printable Text without adding a Line-Break"""

        assert text.isprintable(), (text,)
        self.write(text)

    def write_some_controls(self, *texts: str) -> None:
        """Write the Byte Encodings of >= 0 Unprintable Control Texts"""

        for text in texts:
            self.write_one_control(text)

        # may write zero controls

    def write_one_control(self, text: str) -> None:
        """Write the Byte Encodings of one Unprintable Control Text"""

        if not text:
            return

        assert not text.isprintable(), (text,)

        encode = text.encode()
        kbf = KeyByteFrame(encode)  # may raise UnicodeEncodeError
        kbf.tilt_to_close_frame()  # like stop staying open to accept b x y into ⎋[⇧M{b}{x}{y}
        assert (not kbf.printable) and kbf.closed, (encode, kbf)

        self.write(text)

        # presumes writes of arbitrary bytes will go to 'tb.write_some_bytes'
        # does 'may raise UnicodeEncodeError' on purpose

    def write(self, text: str) -> None:
        """Write the Byte Encodings of Text without adding a Line-Break"""

        tb = self.terminal_boss
        data = text.encode()  # may raise UnicodeEncodeError
        tb.write_some_bytes(data)

        # todo: one 'def write' per project is exactly enough?

        # presumes writes of arbitrary bytes will go to 'tb.write_some_bytes'
        # does 'may raise UnicodeEncodeError' on purpose


class KeyboardReader:
    """Read Frames of Input from the Terminal Keyboard"""

    terminal_boss: TerminalBoss

    y_high: int  # H W always positive after initial (-1, -1)
    x_wide: int

    row_y: int  # todo: row_y_column_x: tuple[int, ...] to be initially Empty Tuple
    column_x: int

    def __init__(self, terminal_boss: TerminalBoss) -> None:

        self.terminal_boss = terminal_boss

        self.row_y = -1
        self.column_x = -1
        self.y_high = -1
        self.x_wide = -1

    #
    # Split the Input Bytes of a Cursor Position Report into >= 1 Frames,
    # and update the H W Y X of this KeyboardReader
    #

    def read_byte_frames(self) -> tuple[bytes, ...]:
        """Read one Frame at a time, and help the Client ignore H W Y X"""

        (click_release_frame, after) = self._read_click_release_frame_and_after_()

        frame_list = list()
        if click_release_frame:
            frame_list.append(click_release_frame)

        while after:
            (frame, next_after) = self._bytes_split_frame_(after)
            assert frame, (frame, next_after, after)
            assert (frame + next_after) == after, (frame, next_after, after)

            frame_list.append(frame)
            after = next_after

        frames = tuple(frame_list)
        assert frames, (frames,)

        return frames

    def _read_click_release_frame_and_after_(self) -> tuple[bytes, bytes]:
        """Read Bytes, but split off a leading ⌥-Click if present"""

        reads = self.read_bytes()
        assert reads, (reads,)

        (arrowheads, after) = self.bytes_split_arrowheads(reads)
        assert arrowheads or after, (arrowheads, after, reads)

        click_release_frame = b""
        if arrowheads:
            click_release_frame = self._arrowheads_to_frame_(arrowheads)
            assert click_release_frame, (click_release_frame, arrowheads)

        return (click_release_frame, after)

    def bytes_split_arrowheads(self, data: bytes) -> tuple[str, bytes]:
        """Split a Burst of Arrows into a Head of Arrows and a Tail of Bytes"""

        marks: list[str] = list()
        after = b""

        assert ClassicArrowEncodes == (b"\033[A", b"\033[B", b"\033[C", b"\033[D")

        if len(data) <= 2 * 3:  # takes double ClassicArrowEncodes as 8-way Compass Arrows
            return ("", data)

        for i in range(0, len(data), 3):
            few = data[i:][:3]  # spans of 3 bytes, but maybe short at end

            if few not in (b"\033[A", b"\033[B", b"\033[C", b"\033[D"):
                after = data[i:]
                break

            ord_mark = few[-1]
            mark = chr(ord_mark)  # the Csi Final Byte

            assert mark in ("A", "B", "C", "D"), (mark, few)
            marks.append(mark)

        arrowheads = "".join(marks)
        return (arrowheads, after)

    def _arrowheads_to_frame_(self, arrowheads: str) -> bytes:
        """Convert a Burst of Arrows into a ⌥-Click Release"""

        y = self.row_y
        x = self.column_x
        h = self.y_high
        w = self.x_wide

        assert ClassicArrowEncodes == (b"\033[A", b"\033[B", b"\033[C", b"\033[D")

        o = (y, x, h, w, arrowheads)

        for a in arrowheads:

            if x > w:
                x -= w
                y += 1

            if a == "A":

                y -= 1

            elif a == "B":

                y += 1

            elif a == "C":

                x += 1

            else:
                assert a == "D", (a,)

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
            x -= 1

        f = int("0b01000", base=0)  # f = 0b⌃⌥⇧00
        option_mouse_release = f"\033[<{f};{x};{y}m".encode()

        return option_mouse_release  # lower 'm' for Release

    def _bytes_split_frame_(self, data: bytes) -> tuple[bytes, bytes]:
        """Split one Frame off the Start of the Bytes"""

        assert KeyboardDecoder.OptionAccents == ("`", "´", "¨", "ˆ", "˜")
        assert KeyboardDecoder.OptionGraveGrave == "``"

        assert _NorthEastArrowEncode_ == "\033[↗".encode()
        assert _NorthWestArrowEncode_ == "\033[↖".encode()
        assert _SouthWestArrowEncode_ == "\033[↙".encode()
        assert _SouthEastArrowEncode_ == "\033[↘".encode()

        if not data:
            return (data, b"")

        decode = KeyByteFrame.bytes_decode_if(data)

        # Accept the b"``" as the Frame of ⌥⇧`

        if len(decode) == 2:
            if decode == "``":  # ⌥⇧` `
                frame = data
                after = b""
                return (frame, after)

            # Split the ⌥ Accents arriving together with an Unaccented Decode

            accents = ("`", "´", "¨", "ˆ", "˜")  # ⌥⇧` ⌥⇧E ⌥⇧U ⌥⇧I ⌥⇧N
            if decode[0] in accents:
                frame = decode[0].encode()
                after = decode[1:].encode()
                return (frame, after)

        # Accept Double-Key-Jam's as 8-way Compass Arrows  # todo7:

        pass

        # Split one Text or Control Frame off the Start of the Bytes

        after = b""

        kbf = KeyByteFrame(b"")
        for i in range(len(data)):
            kbyte = data[i:][:1]
            kbytes = data[i:][1:]

            extras = kbf.take_kbyte_if(kbyte)
            if extras:
                assert kbf.closed, (kbf.closed, extras, kbyte, kbf)
                after = extras + kbytes
                break

            if kbf.closed:
                after = kbytes
                break

        frame = kbf.to_frame_bytes()
        assert (frame + after) == data, (frame, after, data)

        return (frame, after)

    #
    # Frame the Input Bytes that share a Cursor Position Report,
    # and update the H W Y X of this KeyboardReader
    #

    def read_bytes(self) -> bytes:
        """Frame the Bytes that share a Cursor Position Report"""

        tb = self.terminal_boss
        fileno = tb.fileno

        # Read one Byte, then call for Cursor Position, then block till it comes

        (yx, reads) = self.read_yx_bytes()
        (row_y, column_x) = yx

        fd = fileno
        (x_wide, y_high) = os.get_terminal_size(fd)

        # Publish this fresh H W Y X sample separately

        assert y_high >= 5, (y_high,)  # todo: test of Terminals smaller than macOS Terminals
        assert x_wide >= 20, (x_wide,)  # todo: test of 9 Columns x 2 Rows at macOS iTerm2

        self.row_y = row_y
        self.column_x = column_x

        self.y_high = y_high
        self.x_wide = x_wide

        # Succeed

        return reads

    def read_yx_bytes(self) -> tuple[tuple[int, int], bytes]:
        """Read one Byte, then call for Cursor Position, then block till it comes"""

        tb = self.terminal_boss

        assert DSR6 == "\033[" "6n"
        assert CPR_Y_X == "\033[" "{};{}R"

        tb.write_some_bytes(b"\033[6n")  # ⎋[6n
        tb.kbhit(timeout=0e0)  # flushes after .write_some_bytes

        row_y = -1
        column_x = -1
        ba = bytearray()

        while True:

            read = tb.read_one_byte()
            ba.extend(read)

            if row_y < 0:
                m = re.search(rb"\033\[([0-9]+);([0-9]+)R$", string=ba)  # ⎋[{y};{x}⇧R
                if not m:
                    continue

                n = len(m.group(0))
                row_y = int(m.group(1))
                column_x = int(m.group(2))

                del ba[-n:]

                if not ba:  # someone else wrote ⎋[6n earlier
                    continue

            if not tb.kbhit(timeout=0e0):
                break

        yx = (row_y, column_x)
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
    #   ⌥` sends b"``" always together
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

            extras = self.take_kbyte_if(kbyte)
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

        encode = self.to_frame_bytes()

        if encode == b"\033[M":  # takes the ⎋[⇧M DL_Y that isn't the ⎋[⇧M{b}{x}{y} _CLICK3_
            assert (not printable) and (not neck) and (not backtail), (head, self, encode)
            assert head == b"\033[M", (head, self, encode)

            if not stash:
                assert head == b"\033[M", (head,)
                assert not closed, (closed, self)

                del head[len(b"\033[") :]
                backtail.extend(b"M")

                self.close_frame()

        # todo: an awful lot of code here, for a dramatically simple idea?

        # like stop staying open to accept b x y into ⎋[⇧M{b}{x}{y}

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

    def take_kencode_if(self, data: bytes) -> bytes:
        """Try to take X Bytes in and return 0 <= Y <= X Bytes that don't fit"""

        for index in range(len(data)):
            kbyte = data[index:][:1]
            kbytes = data[index:][1:]

            extras = self.take_kbyte_if(kbyte)
            if extras:
                extras_plus = extras + kbytes
                return extras_plus

        return b""

    def take_kbyte_if(self, data: bytes) -> bytes:
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

        encode = bytes(stash + kbyte)
        try:
            decode = encode.decode()
        except UnicodeDecodeError:
            decode = ""

        if not decode:
            if KeyByteFrame.bytes_to_later_decode_if(encode):
                stash.extend(kbyte)
                return b""

        assert len(decode) <= 1, (len(decode), decode, encode)

        stash.clear()

        # Take the Bytes in before the first Head, or without ever a Head

        if not head:
            extras = self._take_before_head_if_(encode, decode=decode)
            return extras

        # Take later Bytes in differently, after starts with each kind of Head

        assert not printable, (printable,)

        dent = len(head) - len(head.lstrip(b"\033"))
        dent = (dent - 1) if dent else 0
        undented_head = head[dent:]

        if undented_head == b"\033":
            extras = self._take_after_esc_if_(encode)
            return extras

        elif undented_head == b"\033O":
            extras = self._take_after_ss3_if_(encode)
            return extras

        elif undented_head == b"\033[M":
            extras = self._take_after_csi_m_if_(encode)
            return extras

        elif undented_head == b"\033[":
            extras = self._take_after_csi_if_(encode, decode=decode)
            return extras

        elif undented_head == b"\033]":
            extras = self._take_after_osc_if_(encode, decode=decode)
            return extras

        assert False, (head, head[dent:], dent, self)

    def _take_before_head_if_(self, encode: bytes, decode: str) -> bytes:
        """Take 1..4 more Bytes in, before any Head, else return what doesn't fit"""

        printable = self.printable
        head = self.head

        # Take 1 Decoded Printable Char, without closing the Frame

        if decode:
            if decode.isprintable():
                self.printable = printable + encode
                return b""

        # End a Text Frame before Unprintable or Undecodable Bytes

        if printable:
            self.close_frame()
            return encode

        # Take 1..4 Unprintable or Undecodable Bytes as Head

        head.extend(encode)
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

    def _take_after_esc_if_(self, encode: bytes) -> bytes:
        """Take 1..4 more Bytes in, after ⎋ Esc, else return what doesn't fit"""

        head = self.head

        # Take one of the ⎋ Esc Head's, without closing the Frame

        head_plus = head + encode
        if head_plus in KeyByteFrame.Headbook:
            lstrip = head_plus.lstrip(b"\033")
            assert len(lstrip) <= 1, (head_plus,)

            head.extend(encode)
            return b""

            # doesn't take ⇧M after \⎋ [ here

        # Take ⎋ Esc as an Emacs Meta Byte before 1..4 Bytes

        head.extend(encode)
        self.close_frame()
        return b""

    def _take_after_ss3_if_(self, encode: bytes) -> bytes:
        """Take 1..4 more Bytes in, after ⎋O SS3, else return what doesn't fit"""

        head = self.head

        head.extend(encode)
        self.close_frame()
        return b""

    def _take_after_csi_m_if_(self, encode: bytes) -> bytes:
        """Take 1..4 more Bytes in, after ⎋[⇧M, else return what doesn't fit"""

        head = self.head
        backtail = self.backtail

        # Take up to three B X Y Chars after the Head, if all printable

        head_backtail_plus = bytes(head + backtail + encode)
        plus_later = KeyByteFrame.bytes_to_later_decode_if(head_backtail_plus)
        assert not plus_later, (plus_later, head, backtail, encode)

        plus_decode = KeyByteFrame.bytes_decode_if(head_backtail_plus)
        if plus_decode:
            if len(plus_decode) <= 6:
                backtail.extend(encode)
                if len(plus_decode) == 6:
                    self.close_frame()
                return b""

        # Take up to three B X Y Bytes after the Head without limitation

        fit = 6 - len(head + backtail)
        if fit > 0:
            backtail.extend(encode[:fit])
            extra = encode[fit:]
            if len(head_backtail_plus) >= 6:
                self.close_frame()
            return extra  # maybe empty

        # Close the ⎋[⇧M Frame after 6 Bytes or before

        self.close_frame()
        return encode

    def _take_after_csi_if_(self, encode: bytes, decode: str) -> bytes:
        """Take 1..4 more Bytes in, after ⎋[ CSI, else return what doesn't fit"""

        code = ord(decode)

        head = self.head
        neck = self.neck
        backtail = self.backtail

        assert _CLICK3_ == "\033[M"

        # Take the 3-Byte ⎋[⇧M Esc Head, without closing the Frame

        if (not neck) and (not backtail):
            head_plus = head + encode
            if head_plus in KeyByteFrame.Headbook:
                assert head_plus == b"\033[M", (head_plus,)
                head.extend(encode)
                return b""

        # Grow the ⎋[ Csi Frame with 1 Decoded Printable Char

        if decode and decode.isprintable():
            assert code >= 0x20, (code, decode, encode)

            # Grow the Neck until the Backtail starts

            if 0x30 <= code < 0x40:  # 16 Parameter Codes  # 0123456789:;<=>?

                if not backtail:
                    neck.extend(encode)
                    return b""

                # Close before more Params, if Backtail has started

                self.close_frame()
                return encode

            # Grow the Backtail

            if 0x20 <= code < 0x30:  # 16 Intermediate Codes  # ␢!"#$%&\'()*+,-./
                backtail.extend(encode)
                return b""

            # Close after a Csi Final Code, or after Printable Unicode

            assert code >= 0x40, (code, decode, encode)  # 63 Final Codes  # @A Z[\\]^_`a z{|}~

            backtail.extend(encode)
            self.close_frame()
            return b""

        # Close the ⎋[ Csi Frame before Unprintable or Undecodable Bytes

        self.close_frame()
        return encode

    def _take_after_osc_if_(self, encode: bytes, decode: str) -> bytes:
        """Take 1..4 more Bytes in, after ⎋] OSC, else return what doesn't fit"""

        neck = self.neck
        backtail = self.backtail

        assert BEL == "\007"
        assert ST == "\033\134"

        # Grow the ⎋] Osc Frame with 1 Decoded Printable Char

        if not backtail:
            if decode and decode.isprintable():
                neck.extend(encode)
                return b""

        # Close the ⎋] Osc Frame with BEL or ST

        if decode == "\007":
            backtail.extend(encode)
            self.close_frame()
            return b""

        if not backtail:
            if decode == "\033":
                backtail.extend(encode)
                return b""

        if backtail == b"\033":
            if decode == "\134":
                backtail.extend(encode)
                self.close_frame()
                return b""

            # todo: how should other Bytes past "\033" close an ⎋] Osc Frame?

        # Close the ⎋] Osc Frame before Unprintable or Undecodable Bytes

        self.close_frame()
        return encode

    #
    # Work with Decodable and Undecodable Bytes
    #

    @staticmethod
    def bytes_decode_if(data: bytes) -> str:
        """Say if printable"""

        try:
            decode = data.decode()
            return decode  # returns first found
        except UnicodeDecodeError:
            pass

        return ""

    Endswiths = (b"\xbf", b"\x80\x80", b"\xbf\xbf", b"\x80\x80\x80", b"\xbf\xbf\xbf")

    @staticmethod
    def bytes_to_later_decode_if(data: bytes) -> str:
        """Say if some Bytes start 1 or more UTF-8 Encodings of Chars"""

        endswiths = KeyByteFrame.Endswiths

        for endswith in endswiths:
            encode = data + endswith
            try:
                decode = encode.decode()
                assert len(decode) >= 1, (decode,)
                return decode  # returns first found
            except UnicodeDecodeError:
                continue

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


Y1 = 1  # min Y of Terminal Cursor
X1 = 1  # min X of Terminal Cursor

PN0 = 0  # default Csi Pn = 0 for some
PN1 = 1  # default Csi Pn = 1 for others
_MAX_PN_32100_ = 32100  # max Csi Pn = 32100 exceeds the x_wide x y_high of most Terminal Screens

BEL = "\007"  # 00/07 Bell

_FACTOR_MARK_ = "\025"  # 01/05 ⌃U Emacs Global-Map Universal-Argument

ESC = "\033"  # 01/11 Escape ⎋

SS3 = "\033O"  # 01/11 04/15 Single Shift Three  # ⎋O
CSI = "\033["  # 01/11 05/11 Control Sequence Introducer  # ⎋[
OSC = "\033]"  # 01/11 05/13 Operating System Command  # ⎋]

ST = "\033\134"  # 01/11 05/12 String Terminator  # ⎋\


ICH_X = "\033[" "{}" "@"  # Csi 04/00 [Insert] Cursor Horizontal [Pn] [Columns]

CUU_Y = "\033[" "{}" "A"  # Csi 04/01 Cursor Up [Pn] [Rows]
CUP_Y_X = "\033[" "{};{}H"  # Csi 04/08 [Choose] Cursor Position [Y and X]
ED_PS = "\033[" "{}" "J"  # Csi 04/10 Erase Data [Ps]  # Ps 0 1 2 3
DL_Y = "\033[" "{}M"  # Csi 04/13 Delete Line [Row]

VPA_Y = "\033[" "{}" "d"  # Csi 06/04 Vertical Position Absolute [Row]

DECIC_X = "\033[" "{}" "'}}"  # Csi 07/13 [DEC] Insert Column [Pn]
DECDC_X = "\033[" "{}" "'~"  # Csi 07/14 [DEC] Delete Column [Pn]

_CLICK3_ = "\033[M"  # ⎋[⇧M{b}{x}{y} Click Press/ Release


DSR6 = "\033[" "6n"  # Csi 06/14 [Request] Device Status Report  # Ps 6 Request CPR  # ⎋[6N
CPR_Y_X = "\033[" "{};{}R"  # ⎋[y;x⇧R


#
# Speak of a Byte Encoding as a Sequence of Chords of Keycaps
#


class KeyboardDecoder:
    """Speak of a Byte Encoding as a Sequence of Chords of Keycaps"""

    selves: list[KeyboardDecoder] = list()

    decode_by_kseq: dict[str, str]
    kseqs_by_decode: dict[str, tuple[str, ...]]

    def __init__(self) -> None:

        KeyboardDecoder.selves.append(self)

        self.decode_by_kseq = dict()
        self.kseqs_by_decode = dict()

        self._add_basic_kseqs_()
        self._invert_decode_by_kseq_()

    #
    # Speak of a Byte Encoding as a Sequence of Chords of Keycaps
    #

    def frame_to_echo(self, frame: bytes) -> str:
        """Form a brief Repr of one Input Frame"""

        # Show Keycaps, if available as ⌫ ⇧⇥ ⇥ etc, except show ⏎ as ⌃M

        kseqs = self.bytes_to_kseqs_if(frame)
        if kseqs:
            echo = kseqs[0]
            assert echo.isprintable(), (echo,)
            return echo  # ⌫  # ⇧⇥  # ⇥  # ⏎

        # Show the unquoted Repr, if not decodable

        try:
            kdecode = frame.decode()
        except UnicodeDecodeError:
            kdecode = ""

        if not kdecode:
            echo = repr(frame)[1:-1]
            assert echo.isprintable(), (echo,)
            return echo

        # Show one Keycap per Character, if decodable

        echo = ""
        for decode in kdecode:
            encode = decode.encode()
            kseqs = self.bytes_to_kseqs_if(encode)
            kseq = kseqs[0] if kseqs else repr(decode)[1:-1]
            echo += kseq

        assert echo.isprintable(), (echo,)
        return echo

    def bytes_to_kseqs_if(self, data: bytes) -> tuple[str, ...]:
        """Speak of a Byte Encoding as a Sequence of Chords of Keycaps"""

        decode = data.decode()

        kseqs_by_decode = self.kseqs_by_decode

        if decode in kseqs_by_decode.keys():
            kseqs = kseqs_by_decode.get(decode, tuple())
            return kseqs

        return tuple()

    #
    # Add the Keycap Sequences for US-Ascii at MacBook
    #

    def _add_basic_kseqs_(self) -> None:
        """Add the Keycap Sequences for US-Ascii at MacBook"""

        decode_by_kseq = self.decode_by_kseq

        # Add the named Keycaps: Esc, Tab, ⇧Tab, Return, Delete

        d0 = {
            r"⇥": "\t",  # ⌃I
            r"⏎": "\r",  # ⌃M
            r"⎋": "\033",  # ⌃[
            r"⇧⇥": "\033[" "Z",  # ⎋ [ ⇧Z
            r"⌫": "\177",  # ⌃⇧?
        }

        for k, v in d0.items():
            assert k not in decode_by_kseq.keys(), (k,)
            decode_by_kseq[k] = v

        # Add the forms of Spacebar

        d1 = {
            r"␢": "\040",  # ⌃`
            r"⌃␢": "\000",  # ⌃⇧@
            r"⌥␢": "\240",  # U+00A0 No-Break Space
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
            decode = chr(code)

            if kcap not in ("⌃`", "⌃⇧?"):
                assert kcap not in decode_by_kseq.keys(), (kcap,)
                decode_by_kseq[kcap] = decode

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

        # Add the Basic Arrows and the Double-Key-Jam Arrows  # todo7:

        d3 = {
            r"↑": "\033[" "A",  # ⎋[⇧A
            r"↓": "\033[" "B",  # ⎋[⇧B
            r"→": "\033[" "C",  # ⎋[⇧C
            r"←": "\033[" "D",  # ⎋[⇧D
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

    #
    # Index the Keycap Sequences by their Decodes
    #

    OptionAccents = ("`", "´", "¨", "ˆ", "˜")  # ⌥⇧` ⌥⇧E ⌥⇧U ⌥⇧I ⌥⇧N
    OptionGraveGrave = "``"  # ⌥⇧` `

    def _invert_decode_by_kseq_(self) -> None:
        """Index the Keycap Sequences by their Decodes"""

        decode_by_kseq = self.decode_by_kseq
        kseqs_by_decode = self.kseqs_by_decode

        # Index the Sequences collected by now

        d = collections.defaultdict(list)
        for kseq, decode in decode_by_kseq.items():
            d[decode].append(kseq)

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
            decode = option

            assert kseq not in decode_by_kseq.keys(), (kseq,)
            decode_by_kseq[kseq] = decode

            d[decode].append(kseq)

            # ⌥Y comes through as the U+005C Reverse-Solidus, not U+00A5 ¥ Yen-Sign

        assert option_printables.count("¥") == 8  # ⌥␢ ⌥E ⌥I ⌥N ⌥U ⌥Y ⌥` ⌥⌫

        option_kseq_by_decode = {  # upper "j́" is "J́" len 2 decode, led by plain U+004A 'J'
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

        for decode, kseq in option_kseq_by_decode.items():

            if kseq in decode_by_kseq.keys():
                assert decode_by_kseq[kseq] == decode, (decode_by_kseq[kseq], decode, kseq)
            else:
                decode_by_kseq[kseq] = decode
                d[decode].append(kseq)

            if " " in kseq:
                ks = kseq[:-1] + "⇧" + kseq[-1:]
                dc = decode.upper()  # 'Á' from 'á'
                if dc != decode:

                    if ks in decode_by_kseq.keys():
                        assert decode_by_kseq[ks] == dc, (decode_by_kseq[ks], dc, ks)
                    else:
                        decode_by_kseq[ks] = dc
                        d[dc].append(ks)

        # Add the "Use Option as Meta key" of macOS Terminal

        for code in range(0, 0x80):
            if code not in (0, 0x1E):  # ⎋⌃␢ and ⎋⌃⇧@ and ⎋⌃⇧^ don't
                decode = chr(code)

                kseqs = tuple(d[decode])
                for kseq in kseqs:
                    assert " " not in kseq, (kseq,)

                    alt_kseq = "⎋" + kseq  # '⎋␢'
                    alt_decode = "\033" + decode

                    assert alt_kseq not in decode_by_kseq.keys(), (alt_kseq,)
                    decode_by_kseq[alt_kseq] = alt_decode

                    d[alt_decode].append(alt_kseq)

                    # ⎋B hides behind ⌥←, ⎋F hides behind ⌥→

        kseqs = ("⇧⇥", "↑", "↓", "→", "←")
        for kseq in kseqs:
            assert " " not in kseq, (kseq,)
            decode = decode_by_kseq[kseq]

            alt_kseq = "⎋" + kseq  # '⎋␢'
            alt_decode = "\033" + decode

            assert alt_kseq not in decode_by_kseq.keys(), (alt_kseq,)
            decode_by_kseq[alt_kseq] = alt_decode

            d[alt_decode].append(alt_kseq)

            # ⎋← hides behind ⎋B behind ⌥←, ⎋→ hides behind ⎋F behind ⌥→

        # Convert to immutable Tuples from mutable Lists

        for decode, kseq_list in d.items():
            assert decode not in kseqs_by_decode, (decode, kseqs_by_decode[decode], kseq_list)
            kseqs_by_decode[decode] = tuple(kseq_list)

        # no explicit mention of ÁÉÍJ́ÓÚ ÂÊÎÔÛ ÃÑÕ ÄËÏÖÜŸ ÀÈÌÒÙ


ClassicArrowEncodes = (b"\033[A", b"\033[B", b"\033[C", b"\033[D")

UpwardsArrowEncode = b"\033[A"
DownwardsArrowEncode = b"\033[B"
RightwardsArrowEncode = b"\033[C"
LeftwardsArrowEncode = b"\033[D"

_NorthEastArrowEncode_ = "\033[↗".encode()  # W D, D W
_NorthWestArrowEncode_ = "\033[↖".encode()  # A W, W A
_SouthWestArrowEncode_ = "\033[↙".encode()  # A S, S A
_SouthEastArrowEncode_ = "\033[↘".encode()  # S D, D S


#
# Try things
#


def _try_key_byte_frame_() -> None:

    assert DL_Y == "\033[" "{}M"
    assert _CLICK3_ == "\033[M"
    assert UpwardsArrowEncode == b"\033[A"
    assert ST == "\033\134"

    # Do nothing with grace & elegance

    KeyByteFrame(b"")

    # Speak well of ↑ and ⎋↑

    kbf = KeyByteFrame(b"\033[A")
    assert kbf.to_frame_bytes() == b"\033[A", (kbf,)
    assert kbf.closed, (kbf,)

    kbf = KeyByteFrame(b"\033\033[A")
    assert kbf.to_frame_bytes() == b"\033\033[A", (kbf,)
    assert kbf.closed, (kbf,)

    # Dance well with the _CLICK3_ clash into DL_Y without Pn

    kbf = KeyByteFrame(b"\033[M")
    assert kbf.to_frame_bytes() == b"\033[M", (kbf,)
    assert not kbf.closed, (kbf,)  # because could be ⎋[⇧M{b}{x}{y}

    kbf = KeyByteFrame(b"\033[Mabc")
    assert kbf.to_frame_bytes() == b"\033[Mabc", (kbf,)
    assert kbf.closed, (kbf,)

    kbf = KeyByteFrame(b"\033[Mab\xff")
    assert kbf.to_frame_bytes() == b"\033[Mab\xff", (kbf,)
    assert kbf.closed, (kbf,)

    # Accept 8-way Compass Arrows, not just the 4-way Most Classic Arrows

    kbf = KeyByteFrame("\033[↗".encode())
    assert kbf.to_frame_bytes() == "\033[↗".encode(), (kbf,)
    assert kbf.closed, (kbf,)

    # Accept the ⎋\ String Terminator (ST) to close an ⎋] Osc Frame

    kbf = KeyByteFrame(b"\033]11;?\033\\")
    assert kbf.to_frame_bytes() == b"\033]11;?\033\\", (kbf,)
    assert kbf.closed, (kbf,)

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
# Amp up Import Traceback
#
# Especially when installed via:  sys.excepthook = excepthook
#


with_excepthook = sys.excepthook  # aliases old hook, and fails fast to chain hooks
assert with_excepthook.__module__ == "sys", (with_excepthook.__module__,)
assert with_excepthook.__name__ == "excepthook", (with_excepthook.__name__,)

assert sys.__stderr__ is not None  # refuses to run headless
with_stderr = sys.stderr


assert int(0x80 + signal.SIGINT) == 130  # discloses the Nonzero Exit Code for after ⌃C SigInt


def excepthook(  # ) -> ...:
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: types.TracebackType | None,
) -> None:
    """Run at Process Exit"""

    sys.excepthook = with_excepthook

    if exc_type is SystemExit:
        assert sys.flags.interactive, (sys.flags.interactive, exc_type, exc_value)  # aka python3 -i
        return

        # consciously doesn't call: with_excepthook(exc_type, exc_value, exc_traceback)

    # Quit loudly for KeyboardInterrupt

    if exc_type is KeyboardInterrupt:
        pass

    # Quit quickly quietly, if BdbQuit

    if exc_type is bdb.BdbQuit:
        with_stderr.write("BdbQuit\n")
        sys.exit(130)  # 0x80 + signal.SIGINT  # same as for KeyboardInterrupt

    # Print the Traceback, etc

    print(file=with_stderr)
    print(file=with_stderr)  # twice
    print("ExceptHook", file=with_stderr)

    with_excepthook(exc_type, exc_value, exc_traceback)

    # Launch the Post-Mortem Debugger

    print(">" ">" "> pdb.pm()", file=with_stderr)  # (3 * ">") spelled unlike a Git Conflict
    pdb.pm()


#
# Amp up Import UnicodeData
#
# P=litglass.py && cat $P |python3 -c 'import sys; print(repr("".join(sorted(set(sys.stdin.read())))))'
#


def _try_unicode_source_texts_() -> None:
    """Explicitly don't limit our Source Text to US-Ascii"""

    assert "" == "\uf8ff"  # U+F8FF  # last of U+E000 .. U+F8FF Private Use Area (PUA)

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
    # The Apple MacBook Keyboard doesn't send U+2196..U+2199 Diagonal Arrows as such
    #
    #   ↗ ↖ ↙ ↘
    #
    # June/1993 Unicode 1.1.0 gave us these four, among its U+2190 .. U+219F Symbols And Arrows
    #

    #
    # Here in 2025 we're running no Tests of Unicode U+FB01 and U+FB02
    #
    #   ﬁ ﬂ
    #
    # And no Tests of Unicode U+0131 .. U+25CA
    #
    #   ıŒœŸƒˆˇ˘˙˚˛˜˝́Ωπ–—‘’‚“”„†‡•…‰‹›⁄€™←↑→↓⇥⇧⇪∂∆∏∑√∞∫≈≠≤≥⌃⌘⌥⌫⎋⏎␢◊
    #
    # And no Tests of Unicode U+00A1 .. U+00F8
    #
    #   ¡¢£¥§¨©ª«¬®¯°±´µ¶·¸º»¿Çßç÷ø
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


# todo7: the Arrows of the ⇧ Shifted Game, and Git Push, but then

# todo8: take the ⌃ ⌥ ⇧ out of the Key Caps of the Shifted Games


# todo9: --egg=keycaps 8 at ⌃ ⌥ ⇧ including the Fn, 8 more at ⎋

# todo9: --egg=resize to fit the Terminal to the Gameboard and vice versa


# todo9: add Fn Keycaps

# todo9: drop Keycaps specific to macOS Terminal, when elsewhere
# todo9: add iTerm2 Keycaps
# todo9: add Google Cloud Shell Keycaps


# todo9: pick apart text key jams and unbracketed text paste


# todo9: echo input well, like to show ⎋ [ ' 2 is two Frames:  ⎋[' and 2
# todo9: show settings
# todo9: place input echoes on the side
# todo9: vs scroll while echo of ScreenChangeOrder's in the far Southeast


# 3456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/litglass.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
