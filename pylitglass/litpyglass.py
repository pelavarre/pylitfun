#!/usr/bin/env python3

r"""
usage: litpyglass.py [--egg=EGG ...]

loop back to write Screen after reading from Touch/ Mouse/ Key

options:
  --egg EGG  a hint of how to behave, such as 'frames' or 'nanos'
  --typeahead BYTES  read these Bytes as typed ahead, each after 150ms of Terminal silence

quirks:
  quits when given an unprintable, 3 times in a row, but 100ms or more apart, across less than 3s
  --egg=skater never quits on an arrow key, since it moves the cursor instead

examples:
  python3 pylitglass/litpyglass.py  # show these examples
  chmod +x pylitglass/litpyglass.py
  pylitglass/litpyglass.py --  # pass the self-tests and exit zero, else exit nonzero
  pylitglass/litpyglass.py --egg=bytes  # print your input bytes, on screen
  pylitglass/litpyglass.py --egg=nanos  # print your input bytes and when they arrived
  pylitglass/litpyglass.py --egg=frames  # print your inputs split into frames, named when known
  pylitglass/litpyglass.py --egg=strikes  # print your input frames as strikes else text
  pylitglass/litpyglass.py --egg=skater  # leave a reverse pair where the arrow keys take the cursor
  pylitglass/litpyglass.py --typeahead="$(printf '\r\r\r')"  # quit by itself
"""

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import collections
import dataclasses
import decimal
import errno
import functools
import io
import json
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


_SHIFT_CAPS_ = ("⎋", "⌃", "⌥", "⇧", "⌘", "Fn")  # the Shift Marks of joined Key Caps, but in order


_1_COLUMN_ = 1  # smallest .column_x
_2_COLUMNS_ = 2  # our Square Pixels print as two Spaces side by side
_20_COLUMNS_ = 20  # macOS Terminal `stty size` always says width of 20 or more

_3_GIGA_NANOS_ = 3 * 10**9  # too slow to take 3 same inputs in a row as a quit request
_10_MEGA_NANOS_ = 10 * 10**6  # a Dead Key or a Mouse Report sends its Bytes closer, Keys come slower
_50_MEGA_NANOS_ = 50 * 10**6  # two Arrow Keys struck together come closer, a held Key repeats slower
_100_MEGA_NANOS_ = 100 * 10**6  # too fast to take 3 in a row as a quit request
_150_MEGA_NANOS_ = 150 * 10**6  # keys typed ahead can come about as fast as a typist's

_1_ROW_ = 1  # smallest .row_y  # our Square Pixels span 1 Row
_5_ROWS_ = 5  # macOS Terminal `stty size` always says height of 5 or more


CR_EL_PS0 = "\r\n" "⎋[K "  # scrolls up the present Screen Row, starts writing the next
CR_EL_PS0 = "\r" "\033[K"  # wipes and replaces the present Screen Row
# last wins


assert unicodedata.name("¤").title() == "Currency Sign"  # like � but calmer, to mean unprintable


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

    if shargv == ["--"]:
        import tests  # beside this file, and only when asked

        tests.main()
        return

    # Pick a demo, else freak

    eggs = list(_.removeprefix("--egg=") for _ in shargv if _.startswith("--egg="))
    if not eggs:
        eggs.append("bytes")

    xxta = "--typeahead="
    typeaheads = list(_.removeprefix(xxta) for _ in shargv if _.startswith(xxta))
    typeahead = os.fsencode("".join(typeaheads))  # todo: tighter parsing of .shargv

    gw = GlassWorker()

    if "bytes" in eggs:
        tb = gw.show_bytes(typeahead=typeahead)
    elif "nanos" in eggs:
        tb = gw.show_nanos(typeahead=typeahead)
    elif "frames" in eggs:
        tb = gw.show_frames(typeahead=typeahead)
    elif "strikes" in eggs:
        tb = gw.show_strikes(typeahead=typeahead)
    elif "skater" in eggs:
        tb = gw.show_skater(typeahead=typeahead)
    else:
        assert False, (eggs,)  # not in: bytes, nanos, frames, strikes, skater

    tb.str_print("")

    # ends with 0 or 1 or 2 empty lines
    # 0 for Stdin Eof, 1 commonly, 2 for quit via Return Return Return in particular

    # Write the Input and the Output kept, only after the last Output,
    # counting Nanos in both from the first Nanos kept in either

    ibk = tb.ibk
    obk = tb.obk
    first_nanos = ibk.nano_list[:1] + obk.nano_list[:1]
    zero_nano = min(first_nanos, default=0)  # 0 when no Byte was kept, of Input or of Output

    ibk.pairs_write_file("i.jsonl", zero_nano=zero_nano)
    obk.pairs_write_file("o.jsonl", zero_nano=zero_nano)
    tb.typescript_write_file("o.typescript")


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


@dataclasses.dataclass(order=True)
class GlassWorker:
    """Show off one Terminal feature and another"""

    def show_bytes(self, typeahead: bytes) -> TerminalBoss:
        """Print your Input Bytes on screen"""

        # Launch (and prompt just once and early)

        tb = TerminalBoss(typeahead=typeahead, farewell_bytes=b"")
        tb.str_print("")  # signals very very quietly that we have run this far since launching

        tb.str_print("Press Return three times quickly, to quit")
        tb.str_print("")

        ibk = tb.ibk
        with tb:
            while True:

                # Read

                sys.stdout.flush()  # flushes well-known outputs before blocking on well-known input
                sys.stderr.flush()

                b = tb.read_one_byte_if()
                if not b:
                    break

                # Print, and separate on request

                tb.str_print(f"{ord(b)} {bytes_repr(b)}")
                if b == b"\r":
                    tb.str_print("")

                # Quit on request

                if ibk.is_quitting_bytes():
                    break

        return tb

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

    def show_nanos(self, typeahead: bytes) -> TerminalBoss:
        """Print your Input Bytes (and how quickly they arrived)"""

        # Launch (and prompt just once and early)

        tb = TerminalBoss(typeahead=typeahead, farewell_bytes=b"")
        tb.str_print("")  # signals very very quietly that we have run this far since launching

        tb.str_print("Press Return three times quickly, to quit")
        tb.str_print("")

        first_nanos = tb.obk.nano_list[:1]  # the first Nanos kept, since no Input has come yet
        before = min(first_nanos)

        ibk = tb.ibk
        with tb:
            while True:

                # Read

                sys.stdout.flush()  # flushes well-known outputs before blocking on well-known input
                sys.stderr.flush()

                b = tb.read_one_byte_if()
                if not b:
                    break

                after = ibk.nano_list[-1]  # the Nanos the Boss kept for this Byte

                # Print, and separate on request

                code = ord(b)
                between = after - before
                before = after

                tb.str_print(f"{between:_} {code} {bytes_repr(b)}")
                if b == b"\r":
                    tb.str_print("")

                # Quit on request

                if ibk.is_quitting_bytes():
                    break

        return tb

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

    def show_frames(self, typeahead: bytes) -> TerminalBoss:
        """Print your Input Byte Frames, as Key Caps when known, and how quickly they arrived"""

        # Launch

        tb = TerminalBoss(typeahead=typeahead, farewell_bytes=b"")
        tb.str_print("")  # signals very very quietly that we have run this far since launching

        tb.str_print("Press Return three times quickly, to quit")
        tb.str_print("")

        tfr = TerminalFrameReader(tb)
        with tb:
            for taken, frame, nanobytes in tfr.take_frames_and_yield_each(stalwarts=()):

                # Prompt for next Byte, while growing the Frame

                data = frame.to_frame_bytes()  # maybe empty
                if not taken:
                    self.frame_print(data, nanobytes=nanobytes, end=" + ", tb=tb)

                    continue

                # Print each Frame taken as 1 Line,
                # Except in reply to ⏎ Return, do split Frame Lines into paragraphs

                self.frame_print(data, nanobytes=nanobytes, end="\r\n", tb=tb)

                if data == b"\r":
                    tb.str_print("")

        return tb

    def frame_print(
        self, data: bytes, nanobytes: tuple[tuple[int, bytes], ...], end: str, tb: TerminalBoss
    ) -> None:
        """Print 'caps data = nanos bytes ...' as a whole line, or as the start of one"""

        kd = keyboard_decoder()

        def ns(n: int) -> str:  # reps Int's as counting Nanoseconds
            rep = decimal_int_chop_to_eng_metric(n, one="1ns")  # reps 987*10**12 as '987ks'
            return rep

        words: list[str] = list()

        # Choose the words

        caps = kd.nanobytes_to_key_caps_if(nanobytes)  # ⎋, ⎋[, ↑ when typed slowly
        if caps:
            words.append(caps)

        decode = TerminalByteFrame.bytes_decode_if(data)
        if decode:
            if decode.isprintable() and (decode.strip() == decode):
                words.append(decode)
            else:
                words.append(str_repr(decode))

        words.append(f"{bytes_repr(data)} =")

        reps = list()
        for i, (waited, b) in enumerate(nanobytes):
            if (i == 0) or (waited != 0):  # drops all but the first mention of '0ns'
                reps.append(ns(waited))

            reps.append(bytes_repr(b))

        words.extend(reps)

        # Print the words

        start = CR_EL_PS0  # often '\r' '\033[K'
        join = " ".join(words)
        tb.str_write(f"{start}{join}{end}")  # todo: add a tb.str_print(text, end=end)

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

    def show_strikes(self, typeahead: bytes) -> TerminalBoss:
        """Print your Input Byte Frames, as Key Caps when known, and as Text when printable"""

        # Launch

        tb = TerminalBoss(typeahead=typeahead, farewell_bytes=b"")
        tb.str_print("")  # signals very very quietly that we have run this far since launching

        tb.str_print("Press Return three times quickly, to quit")
        tb.str_print("")

        restart = CR_EL_PS0  # often '\r' '\033[K'

        assert _50_MEGA_NANOS_ == 50 * 10**6  # two Arrows struck together, a held Key slower

        with tb:
            ts = TerminalShadow(tb)  # needs no Shadow, when just showing Strikes
            ist = InputStrikeTaker(ts, arrow_wait_nanos=_50_MEGA_NANOS_)

            for strike in ist.take_input_strikes_and_yield_each(stalwarts=()):

                taken = strike.taken
                caps = strike.caps
                printables = strike.printables

                # Prompt for the first Byte of a Frame

                data = strike.to_strike_bytes()  # maybe empty
                if not data:
                    assert not taken, (taken, strike)

                    tb.str_write(f"{restart}+ ")

                    continue

                # Speak of the Frame as its Caps, else as ⌘V when no Caps send it

                words: list[str] = list()

                words.append(caps if caps else "⌘V")
                words.append(str_repr(printables))
                words.append(bytes_repr(data))

                join = " ".join(words)

                # Prompt for next Byte, while growing the Frame

                if not taken:
                    tb.str_write(f"{restart}{join} + ")

                    continue

                # Print each Frame taken as a line

                tb.str_print(f"{restart}{join}")

            # Erase the Prompt left behind when Stdin Eof ends the Frames

            tb.str_write(restart)

        return tb

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

    def show_skater(self, typeahead: bytes) -> TerminalBoss:
        """Leave a Reverse Pixel of two Spaces behind the Cursor as the → ↑ ← ↓ Keys move it"""

        kd = keyboard_decoder()

        # Choose which Key Caps don't tell us to quit, not even when struck three times quickly

        stalwarts_list = "→ ↑ ← ↓".split()
        stalwarts_list += "⇧← ⇧→ ⌥← ⌥→ ⌥↑ ⌥↓ ⎋⇧← ⎋⇧→".split()
        stalwarts_list += "⇧Fn↑ ⇧Fn↓ ⇧Fn→ ⇧Fn←".split()

        stalwarts = tuple(kd.decode_by_echo[_].encode() for _ in stalwarts_list)
        assert tuple(_.decode() for _ in stalwarts[:4]) == _CARDINAL_ENWS_ARROWS_

        for stalwart_caps in stalwarts_list:
            stalwart_split = InputStrikeTaker.caps_split_arrow_else(stalwart_caps)
            assert stalwart_split, (stalwart_caps,)

            _, stalwart_arrow = stalwart_split
            assert stalwart_arrow in ["←", "↑", "→", "↓"], (stalwart_caps,)

        # Choose what to write at exit

        assert CR == "\r"
        assert CUU_Y.format("") == "\033[" "A"
        assert CUD_Y.format(_MAX_PN_32100_) == "\033[" "32100" "B"
        assert SHOW_CUSR_SM_PSQ25 == "\033[" "?25h"
        assert NO_SGR_PS == "\033[" "m"

        farewells = (
            "\r",  # leaps to left of Screen Row
            "\033[" "m",  # reverts the Text Styles
            "\033[" "?25h",  # shows the Cursor
            "\033[" "32100" "B",  # leaps to last Screen Row
            "\033[" "A",  # leaps to one Screen Row up from last
        )

        farewell_bytes = "".join(farewells).encode()

        # Launch elegantly, almost silently, without printing instructions

        assert _50_MEGA_NANOS_ == 50 * 10**6  # two Arrows struck together, a held Key slower

        tb = TerminalBoss(typeahead=typeahead, farewell_bytes=farewell_bytes)
        with tb:
            ts = TerminalShadow(tb)
            ist = InputStrikeTaker(ts, arrow_wait_nanos=_50_MEGA_NANOS_)

            # Find where the Cursor is and how big the Screen is

            ist.pull_yx_hw_from_ts_else(stalwarts=stalwarts)
            tb.tty_setraw_before_farewell()  # takes ⌃C ⌃D ⌃Z ⌃\ as Input, and Return as b"\r"

            # Choose how to hail now, before farewell later

            assert CR == "\r"
            assert BS == "\b"
            assert SHOW_CUSR_SM_PSQ25 == "\033[" "?25h"

            base_place = ts.base_place
            max_first_x = base_place.x_max - 1  # the last Column where a Pair of Spaces fits
            back_count = max(0, base_place.column_x - max_first_x)  # zero or more Backspaces
            assert back_count >= 0, (back_count,)

            hails = (
                "\033[" "m",  # reverts the Text Styles
                "\033[" "?25h",  # shows the Real Cursor
                "\b" * back_count,  # steps West as far as it must, no more
            )
            hail_text = "".join(hails)

            ts.str_write_base_tb(hail_text)  # calls to shadow Hail only after pulling X W Y H

            assert _2_COLUMNS_ == 2
            assert _1_ROW_ == 1
            assert ts.is_writeable_base_area(area_width=2, area_height=1), (ts.base_place,)

            # Loop till quit (such as by pressing Return three times quickly)

            digits = "0123456789"
            i = "0"  # .i is our Prompt at the next Byte that doesn't complete a Frame
            xo = "X"  # .xo is our Prompt at the next meaningless Frame

            for isap in ist.take_input_strikes_and_yield_each_placed(stalwarts=stalwarts):
                strike = isap.strike
                place = isap.place

                taken = strike.taken
                caps = strike.caps

                # Cycle a Prompt across 1234567890, at each Byte of an Open Frame not taken

                assert BS == "\b"

                data = strike.to_strike_bytes()  # Bytes from 0, 1, or more Frames
                if not taken:
                    (frame,) = strike.frames  # a Strike not taken holds the one Open Frame
                    assert not frame.closed, (frame,)

                    if data:
                        j = digits[(digits.index(i) + len(data)) % len(digits)]
                        ts.str_write_top_tb(f"{j}\b")
                        # todo0: no visible change of Prompt at pasting N * 10 bytes

                    continue

                # Pick out the bounces back, if these Key Caps are Arrows saying move ahead

                bounce_caps_tuple_by_caps = {  # sorted by Caps Codepoints
                    "←": ("→",),  # a Cardinal Arrow bounces only to its opposite
                    "↑": ("↓",),
                    "→": ("←",),
                    "↓": ("↑",),
                    "↖": ("↑", "←", "↘"),  # an Intercardinal Arrow settles for the half that fits:
                    "↗": ("↑", "→", "↙"),  # just its North or South, else just its East or West,
                    "↘": ("↓", "→", "↖"),  # and bounces to its opposite only when neither half fits
                    "↙": ("↓", "←", "↗"),
                }

                shifts_arrow = InputStrikeTaker.caps_split_arrow_else(caps)
                if shifts_arrow:
                    _, arrow_caps = shifts_arrow  # the bare Arrow, whatever shifts came with it
                    bounce_caps_tuple = bounce_caps_tuple_by_caps[arrow_caps]

                    # Undo the Prompts written in the Top Layer, if any

                    self.ts_undo_enough_top_tb(ts)  # same here as whe quitting

                    # Move ahead, or bounce back (so as to avoid nop or spill)

                    base_text = self.form_base_text(ts, caps=arrow_caps)
                    if place:
                        try_caps_tuple = (arrow_caps,) + bounce_caps_tuple
                        try_texts = tuple(self.form_base_text(ts, caps=_) for _ in try_caps_tuple)
                        writable_texts = list(
                            _ for _ in try_texts if ts.is_writable_place_after_strs(text=_)
                        )
                        assert writable_texts, (arrow_caps, len(writable_texts), place)
                        base_text = writable_texts[0]

                    # Write the Reverse Pair into the Base Layer, and leap ahead or bounce back

                    ts.str_write_base_tb(base_text)

                    # Write a Plain Pair into the Top Layer, but only over a written Cell

                    assert _2_COLUMNS_ == 2
                    assert _1_ROW_ == 1

                    if not ts.base.is_shadowed_area(area_width=_2_COLUMNS_, area_height=_1_ROW_):
                        ts.str_write_base_tb(SHOW_CUSR_SM_PSQ25)
                    else:
                        top_text = self.form_top_text(ts)
                        ts.str_write_top_tb(HIDE_CUSR_RM_PSQ25 + top_text)

                    # Restart the Open Frame Prompt, after each Meaningful Frame

                    i = "0"
                    continue

                # Else cycle the Prompt at the Meaningless Frame, between X and O

                assert BS == "\b"

                ts.str_write_top_tb(f"{xo}\b")
                xo = "O" if (xo == "X") else "X"

                # And do cycle the Open Frame Prompt forward by all the Meaningless Bytes

                i = digits[(digits.index(i) + len(data)) % len(digits)]
                continue  # explicitly

            # Quit happy

            self.ts_undo_enough_top_tb(ts)
            # redraws the Base Layer over our Prompts, such as at our Quit Signal

        return tb

    def ts_undo_enough_top_tb(self, ts: TerminalShadow) -> None:
        """Work hard to undo enough of the Prompts, just before moving on or quitting"""

        top = ts.top
        top_place = top.place

        if len(top.write_by_xy) == 1:
            (xy,) = top.write_by_xy.keys()
            assert (top_place.column_x, top_place.row_y) == xy, (xy, top_place)

            top.write_by_xy.clear()  # intentionally forgets to undo a single Prompt Char

        ts.undo_top_tb()

    def form_base_text(self, ts: TerminalShadow, caps: str) -> str:
        """Spell the move: a Reverse Pixel for the Base Layer, and a step toward an Arrow Key"""

        base_place = ts.base_place

        assert SP == " "

        assert CUU_Y == "\033[" "{}" "A"
        assert CUD_Y == "\033[" "{}" "B"
        assert CUF_X == "\033[" "{}" "C"
        assert CUB_X == "\033[" "{}" "D"

        assert NO_SGR_PS == "\033[" "m"
        assert REVERSE_SGR_PS7 == "\033[" "7m"

        square = 2 * " "  # two Spaces side by side, one Square Pixel
        plain = NO_SGR_PS  # reverts the Text Styles
        reverse = REVERSE_SGR_PS7  # swaps to color B on F, from color F on B

        square_leap_by_caps = {  # for 2x1 Terminal Screen Cells  # sorted by Caps Codepoints
            "←": 2 * CUB_X.format(""),  # Back West
            "↑": 1 * CUU_Y.format(""),  # Up North
            "→": 2 * CUF_X.format(""),  # "Forward" East
            "↓": 1 * CUD_Y.format(""),  # Down South
            "↖": 1 * CUU_Y.format("") + 2 * CUB_X.format(""),  # Up North, then Back West
            "↗": 1 * CUU_Y.format("") + 2 * CUF_X.format(""),  # Up North, then "Forward" East
            "↘": 1 * CUD_Y.format("") + 2 * CUF_X.format(""),  # Down South, then "Forward" East
            "↙": 1 * CUD_Y.format("") + 2 * CUB_X.format(""),  # Down South, then Back West
        }

        leap = square_leap_by_caps[caps]

        # Choose what to leave behind

        back = self.form_back_text(base_place)
        base_text = f"{reverse}{square}{plain}{back}" + leap

        # Succeed

        return base_text

    def form_top_text(self, ts: TerminalShadow) -> str:
        """Spell a Plain Pixel for the Top Layer, where the Cursor sits"""

        base_place = ts.base_place

        assert SP == " "

        square = 2 * " "  # two Spaces side by side, one Square Pixel, the Cursor's own plain place

        back = self.form_back_text(base_place)
        top_text = f"{square}{back}"
        return top_text

    def form_back_text(self, place: TerminalPlace) -> str:
        """Spell how to back the Cursor up over two Spaces written at its Place"""

        assert _2_COLUMNS_ == 2
        assert BS == "\b"

        back = "\b\b"  # backs up over two Columns

        if place:
            if (place.column_x + 1) >= place.x_width:
                back = "\b"  # backs up over one Column

        return back


