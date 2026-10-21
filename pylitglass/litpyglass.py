#!/usr/bin/env python3

r"""
usage: litpyglass.py [--egg=EGG ...]

loop back to write Screen after reading from Touch/ Mouse/ Key

options:
  --egg EGG  a hint of how to behave, such as 'bytes' or 'frames'

quirks:
  quits when given an unprintable, 3 times in a row, but 100ms or more apart, across less than 3s

examples:
  python3 pylitglass/litpyglass.py  # show these examples
  chmod +x pylitglass/litpyglass.py
  pylitglass/litpyglass.py --  # pick a demo and run it
  pylitglass/litpyglass.py --egg=bytes  # print your input bytes, on screen
  pylitglass/litpyglass.py --egg=nanos  # print your input bytes and when they arrived
  pylitglass/litpyglass.py --egg=frames  # print your inputs split into frames, named when known
  pylitglass/litpyglass.py --egg=strikes  # print your input frames as strikes else text
"""

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import collections
import dataclasses
import decimal
import errno
import functools
import io
import os
import re
import select
import string
import sys
import termios
import textwrap
import time
import tty
import typing
import unicodedata

_: object  # blocks Mypy from narrowing the Datatype of '_ =' at first mention

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


#
# Configure
#


_3_GIGA_NANOS_IS_TOO_SLOW_ = 3 * 10**9  # too slow to take 3 same inputs in a row as a quit request
_100_MEGA_NANOS_IS_TOO_FAST_ = 100 * 10**6  # too fast to take 3 in a row as a quit request


CR_EL_PS0 = "\r\n" "⎋[K "  # scrolls up the present Screen Row, starts writing the next
CR_EL_PS0 = "\r" "\033[K"  # wipes and replaces the present Screen Row
# last wins


assert unicodedata.name("¤").title() == "Currency Sign"


#
# Run from the Shell Command Line
#


def main() -> None:
    """Run from the Shell Command Line"""

    # Help or don't help

    closing = _main_doc_scrape_closing_()

    shargv = sys.argv[1:]
    if not shargv:
        print()
        print(closing)
        print()

        sys.exit(0)  # exits zero after printing help

    print()  # signal very very quietly that we have run this far since launching

    # Pick a demo, else freak  # todo: tighter parsing of .shargv

    eggs = list(_.removeprefix("--egg=") for _ in shargv if _.startswith("--egg="))
    if not eggs:
        eggs.append("bytes")

    gw = GlassWorker()
    gw.nano_launch = time.perf_counter_ns()

    if "bytes" in eggs:
        gw.show_bytes()
    elif "nanos" in eggs:
        gw.show_nanos()
    elif "frames" in eggs:
        gw.show_frames()
    elif "strikes" in eggs:
        gw.show_strikes()
    else:
        assert False, (eggs,)

    # Self-test quickly, and succeed

    _try_terminal_byte_frame_()
    _try_keyboard_decoder_()

    print()

    # ends with 0 or 1 or 2 empty lines
    # 0 for Stdin Eof, 1 commonly, 2 for quit via Return Return Return in particular


def _main_doc_scrape_closing_() -> str:
    """Scrape out the last Graf of Main Doc, minus its header"""

    doc = __doc__ or ""  # pylance fears __doc__ is None
    header = "examples:\n"
    index = doc.index(header) + len(header)
    closing = textwrap.dedent(doc[index:]).strip()

    return closing


#
# Show off one Terminal feature and another
#


class GlassWorker:
    """Show off one Terminal feature and another"""

    nano_launch: int = -1  # -1, else sampled at Process Launch

    def show_bytes(self) -> None:
        """Print your Input Bytes on screen"""

        # Launch (and prompt just once and early)

        print("Press Return three times quickly, to quit")
        print()

        with TerminalBoss() as tb:
            ibk = ByteKeeper()

            while True:

                # Read

                sys.stdout.flush()  # flushes well-known outputs before blocking on well-known input
                sys.stderr.flush()

                b = tb.read_one_byte_if()
                if not b:
                    break

                nano = time.perf_counter_ns()
                ibk.append_one_byte(b, nano=nano)

                # Print, and separate on request

                print(ord(b), bytes_repr(b), end="\r\n")
                if b == b"\r":
                    print()

                # Quit on request

                if ibk.is_quitting_bytes():
                    break

    _ = r"""

        ] % pylitglass/litpyglass.py --egg=bytes
        ]
        ] Press Return three times quickly, to quit
        ]
        ] 27 b'\033'
        ] 91 b'['
        ] 65 b'A'
        ] 13 b'\r'
        ]
        ] 9 b'\t'
        ] 9 b'\t'
        ] 9 b'\t'
        ]
        ] %

    """  # (the many ']'s at left margin block VsCode freaking out over '[' spoken without ']')

    def show_nanos(self) -> None:
        """Print your Input Bytes (and how quickly they arrived)"""

        # Launch (and prompt just once and early)

        print("Press Return three times quickly, to quit")
        print()

        before = self.nano_launch

        with TerminalBoss() as tb:
            ibk = ByteKeeper()

            while True:

                # Read

                sys.stdout.flush()  # flushes well-known outputs before blocking on well-known input
                sys.stderr.flush()

                b = tb.read_one_byte_if()
                if not b:
                    break

                after = time.perf_counter_ns()
                ibk.append_one_byte(b, nano=after)

                # Print, and separate on request

                code = ord(b)
                between = after - before
                before = after

                print(f"{between:_}", code, bytes_repr(b), end="\r\n")
                if b == b"\r":
                    print()

                # Quit on request

                if ibk.is_quitting_bytes():
                    break

    _ = r"""

        ] % pylitglass/litpyglass.py --egg=nanos
        ]
        ] Press Return three times quickly, to quit
        ]
        ] 2_001_201_167 27 b'\033'
        ] 536_090_125 91 b'['
        ] 529_302_167 65 b'A'
        ] 639_591_500 13 b'\r'
        ]
        ] 1_229_210_041 3 b'\003'
        ] 330_829_750 3 b'\003'
        ] 327_861_042 3 b'\003'
        ]
        ] %

    """  # (the many ']'s at left margin block VsCode freaking out over '[' spoken without ']')

    def show_frames(self) -> None:
        """Print your Input Byte Frames, as Key Caps when known, and how quickly they arrived"""

        # Launch

        print("Press Return three times quickly, to quit")
        print()

        with TerminalBoss() as tb:
            tfr = TerminalFrameReader()

            for taken, frame, cells in tfr.take_frames(tb):
                data = frame.to_frame_bytes()  # maybe empty

                # Prompt for next Byte, while growing the Frame

                if not taken:
                    self.frame_print(data, cells=cells, end=" + ")

                    continue

                # Print each Frame taken as a line

                self.frame_print(data, cells=cells, end="\r\n")

                if data == b"\r":  # pressing Return splits Frame Lines into paragraphs
                    print()

    def frame_print(self, data: bytes, cells: list[int | bytes], end: str) -> None:
        """Print 'caps data = cell cell ...' as a whole line, or as the start of one"""

        kd = keyboard_decoder()

        def ns(n: int) -> str:  # reps Int's as counting Nanoseconds
            rep = decimal_int_chop_to_eng_metric(n, one="1ns")  # reps 987*10**12 as '987ks'
            return rep

        words: list[str] = list()

        # Choose the words

        caps = kd.bytes_to_key_caps_if(data)  # ⎋, ⎋[, ↑ when typed slowly
        if caps:
            words.append(caps)

        decode = TerminalByteFrame.bytes_decode_if(data)
        if decode:
            if decode.isprintable() and (decode.strip() == decode):
                words.append(decode)
            else:
                words.append(str_repr(decode))

        words.append(f"{bytes_repr(data)} =")

        piths = [c for (i, c) in enumerate(cells) if (i == 0) or (c != 0)]  # drops adds of '0ns'
        reps = [(ns(p) if isinstance(p, int) else bytes_repr(p)) for p in piths]
        words.extend(reps)

        # Print the words

        start = CR_EL_PS0  # often '\r' '\033[K'
        join = " ".join(words)
        print(f"{start}{join}{end}", end="")

        # known: "\r" snaps back the Terminal Column X only until the Terminal Row overflows
        # known: inject wide texts to overflow thin terminals

    _ = r"""

        ] % pylitglass/litpyglass.py --egg=frames
        ]
        ] Press Return three times quickly, to quit
        ]
        ] ⌥EJ j́ b'j\314\201' = 3.98s b'j' 572µs b'\314' b'\201'
        ] ⇥ '\t' b'\t' = 1.11s b'\t'
        ] ⌥P π b'\317\200' = 535ms b'\317' b'\200'
        ] ↑ '\033[A' b'\033[A' = 750ms b'\033' b'[' b'A'
        ] ⌥EE é b'\303\251' = 534ms b'\303' b'\251'
        ] ⏎ '\r' b'\r' = 537ms b'\r'
        ]
        ] Q ⇧Q ␢ 'qQ ' b'qQ ' = 478ms b'q' 474ms b'Q' 477ms b' '
        ] ⏎ '\r' b'\r' = 530ms b'\r'
        ]
        ] ⏎ '\r' b'\r' = 161ms b'\r'
        ]
        ] ⏎ '\r' b'\r' = 160ms b'\r'
        ]
        ]
        ] %

    """  # (the many ']'s at left margin block VsCode freaking out over '[' spoken without ']')

    def show_strikes(self) -> None:
        """Print your Input Byte Frames, as Key Caps when known, and as Text when printable"""

        # Launch

        print("Press Return three times quickly, to quit")
        print()

        with TerminalBoss() as tb:
            sp = ScreenProxy()

            for taken, strikes, printables, frame in sp.take_strikes_else_printables(tb):
                data = frame.to_frame_bytes()  # maybe empty

                start = CR_EL_PS0  # often '\r' '\033[K'

                # Prompt for the first Byte of a Frame

                if not data:
                    assert not taken, (taken, frame)
                    print(f"{start}+ ", end="")

                    continue

                # Speak of the Frame as its Strikes when known, else as ⌘V, since no Key Cap sends it

                words: list[str] = list()

                words.append(strikes if strikes else "⌘V")
                words.append(str_repr(printables))
                words.append(bytes_repr(data))

                join = " ".join(words)

                # Prompt for next Byte, while growing the Frame

                if not taken:
                    print(f"{start}{join} + ", end="")

                    continue

                # Print each Frame taken as a line

                print(f"{start}{join}\r\n", end="")

            # Erase the Prompt left behind when Stdin Eof ends the Frames

            start = CR_EL_PS0  # often '\r' '\033[K'
            print(start, end="")

    _ = r"""

        ] % pylitglass/litpyglass.py --egg=strikes
        ]
        ] Press Return three times quickly, to quit
        ]
        ] ↑ '' b'\033[A'
        ] ⌃A '' b'\001'
        ] ⇥ '' b'\t'
        ] Q ⇧Q ␢ ⌥P ⌥EJ ⌥⇧@ 'qQ πj́€' b'qQ \317\200j\314\201\342\202\254'
        ] ⌘V '' b'\377'
        ] ⏎ '' b'\r'
        ] ⏎ '' b'\r'
        ] ⏎ '' b'\r'
        ]
        ] %

    """  # (the many ']'s at left margin block VsCode freaking out over '[' spoken without ']')


