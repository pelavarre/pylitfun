#!/usr/bin/env python3

r"""
usage: sqaxels.py [--typeahead=BYTES]

draw Square Pixels of two Spaces side by side, and keep the drawing in io.typescript

options:
  --typeahead BYTES  read these Bytes as typed ahead, each after 150ms of Terminal silence

quirks:
  quits when given an unprintable, 3 times in a row, but 100ms or more apart, across less than 3s
  never quits on an arrow key, since it moves the cursor instead
  never quits on a Space, which toggles the Pixel at the Cursor between Reverse and Plain
  never quits on ⎋[⇧L, which inserts a Row at the Cursor
  replays io.typescript from where the Cursor starts, and rewrites io.typescript at quit

examples:
  python3 pylitglass/sqaxels.py  # show these examples
  chmod +x pylitglass/sqaxels.py
  pylitglass/sqaxels.py --  # draw with the → ↑ ← ↓ Keys and the Space Key
  pylitglass/sqaxels.py --typeahead="$(printf ' \033[C \r\r\r')"  # draw two Pixels and quit
"""

# ⚠️ ↓↓↓ Below written by Claude·Ai, reviewed by almost no living people


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import dataclasses
import os
import sys
import textwrap

import litpyglass  # beside this file

_: object  # blocks Mypy from narrowing the Datatype of '_ =' at first mention

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


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

    # Draw, else freak

    xxta = "--typeahead="
    typeaheads = list(_.removeprefix(xxta) for _ in shargv if _.startswith(xxta))
    typeahead = os.fsencode("".join(typeaheads))  # todo: tighter parsing of .shargv

    strays = list(_ for _ in shargv if (_ != "--") and not _.startswith(xxta))
    if strays:
        assert False, (shargv,)  # not in: --, --typeahead=BYTES

    sw = SqaxelsWorker()
    tb = sw.show_sqaxels(typeahead=typeahead)

    tb.str_print("")


def _main_doc_scrape_closing_() -> str:
    """Scrape out the last Graf of Main Doc, minus its header"""

    doc = __doc__ or ""  # pylance fears __doc__ is None
    header = "examples:\n"
    index = doc.index(header) + len(header)
    closing = textwrap.dedent(doc[index:]).strip()

    return closing


#
# Edit a drawing of Square Pixels in the Terminal
#