#
# Speak of each Frame as Printable, and/or as known Key Caps, else as ⌘V Paste
#


@dataclasses.dataclass
class InputStrikeTaker:
    """Speak of each Frame as Printable, and/or as known Key Caps, else as ⌘V Paste"""

    held_strikes: list[InputStrike]  # Input Strikes delayed while waiting for YX HW
    ts: TerminalShadow  # the Terminal we write through, and the Place it last reported
    tfr: TerminalFrameReader  # the Frames taken so far, and the Open Frame
    arrow_wait_nanos: int  # the Nanos we wait for the second Arrow of a Pair, 0 for none

    def __init__(self, ts: TerminalShadow, arrow_wait_nanos: int) -> None:

        assert arrow_wait_nanos >= 0, (arrow_wait_nanos,)

        self.ts = ts
        self.arrow_wait_nanos = arrow_wait_nanos
        self.tfr = TerminalFrameReader(ts.tb)
        self.held_strikes = list()

    def pull_yx_hw_from_ts_else(self, stalwarts: tuple[bytes, ...]) -> None:
        r"""Find where the Cursor is and how big the Screen is, asking only a Terminal"""

        held_strikes = self.held_strikes
        ts = self.ts
        tb = ts.tb

        isatty = tb.isatty
        if isatty:  # asks only a Tty Terminal for YX and HW in order
            ts.ask_yx_hw_from_tb()

        tags: list[str] = list()  # the kinds of reply taken, "YX" and "HW"
        for strike in self.take_input_strikes_and_yield_each(stalwarts=stalwarts):
            data = strike.to_strike_bytes()

            # Drop every partial Strike yielded and not taken before the last Reply

            if not strike.taken:
                continue

            # Quit at ⌃D b"\004" as the Shell would, despite SetCBreak taking it as Input not Signal

            if data == b"\004":
                break

            # Divert two or more YX HW Replies, but hold other Taken Frames

            reply = ts.shadow_read_data_else(data)
            if reply:
                tags.append(reply[0])  # briefly remembers order, but accepts either order
            else:
                held_strikes.append(strike)  # trusts other Code to yield these soon enough

            # Quit after taking YX and HW Replies

            if ("YX" in tags) and ("HW" in tags):
                break

        if ("YX" not in tags) or ("HW" not in tags):
            tb.str_print("Input ended before Y X H W replies to ⎋[6N and ⎋[18T")
            sys.exit(1)

            # easy to test tags as absent, present, disordered, ordered at no Terminal

        # todo: read a fresh Y X from the Terminal at each Strike, not guessed by Shadow
        # todo: catch changes of the H W of the Terminal, as at a resize

        # todo: stop parallel ⎋ Keyboard Inputs from disrupting the Frames of either Reply
        # todo: keep late Replies out of the Shell, when Quit comes between Asks and Replies

    def take_input_strikes_and_yield_each_placed(
        self, stalwarts: tuple[bytes, ...]
    ) -> typing.Iterator[InputStrikeAtPlace]:
        """Yield each Strike with the Place the Shadow knows, but first the Held Strikes"""

        held_strikes = self.held_strikes
        ts = self.ts

        layer = ts.base

        # Yield each Strike held while waiting for the Terminal to report YX HW

        while held_strikes:
            strike = held_strikes.pop(0)

            isap = InputStrikeAtPlace(strike=strike, place=layer.place)
            yield isap

        # Yield each Strike taken since, except swallow Replies to YX HW Asks

        for strike in self.take_input_strikes_and_yield_each(stalwarts=stalwarts):
            data = strike.to_strike_bytes()  # maybe empty

            reply = ts.shadow_read_data_else(data)
            if reply:
                continue

            isap = InputStrikeAtPlace(strike=strike, place=layer.place)
            yield isap

    def take_input_strikes_and_yield_each(
        self, stalwarts: tuple[bytes, ...]
    ) -> typing.Iterator[InputStrike]:
        """Yield an InputStrike for each Frame yielded (while growing or when taken)"""

        tb = self.ts.tb
        tfr = self.tfr
        arrow_wait_nanos = self.arrow_wait_nanos
        kd = keyboard_decoder()

        held_arrow: InputStrike | None = None  # a taken Cardinal Arrow, held for a mate

        for taken, frame, nanobytes in tfr.take_frames_and_yield_each(stalwarts=stalwarts):
            data = frame.to_frame_bytes()  # maybe empty

            # Speak of the Frame as Text, when its Bytes decode as Printable

            printables = ""
            decode = TerminalByteFrame.bytes_decode_if(data)
            if decode and decode.isprintable():
                printables = decode

            # Speak of the Frame as Strikes, when the Keyboard Decoder names its Key Caps

            caps = kd.nanobytes_to_key_caps_if(nanobytes)  # ⎋, ⎋[, ↑ when typed slowly
            assert caps == caps.strip(), (caps, frame)

            strike = InputStrike(taken=taken, caps=caps, printables=printables, frames=(frame,))

            is_taken_arrow = False
            if taken:

                shifts_arrow = InputStrikeTaker.caps_split_arrow_else(caps)
                if shifts_arrow:
                    _, arrow = shifts_arrow

                    is_taken_arrow = arrow in ("→", "↑", "←", "↓")  # the ENWS Arrows

            if held_arrow:

                # Peek ahead, past an empty Open Frame for at most arrow_wait_nanos, or into Typeahead

                if (not taken) and (not data):  # past an empty Open Frame
                    if tb.typeahead or tb.stdio_select_select(timeout=arrow_wait_nanos / 1e9):
                        yield strike
                        continue

                if not taken:  # into Typeahead
                    if tb.typeahead:
                        yield strike
                        continue

                # Join a taken Cardinal Arrow, if it fits, to the Arrow held

                if is_taken_arrow:
                    joined_strike = InputStrikeTaker.arrows_join_else(held_arrow, strike)
                    if joined_strike:
                        held_arrow = None
                        yield joined_strike
                        continue

                # Give up and yield the Arrow held, before the Strike that ended the hold

                yield held_arrow
                held_arrow = None

            # Hold a taken Cardinal Arrow, unless we never join

            is_joining = arrow_wait_nanos > 0  # a wait of 0 holds nothing and joins nothing
            if is_joining and is_taken_arrow:
                held_arrow = strike
                continue

            # Always do yield the Strike, be it now or later

            yield strike

        # Yield the Arrow still held at End of Input or Quit

        if held_arrow:
            yield held_arrow

        # todo: prove a Caller who quits reading early never loses the Arrow held

    @staticmethod
    def arrows_join_else(first: InputStrike, second: InputStrike) -> InputStrike | None:
        """Join two Cardinal Arrows on different axes into one Intercardinal Arrow, else None"""

        assert _SHIFT_CAPS_ == ("⎋", "⌃", "⌥", "⇧", "⌘", "Fn")

        diagonal_by_straights = {  # four pairs of sums, each sum adding up to one Intercardinal
            "↑→": "↗",  # ↗ ↖ ↙ ↘ is counterclockwise from Northeast
            "→↑": "↗",
            "↑←": "↖",
            "←↑": "↖",
            "↓←": "↙",
            "←↓": "↙",
            "↓→": "↘",
            "→↓": "↘",
        }

        # Pair no Cardinal Arrows until both taken

        if not (first.taken and second.taken):
            return None

        # Pair no Cardinal Arrows when the Strikes aren't Arrows

        first_split = InputStrikeTaker.caps_split_arrow_else(first.caps)
        second_split = InputStrikeTaker.caps_split_arrow_else(second.caps)
        if (first_split is None) or (second_split is None):
            return None

        # Pair no Cardinal Arrows when the Pair doesn't fit to form an Intercardinal Arrow

        first_shifts, first_arrow = first_split
        second_shifts, second_arrow = second_split

        arrows = first_arrow + second_arrow
        if arrows not in diagonal_by_straights.keys():
            return None  # such as ↑↑ or ↑↓, two Arrows on one axis

        diagonal_arrow = diagonal_by_straights[arrows]

        # Keep every Shift of both Arrows, each once, in the order ⎋ ⌃ ⌥ ⇧ ⌘ Fn

        shifts = tuple(_ for _ in _SHIFT_CAPS_ if (_ in first_shifts) or (_ in second_shifts))

        # Pair the two Cardinal Arrows in the order of arrival

        (first_frame,) = first.frames
        (second_frame,) = second.frames
        assert first_frame.closed and second_frame.closed, (first_frame, second_frame)

        # Succeed

        caps = "".join(shifts) + diagonal_arrow  # '⇧Fn↘'
        strike = InputStrike(
            taken=True, caps=caps, printables="", frames=(first_frame, second_frame)
        )

        return strike

    @staticmethod
    def caps_split_arrow_else(caps: str) -> tuple[tuple[str, ...], str] | None:
        """Split Key Caps of zero or more shifts vs one of → ↑ ← ↓ or ↗ ↖ ↙ ↘, else return None"""

        assert _SHIFT_CAPS_ == ("⎋", "⌃", "⌥", "⇧", "⌘", "Fn")

        assert caps == caps.strip(), (caps,)

        shifts: list[str] = list()
        rest = caps
        while rest:
            heads = list(_ for _ in _SHIFT_CAPS_ if rest.startswith(_))
            if not heads:
                break

            (head,) = heads
            shifts.append(head)
            rest = rest[len(head) :]

        if rest not in (("→", "↑", "←", "↓") + ("↗", "↖", "↙", "↘")):  # ENWS & NE NW SW SE Arrows
            return None  # such as ⎋[ or ⇧A or empty

        split = (tuple(shifts), rest)
        return split