#
# Speak of each Frame as Strikes when its Key Caps are known, and as Text when printable
#


class ScreenProxy:
    """Speak of each Frame as Strikes when its Key Caps are known, and as Text when printable"""

    tfr: TerminalFrameReader  # the Frames taken so far, and the Open Frame
    kd: KeyboardDecoder  # the Key Caps known to send Bytes

    def __init__(self) -> None:

        self.tfr = TerminalFrameReader()
        self.kd = keyboard_decoder()

    def take_strikes_else_printables(
        self, tb: TerminalBoss
    ) -> typing.Iterator[tuple[bool, str, str, TerminalByteFrame]]:
        """Yield (Taken, Strikes, Printables, Frame) per Frame open or taken, and drop its Cells"""

        tfr = self.tfr
        kd = self.kd

        for taken, frame, _ in tfr.take_frames(tb):
            data = frame.to_frame_bytes()  # maybe empty

            # Speak of the Frame as Text, when its Bytes decode as Printable

            printables = ""
            decode = TerminalByteFrame.bytes_decode_if(data)
            if decode and decode.isprintable():
                printables = decode

            # Speak of the Frame as Strikes, when the Keyboard Decoder names its Key Caps

            strikes = kd.bytes_to_key_caps_if(data)  # ⎋, ⎋[, ↑ when typed slowly
            assert strikes == strikes.strip(), (strikes, frame)

            yield (taken, strikes, printables, frame)


#
# Speak of Byte Frames as Strikes of Key Caps at a MacBook
#


@functools.cache
def keyboard_decoder() -> KeyboardDecoder:
    """Build the one KeyboardDecoder, once, and hand it back on each later call"""

    kd = KeyboardDecoder()
    return kd