@dataclasses.dataclass(order=True)
class SqaxelsWorker:
    """Edit a drawing of Square Pixels in the Terminal"""

    def show_sqaxels(self, typeahead: bytes) -> litpyglass.TerminalBoss:
        """Move the Cursor with the → ↑ ← ↓ Keys, and toggle the Pixel at it with the Space Key"""

        kd = litpyglass.keyboard_decoder()

        # Choose which Key Caps don't tell us to quit, not even when struck three times quickly

        stalwarts_list = "→ ↑ ← ↓".split()
        stalwarts_list += "⇧← ⇧→ ⌥← ⌥→ ⌥↑ ⌥↓ ⎋⇧← ⎋⇧→".split()
        stalwarts_list += "⇧Fn↑ ⇧Fn↓ ⇧Fn→ ⇧Fn←".split()

        arrow_stalwarts = tuple(kd.decode_by_echo[_].encode() for _ in stalwarts_list)
        assert tuple(_.decode() for _ in arrow_stalwarts[:4]) == litpyglass._CARDINAL_ENWS_ARROWS_

        for stalwart_caps in stalwarts_list:
            stalwart_split = litpyglass.InputStrikeTaker.caps_split_arrow_else(stalwart_caps)
            assert stalwart_split, (stalwart_caps,)

            _, stalwart_arrow = stalwart_split
            assert stalwart_arrow in ["←", "↑", "→", "↓"], (stalwart_caps,)

        # Choose the ⎋[⇧L that inserts a Row to not tell us to quit either

        assert litpyglass.IL_Y.format("") == "\033[" "L"

        stalwarts = arrow_stalwarts + (b"\033[" b"L",)

        # Choose what to write at exit

        assert litpyglass.CR == "\r"
        assert litpyglass.CUU_Y.format("") == "\033[" "A"
        assert litpyglass.CUD_Y.format(litpyglass._MAX_PN_32100_) == "\033[" "32100" "B"
        assert litpyglass.SHOW_CUSR_SM_PSQ25 == "\033[" "?25h"
        assert litpyglass.NO_SGR_PS == "\033[" "m"

        farewells = (
            "\r",  # leaps to left of Screen Row
            "\033[" "m",  # reverts the Text Styles
            "\033[" "?25h",  # shows the Cursor
            "\033[" "32100" "B",  # leaps to last Screen Row
            "\033[" "A",  # leaps to one Screen Row up from last
        )

        farewell_bytes = "".join(farewells).encode()

        # Launch elegantly, almost silently, without printing instructions

        # two Arrows struck together come closer than 50ms, a held Key repeats slower

        assert litpyglass._50_MEGA_NANOS_ == 50 * 10**6

        tb = litpyglass.TerminalBoss(typeahead=typeahead, farewell_bytes=farewell_bytes)
        with tb:
            ts = litpyglass.TerminalShadow(tb)
            ist = litpyglass.InputStrikeTaker(ts, arrow_wait_nanos=litpyglass._50_MEGA_NANOS_)

            # Find where the Cursor is and how big the Screen is

            ist.pull_yx_hw_from_ts_else(stalwarts=stalwarts)
            tb.tty_setraw_before_farewell()  # takes ⌃C ⌃D ⌃Z ⌃\ as Input, and Return as b"\r"

            # Choose how to hail now, before farewell later

            assert litpyglass.CR == "\r"
            assert litpyglass.BS == "\b"
            assert litpyglass.SHOW_CUSR_SM_PSQ25 == "\033[" "?25h"

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

            assert litpyglass._2_COLUMNS_ == 2
            assert litpyglass._1_ROW_ == 1
            area_width = litpyglass._2_COLUMNS_
            area_height = litpyglass._1_ROW_
            assert ts.is_writeable_base_area(area_width=area_width, area_height=area_height), (
                ts.base_place,
            )

            # Replay the drawing kept by an earlier run, if it fits where the Cursor is

            typescript_path = "io.typescript"
            typescript_text = ""
            if os.path.exists(typescript_path):
                with open(typescript_path, "rb") as f:
                    typescript_text = f.read().decode()

            is_fitting = True
            if typescript_text:
                is_fitting = ts.is_writable_place_after_strs(typescript_text)

            if is_fitting and typescript_text:
                ts.str_write_base_tb(typescript_text)  # so the Shadow knows every Cell
                # todo: replay of io.typescript is relative to where the Cursor starts

            # Loop till quit (such as by pressing Return three times quickly)

            if is_fitting:
                self.take_strikes_tb(ts, ist=ist, stalwarts=stalwarts)

            # Quit happy, keeping the drawing, but not the farewell

            if is_fitting:
                tb.typescript_write_file(typescript_path)

        # Freak when the drawing did not fit, after leaving the Terminal as we found it

        if not is_fitting:
            tb.str_print(f"{typescript_path} does not fit on this Screen from here")
            sys.exit(1)

        return tb

    def take_strikes_tb(
        self,
        ts: litpyglass.TerminalShadow,
        ist: litpyglass.InputStrikeTaker,
        stalwarts: tuple[bytes, ...],
    ) -> None:
        """Leap at each Arrow and toggle at each Space, till the Strikes end or say quit"""

        open_frame: litpyglass.TerminalByteFrame | None = None  # the Frame being acted on
        open_length = 0  # the Bytes of the Open Frame already acted on

        for isap in ist.take_input_strikes_and_yield_each_placed(stalwarts=stalwarts):
            strike = isap.strike
            place = isap.place

            taken = strike.taken
            caps = strike.caps
            printables = strike.printables

            data = strike.to_strike_bytes()  # Bytes from 0, 1, or more Frames

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

            shifts_arrow = litpyglass.InputStrikeTaker.caps_split_arrow_else(caps)
            if taken and shifts_arrow:
                _, arrow_caps = shifts_arrow  # the bare Arrow, whatever shifts came with it
                bounce_caps_tuple = bounce_caps_tuple_by_caps[arrow_caps]

                # Move ahead, or bounce back (so as to avoid nop or spill)

                assert place, (place,)
                assert litpyglass.CUF_X.format("") == "\033[" "C"

                try_caps_tuple = (arrow_caps,) + bounce_caps_tuple
                try_leaps = tuple(self.form_leap_text(caps=_) for _ in try_caps_tuple)

                # A leap fits only when the whole Pair fits at the landing place,
                # so the Pair needs its East Column too

                writable_leaps = list(
                    _ for _ in try_leaps if ts.is_writable_place_after_strs(text=_ + "\033[" "C")
                )
                assert writable_leaps, (arrow_caps, len(writable_leaps), place)

                # Write no Pair, only the leap ahead or the bounce back

                ts.str_write_base_tb(writable_leaps[0])
                continue

            # Insert a Row at the Cursor, and leave the Cursor where it is

            assert litpyglass.IL_Y.format("") == "\033[" "L"

            if taken and (data == b"\033[" b"L"):
                ts.str_write_base_tb("\033[" "L")
                continue

            # Wait for the Frame to be taken while Bytes are still typed ahead, since
            # an Arrow struck before this Open Frame may be held back and yield after it

            if (not taken) and ts.tb.typeahead:
                continue

            # Count the Spaces that arrive fresh, in the Open Frame or when it is taken

            (frame,) = strike.frames  # only a joined Arrow holds two Frames, and it left above
            if frame is not open_frame:
                open_frame = frame
                open_length = 0  # a later Frame, whether or not this Strike took it

            assert len(data) >= open_length, (len(data), open_length)
            fresh_data = data[open_length:]

            space_count = 0
            if printables:  # a Space inside a Control Frame, such as a Mouse report, is no Space
                space_count = fresh_data.count(b" ")
                open_length = len(data)

            for step in range(space_count):
                self.ts_toggle_pixel_tb(ts)

            # todo: no visible change at a Strike that is neither Arrow nor Space

    def form_leap_text(self, caps: str) -> str:
        """Spell the step of one Square Pixel toward an Arrow Key, without any Pair"""

        assert litpyglass.CUU_Y.format("") == "\033[" "A"
        assert litpyglass.CUD_Y.format("") == "\033[" "B"
        assert litpyglass.CUF_X.format("") == "\033[" "C"
        assert litpyglass.CUB_X.format("") == "\033[" "D"

        square_leap_by_caps = {  # for 2x1 Terminal Screen Cells  # sorted by Caps Codepoints
            "←": 2 * "\033[" "D",  # Back West
            "↑": 1 * "\033[" "A",  # Up North
            "→": 2 * "\033[" "C",  # "Forward" East
            "↓": 1 * "\033[" "B",  # Down South
            "↖": 1 * "\033[" "A" + 2 * "\033[" "D",  # Up North, then Back West
            "↗": 1 * "\033[" "A" + 2 * "\033[" "C",  # Up North, then "Forward" East
            "↘": 1 * "\033[" "B" + 2 * "\033[" "C",  # Down South, then "Forward" East
            "↙": 1 * "\033[" "B" + 2 * "\033[" "D",  # Down South, then Back West
        }

        leap = square_leap_by_caps[caps]
        return leap

    def ts_toggle_pixel_tb(self, ts: litpyglass.TerminalShadow) -> None:
        """Write the Pair at the Cursor as Reverse if it is not, else as Plain, and stay put"""

        base_place = ts.base_place

        assert litpyglass.SP == " "
        assert litpyglass.NO_SGR_PS == "\033[" "m"
        assert litpyglass.REVERSE_SGR_PS7 == "\033[" "7m"

        square = 2 * " "  # two Spaces side by side, one Square Pixel
        plain = litpyglass.NO_SGR_PS  # reverts the Text Styles
        reverse = litpyglass.REVERSE_SGR_PS7  # swaps to color B on F, from color F on B

        assert litpyglass._2_COLUMNS_ == 2
        assert litpyglass._1_ROW_ == 1
        assert ts.is_writeable_base_area(area_width=2, area_height=1), (base_place,)

        # Choose what to leave behind

        gw = litpyglass.GlassWorker()
        back = gw.form_back_text(base_place)

        if not self.is_reverse_place(ts):
            base_text = f"{reverse}{square}{plain}{back}"
        else:
            base_text = f"{plain}{square}{back}"

        # Write the Pair into the Base Layer, and back up to the Cursor

        ts.str_write_base_tb(base_text)

    def is_reverse_place(self, ts: litpyglass.TerminalShadow) -> bool:
        """Say if the Cell at the Cursor holds a Space written in Reverse"""

        base = ts.base
        base_place = base.place

        write_by_xy = base.write_by_xy
        xy = (base_place.column_x, base_place.row_y)

        # Say no for a Cell never written

        if xy not in write_by_xy.keys():
            return False

        # Say yes only for a Cell written with Reverse in force

        assert litpyglass.REVERSE_SGR_PS7 == "\033[" "7m"

        cell_styles, cell_text = write_by_xy[xy]
        is_reverse = (cell_text == " ") and (litpyglass.REVERSE_SGR_PS7 in cell_styles)
        return is_reverse


if __name__ == "__main__":
    main()


# ⚠️ ↑↑↑ Above written by Claude·Ai, reviewed by almost no living people