@dataclasses.dataclass(order=True)
class InputStrike:
    """Speak of one Frame, or the two Frames of an Intercardinal Arrow, as Strikes and as Text"""

    taken: bool  # closed or bounced or cut at Quit, else still the Open Frame
    caps: str  # the Key Caps best known as sending these Bytes, else ''
    printables: str  # the Bytes decoded, if printable, else ''
    frames: tuple[TerminalByteFrame, ...]  # the Frames in order of arrival (often just one)

    def to_strike_bytes(self) -> bytes:
        """Return the Bytes of the Frames, catenated in order of arrival"""

        frames = self.frames

        data = b"".join(_.to_frame_bytes() for _ in frames)
        return data


@dataclasses.dataclass(order=True)
class InputStrikeAtPlace:
    """Speak of one InputStrike at one Screen Place"""

    strike: InputStrike  # what the Input
    place: TerminalPlace  # where the Cursor, how big the Screen


#
# Speak of Byte Frames as Strikes of Key Caps at a MacBook
#


@functools.cache
def keyboard_decoder() -> KeyboardDecoder:
    """Build the one KeyboardDecoder, once, and hand it back on each later call"""

    kd = KeyboardDecoder()
    return kd


@dataclasses.dataclass
class KeyboardDecoder:
    """Speak of Str's as Key Caps struck at a MacBook, and vice versa"""

    decode_by_echo: dict[str, str]  # '⇥': '\t'  # '⌃I': '\t'
    echoes_by_decode: dict[str, tuple[str, ...]]  # '\t' to ('⇥', '⌃I', '⌃⇥', '⌥⇥', ...) all 7 ways
    dead_echo_by_decode: dict[str, str]  # 'é': '⌥EE'  # '´q': '⌥E Q'

    PlainCapsWithoutFn = r"""
        ⎋
        ` 1 2 3 4 5 6 7 8 9 0 - = ⌫
        ⇥ Q W E R T Y U I O P [ ] \
        A S D F G H J K L ; ' ⏎
        Z X C V B N M , . /
        ␢ ← ↑ → ↓
    """  # Plain Caps apart from F1..F12 etc  # ␢ ← ↑ → ↓ is sorted by Codepoint

    ShiftCapsWithoutFn = """
        ⎋
        ~ ! @ # $ % ^ & * ( ) _ + ⌫
        ⇥ Q W E R T Y U I O P { } |
        A S D F G H J K L : " ⏎
        Z X C V B N M < > ?
        ␢ ← ↑ → ↓
    """  # ⇧~ ⇧! etc are Shift Caps apart from ⇧ F1..F12 etc  # ␢ ← ↑ → ↓ is sorted by Codepoint

    AvailableShifts: typing.ClassVar[tuple[str, ...]]  # ⇧ ⌃ ⌥  # ⌃⇧ ⌥⇧ ⌃⌥  # ⌃⌥⇧  # ⎋ ⎋⇧ ⎋⌃ ⎋⌃⇧
    AvailableShifts = ("", "⇧", "⌃", "⌥", "⌃⇧", "⌥⇧", "⌃⌥", "⌃⌥⇧", "⎋", "⎋⇧", "⎋⌃", "⎋⌃⇧")
    # Shift Combinations sorted from least to most difficult to type out on a MacBook US Keyboard

    class DeadKeys:
        """Speak of the five ⌥ Dead Keys, of the Letters they accent & of the Accents they send"""

        LettersByEcho = {  # the Letters each Dead Key does accent, at the U.S. Layout of macOS
            "⌥`": "aeiou",
            "⌥E": "aeiouj",  # ⌥E J sends 'j' before a Combining Acute Accent, to land as 'j́'
            "⌥I": "aeiou",
            "⌥N": "ano",
            "⌥U": "aeiouy",
        }

        AccentedByEcho = {  # the Char each Dead Key sends, when struck before each of its Letters
            "⌥`": "àèìòù",
            "⌥E": "áéíóú",  # ⌥E J sends no one Char
            "⌥I": "âêîôû",
            "⌥N": "ãñõ",
            "⌥U": "äëïöüÿ",
        }

        EchoByAccent = {  # each Dead Key sends its Accent ahead of a Letter it doesn't accent
            "\u0060": "⌥`",  # Grave Accent `  # also sent by ⌥⇧~
            "\u00b4": "⌥E",  # Acute Accent ´  # also sent by ⌥⇧E
            "\u02c6": "⌥I",  # Modifier Letter Circumflex Accent ˆ  # also sent by ⌥⇧I
            "\u02dc": "⌥N",  # Small Tilde ˜  # also sent by ⌥⇧N
            "\u00a8": "⌥U",  # Diaeresis ¨  # also sent by ⌥⇧U
        }

        # ⌥X Space, ⌥X ⌥X, and ⌥⇧X each send the Accent alone, as one Byte or Char with no sign of
        # the Space, the ⌥, or the wait between two Strikes. A lone Accent says ⌥⇧X here, and the
        # ⌥` Dead Key's lone Grave Accent says the ` Key, which sends the same Byte.

        assert sorted(AccentedByEcho.keys()) == sorted(LettersByEcho.keys())
        assert sorted(EchoByAccent.values()) == sorted(LettersByEcho.keys())

    def __init__(self) -> None:

        self.decode_by_echo = dict()
        self._form_macos_keyboards_()
        self._form_apple_terminal_keyboards_()

        self.echoes_by_decode = self._form_echoes_by_decode_()
        self.dead_echo_by_decode = self._form_dead_echo_by_decode_()

        # todo: port the iTerm2 and Ghostty Keyboards from bin/litglass.py, as diffs from this one

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

        shifts = "⇧"  # ⇧← and ⇧→ send ⎋[1;2⇧D and ⎋[1;2⇧C

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
        """  # our sourceline detailing "033.011 ... 033.034" is more than 100 Chars wide

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
        """  # our sourceline detailing "⎋⎋[⇧Z 033.021 ... 033.034" is more than 100 Chars wide

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # todo: rename .strikes .cap_strikes .bytes_names .echo, to not collide with InputStrike

    def _add_keyboard_(self, shifts: str, strikes: str) -> None:
        """Add in 1 Keyboard of Key Caps and their Strikes"""

        assert shifts in KeyboardDecoder.AvailableShifts, (shifts,)

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
            t = bytes_names  # not these Shifts, not these Chars
            assert t not in ("⎋⌃⌥⇧" + "`" + "~"), (t, bytes_names)

            encode = bytes_names.encode()
            return encode

        # Accept single Characters escaped, no matter if shifted or not

        assert ESC == "\033"

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

        csi = re.fullmatch(r"(⎋|⎋⎋)(\[)([0-9;]*)⇧([ABCDFHPQRSZ~])", string=bytes_names)
        if csi:  # ⎋[⇧Z  # ⎋[1;2⇧C  # ⎋⎋[⇧D  # ⎋[17⇧~  # ⎋[⇧F  # ⎋[⇧H
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

        # 2 ⇧  # Sideband Bells on ⇧ F1 F2 F3 F4

        shifts = "⇧"  # ⇧← and ⇧→ send ⎋[1;2⇧D and ⎋[1;2⇧C

        caps = "F5 F6 F7 F8" + " " + "F9 F10 F11 F12"  # without "F1 F2 F3 F4" + " " +
        strikes = """
            ⎋[25⇧~ ⎋[26⇧~ ⎋[28⇧~ ⎋[29⇧~
            ⎋[31⇧~ ⎋[32⇧~ ⎋[33⇧~ ⎋[34⇧~
        """  # omitting ⎋[27⇧~

        self._keyboard_add_some_(caps, strikes=strikes, shifts=shifts)

        fn_arrow_caps = "Fn↑ Fn↓ Fn→ Fn←"
        fn_arrow_strikes = """
            ⎋[5⇧~ ⎋[6⇧~ ⎋[⇧F ⎋[⇧H
        """

        self._keyboard_add_some_(fn_arrow_caps, strikes=fn_arrow_strikes, shifts=shifts)

        # 3 ⌃  # Sideband Bells on ⌃ F2 F3 F4 F5 F6, ⌃ F9 F10 F11 F12  # No Codes on ⌃ F1 F7 F8

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

        # 5 ⌃⇧  # Sideband Bells on ⌃⇧ F1..F6, ⌃⇧ F8..F12  # No Codes on ⌃⇧ F7
        # 6 ⌥⇧  # Sideband Bells on ⌥⇧ F1..F12
        # 7 ⌃⌥  # Sideband Bells on ⌃⌥ F1..F12
        # 8 ⌃⌥⇧  # Sideband Bells on ⌃⌥⇧ F1..F12

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
        """  # omitting ⎋[16⇧~  # not-colliding with ⎋[ ⇧R

        self._keyboard_add_some_(caps, strikes=strikes, shifts=shifts)

        # ⎋⇧O⇧P ⎋⇧O⇧Q ⎋⇧O⇧R ⎋⇧O⇧S  # ⎋[15⇧~ ⎋[17⇧~ ⎋[18⇧~ ⎋[19⇧~  # ⎋[20⇧~ ⎋[21⇧~

    def _keyboard_add_some_(self, caps: str, strikes: str, shifts: str) -> None:
        """Add some Key Caps at Strikes to a Keyboard"""

        caps_split = caps.split()
        strikes_split = strikes.split()
        assert shifts in KeyboardDecoder.AvailableShifts, (shifts,)

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

        assert shifts in KeyboardDecoder.AvailableShifts, (shifts,)
        caps = "F1 F2 F3 F4" + " " + "F5 F6 F7 F8" + " " + "F9 F10 F11 F12"
        strikes = 12 * " 033.020"  # ⎋⌃P
        self._keyboard_add_some_(caps, strikes=strikes, shifts=shifts)

    def _form_echoes_by_decode_(self) -> dict[str, tuple[str, ...]]:
        """Invert our Decode_by_Echo Dict, but sort it to more celebrate the more available Echoes"""

        decode_by_echo = self.decode_by_echo
        available_shifts = KeyboardDecoder.AvailableShifts

        def _to_echo_sort_key_(echo: str) -> tuple[bool, int, int, str]:
            """Say how to sort multiple Echoes from most to least available"""

            assert len(echo.split()) == 1, (len(echo.split()), echo)

            lstrip = echo.lstrip("⎋⌃⌥⇧")  # sorted as in naming macOS Keyboard Shortcuts
            cap = lstrip if lstrip else echo[-1:]  # Cap is last Shift when Echo is all Shifts
            shifts = echo[: -len(cap)]

            fnwide = bool(len(cap) > 1)  # all others before F1..F12 or with Fn
            available = available_shifts.index(shifts)  # Unshifted to ⇧ to ⌃ etc to ⌃⌥⇧ to ⎋ etc
            fnwidth = len(cap)  # all of F1..F9 before all of F10..F12 before Fn← Fn↑ Fn→ Fn↓

            echo_key = (fnwide, available, fnwidth, cap)
            return echo_key

            # P before ⇧P before ⌃P etc before ⌃⌥⇧P, before ⎋P, before F9 before F10 before Fn↓

        vxk = decode_by_echo

        kkxv = collections.defaultdict(list)
        for k, v in vxk.items():
            assert k and v, (k, v)
            kkxv[v].append(k)

        assert "" not in vxk.keys()

        d = dict()
        for v, kk in kkxv.items():
            assert kk, (v, kk)
            d[v] = tuple(sorted(kk, key=_to_echo_sort_key_))

        assert "" not in d.keys()

        return d

    def _form_dead_echo_by_decode_(self) -> dict[str, str]:
        """Say which ⌥ Dead Key and Letter send which Text, for 5 Dead Keys before 94 Chars"""

        dead_keys_accented_by_echo = KeyboardDecoder.DeadKeys.AccentedByEcho
        dead_keys_echo_by_accent = KeyboardDecoder.DeadKeys.EchoByAccent
        dead_keys_letters_by_echo = KeyboardDecoder.DeadKeys.LettersByEcho

        echoes_by_decode = self.echoes_by_decode

        d: dict[str, str] = dict()

        # List the 2 Letters that come before a Combining Mark

        d["j\u0301"] = "⌥EJ"  # only ⌥E J and ⌥E ⇧J send a Letter and then a Combining Mark
        d["J\u0301"] = "⌥E⇧J"

        # List the 48 Letters that come accented as 1 Combined Char

        for echo, accenteds in dead_keys_accented_by_echo.items():
            letters = dead_keys_letters_by_echo[echo]
            assert len(accenteds) == len(letters.rstrip("j")), (accenteds, letters)

            for lower, accented in zip(letters, accenteds):  # stops before the 'j' of ⌥E J
                upper = lower.upper()

                assert accented not in d.keys(), (accented,)
                assert accented.upper() not in d.keys(), (accented.upper(),)

                d[accented] = echo + echoes_by_decode[lower][0]  # 'é': '⌥EE'
                d[accented.upper()] = echo + echoes_by_decode[upper][0]  # 'É': '⌥E⇧E'

        # List the 210 Letters that come after an Accent

        for accent, echo in dead_keys_echo_by_accent.items():
            for letter in string.ascii_letters:
                if letter.lower() not in dead_keys_letters_by_echo[echo]:

                    assert (accent + letter) not in d.keys(), (accent + letter,)
                    d[accent + letter] = echo + " " + echoes_by_decode[letter][0]  # '´q': '⌥E Q'

        # List the 210 Digits and Punctuation Marks that come after an Accent

        for accent, echo in dead_keys_echo_by_accent.items():
            for mark in string.digits + string.punctuation:

                assert (accent + mark) not in d.keys(), (accent + mark,)
                d[accent + mark] = echo + " " + echoes_by_decode[mark][0]  # '´-': '⌥E -'

        assert len(d) == 5 * (52 + 10 + 32), (len(d),)  # before 52 Letters, 10 Digits, 32 Marks

        return d

    #
    # Speak of Bytes as Strikes of Key Caps at a MacBook
    #

    def nanobytes_to_key_caps_if(self, nanobytes: tuple[tuple[int, bytes], ...]) -> str:
        """Name the Key Caps struck to send each burst of Bytes, else an Empty Str when unsure"""

        assert _10_MEGA_NANOS_ == 10 * 10**6  # a Dead Key sends its Accent & Letter closer

        data = b"".join(b for (_, b) in nanobytes)

        # Name the Bytes of an unprintable Frame the same, no matter if quick or slow

        text = TerminalByteFrame.bytes_decode_if(data)  # decodable, but maybe not printable
        if not (text and text.isprintable()):
            caps = self._burst_bytes_to_key_caps_if_(data)
            return caps  # ↑ when typed slowly as ⎋ [ ⇧A

            # todo: echo ⎋[⇧M{b}{x}{y} lots more meaningfully than ⎋ [ ⇧M A B C, as Button and X Y

        # Cut Text into bursts, before each Char whose last Byte came slowly

        bursts: list[str] = list()
        index = 0  # counts the Bytes that came before this Char
        for t in text:
            length = len(t.encode())
            waited = sum(w for (w, _) in nanobytes[index:][:length])  # till its last Byte
            index += length

            is_slow = waited >= _10_MEGA_NANOS_
            if (not bursts) or is_slow:
                bursts.append("")

            bursts[-1] += t

        # Name the Key Caps of each burst

        # todo: fix how ` and then P read as ⌥` P, when pasted or struck less than 10 ms apart

        words: list[str] = list()
        for burst in bursts:
            burst_caps = self._burst_bytes_to_key_caps_if_(burst.encode())
            if not burst_caps:
                return ""  # such as a Combining Mark that came slowly, which no Key sends

            words.append(burst_caps)

        # Succeed

        caps = " ".join(words)
        return caps  # ⌥I P as a burst  # ⌥⇧I P when struck slowly  # ⇧A ⇧B ⇧C when pasted

    def _burst_bytes_to_key_caps_if_(self, data: bytes) -> str:
        """Name the Key Caps struck to send this burst of Bytes, else an Empty Str when unsure"""

        dead_echo_by_decode = self.dead_echo_by_decode

        # Give up quickly on Undecodable Bytes

        text = TerminalByteFrame.bytes_decode_if(data)
        if not text:
            return ""

        # Echo the one Chord of Key Caps that sends the whole Text, when there is one

        data_echoes = self._bytes_to_sorted_echoes_if_(data)
        if data_echoes:
            echo = data_echoes[0]
            return echo  # ⇥  # ⏎  # ↑  # ⌃A  # ⌥⇧E

        # Glue Chars together, where a ⌥ Dead Key and then a Letter send them together

        decodes: list[str] = list()
        for t in text:
            if decodes and ((decodes[-1] + t) in dead_echo_by_decode.keys()):
                decodes[-1] += t  # '´' and then 'q'  # 'j' and then its Combining Acute Accent
                continue

            decodes.append(t)

        # Echo two Chords per Dead Key and Letter, and else one Chord per Char

        echoes: list[str] = list()
        for decode in decodes:

            if decode in dead_echo_by_decode.keys():
                dead_echo = dead_echo_by_decode[decode]
                echoes.append(dead_echo)  # ⌥EE  # ⌥EJ  # ⌥E Q
                continue

            decode_echoes = self._bytes_to_sorted_echoes_if_(decode.encode())
            if not decode_echoes:
                return ""  # such as a Combining Mark struck twice or pasted, which no Key sends

                # todo: each ⌥ Combining Mark struck indistinguishable from ⌥⇧ of same Key Cap?

            decode_echo = decode_echoes[0]
            echoes.append(decode_echo)

        caps = " ".join(echoes)
        return caps  # ⌥EJ  # ⌥EE  # ⇧A ⇧B ⇧C  # ⌥I P

    def _bytes_to_sorted_echoes_if_(self, data: bytes) -> tuple[str, ...]:
        """Speak of Bytes as Strikes of Chords of Key Caps"""

        text = data.decode()

        echoes_by_decode = self.echoes_by_decode

        if text in echoes_by_decode.keys():
            echoes = echoes_by_decode[text]
            return echoes

            # tuple of '⎋', of '␢', of '⌥⇧⇥', of '⌃⌥⇧Fn'

        return tuple()


#
# Write Bytes to a Terminal, and remember many of the Bytes
#


@dataclasses.dataclass
class TerminalShadow:
    """Keep a copy of what we've written to a Terminal"""

    tb: TerminalBoss  # the one Terminal we write through

    base: TerminalLayer  # the Base Layer, what we know we wrote and mean to leave
    top: TerminalLayer  # the Top Layer, what we know we wrote and mean to undo
    # todo: more Layers than just the Top Layer and the Base Layer

    def __init__(self, tb: TerminalBoss) -> None:

        self.tb = tb

        place = TerminalPlace(column_x=1, x_max=1, x_width=1, row_y=1, y_height=1)
        assert not place, (place,)

        self.base = TerminalLayer(place=place, text_styles=(), write_by_xy=dict())

        top_place = dataclasses.replace(place)  # clones
        self.top = TerminalLayer(place=top_place, text_styles=(), write_by_xy=dict())

    @property
    def base_place(self) -> TerminalPlace:
        """Say where the Cursor is in the Base Layer, and how big the Screen is"""

        base = self.base
        return base.place

    def is_writeable_base_area(self, /, area_width: int, area_height: int) -> bool:
        """Say if every Cell of the Area, to the East & South of here, may be written"""

        base = self.base
        writeable = base.is_writeable_area(area_width=area_width, area_height=area_height)
        return writeable

    def ask_yx_hw_from_tb(self) -> None:
        """Ask for Replies to say where the Cursor is and how big the Screen is, later, in order"""

        assert DSR6 == "\033[" "6n"
        assert XTWINOPS_18 == "\033[" "18" "t"

        tb = self.tb

        asks = DSR6 + XTWINOPS_18
        tb.asks_write_flush(asks.encode())  # adds to the o.jsonl, but cuts from the o.typescript

    def shadow_read_data_else(self, data: bytes) -> tuple[str, int, int] | None:
        """Take the Cursor Column and Row, or the Screen Width and Height, from the Terminal"""

        base = self.base
        top = self.top

        assert _5_ROWS_ == 5
        assert _20_COLUMNS_ == 20

        reply = TerminalFrameDecoder.bytes_to_yx_or_hw_reply_else(data)
        if not reply:
            return reply

        tag, int1, int2 = reply  # maybe same as was, maybe different
        assert tag in ("YX", "HW"), (tag,)

        # Update the X Y in the Layer where the Cursor sits

        if tag == "YX":
            assert int1 >= _1_ROW_, (int1,)
            assert int2 >= _1_COLUMN_, (int2,)

            area_layer = top if top else base  # the Top, once it is on
            next_place = dataclasses.replace(area_layer.place, column_x=int2, row_y=int1)
            area_layer.place = next_place  # replace with the next, no matter if equal or not

        # Else calculate the X Max from the X Width

        else:
            assert tag == "HW", (tag,)
            assert int1 >= _5_ROWS_, (int1,)
            assert int2 >= _20_COLUMNS_, (int2,)

            x_width = int2
            x_max = x_width - (x_width % 2)  # an odd Width W+1 acts as W

            place1 = dataclasses.replace(base.place, x_max=x_max, x_width=int2, y_height=int1)
            place2 = dataclasses.replace(place1)

            # Update the W H in the Base always, and update the Top to match if Top truthy

            base.place = place1  # replace with the next, no matter if equal or not
            if top:
                top.place = place2

        # Succeed

        return reply

        # todo0: get unhappy when not next_place.is_onscreen_place
        # todo: think harder about place.__bool__ undecided after XY until WH

    def str_write_base_tb(self, text: str) -> None:
        """Write the Text and shadow the Write"""

        tb = self.tb
        base = self.base
        top = self.top

        # Require a Write that we can shadow in full

        assert base, (base.place, text)

        assert IL_Y.format("") == "\033[" "L"
        assert DL_Y.format("") == "\033[" "M"
        if (IL_Y.format("") in text) or (DL_Y.format("") in text):
            assert not top, (top.place, text)

            # todo: insert or delete Rows while the Top Layer is on

        fork_layer = base.fork_layer()
        fork_written = fork_layer._write_some_or_all_strs_(text)
        assert fork_written, (text, base.place)

        # Shadow in full

        again = base._write_some_or_all_strs_(text)
        assert again is fork_written, (again, fork_written)

        # Write in full, for real

        tb.bytes_write_flush(text.encode())

    def str_write_top_tb(self, text: str) -> None:
        """Write the Text and shadow the Write in the Top Layer only, to undo it later"""

        tb = self.tb
        base = self.base
        top = self.top

        # Require a Write that we can shadow

        assert base, (base.place, text)

        assert IL_Y.format("") == "\033[" "L"
        assert DL_Y.format("") == "\033[" "M"

        assert IL_Y.format("") not in text, (text,)
        assert DL_Y.format("") not in text, (text,)

        area_layer = top if top else base
        fork_layer = area_layer.fork_layer()
        assert fork_layer, (fork_layer.place,)

        fork_written = fork_layer._write_some_or_all_strs_(text)
        assert fork_written, (text, area_layer.place)

        # Turn the Top Layer on where the Base Layer is, when it was off

        if not top:
            top.place = dataclasses.replace(base.place)  # clones
            top.text_styles = base.text_styles  # immutable

        # Shadow in full, in the Top Layer only, leaving the Base Layer as it was

        again = top._write_some_or_all_strs_(text)
        assert again is fork_written, (again, fork_written)

        # Write in full, for real

        tb.bytes_write_flush(text.encode())

    def undo_top_tb(self) -> None:
        """Write the Base Layer's Cells back over each Cell of the Top Layer, and turn the Top off"""

        tb = self.tb
        base = self.base
        top = self.top

        assert base, (base.place,)

        # Do nothing when the Top Layer is off, as a Top Layer of 1 by 1 is

        if not top:
            return

        base_place = dataclasses.replace(base.place)  # clones, to keep what it was at entry
        base_styles = base.text_styles

        # Plan for a Write to rewrite every Cell written via the Top Layer

        hope_layer = top.fork_layer()  # starts where the Terminal Cursor is, which is in the Top

        hope_text = ""
        yx_sorted = sorted((y, x) for (x, y) in top.write_by_xy.keys())
        for y, x in yx_sorted:  # from North to South, from West to East

            assert SP == " "
            assert NO_SGR_PS == "\033[" "m"

            assert (x, y) in base.write_by_xy.keys(), (x, y, base_place)

            leap = TerminalShadow.form_leap_back(hope_layer.place, column_x=x, row_y=y)
            cell_styles, cell_text = base.write_by_xy[(x, y)]
            cell_write = leap + NO_SGR_PS + "".join(cell_styles) + cell_text
            hope_written = hope_layer._write_some_or_all_strs_(cell_write)
            assert hope_written, (cell_write, hope_layer.place)

            hope_text += cell_write

        # Plan to put the Terminal Cursor & Text Styles back to where they were

        assert NO_SGR_PS == "\033[" "m"

        leap = TerminalShadow.form_leap_back(
            hope_layer.place, column_x=base_place.column_x, row_y=base_place.row_y
        )
        end_text = NO_SGR_PS + "".join(base_styles) + leap

        hope_written = hope_layer._write_some_or_all_strs_(end_text)
        assert hope_written, (end_text, hope_layer.place)
        assert hope_layer.place == base_place, (hope_layer.place, base_place)

        hope_text += end_text

        # Turn off the Top

        top.clear_layer()

        # Write it for real

        tb.bytes_write_flush(hope_text.encode())

    @staticmethod
    def form_leap_back(place: TerminalPlace, column_x: int, row_y: int) -> str:
        """Spell how to move the Terminal Cursor West along its Row to a Column"""

        assert place.row_y == row_y, (place.row_y, row_y)

        from_x = min(place.column_x, place.x_width)  # (x > width) is while waiting to wrap
        x_west = from_x - column_x
        assert x_west >= 0, (x_west, from_x, column_x)

        assert CUB_X == "\033[" "{}" "D"
        leap = CUB_X.format(x_west) if x_west else ""

        return leap

        # todo0: larger leaps from arbitrary places such as a pasted ⎋[9;8R
        # todo: cope with a pasted ⎋[1;4R that comes while the Top Layer is on

    def is_writable_place_after_strs(self, text: str) -> bool:
        """Say if writing the Str keeps the Terminal Cursor inside the Writable Area"""

        base = self.base
        base_place = base.place

        assert base_place.is_writable_place(), (base_place,)

        fork_layer = base.fork_layer()
        fork_written = fork_layer._write_some_or_all_strs_(text)
        if not fork_written:
            return False

        fork_place = fork_layer.place
        if not fork_place.is_writable_place():
            return False

        return True

    # todo: change the Terminal Shadow when we write Controls we have named
    # todo: shadow the hide ⎋[⇧?25L and the show ⎋[⇧?25H of the Cursor, when a need for it comes
    # todo: stay fit to code some other game with different conventions