class KeyboardDecoder:
    """Speak of Byte Frames as Strikes of Key Caps at a MacBook"""

    decode_by_echo: dict[str, str]
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

    assert sorted(ShortcutShifts) == sorted(FamiliarShifts)

    DeadKeyEchoByCombining = {  # Typists say Dead Keys do not step the Cursor forward
        "\u0300": "⌥`",  # Combining Grave Accent
        "\u0301": "⌥E",  # Combining Acute Accent
        "\u0302": "⌥I",  # Combining Circumflex Accent
        "\u0303": "⌥N",  # Combining Tilde
        "\u0308": "⌥U",  # Combining Diaeresis
    }

    def __init__(self) -> None:

        self.decode_by_echo = dict()
        self._form_macos_keyboards_()
        self._form_apple_terminal_keyboards_()

        self.echoes_by_decode = self._form_echoes_by_decode_()

    def _form_macos_keyboards_(self) -> None:
        """Form the ordinary Apple MacBook Keyboards of Bytes sent by Caps"""

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
        """  # the '...' in here mark Key Strikes that send no Bytes: a Bell, the ⌃⏎ Menu, or macOS

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
        """  # the five ¤ splats in here mark Dead Keys that do not step the Cursor forward

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
        """  # the '...' in here mark Key Strikes that send no Bytes: a Bell, or the ⌃⇧⏎ Menu

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 6 ⌥⇧

        shifts = "⌥⇧"  # ⌥⇧K sends the Apple Logo, coded here as \uf8ff
        strikes = """
            033
            140 ⁄ € ‹ › ﬁ ﬂ ‡ ° · ‚ — ± 177
            ⎋[⇧Z Œ „ ´ ‰ ˇ Á ¨ ˆ Ø ∏ ” ’ »
            Å Í Î Ï ˝ Ó Ô \uf8ff Ò Ú Æ 015
            ¸ ˛ Ç ◊ ı ˜ Â ¯ ˘ ¿
            302.240 ⎋[⇧D ⎋[⇧A ⎋[⇧C ⎋[⇧B
        """  # can't be = r""", because \u inside.

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
        """  # the '...' in here mark Key Strikes that send no Bytes: a Bell instead
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

        # 10 ⎋⇧

        shifts = "⎋⇧"
        strikes = """
            033.033
            033.176 ⎋⇧! ⎋⇧@ ⎋⇧# ⎋⇧$ ⎋⇧% ⎋⇧^ ⎋⇧& ⎋⇧* ⎋⇧( ⎋⇧) ⎋⇧_ ⎋⇧+ 033.010
            ⎋⎋[⇧Z ⎋⇧Q ⎋⇧W ⎋⇧E ⎋⇧R ⎋⇧T ⎋⇧Y ⎋⇧U ⎋⇧I ⎋⇧O ⎋⇧P ⎋⇧{ ⎋⇧} ⎋⇧|
            ⎋⇧A ⎋⇧S ⎋⇧D ⎋⇧F ⎋⇧G ⎋⇧H ⎋⇧J ⎋⇧K ⎋⇧L ⎋⇧: ⎋⇧" 033.015
            ⎋⇧Z ⎋⇧X ⎋⇧C ⎋⇧V ⎋⇧B ⎋⇧N ⎋⇧M ⎋⇧< ⎋⇧> ⎋⇧?
            033.040 ⎋⎋[⇧D ⎋⎋[⇧A ⎋⎋[⇧C ⎋⎋[⇧B
        """  # 033.117 ⎋O stops without closing its Frame (like could be ⎋OP)

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
            decode = self._cap_strikes_to_decode_if_(cap_strikes, echo=echo)
            if decode:
                self._keyboard_add_decode_(decode, echo=echo)

    def _cap_strikes_to_decode_if_(self, cap_strikes: str, echo: str) -> str:
        """Convert to Decode of Byte Encoding of Key Strike"""

        assert len(echo.split()) == 1, (len(echo.split()), echo)

        if cap_strikes in ("...", "¤"):  # splats of width 3 and width 1
            return ""

        cap_strikes_split = [cap_strikes]
        if cap_strikes not in (".", "⎋."):  # "." is in N M , . /  # "⎋." is in 033.015 ⎋, ⎋. ⎋/
            cap_strikes_split = cap_strikes.split(".")

        ba = bytearray()
        for bytes_names in cap_strikes_split:
            data = self._bytes_names_to_bytes_(bytes_names)
            ba.extend(data)

        decode = ba.decode()
        assert ba and decode, (ba, decode)

        return decode  # unprintable b"\177" for "177"  # unprintable b"\302\240" for "302.240"

    def _bytes_names_to_bytes_(self, bytes_names: str) -> bytes:
        """Convert one or a few Bytes Names from a Key Cap Strike to the Bytes named"""

        # Accept single Characters

        if len(bytes_names) == 1:  # '€'
            t = bytes_names
            assert t not in ("⎋⌃⌥⇧" + "`" + "~"), (t, bytes_names)
            # not these Shifts, not these Chars
            return bytes_names.encode()

        # Accept single Characters escaped, no matter if shifted or not

        if bytes_names == "⎋⎋":  # ⎋⎋
            return b"\033\033"

        if bytes_names.startswith("⎋") and (len(bytes_names) == 2):  # ⎋Z  # ⎋/  # rejects ⎋`
            t = bytes_names[1:]
            if t not in (string.digits + string.ascii_uppercase):
                assert t in ("-=" + "[]\\" + ";'" + ",./"), (t, bytes_names)
                # only also these Marks, in Keyboard Order

            encode = b"\033" + t.lower().encode()
            return encode

        if bytes_names.startswith("⎋⇧") and (len(bytes_names) == 3):  # ⎋⇧Z  # ⎋⇧?  # rejects ⎋⇧~
            t = bytes_names[2:]
            if t not in string.ascii_uppercase:  # only these
                assert t in ("!@#$%^&*()_+" + "{}|" + ':"' + "<>?"), (t, bytes_names)
                # only also these Marks, in ⇧ Keyboard Order
            encode = b"\033" + t.encode()
            return encode

        # Accept three Octal Digits as an Octet

        octet = re.fullmatch(r"[0-7][0-7][0-7]", string=bytes_names)
        if octet:  # 177  # 302  # 240
            d = int(bytes_names, base=0o010)  # raises ValueError when > 0o377
            encode = bytes([d])
            return encode

        # Accept simple Ss3 Frames spoken as ⎋O... ⇧...

        ss3 = re.fullmatch(r"(⎋)⇧(O)⇧([PQRS])", string=bytes_names)
        if ss3:  # ⎋⇧O⇧S
            encode = b"\033" + ss3.group(2).encode() + ss3.group(3).encode()
            return encode

        # Accept simple Csi Frames spoken as ⎋[... ⇧..., even when preceded by one extra ⎋

        csi = re.fullmatch(r"(⎋|⎋⎋)(\[)([0-9;]*)⇧([ABCDPQRSZ~])", string=bytes_names)
        if csi:  # ⎋[⇧Z  # ⎋[1;2⇧C  # ⎋⎋[⇧D  # ⎋[17⇧~
            encode = len(csi.group(1)) * b"\033"
            encode += csi.group(2).encode() + csi.group(3).encode()
            encode += csi.group(4).encode()
            return encode

        assert False, (bytes_names,)

    def _keyboard_add_decode_(self, decode: str, echo: str) -> None:
        """Add a Key Cap and its Byte Encoding to a Keyboard"""

        assert decode, (decode, echo)
        assert len(echo.split()) == 1, (len(echo.split()), echo)

        decode_by_echo = self.decode_by_echo

        assert echo not in decode_by_echo.keys(), (echo, decode_by_echo[echo])
        decode_by_echo[echo] = decode

    def _form_apple_terminal_keyboards_(self) -> None:
        """Form an Apple macOS Terminal Keyboard, out of Bytes Names"""

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
        """Add a Key Cap and its Bytes Names to a Keyboard"""

        assert len(echo.split()) == 1, (len(echo.split()), echo)
        decode = self._cap_strikes_to_decode_if_(cap_strikes, echo=echo)
        self._keyboard_add_decode_(decode, echo=echo)

    def _add_twelve_fn_meta_control_p_(self, shifts: str) -> None:
        """Add the Twelve F Keys at the one Decode"""

        assert shifts in KeyboardDecoder.ShortcutShifts, (shifts,)
        caps = "F1 F2 F3 F4" + " " + "F5 F6 F7 F8" + " " + "F9 F10 F11 F12"
        strikes = 12 * " 033.020"  # ⎋⌃P
        self._keyboard_add_some_(caps, strikes=strikes, shifts=shifts)

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

    #
    # Speak of Bytes as Strikes of Key Caps at a MacBook
    #

    def bytes_to_key_caps_if(self, data: bytes) -> str:
        """Name the Key Caps struck to send these Bytes, else an Empty Str when unsure"""

        dead_key_echo_by_combining = KeyboardDecoder.DeadKeyEchoByCombining

        # Give up on Undecodable Bytes

        text = TerminalByteFrame.bytes_decode_if(data)
        if not text:
            return ""

        # Name the one Chord of Key Caps that sends the whole Text, when there is one

        echoes = self.bytes_to_echoes_if(data)
        if echoes:
            echo = echoes[0]
            return echo  # ⇥  # ⏎  # ↑  # ⌃A  # ⌥⇧E

        # Else name one Chord per Char, with each ⌥ Dead Key struck before the Char it accents

        nfd = unicodedata.normalize("NFD", text)  # splits é into e plus Combining Acute Accent

        words: list[str] = list()
        dead_key_echo = ""
        for t in nfd:

            if t in dead_key_echo_by_combining.keys():
                if (not words) or dead_key_echo:
                    return ""  # a Combining Mark pasted alone or doubled, which no Key sends

                dead_key_echo = dead_key_echo_by_combining[t]
                words[-1] = dead_key_echo + words[-1]  # glued before the Char, as struck
                continue

            dead_key_echo = ""

            t_echoes = self.bytes_to_echoes_if(t.encode())
            if not t_echoes:
                return ""  # such as a Char that no MacBook Keyboard sends

            t_echo = t_echoes[0]
            words.append(t_echo)

        caps = " ".join(words)
        return caps  # ⌥EJ  # ⌥EE  # ⇧A ⇧B ⇧C

    def bytes_to_echoes_if(self, data: bytes) -> tuple[str, ...]:
        """Speak of Bytes as Strikes of Chords of Key Caps"""

        text = data.decode()

        echoes_by_decode = self.echoes_by_decode

        if text in echoes_by_decode.keys():
            echoes = echoes_by_decode[text]
            return echoes

            # tuple of '⎋', of '␢', of '⌥⇧⇥', of '⌃⌥⇧Fn'

        return tuple()


def _try_keyboard_decoder_() -> None:
    """Try KeyboardDecoder things"""

    kd = keyboard_decoder()

    # Pair up Bytes with the Key Caps struck to send them, else with an Empty Str

    pairs = (
        #
        (b"", ""),  # nothing struck
        (b"\t", "⇥"),  # a Control Byte
        (b"\r", "⏎"),
        (b"\001", "⌃A"),
        (b"\033", "⎋"),
        (b"\033[A", "↑"),  # a Csi Terminal Byte Frame
        (b"\033[1;2C", "⇧→"),
        (b"\033[", "⎋["),  # ⎋ struck before [
        (b"\033[1", "⎋ [ 1"),  # three Key Caps struck, though no Chord sends these Bytes
        (b"\033[a", "⎋ [ A"),  # three Key Caps struck, and the trailing b'a' closes the Frame
        (b" ", "␢"),  # a Printable Char
        (b"j", "J"),
        (b"J", "⇧J"),
        (b"ABC", "⇧A ⇧B ⇧C"),  # a Paste
        (b"\377", ""),  # an Undecodable Byte
        #
        ("é".encode(), "⌥EE"),  # 'é' as 1 Char  # NFD would split out a Combining Acute Accent
        ("j́".encode(), "⌥EJ"),  # 'j' before Combining Acute Accent, from Dead Key & then J Key
        ("´".encode(), "⌥⇧E"),  # the Spacing Acute Accent, as struck
        ("\u0301".encode(), ""),  # the Combining Acute Accent by itself, which no Key sends
        ("a\u0301\u0308".encode(), ""),  # two Combining Marks on one Char, which no Key sends
        #
        (b"\033OP", "F1"),  # an Ss3 Terminal Byte Frame
        (b"\033[17~", "F6"),  # F6 over ⌥F1 or ⎋F1, which send the same Bytes
        (b"\033[23~", "⌥F6"),  # ⌥F6 because macOS Mission Control often steals F11
        (b"\033[24~", "F12"),  # F12 over ⌥F7 or ⎋F7
        (b"\033[25~", "⇧F5"),  # ⇧F5 over ⌥F8 or ⎋F8
        (b"\033[22~", "⎋ [ 2 2 ⇧~"),  # no F Key sends ⎋[22~  # F10 sends 21, F11 sends 23
        (b"\033\020", "⎋⌃P"),  # ⎋⌃P over ⎋⇧F1 .. ⎋⌃⇧F12, which send the same Bytes
        #
    )

    for data, want in pairs:
        caps = kd.bytes_to_key_caps_if(data)
        assert caps == want, (caps, want, data)

    # Show Unicode tells Apple that the Dead Key should accent the Char struck after it

    dead_key_echo_by_combining = KeyboardDecoder.DeadKeyEchoByCombining
    for t in dead_key_echo_by_combining.keys():
        assert unicodedata.combining(t), (t,)


#
# Read Bytes from a Terminal, place them into Frames, and say when each Byte arrived
#


class TerminalFrameReader:
    """Read Bytes from a Terminal, place them into Frames, and say when each Byte arrived"""

    tft: TerminalFrameTaker  # the Frames taken so far, and the Open Frame
    cells: list[int | bytes]  # the Nanos waited and the Bytes read, not yet handed out with a Frame

    def __init__(self) -> None:

        self.tft = TerminalFrameTaker()
        self.cells = list()

    def take_frames(
        self, tb: TerminalBoss
    ) -> typing.Iterator[tuple[bool, TerminalByteFrame, list[int | bytes]]]:
        """Yield (False, Open Frame, Cells) before each Read, and (True, Taken Frame, Cells) after"""

        tft = self.tft
        cells = self.cells

        before = time.perf_counter_ns()  # doesn't measure time to launch

        while True:

            # Yield the Open Frame before each Read, as a Frame not yet taken

            taken = False
            yield (taken, tft.frame, cells)

            # Block to fetch >= 1 Bytes

            sys.stdout.flush()  # flushes well-known outputs before blocking on well-known input
            sys.stderr.flush()

            data = tb.read_some_bytes_if()
            if not data:
                break  # quits at Stdin Eof

            after = time.perf_counter_ns()  # counts time-to-read Bytes as waiting for next Bytes
            waited = after - before
            before = after

            # Place each Byte into the first Frame or a later Frame, and mark how slowly it arrived

            nano = time.perf_counter_ns()

            for i in range(len(data)):
                b = data[i:][:1]
                beyond = data[i:][1:]

                # Ask if we've already fetched a Combining Mark to complete a Frame EndsWith Text

                peek = ""
                for n in range(1, 5):  # accepts 1..4 Bytes of UTF-8
                    text = TerminalByteFrame.bytes_decode_if(beyond[:n])
                    if text:
                        if unicodedata.category(text) in ("Mn", "Mc", "Me"):
                            peek = text  # Mark & (Non-Spacing | Combining/Spacing | Enclosing)
                        break

                # Take the Byte (but leave a Frame EndsWith Text open if Combining Mark peeked)

                tft.take_one_byte(b, nano=nano, peek=peek)

                # Mark how slowly this Byte arrived

                cells.append(waited)
                waited = 0  # waited some ns only for the first Byte of these

                cells.append(b)

            # Yield each Frame taken to place these Bytes

            yield from self._pull_frames_and_yield_each_()

            # Quit when the Frames say to quit

            if tft.is_quitting_frames():
                break

        # Take the Open Frame with the Frames taken before it, at Stdin Eof or at Quit

        tft.take_open_frame_if()  # if it holds Bytes
        yield from self._pull_frames_and_yield_each_()

    def _pull_frames_and_yield_each_(
        self,
    ) -> typing.Iterator[tuple[bool, TerminalByteFrame, list[int | bytes]]]:
        """Yield (True, Taken Frame, Cells) for each Frame taken since last called"""

        tft = self.tft
        cells = self.cells

        frames = tft.frames[tft.index :]  # the Taken Frames not yet pulled
        triples = tft.pull_frame_triples()
        assert len(triples) == len(frames), (len(triples), len(frames))

        for frame, triple in zip(frames, triples):
            start, end, data = triple
            assert data == frame.to_frame_bytes(), (data, frame)

            length = 2 * len(data)  # two cells per Byte
            assert len(cells) >= length, (len(cells), length, data)

            _cells_ = cells[:length]
            del cells[:length]

            taken = True
            yield (taken, frame, _cells_)


#
# Take Frames out of the Bytes arriving, and track when each Byte arrived
#


@dataclasses.dataclass(order=True)  # , frozen=True)
class TerminalFrameTaker:
    """Take Frames out of the Bytes arriving, and track when each Byte arrived"""

    bk: ByteKeeper  # the Bytes, and when each arrived

    frame: TerminalByteFrame  # the Open Frame
    frames: list[TerminalByteFrame]  # the Taken Frames, each closed, or bounced, or cut at Eof/ Quit
    index: int  # how many Taken Frames also pulled

    def __init__(self) -> None:

        self.bk = ByteKeeper()

        self.frame = TerminalByteFrame(b"")  # the first open Frame
        self.frames = list()
        self.index = 0

    def take_one_byte(self, b: bytes, nano: int, peek: str) -> None:
        """Say 1 more Byte arrived, and when, and take each Frame as it closes or bounces"""

        bk = self.bk

        # Stamp the Byte with when it arrived

        assert len(b) == 1, (len(b), b)

        bk.append_one_byte(b, nano=nano)

        # Grow the Frame, or grow and take, or don't grow but do take, or shrink and take

        frame = self.frame  # early
        extras1 = self._frame_take_data_if_(b, peek=peek)  # .peek passes through

        if not extras1:
            return

        _frame_ = self.frame  # late

        assert _frame_ is not frame, (_frame_, frame)  # new Empty Frame, because the Extras bounced
        assert not _frame_, (_frame_,)

        # Add enough more Frames to place all the Bytes

        extras2 = self._frame_take_data_if_(extras1, peek=peek)  # .peek passes through
        if extras2:

            extras3 = self._frame_take_data_if_(extras2, peek=peek)  # .peek passes through
            assert not extras3, (extras3,)

            # Three calls of ._frame_take_data_if_ are always enough,
            # because post-conditions at ._frame_take_data_if_ > .take_data_if > .take_one_byte_if

    def _frame_take_data_if_(self, data: bytes, peek: str) -> bytes:
        """Grow the Frame, replace it if it closes or bounces, and return the bounced Bytes, if any"""

        frame = self.frame
        frames = self.frames

        assert not frame.closed, (frame,)

        # Grow the Open Frame, or grow it & close it, or leave it as it was and bounce

        extras = frame.take_data_if(data, peek=peek)  # .peek passes through

        # Take & replace the Frame if it closed as complete, or if it bounced while incomplete

        _frame_ = frame
        if frame.closed or extras:
            frames.append(frame)

            _frame_ = TerminalByteFrame(b"")  # empty and open
            self.frame = _frame_

        assert (not extras) or (not _frame_), (extras, _frame_)

        # Always leave an Open Frame, and sometimes an Empty Open Frame

        assert not _frame_.closed, (_frame_,)

        return extras

    def take_open_frame_if(self) -> None:
        """Take the Open Frame as cut off, unclosed, if it holds Bytes, as at Stdin Eof or at Quit"""

        frame = self.frame
        frames = self.frames

        assert not frame.closed, (frame,)

        data = frame.to_frame_bytes()
        if not data:
            return

        frames.append(frame)

        _frame_ = TerminalByteFrame(b"")  # empty and open
        self.frame = _frame_

    def pull_frame_triples(self) -> tuple[tuple[int, int, bytes], ...]:
        """Read and clear the (start, end, bytes) triples of Frames taken since last called"""

        bk = self.bk
        frame = self.frame
        frames = self.frames
        index = self.index

        ba = bk.ba
        nano_list = bk.nano_list

        # Pull the Taken Frames not yet pulled

        pulls = frames[index:]
        self.index = len(frames)

        # Measure back from the end of the Bytes, to find where the oldest of them starts

        open_length = len(frame.to_frame_bytes())
        pulls_length = sum(len(_.to_frame_bytes()) for _ in pulls)
        first_index = len(ba) - open_length - pulls_length

        # Say when each started and ended, while walking forward over them

        triples_list: list[tuple[int, int, bytes]] = list()

        start_index = first_index
        for pull in pulls:
            data = pull.to_frame_bytes()
            stop_index = start_index + len(data)

            indexed = bytes(ba[start_index:stop_index])
            assert indexed == data, (indexed, data, start_index, stop_index)

            start = nano_list[start_index]
            end = nano_list[stop_index - 1]

            triple = (start, end, data)
            triples_list.append(triple)

            start_index = stop_index

        assert start_index == (len(ba) - open_length), (start_index, len(ba), open_length)

        triples = tuple(triples_list)
        return triples

    def is_quitting_frames(self) -> bool:
        """Say if the Frames have said please quit soon"""

        bk = self.bk
        frame = self.frame
        frames = self.frames

        ba = bk.ba
        nano_list = bk.nano_list

        # Hand down the last 4 Taken Frames, each with when its last Byte arrived

        open_data = frame.to_frame_bytes()
        stop = len(ba) - len(open_data)  # back past the Open Frame

        pairs_list = list()
        for taken in reversed(frames[-4:]):
            data = taken.to_frame_bytes()
            pairs_list.append((nano_list[stop - 1], data))
            stop -= len(data)

        pairs = list(reversed(pairs_list))  # oldest first, as for Bytes

        # Quit on three same Frames taken

        if is_quitting_shape(pairs):
            if frames[-1].encodes:  # no quitting on repeated Text Frames
                return False

            return True

        # Else quit on two same Frames taken and then the same Frame still open, such as ⎋[ ⎋[ ⎋[

        if open_data:
            open_pair = (nano_list[-1], open_data)
            if is_quitting_shape(pairs[-3:] + [open_pair]):
                if frame.encodes:  # no quitting on repeated Text Frames
                    return False

                return True

        return False


def is_quitting_shape(pairs: list[tuple[int, bytes]]) -> bool:
    """Quits when given same Bytes, 3 times in a row, but >= 100ms apart, across < 3s"""

    nano = time.perf_counter_ns()

    nl = [n for (n, _) in pairs]  # when the last Byte of each arrived
    data_list = [data for (_, data) in pairs]

    last3 = data_list[-3:]
    if not last3:
        return False

    if last3 != (3 * last3[-1:]):  # three in a row
        return False

    age = nano - nl[-3]
    early_gaps = (nl[-3] - nl[-4],) if (len(nl) > 3) else ()
    late_gaps = (nl[-2] - nl[-3], nl[-1] - nl[-2])

    if age >= _3_GIGA_NANOS_IS_TOO_SLOW_:  # as a burst, not just now and then
        return False

    if min(early_gaps + late_gaps) < _100_MEGA_NANOS_IS_TOO_FAST_:  # held, or pasted
        return False

    return True


#
# Frame Bytes of Terminal Input as alone, or as catenated Printable Text, or as Esc Frame
#


_ = r"""

In the leftmost Column are the Bytes in the Frame, from before you offered one more.

The Frames ending with '+' were still open, the others were already closed.

    Frame    \a      ⇥       ⎋       ;       A       ́       €       \xff

    '' +     close   close   open    open    open    open    open    close

    'ab' +   bounce  bounce  bounce  open    open    open    open    bounce

    ⎋ +      close   close   open    close   close   close   close   bounce
    ⎋⎋ +     close   close   bounce  close   close   close   close   bounce
    ⎋O +     close   close   bounce  close   close   close   close   bounce
    ⎋[M +    open    open    open    open    open    open    close6  open
    ⎋[M␢! +  close6  close6  close6  close6  close6  close6  close6  close6

    ⎋[ +     bounce  bounce  bounce  open    close   close   close   bounce
    ⎋[1;5 +  bounce  bounce  bounce  open    close   close   close   bounce
    ⎋[␢ +    bounce  bounce  bounce  bounce  close   close   close   bounce

    ⎋] +     close   bounce  open    open    open    open    open    bounce
    ⎋]0;x +  close   bounce  open    open    open    open    open    bounce
    ⎋]0;x⎋ + bounce2 bounce2 bounce2 bounce2 bounce2 bounce2 bounce2 bounce2

    ⎋j       bounce  bounce  bounce  bounce  bounce  bounce  bounce  bounce
    ⎋Oj      bounce  bounce  bounce  bounce  bounce  bounce  bounce  bounce
    ⎋[A      bounce  bounce  bounce  bounce  bounce  bounce  bounce  bounce
    ⎋⇥       bounce  bounce  bounce  bounce  bounce  bounce  bounce  bounce

As you feed Byte after Byte into a Terminal Byte Frame, it must decide when to:

i ) Open = Take the Byte and keep the Frame open
ii ) Bounce = Reject the Byte and leave the Frame unchanged
iii ) Close = Take the Byte and close the Frame
iv ) Close6 = Take the 6 Bytes and bounce anything after (at ⎋[M legacy)
v ) Bounce2 = Reject the Byte and give back the held ⎋ with it (at ⎋] awaiting the \ of ⎋\)

Given a Peek at a Combining Mark already fetched in the same burst of Bytes, as ⌥E J sends,
a Printable Char opens rather than closes the ⎋ ⎋⎋ ⎋O ⎋[ ⎋[1;5 ⎋[␢ Rows, and the Mark then closes.

Relevant standards include:

    ECMA-35_6th_edition_december_1994.pdf
    ECMA-48_5th_edition_june_1991.pdf

However the public standards only clearly solve 7-bit Bytes.

We solve 8-bit Bytes reasonably well. We tell every Open Frame to accept the 1..4 Bytes
of any Printable Text Char, except that our Open ⎋[M Frames only take 1..3 Bytes, and
our Open ⎋] Osc Frames can bounce 1..5 Bytes because they only take Reverse-Solidus \ after Esc ⎋.

The b'\a' Bel is as special as String Terminator (ST) for ⎋] an Operating System Command (Osc).
The b'\033' ⎋ Esc is special after just one of itself.

The \a ⇥ ⎋ \xff are not printable, the ; A  ́ € are printable.
The € is a printable encoded as 3 Bytes, vs the ; A  ́ are printable encoded as 1 or 2 bytes.

The ; is a Parameter Byte of ⎋[ Control Sequence Introducer (Csi).
The ␢ is an Intermediate Byte of ⎋[ Csi, expected before A is an example Final Byte.
The  ́ is a Combining Mark Character that can merge back into the Printable before it.

The \xff is an example of Undecodable UTF-8.

"""


@dataclasses.dataclass(order=True)  # , frozen=True)
class TerminalByteFrame:
    """Frame Bytes of Terminal Input as alone, or as catenated Printable Text, or as Esc Frame"""

    encodes: bytearray  # b''  # Decodable Printable Text

    head: bytearray  # b''  # N * ESC  # N * ESC + CSI  # N * ESC + SS3  # OSC
    neck: bytearray  # b''  # Csi Params  # Osc Payload
    backtail: bytearray  # b''  # Csi Intermediates and Final  # Osc Terminator  # Esc or Ss3 Char

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

        for d in data:
            b = bytes([d])

            extras = self.take_one_byte_if(b, peek="")
            if extras:
                raise ValueError(extras, b, self)

    def __bool__(self) -> bool:

        truthy = self != TerminalByteFrame(b"")
        return truthy

    def __str__(self) -> str:
        """Speak of the Frame as its Parts, each a Repr of Bytes, plus ' +' while open"""

        encodes = self.encodes

        head = self.head
        neck = self.neck
        backtail = self.backtail

        stash = self.stash

        closed = self.closed

        # Speak of Text as a Repr of Str, with the Repr of Bytes of an unfinished Char after it

        if encodes:
            text = encodes.decode()
            join = str_repr(text)  # "'abc'"
            if stash:
                join += " " + bytes_repr(bytes(stash))  # "'abc' b'\300'"

        # Speak of no Head as the Repr of Bytes stashed, else as b''

        elif not head:
            join = bytes_repr(bytes(stash))  # "b'\300'"  # "b''"

        # Speak of the Head, then the Neck, then the Back & Tail, if any

        else:
            parts = [bytes(head)]

            if neck:
                parts.append(bytes(neck))  # Csi Params  # Osc Payload
            if backtail or stash:
                parts.append(bytes(backtail + stash))  # Csi Back & Tail  # Osc Terminator

            join = " ".join(bytes_repr(_) for _ in parts)

        # Mark an Open Frame with ' +', since more Bytes may yet arrive

        if not closed:
            join += " +"

        assert join.isprintable(), (join,)
        return join

        # "b'\033[' b'6' b' q'"  # "b'\033' b'A'"  # "b'\033[M' b'\302\200\377'"  # "b'\033[' +"

    def clear_frame(self) -> None:  # todo: add 1st call
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

    def tilt_to_close_frame(self) -> None:  # todo: add 1st call
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
    # Pick apart an Esc Csi Escape into its Marks and Ints
    #

    def to_csi_marks_ints_if(self) -> tuple[bytes, tuple[int, ...]]:  # todo: add 1st call
        """Pick out the Nonnegative Int Literals of a Csi Escape"""

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
    # Take 1 Byte in and return 0 Bytes, else return 1..5 Bytes that don't fit
    #

    def take_data_if(self, data: bytes, peek: str) -> bytes:
        """Try to take X Bytes in and return 0 <= Y <= X Bytes that don't fit"""

        for i in range(len(data)):
            b = data[i:][:1]
            beyond = data[i:][1:]

            _peek_ = peek if (not beyond) else ""  # blocks the .peek except just after last Byte

            extras = self.take_one_byte_if(b, peek=_peek_)
            if extras:
                extras_plus = extras + beyond
                return extras_plus

        return b""

    def take_one_byte_if(self, b: bytes, peek: str) -> bytes:
        """Take 1 Byte in and return 0 Bytes, else return 1..5 Bytes that don't fit"""

        assert len(b) == 1, (b,)

        backtail = self.backtail
        stash = self.stash

        # Do the work

        extras = self._take_one_byte_if_(b, peek=peek)  # .peek passes through

        # Sharply limit its results

        assert ESC == "\033"
        assert OSC == "\033]"

        if extras:
            assert extras[-1:] == b, (extras, b)  # every Bounce bounces the new Byte last

            start = extras[:-1]
            if start:
                end = extras[1:]

                # Pass back 1 Frame of Bytes, decodable or not

                if not start.startswith(b"\033"):
                    assert 1 <= len(extras) <= 4, (len(extras), extras, b)
                    assert TerminalByteFrame.bytes_to_later_decode_if(start), (start, extras, b)

                # Else pass back 1 Frame of ⎋ and then 1 Frame of Un/Decodable not ending ⎋\

                else:
                    assert 1 <= len(extras) <= 5, (len(extras), extras, b)
                    tail = TerminalByteFrame.bytes_decode_if(end)
                    assert (not tail) or ((len(tail) == 1) and (tail != "\\")), (end, extras, b)

                    data = self.to_frame_bytes()
                    o = (data, backtail, stash, extras, b)
                    assert data.startswith(b"\033]") and (not backtail) and (not stash), o

        # Succeed

        return extras

        # never more than 2 Frames of Extras

    def _take_one_byte_if_(self, b: bytes, peek: str) -> bytes:
        """Take 1 Byte in and return 0 Bytes, else return 1..5 Bytes that don't fit, unchecked"""

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
            return b

        # Hold 1..3 Bytes to decode later, except after ⎋[⇧M where 0x80..0xFF are raw Coords

        data = bytes(stash + b)
        text = TerminalByteFrame.bytes_decode_if(data)

        if not text:
            if head != b"\033[M":
                if TerminalByteFrame.bytes_to_later_decode_if(data):
                    stash.extend(b)
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
        undented_head = bytes(head[escapes:])

        if undented_head in (b"\033", b"\033O"):  # .peek passes through
            extras = self._take_after_ss3_or_esc_if_(data, text=text, peek=peek)
            return extras

        elif undented_head == b"\033[M":
            extras = self._take_after_csi_m_if_(data)
            return extras

        elif undented_head == b"\033[":  # .peek passes through
            extras = self._take_after_csi_if_(data, text=text, peek=peek)
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

        # Bounce Unprintable or Undecodable Bytes off a Text Frame, leaving it open

        if encodes:
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
        b"\033]",  # ⎋] OSC
    )

    def _take_after_ss3_or_esc_if_(self, data: bytes, text: str, peek: str) -> bytes:
        """Take 1..4 more Bytes in, after ⎋ Esc or ⎋O Ss3, else return what doesn't fit"""

        head = self.head
        backtail = self.backtail

        # Take one of the ⎋ Esc Head's, without closing the Frame

        head_plus = head + data
        if head_plus in TerminalByteFrame.Headbook:
            assert head != b"\033O", (head,)

            lstrip = head_plus.lstrip(b"\033")
            assert len(lstrip) <= 1, (head_plus,)

            head.extend(data)
            return b""

            # doesn't take ⇧M after \⎋[ here

        # Bounce an ⎋ Esc that grows no Headbook Head, leaving the Frame open

        if data == b"\033":
            return data

        # Bounce Undecodable Bytes off the Frame, leaving it open, to start a Frame of their own

        if not text:
            return data

        # Take 1 Char, as the Emacs Meta Char after ⎋ Esc, or as the Final after ⎋O Ss3

        backtail.extend(data)

        if text.isprintable() and peek:  # stays open to complete Printable Text later
            return b""

        self.close_frame()
        return b""

    def _take_after_csi_m_if_(self, data: bytes) -> bytes:
        """Take 1 more Byte in, after ⎋[⇧M, and never bounce it"""

        head = self.head
        backtail = self.backtail

        # Take three raw B X Y Bytes after the Head, each 32 + Coord, so 0x20..0xFF, never decoded

        assert len(data) == 1, (data, head, backtail)  # stashes nothing after ⎋[⇧M
        assert len(head + backtail) < 6, (head, backtail, data)  # closes at 6, before now

        backtail.extend(data)
        if len(head + backtail) == 6:
            self.close_frame()

        return b""

        # ⎋[?1005h Utf-8 Mouse Coords never enabled here, so never decoded here

    def _take_after_csi_if_(self, data: bytes, text: str, peek: str) -> bytes:
        """Take 1..4 more Bytes in, after ⎋[ Csi, else return what doesn't fit"""

        head = self.head
        neck = self.neck
        backtail = self.backtail

        assert _CLICK3_ == "\033[M"

        # Take the 3-Byte ⎋[⇧M Esc Head, without closing the Frame

        if (not neck) and (not backtail):
            head_plus = head + data
            if head_plus in TerminalByteFrame.Headbook:
                assert head_plus == b"\033[M", (head_plus,)
                head.extend(data)
                return b""

        # Grow the ⎋[ Csi Frame with 1 Decoded Printable Char

        if text and text.isprintable():
            code = ord(text)
            assert code >= 0x20, (code, text, data)

            # Grow the Neck until the Backtail starts

            if 0x30 <= code < 0x40:  # 16 Parameter Codes  # 0123456789:;<=>?

                if not backtail:
                    neck.extend(data)
                    return b""

                # Bounce more Params, if Backtail has started, leaving the Frame open

                return data

            # Grow the Backtail

            if 0x20 <= code < 0x30:  # 16 Intermediate Codes  # ␢!"#$%&\'()*+,-./
                backtail.extend(data)
                return b""

            # Close after a Csi Final Code, or after Printable Unicode

            assert code >= 0x40, (code, text, data)  # 63 Final Codes  # @A Z[\\]^_`a z{|}~

            backtail.extend(data)

            if peek:  # stays open to complete Printable Text later
                assert text.isprintable(), (text,)  # because already tested far above
                return b""

            self.close_frame()
            return b""

        # Bounce Unprintable or Undecodable Bytes off the ⎋[ Csi Frame, leaving it open

        return data

    def _take_after_osc_if_(self, data: bytes, text: str) -> bytes:
        """Take 1..4 more Bytes in, after ⎋] Osc, else return the 1..5 that don't fit"""

        neck = self.neck
        backtail = self.backtail

        assert BEL == "\007"
        assert ST == "\033\134"

        # Close the ⎋] Osc Frame with ⎋\ ST, or bounce a held ⎋, or hold ⎋ till ⎋\ ST or Bounce

        if backtail == b"\033":

            if text == "\134":
                backtail.extend(data)
                self.close_frame()
                return b""

            backtail.clear()
            return b"\033" + data

        assert not backtail, (backtail,)

        if text == "\033":
            backtail.extend(data)
            return b""

        # Close the ⎋] Osc Frame with BEL

        if text == "\007":
            backtail.extend(data)
            self.close_frame()
            return b""

        # Grow the ⎋] Osc Frame with 1 Decoded Printable Char

        if text and text.isprintable():
            neck.extend(data)
            return b""

        # Bounce Unprintable or Undecodable Bytes off the ⎋] Osc Frame, leaving it open

        return data

    #
    # Work with Decodable and Undecodable Bytes: bytes_decode_if|bytes_to_later_decode_if
    #

    @staticmethod
    def bytes_decode_if(data: bytes) -> str:
        """Say if decodable"""

        try:
            text = data.decode()
            return text  # maybe empty
        except UnicodeDecodeError:
            pass

        return ""

    Endswiths = (b"\xbf", b"\x80\x80", b"\xbf\xbf", b"\x80\x80\x80", b"\xbf\xbf\xbf")

    @staticmethod
    def bytes_to_later_decode_if(data: bytes) -> str:
        """Say if some Bytes start 1 or more UTF-8 Encodings of Chars"""

        endswiths = (b"\xbf", b"\x80\x80", b"\xbf\xbf", b"\x80\x80\x80", b"\xbf\xbf\xbf")
        assert endswiths == TerminalByteFrame.Endswiths

        for endswith in endswiths:
            data_plus = data + endswith

            try:
                text = data_plus.decode()
            except UnicodeDecodeError:
                continue

            assert len(text) >= 1, (text,)
            return text  # returns first found

        return ""

        # todo: compare Endswiths vs Python 3 encodings.utf_8.IncrementalDecoder

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

    # known: invent UTF-8'ish Encoding beyond 1..4 Bytes for Unicode Codes > 0x10_FFFF ?


def _try_terminal_byte_frame_() -> None:
    """Try TerminalByteFrame things"""

    assert "\u20ac" == "€"  # a popular Printable Character with a 3 Byte Encoding
    assert "\U0001f602" == "😂"  # a popular Printable Character with a 4 Byte Encoding

    try:
        b"\xf4\x8f\xbf\xff".decode()
        assert False
    except UnicodeDecodeError:
        pass

    _try_terminal_byte_frame_1_()

    _try_terminal_byte_frame_2_()

    # todo: merge our two 'def _try_terminal_byte_frame_...' well


def _try_terminal_byte_frame_1_() -> None:
    """Run slow and quick Self-Test's of TerminalByteFrame"""

    _try_open_(b"")  # empty
    _try_headbook_()
    _try_ends_later_()  # ~200ms
    _try_one_more_kbyte_()
    _try_some_control_()
    _try_peeks_()


def _try_headbook_() -> None:
    """Accept the Bytes of any Head of the Headbook, without closing the Frame"""

    headbook = (b"\033", b"\033O", b"\033[", b"\033]")  # ⎋ ⎋⇧O ⎋[ ⎋]
    # assert headbook == TerminalByteFrame.Headbook  # differs: Headbook here adds ⎋⎋ ⎋⎋O ⎋⎋[ ⎋[M

    assert OSC == "\033]", (OSC,)

    for head in headbook:
        _try_open_(head)

        if head == b"\033":
            _try_open_(head + b"\033")
            _try_extra_(head + b"\033", extra=b"\033")
            _try_close_(head, b"\t")
            _try_close_(head, "\u20ac".encode())
            _try_extra_(head, extra=b"\xf4\x8f\xbf\xff")
            _try_extra_(head + b"\033", extra=b"\xf4\x8f\xbf\xff")
        elif head == b"\033O":
            _try_extra_(head, extra=b"\033")
            _try_close_(head, b"\t")
            _try_close_(head, "\u20ac".encode())
            _try_extra_(head, extra=b"\xf4\x8f\xbf\xff")
        elif head == b"\033[":
            _try_close_(head, "\u20ac".encode())  # ruled: Chars close ⎋[
            _try_extra_(head, extra=b"\033")
            _try_extra_(head, extra=b"\t")
            _try_extra_(head, extra=b"\xf4\x8f\xbf\xff")
        elif head == b"\033]":
            _try_open_(head, b"\033")
            _try_open_(head, "\u20ac".encode())
            _try_extra_(head, extra=head)
            _try_extra_(head, extra=b"\t")
            _try_extra_(head, extra=b"\xf4\x8f\xbf\xff")
        else:
            assert False, (head,)


StartBytes = tuple(bytes([_]) for _ in range(0xC2, 0xF4 + 1))  # what UTF-8 completes


def _try_ends_later_() -> None:
    """Require each StartsWith accepted by .bytes_to_later_decode_if via the Endswiths"""

    start_set = set()
    for cp in range(0x110000):  # from 0 up to before first Chr ValueError
        if 0xD800 <= cp <= 0xDFFF:  # skips Surrogates
            continue

        encode = chr(cp).encode()  # only Surrogate Chr would raise UnicodeEncodeError

        for i in range(1, len(encode)):
            start = encode[:i]
            start_set.add(start)

    start_byte_set = set()
    for start in start_set:
        assert TerminalByteFrame.bytes_to_later_decode_if(start), (start,)
        start_byte_set.add(start[:1])

    start_bytes = tuple(sorted(start_byte_set))
    assert start_bytes == StartBytes, (start_bytes, StartBytes)


def _try_one_more_kbyte_() -> None:
    """Try some Frames open to, or closed against, taking more Bytes"""

    # Decline Bytes after Closed

    _try_open_(b"")
    _try_extra_(b"\t", extra=b"\x41")

    # Take Bytes into Stash, while could be decodable

    _try_open_("Superb", b"\xc2")
    _try_open_(b"\xed\x80")  # Head of >= 3 Byte UTF-8 Encoding
    _try_open_(b"\xf4\x80\x80")  # Head of >= 4 Byte UTF-8 Encoding

    # Take 6 Bytes into a Mouse Report, never decoded, then bounce the rest  # ruled: close6

    _try_open_(b"\033[M", b"\xff\xff")  # 5 Undecodable Bytes
    _try_close_(b"\033[M", b".\xc2\xa3")  # 6 Bytes, 2 Chars
    _try_close_(b"\033[M", b"\xf4\x8f\xbf")  # 6 Bytes, unfinished Char

    _try_close_(b"\033[M", b"\xc2\x80\xff")  # 6 Undecodable Bytes
    _try_close_(b"\033[M", b"\xff\xff\xc2")  # 6 Bytes, \xc2 unfinished

    _try_extra_(b"\033[M" b"\xf4\x8f\xbf", extra=b"\xbf")  # bounces past 6
    _try_extra_(b"\033[M" b"\xff\xff\xc2", extra=b"\x80")  # bounces past 6

    # Take Bytes into Text

    _try_open_("\u20ac", "\ufffd".encode()[:-1])

    # Decline 1..4 Unprintable Bytes after Text

    _try_extra_(b"Text", extra=b"\x7f")
    _try_extra_(b"Plain", extra="\uffff".encode())


def _try_some_control_() -> None:
    """Try closing on Unprintable or Undecodable Bytes alone, and on each kind of Head"""

    # Take & close 1 Unprintable Char or 1..4 Undecodable Bytes as an Alt Head

    _try_close_(b"\n")  # 7-bit Control Byte as Head alone
    _try_close_(b"\xc0")  # 8-bit Control Byte as Head alone
    _try_close_(b"\xc2\xad")  # 2 Byte UTF-8 of U+00AD Soft-Hyphen Control as Head alone
    _try_close_(b"\xf5")  # 1 Byte Undecodable as Head alone
    _try_close_(b"\xff")  # 1 Byte Undecodable as Head alone
    _try_close_(b"\xf4\x8f\xbf\xc0")  # 4 Bytes Undecodable as Head alone

    # Take & close 1 Printable Char escaped by a Head simpler than Csi, Esc Csi, and Osc

    _try_close_(b"\033", b"A")  # Head and then Text Tail of a Two-Byte Esc Frame
    _try_close_(b"\033O", b"P")  # Head and then Text Tail of a Three-Byte Ss3 Frame

    # Take & close 1 Unprintable Char escaped by a Simpler Head

    _try_close_(b"\033", b"\t")  # Head and then Control Tail of a Two-Byte Esc Frame

    # Take or don't take 1 Decodable Char escaped by Osc or Csi or Esc Csi

    _try_open_(b"\033[", b"6", b" ")  # Csi Head with Neck and Back but no Tail

    _try_close_(b"\033[", b"1", b"M")  # Csi Tail ⇧M that isn't ⎋[⇧M Head
    _try_close_(b"\033\033[", b"3;5", b"~")  # Esc Csi Head with Neck and Tail, no Back
    _try_close_(b"\033[", b"3;5", b"H")  # Csi Head with Neck and Tail, no Back
    _try_close_(b"\033[", b"6", b" q")  # Csi Head with Neck and Back & Tail

    _try_close_(b"\033]", b"\x07")  # Osc with 007 Bel as Tail
    _try_close_(b"\033]", b"\x1b" b"\\")  # Osc with ⎋\ String Terminator (ST) as Tail

    # Decline 1..4 Undecodable Bytes, when escaped by Csi or Esc Csi or Osc
    # Decline 1 Bytes of Unprintable or Multi-Byte Char

    _try_close_(b"\x1b[", "\u20ac".encode())  # Csi ends with Multi-Byte Char
    _try_open_(b"\x1b]", "\u20ac".encode())  # Osc ends with Multi-Byte Char

    _try_extra_(b"\x1b[", extra=b"\t")  # Csi bounces Unprintable
    _try_extra_(b"\x1b[", extra=b"\xf4\x8f\xff")  # Csi bounces Undecodable

    _try_extra_(b"\x1b]", extra=b"\t")  # Osc bounces Unprintable
    _try_extra_(b"\x1b]", extra="\033\u20ac".encode())  # Osc bounces 3 Byte Encoding
    _try_extra_(b"\x1b]", extra="\033\U0001f602".encode())  # Osc bounces 4 Byte Encoding

    # Try some commonly recurring choices

    assert _END_PASTE_ == "\033[" "201~"

    _try_close_(b"\x1b[", b"201", b"~")


def _try_peeks_() -> None:
    """Stay open for the Combining Mark already fetched, where a Printable Char would close"""

    peek = "\u0301"  # Combining Acute Accent, as ⌥E J sends it after the J
    encode = peek.encode()

    # Stay open after the Printable Char that would have closed, and then close on the Mark

    for data in (b"\033j", b"\033\033j", b"\033Oj", b"\033[A", b"\033[1;5A", b"\033[ q"):
        f = TerminalByteFrame(b"")
        extras = f.take_data_if(data, peek=peek)
        assert (not extras) and (not f.closed), (extras, f, data)

        extras = f.take_data_if(encode, peek="")
        assert (not extras) and f.closed, (extras, f, data)
        assert f.to_frame_bytes() == (data + encode), (f, data)

    # Close anyway, after an Unprintable Char, or after the 6 raw Bytes of ⎋[M

    for data in (b"\t", b"\033\t", b"\033[M !\xff"):
        f = TerminalByteFrame(b"")
        extras = f.take_data_if(data, peek=peek)
        assert (not extras) and f.closed, (extras, f, data)

    # Stay open anyway, as Text, or as ⎋] Osc, and take the Mark

    for data in (b"j", b"\033]0;x"):
        f = TerminalByteFrame(b"")
        extras = f.take_data_if(data, peek=peek)
        assert (not extras) and (not f.closed), (extras, f, data)

        extras = f.take_data_if(encode, peek="")
        assert (not extras) and (not f.closed), (extras, f, data)
        assert f.to_frame_bytes() == (data + encode), (f, data)


def _try_extra_(data: bytes, extra: bytes) -> None:
    """Require the Frame to bounce these Bytes, and to stay as it was"""

    f = TerminalByteFrame(data)
    closed = f.closed

    returned_extra = f.take_data_if(extra, peek="")
    assert returned_extra == extra, (returned_extra, extra, str(f))

    assert f.closed == closed, (f.closed, closed, extra, f)
    assert f == TerminalByteFrame(data), (f, TerminalByteFrame(data))


def _try_open_(*args: str | bytes) -> None:
    """Frame these Bytes, and require the Frame still open"""

    f = _try_bytes_(*args)
    assert not f.closed, (f,)


def _try_close_(*args: bytes) -> None:
    """Frame these Bytes, and require the Frame closed"""

    f = _try_bytes_(*args)
    assert f.closed, (f,)


def _try_bytes_(*args: str | bytes) -> TerminalByteFrame:
    """Frame these Bytes, and require the Str of the Frame to speak each Arg as given"""

    data_list = list()
    for arg in args:
        if isinstance(arg, str):
            data_list.append(arg.encode())
        else:
            data_list.append(arg)

    join = " ".join((str_repr(_) if isinstance(_, str) else bytes_repr(_)) for _ in args)

    fdata = b""
    for data in data_list:
        fdata += data

    f = TerminalByteFrame(fdata)
    fbytes = f.to_frame_bytes()
    fstr = str(f)

    join_plus = join if f.closed else (join + " +")  # ' +' marks an Open Frame

    assert fbytes == fdata, (fbytes, fdata)
    assert fstr == join_plus, (fstr, join_plus)

    return f


def _try_terminal_byte_frame_2_() -> None:
    """Try some Frames: ↑ ⎋↑ ⎋[M ⎋[↗ and the ⎋\\ String Terminator"""

    assert DL_Y == "\033[" "{}M"
    assert _CLICK3_ == "\033[M"
    assert _NorthArrow_ == "\033[A"
    assert ST == "\033\134"
    assert _NortheastArrow_ == "\033[↗"

    # Do nothing with grace & elegance

    TerminalByteFrame(b"")

    # Speak well of ↑ and ⎋↑

    f = TerminalByteFrame(b"\033[A")
    assert f.to_frame_bytes() == b"\033[A", (f,)
    assert f.closed, (f,)

    f = TerminalByteFrame(b"\033\033[A")
    assert f.to_frame_bytes() == b"\033\033[A", (f,)
    assert f.closed, (f,)

    # Dance well with the _CLICK3_ clash into DL_Y without Pn

    f = TerminalByteFrame(b"\033[M")
    assert f.to_frame_bytes() == b"\033[M", (f,)
    assert not f.closed, (f,)  # because could be ⎋[⇧M{b}{x}{y}

    f = TerminalByteFrame(b"\033[Mabc")
    assert f.to_frame_bytes() == b"\033[Mabc", (f,)
    assert f.closed, (f,)

    f = TerminalByteFrame(b"\033[Mab\xff")
    assert f.to_frame_bytes() == b"\033[Mab\xff", (f,)
    assert f.closed, (f,)

    # Accept ↖↗↘↙ Intercardinal Arrows, not just ←↑→↓ Cardinal Arrows

    f = TerminalByteFrame("\033[↗".encode())  # not yet standard
    assert f.to_frame_bytes() == "\033[↗".encode(), (f,)
    assert f.closed, (f,)

    # Accept the ⎋\ String Terminator (ST) to close an ⎋] Osc Frame

    f = TerminalByteFrame(b"\033]11;?\033\\")
    assert f.to_frame_bytes() == b"\033]11;?\033\\", (f,)
    assert f.closed, (f,)


#
# Wrap one Terminal
#


@dataclasses.dataclass(order=True)  # , frozen=True)
class TerminalBoss:
    """Wrap one Terminal"""

    stdio: io.TextIOWrapper
    isatty: bool
    fileno: int  # often 2 == sys.__stderr__.fileno()
    tcgetattr: list[int | list[bytes | int]]  # replaced by .__enter__

    def __init__(self) -> None:

        assert sys.__stdin__, (sys.__stdin__,)
        stdio = sys.__stdin__  # todo: /dev/stderr, /dev/tty
        isatty = stdio.isatty()
        fileno = stdio.fileno()

        self.stdio = stdio
        self.isatty = isatty
        self.fileno = fileno
        self.tcgetattr = list()

    def __enter__(self) -> TerminalBoss:
        r"""Pause line-buffering Input, pause taking \n Output as \r\n, etc"""

        isatty = self.isatty
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        if tcgetattr:  # enters at most once, to make truthy
            return self

        # Flush writes to the Terminal

        sys.stdout.flush()
        sys.stderr.flush()

        # Back up Input Mode before, drain Input, & choose Input Mode after

        widened_list_int: list[int | list[bytes | int]] = [20261010]  # arbitrary 20261010

        truthy_attributes = termios.tcgetattr(fileno) if isatty else widened_list_int
        assert truthy_attributes, (truthy_attributes,)
        self.tcgetattr = truthy_attributes  # replaces falsey with truthy

        if isatty:
            tty.setraw(fileno, when=termios.TCSADRAIN)

        # Succeed

        return self

        # also pauses Return Key meaning ⌃J b'\n', switches to ⌃M b'\r'

        # todo: swap tty.setcbreak in for tty.setraw to change what ⌃C means
        # todo: try termios.TCSAFLUSH to discard Input while entering

    def __exit__(self, *exc_info: object) -> None:
        r"""Resume line-buffering Input, resume taking \n Output as \r\n, etc"""

        isatty = self.isatty
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        if not tcgetattr:  # exits at most once, to make falsey
            return

        # Flush writes to the Terminal

        sys.stdout.flush()
        sys.stderr.flush()

        # Drain Input, restore Input Mode, & clear Input Mode backup

        fd = fileno
        when = termios.TCSADRAIN
        attributes = tcgetattr  # truthy here too
        if isatty:
            termios.tcsetattr(fd, when, attributes)

        self.tcgetattr = list()  # replaces truthy with falsey

        # also resumes Return Key meaning ⌃J b'\n', switches from ⌃M b'\r'

        # todo: try termios.TCSAFLUSH to discard Input while exiting

    def stdio_select_select(self, timeout: float | None) -> bool:
        """Block till next Input Byte, else till Timeout, else till forever"""

        fileno = self.fileno

        assert self.tcgetattr, (self.tcgetattr,)

        r, w, x = select.select([fileno], [], [], timeout)

        hit = fileno in r

        return hit

        # a la msvcrt.kbhit

    # def poll_till_bytes_available(self) -> None:
    #     """Block till Bytes Available"""
    #
    #     while not self.stdio_select_select(timeout=0e0):
    #         time.sleep(1e-9)  # slightly limits loop rate

    def read_some_bytes_if(self) -> bytes:
        """Read as many Bytes as arrived all at once, else return b''"""

        ba = bytearray()

        while True:

            # Read one Byte, else quit at End-of-Input

            b = self.read_one_byte_if()
            if not b:
                break

            ba.extend(b)

            # Quit when no more Bytes have arrived yet

            if not self.stdio_select_select(timeout=0e0):
                break

        data = bytes(ba)
        return data  # b'j\xcc\x81' from ⌥E J, or a whole ⌘V Paste, or one Byte, or b''

    def read_one_byte_if(self) -> bytes:
        """Read one byte and return it, else return b''"""

        try:
            b = self.read_one_byte()
        except AssertionError:
            raise
        except OSError:
            return b""

        assert len(b) == 1, (b,)
        return b

    def read_one_byte(self) -> bytes:
        """Read one byte and return it, else raise Exception"""

        fileno = self.fileno

        fd = fileno
        length = 1
        b = os.read(fd, length)

        if not b:  # b == b'' only from input stream closed by macOS
            raise OSError(errno.EIO, os.strerror(errno.EIO))  # as Linux does for b''

        assert len(b) == 1, (b,)
        return b


#
# Collect Bytes and track when they arrived
#


@dataclasses.dataclass(order=True)  # , frozen=True)
class ByteKeeper:
    """Collect Bytes and track when they arrived"""

    ba: bytearray  # the Bytes
    nano_list: list[int]  # when the Bytes arrived

    def __init__(self) -> None:

        self.ba = bytearray()
        self.nano_list = list()

    def append_one_byte(self, b: bytes, nano: int) -> None:
        """Say 1 more Byte arrived, and when"""

        assert len(b) == 1, (len(b), b)

        ba = self.ba
        nano_list = self.nano_list

        ba.extend(b)
        nano_list.append(nano)

    def is_quitting_bytes(self) -> bool:
        """Say if the Bytes have said please quit soon"""

        ba = self.ba
        nano_list = self.nano_list

        firsts = range(max(0, len(ba) - 4), len(ba))
        pairs = [(nano_list[i], bytes(ba[i : i + 1])) for i in firsts]

        if is_quitting_shape(pairs):
            if ord(" ") <= ba[-1] <= ord("~"):  # US Ascii Printable, and not \t \n \r etc
                return False

            return True

        return False


#
# Name the more basic Terminal Encodings
#


BEL = "\007"  # 00/07 Bell

ESC = "\033"  # 01/11 Escape ⎋

SS3 = "\033O"  # 01/11 04/15 Single Shift Three  # ⎋O
CSI = "\033["  # 01/11 05/11 Control Sequence Introducer  # ⎋[
OSC = "\033]"  # 01/11 05/13 Operating System Command  # ⎋]

ST = "\033\134"  # 01/11 05/12 String Terminator  # ⎋\


X1 = 1  # min X of Terminal Cursor
Y1 = 1  # min Y of Terminal Cursor


PS0 = 0  # default Csi Ps = 0 for some

PN1 = 1  # default Csi Pn = 1 for others
_MAX_PN_32100_ = 32100  # max Csi Pn = 32100 exceeds the .x_wide .y_high of most Terminal Screens


DECIC_X = "\033[" "{}" "'}}"  # Csi 07/13 [DEC] Insert Column [Pn]
DECDC_X = "\033[" "{}" "'~"  # Csi 07/14 [DEC] Delete Column [Pn]

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

_START_PASTE_ = "\033[" "200~"  # ⎋[200⇧~ Start of Bracketed Paste
_END_PASTE_ = "\033[" "201~"  # ⎋[201⇧~ End of Bracketed Paste

VPA_Y = "\033[" "{}" "d"  # Csi 06/04 Vertical Position Absolute [Row]
SM_PS = "\033[" "{}" "h"  # CSI 06/08 4 Set Mode
RM_PS = "\033[" "{}" "l"  # CSI 06/12 4 Reset Mode
SGR_PS = "\033[" "{}" "m"  # CSI 06/13 Select Graphic Rendition [Text Style]
DSR_PS = "\033[" "{}n"  # Csi 06/14 [Request] Device Status Report [Ps]
DECSCUSR_PS = "\033[" "{}" " q"  # CSI 06/15 [DEC] Set Cursor Style [Ps]  # Two Byte Backtail

DSR0 = "\033[" "0n"  # DSR_PS Ps 0
DSR5 = "\033[" "5n"  # DSR_PS Ps 5 for DSR0
DSR6 = "\033[" "6n"  # DSR_PS Ps 6 for CPR_Y_X

CPR_Y_X = "\033[" "{};{}R"  # ⎋[y;x⇧R


ClassicArrows = ("\033[A", "\033[B", "\033[C", "\033[D")

_NorthArrow_ = "\033[A"  # ←↑→↓ reordered as ↑↓→←
_SouthArrow_ = "\033[B"
_EastArrow_ = "\033[C"
_WestArrow_ = "\033[D"

_NorthwestArrow_ = "\033[↖"  # ⎋[ ↖↗↘↙  # not yet standard
_NortheastArrow_ = "\033[↗"
_SoutheastArrow_ = "\033[↘"
_SouthwestArrow_ = "\033[↙"


_ = _MAX_PN_32100_
_ = _START_PASTE_
_ = _SouthArrow_, _EastArrow_, _WestArrow_
_ = _NorthwestArrow_, _SoutheastArrow_, _SouthwestArrow_


AppleLogo = "\uf8ff"  # Apple Logo occupies U+F8FF = end of U+E000 .. U+F8FF Private Use Area (PUA)
_ = AppleLogo
# known: every mention of  in Source makes Code Patches difficult to send across platforms


#
# Amp up Import BuiltIns
#


def bytes_repr(data: bytes) -> str:
    """Repr the Bytes, but with Octal not Upper/Lower Hex as the escape for Unprintables"""

    _repr_ = repr(data)
    sub = _repr_hex_to_octal_(_repr_)

    return sub

    # b'\342\202\254' for the "€".encode() that PyPi Black spells as b"\xe2\x82\xac"


def str_repr(s: str) -> str:
    """Repr the Str, but with Octal not Upper/Lower Hex as the escape for Unprintables"""

    _repr_ = repr(s)
    sub = _repr_hex_to_octal_(_repr_)

    return sub

    # '\033[A' for the ↑ that PyPi Black spells as "\x1b[A"
    # '\ufeff' unchanged, no Octal form


def _repr_hex_to_octal_(_repr_: str) -> str:
    """Rewrite each \\x Escape of a Repr as a 3-Digit Octal Escape, and leave the rest alone"""

    def _repl_(m: re.Match[str]) -> str:

        escape = m.group(0)
        if escape.startswith("\\x"):
            nybbles = escape.removeprefix("\\x")

            d = int(nybbles, 0x10)
            octal_escape = f"\\{d:03o}"  # 3 Digits always, else r'\7' + '1' would read as r'\71'

            return octal_escape

            # r'\xe2' -> r'\342'  # r'\x07' -> r'\007'

        return escape

        # r'\n' r'\\' r"\'" r'\u2028' r'\U0001f600' unchanged

    sub = re.sub(r"\\(x..|u....|U........|.)", repl=_repl_, string=_repr_)

    return sub


#
# Amp up Import Decimal
#


def decimal_int_chop_to_eng_metric(n: int, one: str) -> str:
    """Convert 9876 to '9.87µs' when one == '1ns', and so on"""

    # Pick apart exactly how to style an 'n' of 1

    nqu = tuple(one)
    numeral, quantum, unit = (nqu[0], "", nqu[-1]) if (len(nqu) == 2) else nqu
    assert numeral == "1", (numeral, quantum, unit, nqu, one)

    si_quanta = tuple("qryzafpnµm") + ("",) + tuple("kMGTPEZYRQ")  # the SI Prefixes since Nov/2022
    quantum_index = si_quanta.index(quantum)  # raises ValueError vs. SI Prefix not found
    quanta = si_quanta[quantum_index:]

    # Clip the 'n' value

    clip = decimal_int_chop_to_eng(n)  # raises ValueError when a Float breaks our ': int' contract

    digits, e, ms = clip.partition("e")
    assert bool(e) == bool(ms), (e, ms, digits, clip, n)

    # Restyle the clipped 'n' value

    i = 0
    if e:
        exp = int(ms)
        assert (exp % 3) == 0, (exp, digits, e, ms, clip, n)
        i = exp // 3
        assert i >= 1, (i, exp, digits, e, ms, clip, n)

    q = quanta[i]  # (q) may be Empty Str
    rep = digits + q + unit  # (q + unit) may be Empty Str

    # Succeed

    return rep  # '0Ω'  # '12ns'  # '9.87µH'  # '654ms'


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
# Run from the Shell Command Line, if not imported
#

if __name__ == "__main__":
    main()


# 3456789_123456789_123456789_123456789 123456789_123456789_123456789_123456789 123456789_123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/pylitglass/litpyglass.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