@dataclasses.dataclass(kw_only=True)  # todo: inconveniently large repr after many writes
class TerminalLayer:
    """Keep a copy of what we could write to a Terminal"""

    place: TerminalPlace  # where the Cursor, how big the Screen
    text_styles: tuple[str, ...]  # the Text Styles in force
    write_by_xy: dict[tuple[int, int], tuple[tuple[str, ...], str]]  # (texts, t) by (x, y)

    def __bool__(self) -> bool:
        truthy = bool(self.place)
        if not truthy:  # all falsey if .place falsey, vs maybe and maybe-not while .place truthy
            assert not self.text_styles, (self.text_styles,)
            assert not self.write_by_xy, (self.write_by_xy,)
        return truthy

    def clear_layer(self) -> None:
        """Drop every Write and Text Style, & change the Layer back to Falsey"""

        self.place = TerminalPlace(column_x=1, x_max=1, x_width=1, row_y=1, y_height=1)
        self.text_styles = ()
        self.write_by_xy.clear()

        assert not self, (self.place,)

    def is_writeable_area(self, /, area_width: int, area_height: int) -> bool:
        """Say if every Cell of the Area, to the East & South of here, may be written"""

        place = self.place

        assert _1_COLUMN_ == 1
        assert _1_ROW_ == 1

        assert area_width >= _1_COLUMN_, (area_width,)
        assert area_height >= _1_ROW_, (area_height,)

        far_x = place.column_x + (area_width - _1_COLUMN_)
        far_y = place.row_y + (area_height - _1_ROW_)
        far_place = dataclasses.replace(place, column_x=far_x, row_y=far_y)

        is_writeable = place.is_writable_place() and far_place.is_writable_place()
        return is_writeable

    def is_shadowed_area(self, /, area_width: int, area_height: int) -> bool:
        """Say if every Cell of the Area, from the Cursor east and south, has been written"""

        place = self.place
        write_by_xy = self.write_by_xy

        assert _1_COLUMN_ == 1
        assert _1_ROW_ == 1

        assert area_width >= _1_COLUMN_, (area_width,)
        assert area_height >= _1_ROW_, (area_height,)

        xy_pairs = list(
            (place.column_x + step_x, place.row_y + step_y)
            for step_y in range(area_height)
            for step_x in range(area_width)
        )

        all_written = all(xy in write_by_xy.keys() for xy in xy_pairs)
        return all_written

    def fork_layer(self) -> TerminalLayer:
        """Start a new Layer at the same Place, with the same Text Styles, with no Writes"""

        place = self.place
        text_styles = self.text_styles

        fork_place = dataclasses.replace(place)  # clones

        layer = TerminalLayer(
            place=fork_place,
            text_styles=text_styles,  # immutable
            write_by_xy=dict(),
        )

        return layer

    def _write_some_or_all_strs_(self, text: str) -> bool:
        """Write all the Str into this Layer and return True, or less than all and return False"""

        place = self.place
        text_styles = self.text_styles
        write_by_xy = self.write_by_xy

        assert place.is_onscreen_place(), (place,)
        fewer = TerminalLayer.text_styles_compress(text_styles)  # fewer or same
        assert text_styles == fewer, (text_styles, fewer)

        next_styles = text_styles  # immutable, replaceable
        for m in re.finditer(r"\033\[([0-9;?]*)([@-~])|(.)", text):
            params, final, t = m.groups()
            split = m.group(0)

            # Fail fast

            if not place.is_onscreen_place():
                return False

            # Shadow change of (or reaffirmation of) Text Styles

            assert NO_SGR_PS == "\033[" "m"
            assert REVERSE_SGR_PS7 == "\033[" "7m"

            if final == "m":
                assert params in ("", "7"), (params,)
                next_styles = TerminalLayer.text_styles_compress(next_styles + (split,))
                self.text_styles = next_styles
                continue

            # Shadow Y X Moves, to a new place (or to the same place)

            assert BS == "\b"
            assert CR == "\r"
            assert CUU_Y == "\033[" "{}" "A"
            assert CUD_Y == "\033[" "{}" "B"
            assert CUF_X == "\033[" "{}" "C"
            assert CUB_X == "\033[" "{}" "D"

            if (t in ("\b", "\r")) or (final in ("A", "B", "C", "D")):
                assert (not params) or params.isdigit(), (params,)  # copes with ⎋[A and ⎋[3A
                place.write_str_at_place(split)
                continue

            # Shadow the Insert of a Row at the Cursor, without moving the Cursor,
            # not even a Cursor waiting to wrap, as macOS Terminal does

            assert IL_Y.format("") == "\033[" "L"
            if final == "L":
                assert not params, (params,)  # copes with ⎋[⇧L but not yet ⎋[2⇧L
                self._row_insert_at_place_()
                continue

            # Shadow the Delete of the Row at the Cursor, without moving the Cursor,
            # not even a Cursor waiting to wrap, as macOS Terminal does

            assert DL_Y.format("") == "\033[" "M"
            if final == "M":
                assert not params, (params,)  # copes with ⎋[⇧M but not yet ⎋[1⇧M nor ⎋[2⇧M
                self._row_delete_at_place_()
                continue

            # Shadow Printable Text Writes placed in Writable Columns on-screen

            if t and t.isprintable():
                if not place.is_writable_place():
                    return False

                xy = (place.column_x, place.row_y)
                write_by_xy[xy] = (next_styles, t)  # replaces or adds  # different or same
                place.write_str_at_place(split)

                continue

            # Shadow no change for Hiding or Showing the Cursor, until we need to know if it hides

            assert HIDE_CUSR_RM_PSQ25 == "\033[" "?25l"
            assert SHOW_CUSR_SM_PSQ25 == "\033[" "?25h"

            if split in (HIDE_CUSR_RM_PSQ25, SHOW_CUSR_SM_PSQ25):
                continue

            # Freak when asked to shadow anything else

            assert False, (split,)

        # Fail even when it was the last Split that stepped off screen

        if not place.is_onscreen_place():
            return False

        # Succeed

        return True

    def _row_insert_at_place_(self) -> None:
        """Drop the last Row, move down the Rows at & below the Cursor, & fill the Cursor Row"""

        place = self.place
        write_by_xy = self.write_by_xy

        assert place.is_onscreen_place(), (place,)

        # Move down each Write at or below the Cursor Row, but drop each Write of the last Row

        write_by_xy_was = dict(write_by_xy)
        write_by_xy.clear()  # in place, since the Shadow holds this same dict

        for (x, y), write in write_by_xy_was.items():
            if y < place.row_y:  # stays, above the Cursor Row
                assert (x, y) not in write_by_xy.keys(), (x, y)
                write_by_xy[(x, y)] = write

            if place.row_y <= y < place.y_height:  # moves down
                assert (x, y + 1) not in write_by_xy.keys(), (x, y)
                write_by_xy[(x, y + 1)] = write

            # drops the Write, when in the last Row

        # Fill the Cursor Row with plain Spaces, Column W+1 too, even while ⎋[7M Reverse in force

        assert SP == " "

        plain_styles: tuple[str, ...] = ()  # as macOS Terminal paints it, after ⎋[M or ⎋[7M

        for x in range(1, place.x_width + 1):
            assert (x, place.row_y) not in write_by_xy.keys(), (x, place.row_y)
            write_by_xy[(x, place.row_y)] = (plain_styles, " ")

        # todo: fill with the Background Colour in force, as after ⎋[44M, when we shadow Colours

    def _row_delete_at_place_(self) -> None:
        """Drop the Cursor Row, move up the Rows below the Cursor, & fill the last Row"""

        place = self.place
        write_by_xy = self.write_by_xy

        assert place.is_onscreen_place(), (place,)

        # Move up each Write below the Cursor Row, but drop each Write of the Cursor Row

        write_by_xy_was = dict(write_by_xy)
        write_by_xy.clear()  # in place, since the Shadow holds this same dict

        for (x, y), write in write_by_xy_was.items():
            if y < place.row_y:  # stays, above the Cursor Row
                assert (x, y) not in write_by_xy.keys(), (x, y)
                write_by_xy[(x, y)] = write

            if place.row_y < y <= place.y_height:  # moves up
                assert (x, y - 1) not in write_by_xy.keys(), (x, y)
                write_by_xy[(x, y - 1)] = write

            # drops the Write, when in the Cursor Row

        # Fill the last Row with plain Spaces, Column W+1 too, even while ⎋[7M Reverse in force

        assert SP == " "

        plain_styles: tuple[str, ...] = ()  # as macOS Terminal paints it, after ⎋[M or ⎋[7M

        for x in range(1, place.x_width + 1):
            assert (x, place.y_height) not in write_by_xy.keys(), (x, place.y_height)
            write_by_xy[(x, place.y_height)] = (plain_styles, " ")

        # todo: fill with the Background Colour in force, as after ⎋[44M, when we shadow Colours

    @staticmethod
    def text_styles_compress(text_styles: tuple[str, ...]) -> tuple[str, ...]:
        """Drop the Text Style Writes cancelled by later Text Style Writes"""

        assert NO_SGR_PS == "\033[" "m"
        assert REVERSE_SGR_PS7 == "\033[" "7m"

        fewer_styles: list[str] = list()
        for text_style in text_styles:
            assert text_style in (NO_SGR_PS, REVERSE_SGR_PS7), (text_style,)

            if text_style == NO_SGR_PS:
                fewer_styles.clear()

            if text_style not in fewer_styles:
                fewer_styles.append(text_style)  # keep insertion order

        return tuple(fewer_styles)


@dataclasses.dataclass(order=True, kw_only=True)
class TerminalPlace:
    """Speak of where the Cursor is and how big the Screen is"""

    column_x: int  # the Cursor Column, at or away from x=1 in the far West
    x_max: int  # the Screen Columns we dare write, an even count, as if Column W+1 is not there
    x_width: int  # the Screen Columns, at least 1

    row_y: int  # the Cursor Row, at or away from y=1 in the far North
    y_height: int  # the Screen Rows, at least 1

    def __bool__(self) -> bool:
        """Say if the Place Width and Height are other than 1 and 1"""
        truthy = (self.x_width, self.y_height) != (1, 1)
        if not truthy:
            assert self.column_x == self.x_max == self.row_y == 1, (self,)
        return truthy

        # todo: think harder about how filling X Y in early can make __bool__ unavailable

    def write_str_at_place(self, text: str) -> None:
        """Shadow how writing this Str moves the Terminal Cursor"""

        if text.isprintable():
            assert len(text) == 1, (text,)
            self.column_x += 1
            return

            # todo0: cope with double-wide Chars
            # macOS Terminal moves across double-wide Chars
            # 2026/Nov Google Cloud Terminal moves halfway into double-wide Chars

        control = text

        if self.column_x > self.x_width:
            self.column_x = self.x_width  # doesn't wrap when control written

        assert BS == "\b"
        assert CR == "\r"
        assert CUU_Y.format("") == "\033[" "A"
        assert CUD_Y.format("") == "\033[" "B"
        assert CUF_X.format("") == "\033[" "C"
        assert CUB_X.format("") == "\033[" "D"

        xy_step_by_split = {
            "\b": (-1, 0),  # one step West
            "\r": (1 - self.column_x, 0),  # far West
            "\033[" "A": (0, -1),  # one step North
            "\033[" "B": (0, 1),  # one step South
            "\033[" "C": (1, 0),  # one step East
            "\033[" "D": (-1, 0),  # one step West
        }

        count = 1
        split_control = control

        csi = re.fullmatch(r"\033\[([0-9]*)([ABCD])", control)
        if csi:
            ps, final = csi.groups()
            if ps:

                count = int(ps)  # loosely accepts even '0010' as 10, etc
                assert count >= 1, (count, ps)
                split_control = "\033[" + final

        step_x, step_y = xy_step_by_split[split_control]

        self.column_x += count * step_x
        self.row_y += count * step_y

    def is_onscreen_place(self) -> bool:
        """Say if the Cursor sits on the Screen, or just past the right edge, waiting to wrap"""

        on_x = 1 <= self.column_x <= (self.x_width + 1)
        on_y = 1 <= self.row_y <= self.y_height
        return on_x and on_y

    def is_writable_place(self) -> bool:
        """Say if the Cursor sits where a Char may be written"""

        in_x = 1 <= self.column_x <= self.x_max
        in_y = 1 <= self.row_y <= self.y_height
        return in_x and in_y


#
# Read Bytes from a Terminal, place them into Frames, and say when each Byte arrived
#


@dataclasses.dataclass(order=True)
class TerminalFrameReader:
    """Read Bytes from a Terminal, place them into Frames, and say when each Byte arrived"""

    tb: TerminalBoss  # the Terminal we read from
    tft: TerminalFrameTaker  # the Frames taken so far, and the Open Frame
    nanobytes: list[tuple[int, bytes]]  # (Nanos waited, Byte read) for each Byte read

    def __init__(self, tb: TerminalBoss) -> None:

        self.tb = tb
        self.tft = TerminalFrameTaker(tb)
        self.nanobytes = list()

    def take_frames_and_yield_each(
        self, stalwarts: tuple[bytes, ...]
    ) -> typing.Iterator[tuple[bool, TerminalByteFrame, tuple[tuple[int, bytes], ...]]]:
        """Yield (False, Open Frame, Nanobytes) before taking, (True, Taken Frame, same) after"""

        tb = self.tb
        tft = self.tft
        nanobytes = self.nanobytes

        before = time.perf_counter_ns()  # doesn't measure time to launch

        # Yield first each Taken Frame left behind, by a Caller who quit before it

        yield from self._pull_frames_and_yield_each_()

        while True:

            # Yield the Open Frame before each Read, as a Frame not yet taken

            taken = False
            frame_nanobytes = tuple(nanobytes)  # copies, so no Caller changes ours
            frame_triple = (taken, tft.frame, frame_nanobytes)
            yield frame_triple

            # Block to fetch >= 1 Bytes

            sys.stdout.flush()  # flushes well-known outputs before blocking on well-known input
            sys.stderr.flush()

            had_typeahead = bool(tb.typeahead)  # before the read pops a Typeahead Byte
            data = tb.read_some_bytes_if()
            if not data:
                break  # quits at Stdin Eof

            after = time.perf_counter_ns()  # counts time-to-read Bytes as waiting for next Bytes
            waited = after - before
            before = after

            # Place each Byte into the first Frame or a later Frame, and mark how slowly it arrived

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

                tft.take_one_byte(b, peek=peek)

                # Close a typed ⎋[⇧M as Delete Row, since a Mouse Report comes whole in one burst

                assert _10_MEGA_NANOS_ == 10 * 10**6  # Mouse Report Bytes come closer, Keys slower
                is_slow_alone_without_typeahead = (
                    (not beyond) and (waited >= _10_MEGA_NANOS_) and (not had_typeahead)
                )
                if is_slow_alone_without_typeahead:
                    tft.tilt_open_frame_if()

                    # todo: a Mouse Report cut by a slow link, right after its ⇧M, reads as typed

                # Mark how slowly this Byte arrived

                nanobyte = (waited, b)
                nanobytes.append(nanobyte)
                waited = 0  # waited some ns only for the first Byte of these

            # Yield each Frame taken to place these Bytes

            yield from self._pull_frames_and_yield_each_()

            # Quit when the Frames say to quit

            if tft.is_quitting_frames(stalwarts=stalwarts):
                break

        # Take the Open Frame with the Frames taken before it, at Stdin Eof or at Quit

        tft.take_open_frame_else()  # if it holds Bytes
        yield from self._pull_frames_and_yield_each_()

    def _pull_frames_and_yield_each_(
        self,
    ) -> typing.Iterator[tuple[bool, TerminalByteFrame, tuple[tuple[int, bytes], ...]]]:
        """Yield (True, Taken Frame, Nanobytes) for each Frame taken since last called"""

        tft = self.tft
        nanobytes = self.nanobytes

        while True:

            # Pull one Frame at a time, lest a Caller who quits drop the Frames behind

            pulled = tft.pull_one_frame_triple_else()
            if not pulled:
                break

            frame, start, end, data = pulled
            assert data == frame.to_frame_bytes(), (data, frame)

            length = len(data)  # one nanobyte per Byte
            assert len(nanobytes) >= length, (len(nanobytes), length, data)

            frame_nanobytes = tuple(nanobytes[:length])  # copies, so no Caller changes ours
            del nanobytes[:length]

            taken = True
            frame_triple = (taken, frame, frame_nanobytes)
            yield frame_triple


#
# Take Frames out of the Bytes arriving, and track when each Byte arrived
#


@dataclasses.dataclass(order=True)
class TerminalFrameTaker:
    """Take Frames out of the Bytes arriving, and track when each Byte arrived"""

    tb: TerminalBoss  # the Terminal whose Input Keeper holds the Bytes, and when each arrived

    frame: TerminalByteFrame  # the Open Frame
    frames: list[TerminalByteFrame]  # the Taken Frames (closed, bounced, or cut at Quit)
    index: int  # how many pulled, of the Taken Frames

    def __init__(self, tb: TerminalBoss) -> None:

        self.tb = tb

        self.frame = TerminalByteFrame(b"")  # the first open Frame
        self.frames = list()
        self.index = 0

    def take_one_byte(self, b: bytes, peek: str) -> None:
        """Take 1 more Byte the Boss kept, and take each Frame as it closes or bounces"""

        assert len(b) == 1, (len(b), b)

        # Grow the Frame, or grow and take, or don't grow but do take, or shrink and take

        early_frame = self.frame  # before Extras bounced
        extras1 = self._frame_take_data_if_(b, peek=peek)  # .peek passes through

        if not extras1:
            return

        late_frame = self.frame  # after Extras bounced

        assert late_frame is not early_frame, (late_frame, early_frame)  # after Extras bounced
        assert not late_frame, (late_frame,)

        # Add enough more Frames to place all the Bytes

        extras2 = self._frame_take_data_if_(extras1, peek=peek)  # .peek passes through
        if extras2:

            extras3 = self._frame_take_data_if_(extras2, peek=peek)  # .peek passes through
            assert not extras3, (extras3,)

            # Three calls of ._frame_take_data_if_ are always enough,
            # because post-conditions at ._frame_take_data_if_ > .take_data_if > .take_one_byte_if

    def _frame_take_data_if_(self, data: bytes, peek: str) -> bytes:
        """Grow the Frame, replace it if it closes or bounces, and return any bounced Bytes"""

        frame = self.frame
        frames = self.frames

        assert not frame.closed, (frame,)

        # Grow the Open Frame, or grow it & close it, or leave it as it was and bounce

        extras = frame.take_data_if(data, peek=peek)  # .peek passes through

        # Take & replace the Frame if it closed as complete, or if it bounced while incomplete

        next_frame = frame  # left same, else replaced below
        if frame.closed or extras:
            frames.append(frame)

            next_frame = TerminalByteFrame(b"")  # empty and open
            self.frame = next_frame

        assert (not extras) or (not next_frame), (extras, next_frame)

        # Always leave an Open Frame, and sometimes an Empty Open Frame

        assert not next_frame.closed, (next_frame,)

        return extras

    def tilt_open_frame_if(self) -> None:
        """Take the Open Frame as a closed ⎋[⇧M Delete Row, if it was a bare ⎋[⇧M"""

        frame = self.frame
        frames = self.frames

        assert not frame.closed, (frame,)

        frame.tilt_to_close_frame()  # does nothing unless the Frame holds just ⎋[⇧M
        if not frame.closed:
            return

        frames.append(frame)

        next_frame = TerminalByteFrame(b"")  # empty and open
        self.frame = next_frame

    def take_open_frame_else(self) -> None:
        """Take the Open Frame as cut off, despite unclosed, if it holds Bytes, as at Quit"""

        frame = self.frame
        frames = self.frames

        assert not frame.closed, (frame,)

        data = frame.to_frame_bytes()
        if not data:
            return

        frames.append(frame)

        next_frame = TerminalByteFrame(b"")  # empty and open
        self.frame = next_frame

    def pull_one_frame_triple_else(self) -> tuple[TerminalByteFrame, int, int, bytes] | None:
        """Pull the oldest Taken Frame not yet pulled, with when its Bytes started and ended"""

        ibk = self.tb.ibk
        frame = self.frame
        frames = self.frames
        index = self.index

        ba = ibk.ba
        nano_list = ibk.nano_list

        # Pull the oldest of the Taken Frames not yet pulled, if any

        pulls = frames[index:]
        if not pulls:
            return None

        self.index = index + 1

        # Measure back from the end of the Bytes, to find where the oldest of them starts

        open_length = len(frame.to_frame_bytes())
        pulls_length = sum(len(_.to_frame_bytes()) for _ in pulls)
        start_index = len(ba) - open_length - pulls_length

        # Say when it started and ended

        pull = pulls[0]
        data = pull.to_frame_bytes()
        stop_index = start_index + len(data)

        indexed = bytes(ba[start_index:stop_index])
        assert indexed == data, (indexed, data, start_index, stop_index)

        start = nano_list[start_index]
        end = nano_list[stop_index - 1]

        triple = (pull, start, end, data)
        return triple

    def is_quitting_frames(self, stalwarts: tuple[bytes, ...]) -> bool:
        """Say if the Frames have said please quit soon, but never quit on a Stalwart"""

        ibk = self.tb.ibk
        frame = self.frame
        frames = self.frames

        ba = ibk.ba
        nano_list = ibk.nano_list

        # Hand down the last 4 Taken Frames, each with when its last Byte arrived

        open_data = frame.to_frame_bytes()
        stop = len(ba) - len(open_data)  # back past the Open Frame

        pairs_list = list()
        for taken in reversed(frames[-4:]):
            data = taken.to_frame_bytes()
            pair = (nano_list[stop - 1], data)
            pairs_list.append(pair)
            stop -= len(data)

        pairs = list(reversed(pairs_list))  # oldest first, as for Bytes

        # Quit on three same Frames taken

        if is_quitting_shape(pairs):
            if frames[-1].encodes:  # no quitting on repeated Text Frames
                return False

            if frames[-1].to_frame_bytes() in stalwarts:
                return False  # never quits on a Stalwart

            return True

        # Else quit on two same Frames taken and then the same Frame still open, such as ⎋[ ⎋[ ⎋[

        if open_data:
            open_pair = (nano_list[-1], open_data)
            if is_quitting_shape(pairs[-3:] + [open_pair]):
                if frame.encodes:  # no quitting on repeated Text Frames
                    return False

                return True

        return False

        # todo: quit over ⇧Z ⇧Z in a Vim Workalike, not over three Unprintables
        # todo: fix how a ⏎ within 100 ms of the Y X H W Replies needs a 4th ⏎ to quit


#
# Decode the Bytes of a TerminalByteFrame as carrying a Payload of Int's
#


@dataclasses.dataclass(order=True)
class TerminalFrameDecoder:
    """Decode a Frame as the Reply to a DSR6 or XTWINOPS_18 Ask"""

    @staticmethod
    def bytes_to_yx_or_hw_reply_else(data: bytes) -> tuple[str, int, int] | None:
        """Pick ("YX", Y, X) from a CPR Reply, or ("HW", H, W) from an XTWINOPS_8 Reply, else None"""

        assert CPR_Y_X == "\033[" "{};{}R"  # [ CPR ⇧R Reply to DSR6 N Ask ]
        assert XTWINOPS_8_H_W == "\033[" "8;{};{}" "t"  # [ Reply T Ps 8 to T Ps 18 Ask ]

        decode = data.decode(errors="replace")

        for tag, template in [("YX", CPR_Y_X), ("HW", XTWINOPS_8_H_W)]:
            m = re.fullmatch(TerminalFrameDecoder._whxy_pattern_(template), string=decode)
            if m:
                i1 = int(m.group(1))  # discards leading "0", beyond ECMA specs
                i2 = int(m.group(2))  # (same)

                assert i1 >= 1, (i1, decode)
                assert i2 >= 1, (i2, decode)

                return (tag, i1, i2)

        return None

    @staticmethod
    def _whxy_pattern_(template: str) -> str:
        """Convert to Regex of two Nonnegative Ints, such as XTWINOPS_8_H_W or CPR_Y_X"""

        pattern = re.escape(template).replace(re.escape("{}"), "([0-9]+)")
        return pattern


#
# Frame Bytes of Terminal Input as alone, or as catenated Printable Text, or as Esc Frame
#


_ = r"""

In the leftmost Column are the Bytes in the Frame, from before you offered one more.

The Frames ending with '+' were still open, the others were already closed.

The ⎋[⇧M + Row stays open for its {b}{x}{y} when its ⇧M comes in a burst, but closes as ⎋[⇧M Delete
Row when its ⇧M comes alone and slowly, as typed, and never when Typeahead waits.

    Frame     \a      ⇥       ⎋       ;       A       ́       €       \xff

    '' +      close   close   open    open    open    open    open    close

    'ab' +    bounce  bounce  bounce  open    open    open    open    bounce

    ⎋ +       close   close   open    close   close   close   close   bounce
    ⎋⎋ +      close   close   bounce  close   close   close   close   bounce
    ⎋O +      close   close   bounce  close   close   close   close   bounce
    ⎋[⇧M +    open    open    open    open    open    open    close6  open
    ⎋[⇧M␢/ +  close6  close6  close6  close6  close6  close6  close6  close6

    ⎋[ +      bounce  bounce  bounce  open    close   close   close   bounce
    ⎋[1;5 +   bounce  bounce  bounce  open    close   close   close   bounce
    ⎋[␢ +     bounce  bounce  bounce  bounce  close   close   close   bounce

    ⎋] +      close   bounce  open    open    open    open    open    bounce
    ⎋]0;x +   close   bounce  open    open    open    open    open    bounce
    ⎋]0;x⎋ +  bounce2 bounce2 bounce2 bounce2 bounce2 bounce2 bounce2 bounce2

    ⎋j        bounce  bounce  bounce  bounce  bounce  bounce  bounce  bounce
    ⎋Oj       bounce  bounce  bounce  bounce  bounce  bounce  bounce  bounce
    ⎋[⇧A      bounce  bounce  bounce  bounce  bounce  bounce  bounce  bounce
    ⎋⇥        bounce  bounce  bounce  bounce  bounce  bounce  bounce  bounce

As you feed Byte after Byte into a Terminal Byte Frame, it must decide when to:

i ) Open = Take the Byte and keep the Frame open
ii ) Bounce = Reject the Byte and leave the Frame unchanged
iii ) Close = Take the Byte and close the Frame
iv ) Close6 = Take the 6 Bytes and bounce anything after (at ⎋[⇧M legacy)
v ) Bounce2 = Reject the Byte and give back the held ⎋ with it (at ⎋] awaiting the \ of ⎋\)

Given a Peek at a Combining Mark already fetched in the same burst of Bytes, as ⌥E J sends,
a Printable Char opens rather than closes the ⎋ ⎋⎋ ⎋O ⎋[ ⎋[1;5 ⎋[␢ Rows, and the Mark then closes.

Relevant standards include:

    ECMA-35_6th_edition_december_1994.pdf
    ECMA-48_5th_edition_june_1991.pdf

However the public standards only clearly solve 7-bit Bytes.

We solve 8-bit Bytes reasonably well. We tell every Open Frame to accept the 1..4 Bytes
of any Printable Text Char, except that our Open ⎋[⇧M Frames only take 1..3 Bytes, and
our Open ⎋] Osc Frames can bounce 1..5 Bytes because they only take Reverse-Solidus \ after Esc ⎋.

The b'\a' Bel is as special as String Terminator (ST) for ⎋] an Operating System Command (Osc).
The b'\033' ⎋ Esc is special after just one of itself.

The \a ⇥ ⎋ \xff are not printable, the ; A  ́ € are printable.
The € is a printable encoded as 3 Bytes, vs the ; A  ́ are printable encoded as 1 or 2 bytes.

The ; is a Parameter Byte of ⎋[ Control Sequence Introducer (CSI).
The ␢ is an Intermediate Byte of ⎋[ CSI, expected before A is an example Final Byte.
The  ́ is a Combining Mark Character that can merge back into the Printable before it.

The \xff is an example of Undecodable UTF-8.

"""


@dataclasses.dataclass(order=True)
class TerminalByteFrame:
    """Frame Bytes of Terminal Input as alone, or as catenated Printable Text, or as Esc Frame"""

    encodes: bytearray  # b''  # Decodable Printable Text

    head: bytearray  # b''  # N * ESC  # N * ESC + CSI  # N * ESC + SS3  # OSC
    neck: bytearray  # b''  # Csi Params  # Osc Payload
    backtail: bytearray  # b''  # Csi Intermediates and Final  # Osc Terminator  # Esc or Ss3 Char

    stash: bytearray  # b''  # 1..3 Bytes taken while not printable

    closed: bool  # False while open, True while closed till reopened

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

    def tilt_to_close_frame(self) -> None:
        """Transform into a Closed DL_Y without explicit Pn, if it was _CLICK3_ and no Stash"""

        encodes = self.encodes
        head = self.head
        neck = self.neck
        backtail = self.backtail
        stash = self.stash
        closed = self.closed

        assert _CLICK3_ == "\033[M"
        assert DL_Y == "\033[" "{}" "M"
        assert DL_Y.format("") == _CLICK3_

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

            i_peek = peek if (not beyond) else ""  # blocks the .peek except just after last Byte

            extras = self.take_one_byte_if(b, peek=i_peek)
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

        assert ESC == "\033"

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

        assert ESC == "\033"
        assert SS3 == "\033O"

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

        # todo: develop ⎋[⇧?1005H Mouse Strokes coming in as 6 Char UTF-8 ⎋[⇧M{bord}{xord}{yord}
        # todo: develop ⎋[⇧?1006H Mouse Strokes coming in as US ASCII ⎋[⇧<{b};{x};{y}⇧M and then ...M
        # todo: develop ⎋[⇧?1015H Mouse Strokes coming in as US ASCII ⎋[{32+b};{x};{y}⇧M
        # todo: develop ⌥ Mouse Strokes coming in as a burst of Arrows, with no Mouse mode on
        # todo: read the ⌃ ⌥ ⇧ of a Mouse Stroke out of its {b}, as f = 0b⌃⌥⇧00

        # todo: do cope when Press & Release come in one burst, not much separated in time

        # todo: write ⎋[⇧?1006H beside each ⎋[⇧?1000H that a Program writes through us
        # todo: measure if ⎋[⇧M Strokes still come while ⎋[⇧?1006H is on, away from macOS Terminal
        # todo: measure the Mouse Strokes of the Wheel, of a Drag, and of the other Buttons

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
        assert ST == ("\033" + "\134")

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

        # todo: compare To-Later-Decode-If vs Python 3 encodings.utf_8.IncrementalDecoder

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
    # "\ud800" .. "\udfff"  # rejected as b"\xed\xa0\x80" .. b"\xed\xbf\xbf" surrogates
    # "\ue000"  # b"\xee\x80\x80" accepted
    # "\uffff"  # b"\xef\xbf\xbf" accepted
    #
    # "\U00010000"  # b"\xf0\x90\x80\x80" accepted with "\xf0\xbf\xbf\xbf"
    # "\U0010ffff"  # b"\xf4\x8f\xbf\xbf" accepted with "\xf4\x80\x80\x80"
    #

    # known: invent UTF-8'ish Encoding beyond 1..4 Bytes for Unicode Codes > 0x10_FFFF ?


StartBytes = tuple(bytes([_]) for _ in range(0xC2, 0xF4 + 1))  # what UTF-8 completes


#
# Wrap one Terminal
#


@dataclasses.dataclass
class TerminalBoss:
    """Wrap one Terminal"""

    stdio: io.TextIOWrapper
    isatty: bool
    fileno: int  # often 2 == sys.__stderr__.fileno()
    tcgetattr: list[int | list[bytes | int]]  # replaced by .__exit__ and .__enter__

    typeahead: bytearray  # Bytes to arrive slowly, in between >= 0 other Bytes arriving early
    farewell_bytes: bytes  # written at .__exit__, such as to revert Cursor Style

    ibk: ByteKeeper  # every Byte read, and when
    obk: ByteKeeper  # every Byte written, Asks too, and when
    typescript: bytearray  # every Byte written, but none of the Asks

    def __init__(self, typeahead: bytes, farewell_bytes: bytes) -> None:

        assert sys.__stdin__, (sys.__stdin__,)
        stdio = sys.__stdin__  # todo: /dev/stderr, /dev/tty
        isatty = stdio.isatty()
        fileno = stdio.fileno()

        self.stdio = stdio
        self.isatty = isatty
        self.fileno = fileno
        self.tcgetattr = list()

        self.typeahead = bytearray(typeahead)
        self.farewell_bytes = farewell_bytes

        self.ibk = ByteKeeper()
        self.obk = ByteKeeper()
        self.typescript = bytearray()

    def __enter__(self) -> TerminalBoss:
        r"""Pause line-buffering Input, pause taking \n Output as \r\n, etc"""

        isatty = self.isatty
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        farewell_bytes = self.farewell_bytes

        if tcgetattr:  # enters at most once, to make truthy
            return self

        # Flush writes to the Terminal

        sys.stdout.flush()
        sys.stderr.flush()

        # Enter with an imitation of a truthy termios.tcgetattr(fileno), when not a tty

        if not isatty:
            self.tcgetattr = [20261010]  # arbitrary 20261010
            return self

        # Back up Input Mode before, drain Input, & choose Input Mode after

        attr = termios.tcgetattr(fileno)
        assert attr, (attr,)

        self.tcgetattr = attr  # replaces falsey with truthy

        if farewell_bytes:
            tty.setcbreak(fileno, when=termios.TCSADRAIN)  # ⌃C ⌃Z ⌃\ as Signals, ⌃D as Input
        else:
            tty.setraw(fileno, when=termios.TCSADRAIN)  # ⌃C ⌃D ⌃Z ⌃\ as Input, not as Signals

        # Succeed

        return self

        # also pauses Return Key meaning ⌃J b'\n', switches to ⌃M b'\r', except for a farewell

        # chose termios.TCSADRAIN over termios.TCSAFLUSH, per specs.md § 1

    def tty_setraw_before_farewell(self) -> None:
        r"""Stop taking ⌃C ⌃Z ⌃\ as signals, and take each Return Key as ⌃M b'\r' not ⌃J b'\n'"""

        isatty = self.isatty
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        farewell_bytes = self.farewell_bytes

        if isatty:
            assert tcgetattr and farewell_bytes, (tcgetattr, farewell_bytes, isatty)
            tty.setraw(fileno, when=termios.TCSADRAIN)  # ⌃C ⌃D ⌃Z ⌃\ are Input, not Signal

            # caller may call .tty_setraw_before_farewell more than once, or not at all, oh well

        # ⌃D b"\004" is Input, not Signal, both after tty.setcbreak and after tty.setraw

    def __exit__(self, *exc_info: object) -> None:
        r"""Resume line-buffering Input, resume taking \n Output as \r\n, etc"""

        isatty = self.isatty
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        farewell_bytes = self.farewell_bytes

        if not tcgetattr:  # exits at most once, to make falsey
            return

        # Flush writes to the Terminal, and say farewell

        sys.stdout.flush()
        sys.stderr.flush()

        if farewell_bytes:
            self.bytes_write_flush(farewell_bytes)

        # Drain Input, restore Input Mode, & clear Input Mode backup

        fd = fileno
        when = termios.TCSADRAIN
        attributes = tcgetattr  # truthy here too
        if isatty:
            termios.tcsetattr(fd, when, attributes)

        self.tcgetattr = list()  # replaces truthy with falsey

        # also resumes Return Key meaning ⌃J b'\n', switches from ⌃M b'\r'

        # chose termios.TCSADRAIN here too

    def stdio_select_select(self, timeout: float | None) -> bool:
        """Block till next Input Byte, else till Timeout, else till forever"""

        fileno = self.fileno
        typeahead = self.typeahead

        assert self.tcgetattr, (self.tcgetattr,)

        assert _150_MEGA_NANOS_ == 150 * 10**6  # keys typed ahead, about as fast as a typist's

        rwx_timeout_else = timeout
        if typeahead:  # typeahead delay can be (timeout + 150e-3) or (2 * 150e-3), if timeout
            rwx_timeout_else = 150e-3 if (timeout is None) else min(150e-3, timeout)

            # delivering total delay of only 150e-3 would add a mutable, so never mind

        r, w, x = select.select([fileno], [], [], rwx_timeout_else)
        hit = bool((fileno in r) or typeahead)

        return hit

        # a la msvcrt.kbhit

    def read_some_bytes_if(self) -> bytes:
        """Read as many Bytes as arrived all at once, keep them with one Nanos, else return b''"""

        ibk = self.ibk
        typeahead = self.typeahead

        ba = bytearray()

        while True:

            # Read one Byte, else quit at End-of-Input

            b = self._read_one_byte_if_()
            if not b:
                break

            ba.extend(b)

            # Quit after 1 Typeahead Byte arrives alone, or if no more Bytes have arrived for real

            if typeahead or (not self.stdio_select_select(timeout=0e0)):
                break

        data = bytes(ba)
        nano = time.perf_counter_ns()
        ibk.append_some_bytes(data, nano=nano)  # keeps Input, or b'' at End-of-Input

        return data  # b'j\xcc\x81' from ⌥E J, or a whole ⌘V Paste, or one Byte, or b''

    def read_one_byte_if(self) -> bytes:
        """Read one byte and keep it in the Input, else return b''"""

        ibk = self.ibk

        b = self._read_one_byte_if_()
        nano = time.perf_counter_ns()
        ibk.append_some_bytes(b, nano=nano)  # keeps Input, or b'' at End-of-Input

        return b

    def _read_one_byte_if_(self) -> bytes:
        """Read one byte and return it, else return b'', and keep nothing"""

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
        typeahead = self.typeahead

        # Let the Terminal speak first, else take the next Byte typed ahead

        assert _150_MEGA_NANOS_ == 150 * 10**6  # keys typed ahead, about as fast as a typist's

        if typeahead:
            r, w, x = select.select([fileno], [], [], _150_MEGA_NANOS_ / 1e9)
            if not r:
                b = bytes([typeahead.pop(0)])
                return b

        fd = fileno
        length = 1
        b = os.read(fd, length)

        if not b:  # b == b'' only from input stream closed by macOS
            raise OSError(errno.EIO, os.strerror(errno.EIO))  # as Linux does for b''

        assert len(b) == 1, (b,)
        return b

    def str_print(self, text: str) -> None:
        """Print Text and end its Line, and keep their Bytes in the Output and the Typescript"""

        tcgetattr = self.tcgetattr
        end = "\r\n" if tcgetattr else "\n"  # raw end-of-line, else cooked end-of-line

        self.str_write(f"{text}{end}")

    def str_write(self, text: str) -> None:
        """Print Text with no Newline, and keep its Bytes in the Output and the Typescript"""

        obk = self.obk
        typescript = self.typescript

        encode = text.encode(sys.stdout.encoding, errors=(sys.stdout.errors or "strict"))
        nano = time.perf_counter_ns()

        print(text, end="")
        obk.append_some_bytes(encode, nano=nano)
        typescript.extend(encode)

        # doesn't encode to UTF-8 always  # todo: revisit writing tty output to sys.stdout

    def bytes_write_flush(self, data: bytes) -> None:
        """Write and Flush Bytes, and keep them in the Output and the Typescript"""

        obk = self.obk
        typescript = self.typescript

        nano = time.perf_counter_ns()
        self._bytes_write_flush_(data)
        obk.append_some_bytes(data, nano=nano)
        typescript.extend(data)

    def asks_write_flush(self, data: bytes) -> None:
        """Write and Flush Asks, and keep them in the Output only, not in the Typescript"""

        obk = self.obk

        nano = time.perf_counter_ns()
        self._bytes_write_flush_(data)
        obk.append_some_bytes(data, nano=nano)

        # doesn't replay Asks through Typescript, because that would inject fresh Answers

    def _bytes_write_flush_(self, data: bytes) -> None:
        """Write and Flush Bytes, and keep nothing"""

        sys.stdout.flush()
        sys.stdout.buffer.write(data)  # .buffer.write new since Dec/2008 Python 3.0
        sys.stdout.flush()

    def typescript_write_file(self, path: str) -> None:
        """Write the Bytes of the Typescript, unchanged, into a file"""

        typescript = self.typescript

        with open(path, "wb") as f:
            f.write(typescript)


#
# Collect Bytes and track when they arrived
#


@dataclasses.dataclass(order=True)
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

    def append_some_bytes(self, data: bytes, nano: int) -> None:
        """Say these Bytes all arrived at once, and when"""

        for code in data:
            b = bytes([code])
            self.append_one_byte(b, nano=nano)

    def is_quitting_bytes(self) -> bool:
        """Say if the Bytes have said please quit soon"""

        ba = self.ba
        nano_list = self.nano_list

        firsts = range(max(0, len(ba) - 4), len(ba))
        pairs = list((nano_list[i], bytes(ba[i : i + 1])) for i in firsts)

        if is_quitting_shape(pairs):
            if ord(" ") <= ba[-1] <= ord("~"):  # US Ascii Printable, and not \t \n \r etc
                return False

            return True

        return False

    def pairs_write_file(self, path: str, zero_nano: int) -> None:
        """Write a Header Line, then one [Nanos, Byte] Line per Byte, as Json Lines into a file"""

        ba = self.ba
        nano_list = self.nano_list

        assert len(ba) == len(nano_list), (len(ba), len(nano_list))

        # Count the Nanos from the zero given, and never write a negative Nanos

        lines: list[str] = list()
        lines.append(json.dumps(["Nanos", "Bytes"]))
        for nano, code in zip(nano_list, ba):
            assert nano >= zero_nano, (nano, zero_nano)

            line = json.dumps([nano - zero_nano, code])  # the Byte as an Int
            lines.append(line)

        join = "".join(f"{_}\n" for _ in lines)
        with open(path, "w") as f:
            f.write(join)


def is_quitting_shape(pairs: typing.Sequence[tuple[int, bytes]]) -> bool:
    """Quits when given same Bytes, 3 times in a row, but >= 100ms apart, across < 3s"""

    nano = time.perf_counter_ns()

    nl = list(n for (n, _) in pairs)  # when the last Byte of each arrived
    data_list = list(data for (_, data) in pairs)

    last3 = data_list[-3:]
    if not last3:
        return False

    if last3 != (3 * last3[-1:]):  # three in a row
        return False

    age = nano - nl[-3]
    early_gaps = (nl[-3] - nl[-4],) if (len(nl) > 3) else ()
    late_gaps = (nl[-2] - nl[-3], nl[-1] - nl[-2])

    if age >= _3_GIGA_NANOS_:  # as a burst, not just now and then
        return False

    if min(early_gaps + late_gaps) < _100_MEGA_NANOS_:  # held, or pasted
        return False

    return True


#
# Name the more basic Terminal Encodings
#


BEL = "\007"  # 00/07 Bell \a ␇ ⍾
BS = "\010"  # 00/08 Backspace \b ␈
LF = "\012"  # 00/10 Line Feed \n ␊ ⏎
CR = "\015"  # 00/13 Carriage Return \r ␍ ⏎
ESC = "\033"  # 01/11 Escape ␛ ⎋  # \e outside of Python
SP = "\040"  # 02/00 Space ' ' ␢
# DEL = "\177"  # 07/15 Delete ␡ ⌫


SS3 = "\033O"  # 01/11 04/15 Single Shift Three  # ⎋O
CSI = "\033["  # 01/11 05/11 Control Sequence Introducer  # ⎋[
OSC = "\033]"  # 01/11 05/13 Operating System Command  # ⎋]

ST = "\033\134"  # 01/11 05/12 String Terminator  # ⎋\


X1 = 1  # min X of Terminal Cursor
Y1 = 1  # min Y of Terminal Cursor


PS0 = 0  # default CSI Ps = 0 for some

PN1 = 1  # default CSI Pn = 1 for others
_MAX_PN_32100_ = 32100  # max CSI Pn = 32100 exceeds the .x_wide .y_high of most Terminal Screens


DECIC_X = "\033[" "{}" "'}}"  # CSI 07/13 [DEC] Insert Column [Pn]
DECDC_X = "\033[" "{}" "'~"  # CSI 07/14 [DEC] Delete Column [Pn]

ICH_X = "\033[" "{}" "@"  # CSI 04/00 [Insert] Cursor Horizontal [Pn] [Columns]
CUU_Y = "\033[" "{}" "A"  # CSI 04/01 Cursor Up [Pn] [Rows]
CUD_Y = "\033[" "{}" "B"  # CSI 04/02 Cursor Down [Pn] [Rows]
CUF_X = "\033[" "{}" "C"  # CSI 04/03 Cursor Forward [Pn] [Columns]
CUB_X = "\033[" "{}" "D"  # CSI 04/04 Cursor Backward [Pn] [Columns]
CUP_Y_X = "\033[" "{};{}H"  # CSI 04/08 [Choose] Cursor Position [Y and X]
ED_PS = "\033[" "{}" "J"  # CSI 04/10 Erase in Display  # 0 Tail # 1 Head # 2 Rows # 3 Scrollback
EL_PS = "\033[" "{}" "K"  # CSI 04/11 Erase in Line [Row]  # 0 Tail # 1 Head # 2 Row
IL_Y = "\033[" "{}" "L"  # CSI 04/12 Insert Line [Row]
_CLICK3_ = "\033[M"  # ⎋[⇧M{b}{x}{y} Click Press/ Release  # collides with ⎋[⇧M DL_Y
DL_Y = "\033[" "{}" "M"  # CSI 04/13 Delete Line [Row]
DCH_X = "\033[" "{}" "P"  # CSI 05/00 [Delete] Cursor Horizontal [Pn] [Columns]
SU_Y = "\033[" "{}S"  # CSI 05/03 Scroll Up [Into Scrollback]

_START_PASTE_ = "\033[" "200~"  # ⎋[200⇧~ Start of Bracketed Paste
_END_PASTE_ = "\033[" "201~"  # ⎋[201⇧~ End of Bracketed Paste

VPA_Y = "\033[" "{}" "d"  # CSI 06/04 Vertical Position Absolute [Row]

SM_PS = "\033[" "{}" "h"  # CSI 06/08 4 Set Mode
RM_PS = "\033[" "{}" "l"  # CSI 06/12 4 Reset Mode
SHOW_CUSR_SM_PSQ25 = "\033[" "?25h"  # SM_PS 25 to Show Cursor
HIDE_CUSR_RM_PSQ25 = "\033[" "?25l"  # RM_PS 25 to Hide Cursor

SGR_PS = "\033[" "{}" "m"  # CSI 06/13 Select Graphic Rendition [Text Style]
NO_SGR_PS = "\033[" "m"  # SGR Ps None for Plain
REVERSE_SGR_PS7 = "\033[" "7m"  # SGR_PS 7 for Reverse/Inverse Video
# UNREVERSE_SGR_PS27 = "\033[" "27m"  # SGR_PS 27 to undo SGR_PS 7


DSR_PS = "\033[" "{}n"  # CSI 06/14 Ask for 'Device Status Report' Ps

DSR0 = "\033[" "0n"  # DSR_PS [ Reply N Ps 0 to N Ps 5 Ask ]
DSR5 = "\033[" "5n"  # DSR_PS [ N Ps 5 Ask for Reply N Ps 0 ]

DSR6 = "\033[" "6n"  # DSR_PS [ N Ps 6 Ask for Reply CPR ⇧R ]
CPR_Y_X = "\033[" "{};{}R"  # ⎋[y;x⇧R  # CSI 05/02 [ CPR ⇧R Reply to DSR6 N Ask ]


# DECSCUSR_PS = "\033[" "{}" " q"  # CSI 06/15 [DEC] Set Cursor Style [Ps]  # Two Byte Backtail
# SKID_DECSCUSR_PS4 = "\033[" "4" " q"  # DECSCUSR_PS Ps 4 for steady Skid Mark
# NO_DECSCUSR_PS = "\033[" " q"  # DECSCUSR_PS Ps 0 to revert to default Cursor Style


XTWINOPS = "\033[" "{}" "t"  # CSI 07/04
XTWINOPS_18 = "\033[" "18" "t"  # XTWINOPS [ T Ps 18 Ask for Reply T Ps 8 ]
XTWINOPS_8_H_W = "\033[" "8;{};{}" "t"  # ⎋[8;h;wT  # XTWINOPS [ Reply T Ps 8 to T Ps 18 Ask ]


# ← ↑ → ↓ and ↖ ↗ ↘ ↙ are sorted by Codepoint

_NorthArrow_ = "\033[A"  # ↑ ↓ → ← NSEW is the → ↑ ← ↓ ENWS sorted by Byte Frame
_SouthArrow_ = "\033[B"
_EastArrow_ = "\033[C"
_WestArrow_ = "\033[D"

_CARDINAL_ENWS_ARROWS_ = (  # → ↑ ← ↓ ENWS is counterclockwise from East
    _EastArrow_,  # C →
    _NorthArrow_,  # A ↑
    _WestArrow_,  # D ←
    _SouthArrow_,  # B ↓
)

# _NortheastArrow_ = "\033[↗"  # ↗ ↖ ↙ ↘ is counterclockwise from Northeast
# _NorthwestArrow_ = "\033[↖"  # not yet standard Byte Frames
# _SouthwestArrow_ = "\033[↙"
# _SoutheastArrow_ = "\033[↘"


_ = _START_PASTE_, _END_PASTE_


AppleLogo = "\uf8ff"  # Apple Logo occupies U+F8FF = end of U+E000 .. U+F8FF Private Use Area (PUA)
_ = AppleLogo
# known: every mention of  in Source makes Code Patches difficult to send across platforms


#
# Amp up Import BuiltIns
#


def bytes_repr(data: bytes) -> str:
    """Repr the Bytes, but with Octal not Upper/Lower Hex as the escape for Unprintables"""

    quoted_repr = repr(data)
    sub = _quoted_repr_hex_to_octal_(quoted_repr)

    return sub

    # b'\342\202\254' for the "€".encode() that PyPi Black spells as b"\xe2\x82\xac"


def str_repr(s: str) -> str:
    """Repr the Str, but with Octal not Upper/Lower Hex as the escape for Unprintables"""

    quoted_repr = repr(s)
    sub = _quoted_repr_hex_to_octal_(quoted_repr)

    return sub

    # '\033[A' for the ↑ that PyPi Black spells as "\x1b[A"
    # '\ufeff' unchanged, no Octal form


def _quoted_repr_hex_to_octal_(text: str) -> str:
    """Rewrite each \\x Escape of a Repr as a 3-Digit Octal Escape, and leave the rest alone"""

    def repl(m: re.Match[str]) -> str:

        escape = m.group(0)
        if escape.startswith("\\x"):
            nybbles = escape.removeprefix("\\x")

            d = int(nybbles, 0x10)
            octal_escape = f"\\{d:03o}"  # 3 Digits always, else r'\7' + '1' would read as r'\71'

            return octal_escape

            # r'\xe2' -> r'\342'  # r'\x07' -> r'\007'

        return escape

        # r'\n' r'\\' r"\'" r'\u2028' r'\U0001f600' unchanged

    sub = re.sub(r"\\(x..|u....|U........|.)", repl=repl, string=text)

    return sub


#
# Amp up Import Decimal
#


def decimal_int_chop_to_eng_metric(n: int, one: str) -> str:
    """Convert 9876 to '9.87µs' when one == '1ns', and so on"""

    # Pick apart exactly how to style an 'n' of 1

    si_quanta = tuple("qryzafpnµm") + ("",) + tuple("kMGTPEZYRQ")  # the SI Prefixes since Nov/2022

    if not one.startswith("1"):
        numeral, quantum, unit = ("1", "", one)  # from one == 'Pa'  # from one == 'mol'
    else:
        numeral, quantum, unit = (one[0], "", one[1:])  # from one == '1'  # from one == '1Ω'
        if one[2:]:
            numeral, quantum, unit = (one[0], one[1], one[2:])  # from one == '1nH'
            if one[1] not in si_quanta:
                numeral, quantum, unit = (one[0], "", one[1:])  # from one == '1Hz'

        # one == "Pa" counts 1 "Pa"  # "mol" counts 1 "mol"  # "min" counts 1 "min"
        # one == "1kPa" counts 10**3 of "Pa"  # "1kmol" counts 10**3 "mol"  # "1kmin" 10**3 "min"
        # one="1Pa" counts 10**15 of "a"  # one="1mol" counts 10**-3 "ol"  # "1min" 10**-3 "in"

    assert numeral == "1", (numeral, quantum, unit, one)
    quantum_index = si_quanta.index(quantum)
    quanta = si_quanta[quantum_index:]

    # Clip the 'n' value

    chop = decimal_int_chop_to_eng(n)  # raises ValueError when a Float breaks our ': int' contract

    before, sep, after = chop.partition("e")
    assert bool(sep) == bool(after), (sep, after, before, chop, n)

    # Restyle the clipped 'n' value

    i = 0
    if sep:
        exp = int(after)
        assert (exp % 3) == 0, (exp, before, sep, after, chop, n)
        i = exp // 3
        assert i >= 1, (i, exp, before, sep, after, chop, n)

    q = quanta[i]  # (q) may be Empty Str
    rep = before + q + unit  # (q + unit) may be Empty Str

    # Succeed

    return rep  # '0Ω'  # '12ns'  # '9.87µH'  # '654ms'  # '33kPa'

    # 'def decimal_int_chop_to_eng_metric' last modified for py2def.py on 2026-11-08 or later


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


# todo: grow into a Python Module we could imagine adding alongside 'import tty'


# 3456789_123456789_123456789_123456789 123456789_123456789_123456789_123456789 123456789_123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/pylitglass/litpyglass.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
