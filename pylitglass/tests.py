#!/usr/bin/env python3

r"""
usage: pylitglass/litpyglass.py -- >/dev/null 2>/dev/null

import & call litpyglass.py, then pass/ fail by process exit return status code as zero/not

quirks:
  runs via:  import tests; tests.main()

examples:
  make slow  # runs these tests
"""

# code reviewed by Black, Flake8, Mypy-Strict, & Pylance-Standard  # but not by living people


# ⚠️ ↓↓↓ Below written by Claude·Ai, reviewed by almost no living people

from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import ast
import concurrent.futures
import contextlib
import dataclasses
import io
import json
import os
import pty
import random
import re
import select
import string
import subprocess
import sys
import tempfile
import termios
import time
import typing

import litpyglass

_: object  # blocks Mypy from narrowing the Datatype of '_ =' at first mention

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


def main() -> None:
    """Run every self-test, and print one line when they pass"""

    # ~6000ms in all, mostly waiting, not computing
    #
    #   100ms: the quit rule's too-fast gap, so each strike below must wait longer than that
    #   150ms: that wait, and also the Typeahead wait per Byte, so each Byte costs 150ms
    #   ~50ms: to start each child Python and import litpyglass, which every Pty Test pays

    _try_terminal_frame_decoder_()  # ~1ms
    _try_terminal_byte_frame_()  # ~330ms, mostly ~327ms _try_ends_later_ over every Char
    _try_keyboard_decoder_()  # ~1ms
    _try_keyboard_decoder_bursts_()  # ~200ms, 10 reads of 20ms each
    _try_terminal_boss_()  # ~490ms, 2 child Pythons
    _try_terminal_boss_return_()  # ~300ms, 2 child Pythons on Ptys at once
    _try_terminal_boss_farewell_()  # ~100ms, 1 child Python
    _try_is_quitting_frames_()  # ~1600ms, 7 Ptys at once, the slowest 6 ⎋ at 150ms apart + 500ms
    _try_is_quitting_stalwarts_()  # ~1ms
    _try_is_quitting_shape_()  # ~1ms
    _try_strikes_spill_()  # ~1000ms, 3 ⏎ at 150ms apart, then 300ms of reading what is left
    _try_terminal_boss_typeahead_()  # ~600ms, 150ms per Typeahead Byte
    _try_terminal_boss_chunks_()  # ~460ms, 150ms per Typeahead Byte
    _try_terminal_boss_keeps_input_()  # ~460ms, 1 child Python on a Pty, 3 Typeahead Bytes
    _try_typeahead_()  # ~550ms, 3 Typeahead ⏎ at 150ms each
    _try_frame_reader_quits_midbatch_()  # ~1ms
    _try_frame_reader_nanobytes_()  # ~10ms, 3 reads of 2ms each
    _try_frame_reader_peek_()  # ~1ms
    _try_frame_reader_tilt_()  # ~180ms, 12 reads of 15ms each
    _try_frame_print_()  # ~1ms
    _try_pull_ends_without_replies_()  # ~1ms
    _try_placed_input_strikes_()  # ~150ms, 1 Pty and 1 child Python off a Terminal
    _try_intercardinal_strikes_()  # ~1200ms, 1 child Python on a Pty, 7 Typeahead Bytes at 150ms
    _try_intercardinal_joins_()
    _try_intercardinal_ahead_()
    _try_intercardinal_splits_()
    _try_arrow_wait_()  # ~300ms, 2 child Pythons on Ptys in turn, one waits 50ms for a mate
    _try_skater_entry_()  # ~900ms, 4 Ptys at once, and 1 child Python off a Terminal
    _try_skater_quits_()  # ~2000ms, 43 Ptys at once, the slowest 3 ⏎ at 150ms apart + 500ms
    _try_skater_fuzz_()  # ~3500ms, 24 Ptys at once, the slowest 10 steps at 150ms apart + 500ms
    _try_skater_edge_()  # ~3500ms, 4 Ptys at once, the slowest 10 → at 150ms apart + 500ms, then 3
    _try_skater_launch_edge_()  # 10 Ptys at once
    _try_input_file_()  # ~400ms, 6 child Pythons off a Terminal at once, then 2 in turn
    _try_boss_writes_()  # ~100ms, 1 child Python off a Terminal
    _try_output_routes_()  # ~10ms, parses litpyglass.py
    _try_typescript_files_()  # ~1000ms, 2 Ptys at once, the slowest 3 ⏎ at 150ms apart + 500ms
    _try_shadow_writes_()  # ~1ms
    _try_shadow_layer_()  # ~1ms
    _try_shadow_top_layer_()  # ~1ms
    _try_shadow_chops_()  # ~1ms
    _try_shadow_row_leap_()  # ~1ms
    _try_shadow_column_leap_()  # ~1ms
    _try_shadow_yx_leap_()  # ~1ms
    _try_shadow_insert_row_()  # ~1ms
    _try_shadow_delete_row_()  # ~1ms
    _try_shadow_dump_()  # ~100ms, 9 Layers dumped, then each replayed 9 ways
    _try_shadow_drop_()  # ~1ms
    _try_screen_replay_()  # ~1ms

    print("tests ok")


def _try_keyboard_decoder_() -> None:
    """Try KeyboardDecoder things, as specs.md § 6 says"""

    kd = litpyglass.keyboard_decoder()

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
        ("è".encode(), "⌥`E"),  # each of the five Dead Keys, before E
        ("ê".encode(), "⌥IE"),
        ("ñ".encode(), "⌥NN"),  # before N, not only before a vowel
        ("ë".encode(), "⌥UE"),
        ("J\u0301".encode(), "⌥E⇧J"),  # 'J' before Combining Acute Accent, from ⌥E & then ⇧J
        ("É".encode(), "⌥E⇧E"),  # a Capital Letter that a Dead Key does accent
        ("j\u0300".encode(), ""),  # 'j' before Combining Grave Accent, which no Key sends
        ("q\u0301".encode(), ""),  # ⌥E Q sends ´q, not 'q' before Combining Acute Accent
        ("p\u0303".encode(), ""),  # ⌥N P sends ˜p
        ("x\u0308".encode(), ""),  # ⌥U X sends ¨x
        ("ĵ".encode(), ""),  # ⌥I J sends ˆj, so no Key sends 'ĵ'
        ("e\u0301".encode(), ""),  # ⌥E E sends 'é' as 1 Char, not 'e' before Combining Acute Accent
        ("qj\u0301".encode(), "Q ⌥EJ"),  # the Mark accents the Char before it, not the first Char
        ("ˆj\u0301".encode(), ""),  # ⌥I J sends ˆj, and then no Key sends the Mark alone
        ("aå".encode(), "A ⌥A"),  # a Char that NFD would split, but that one Chord sends
        ("´".encode(), "⌥⇧E"),  # the Spacing Acute Accent, as struck
        #
        ("ˆp".encode(), "⌥I P"),  # a Dead Key's Accent ahead of a Letter it doesn't accent
        ("`p".encode(), "⌥` P"),  # each of the five Dead Keys
        ("´q".encode(), "⌥E Q"),
        ("˜p".encode(), "⌥N P"),
        ("¨x".encode(), "⌥U X"),
        ("ˆP".encode(), "⌥I ⇧P"),  # ahead of a Capital Letter
        ("ˆe".encode(), "⌥⇧I E"),  # ⌥I E sends ê, so ⌥⇧I and then E sent these
        ("´j".encode(), "⌥⇧E J"),  # ⌥E J sends 'j' before Combining Acute Accent
        ("˜n".encode(), "⌥⇧N N"),  # ⌥N N sends ñ
        ("¨y".encode(), "⌥⇧U Y"),  # ⌥U Y sends ÿ
        ("ˆ ".encode(), "⌥⇧I ␢"),  # ahead of a Space
        ("ˆ1".encode(), "⌥I 1"),  # ahead of a Digit
        ("`-".encode(), "⌥` -"),  # ahead of a Punctuation Mark
        ("´_".encode(), "⌥E ⇧_"),  # ahead of a Shifted Punctuation Mark
        ("˜~".encode(), "⌥N ⇧~"),
        ("¨`".encode(), "⌥U `"),  # ahead of the ` Key
        ("``".encode(), "⌥` `"),  # ⌥` and then the ` Key, as ⌥` ⌥` sends just one `
        ("ˆˆ".encode(), "⌥⇧I ⌥⇧I"),  # ahead of itself
        ("˜Ï".encode(), "⌥⇧N ⌥U⇧I"),  # ahead of a Letter under a Combining Mark of its own
        ("\u0301".encode(), ""),  # the Combining Acute Accent by itself, which no Key sends
        ("a\u0301\u0308".encode(), ""),  # two Combining Marks on one Char, which no Key sends
        #
        (b"\033OP", "F1"),  # an Ss3 Terminal Byte Frame
        (b"\033[17~", "F6"),  # F6 over ⌥F1 or ⎋F1, which send the same Bytes
        (b"\033[23~", "⌥F6"),  # ⌥F6 because macOS Mission Control often steals F11
        (b"\033[24~", "F12"),  # F12 over ⌥F7 or ⎋F7
        (b"\033[25~", "⇧F5"),  # ⇧F5 over ⌥F8 or ⎋F8
        (b"\033[22~", "⎋ [ 2 2 ⇧~"),  # no F Key sends ⎋[22⇧~  # F10 sends 21, F11 sends 23
        (b"\033\020", "⎋⌃P"),  # ⎋⌃P over ⎋⇧F1 .. ⎋⌃⇧F12, which send the same Bytes
        #
        (b"\033[5~", "⇧Fn↑"),  # at macOS Terminal, ⇧Fn↑ ⇧Fn↓ ⇧Fn→ ⇧Fn← send these four Frames
        (b"\033[6~", "⇧Fn↓"),
        (b"\033[F", "⇧Fn→"),
        (b"\033[H", "⇧Fn←"),
        #
    )

    for data, want in pairs:
        caps = kd._burst_bytes_to_key_caps_if_(data)
        assert caps == want, (caps, want, data)

    # Count the pairs of Accent and Letter that name a Dead Key, as the U.S. Layout sends them

    lowers = "abcdefghijklmnopqrstuvwxyz"

    dead_key_caps_list = list()
    for accent in "`´ˆ˜¨":
        for letter in lowers + lowers.upper():
            caps = kd._burst_bytes_to_key_caps_if_((accent + letter).encode())
            if caps.startswith("⌥") and not caps.startswith("⌥⇧"):
                dead_key_caps_list.append(caps)

    assert len(dead_key_caps_list) == 210, (len(dead_key_caps_list),)

    # Count the pairs of Accent and Digit or Punctuation Mark that name a Dead Key too

    marks = string.digits + string.punctuation

    dead_key_mark_caps_list = list()
    for accent in "`´ˆ˜¨":
        for mark in marks:
            caps = kd._burst_bytes_to_key_caps_if_((accent + mark).encode())
            if caps.startswith("⌥") and not caps.startswith("⌥⇧"):
                dead_key_mark_caps_list.append(caps)

    assert len(dead_key_mark_caps_list) == 210, (len(dead_key_mark_caps_list),)


def _try_keyboard_decoder_bursts_() -> None:
    """Try KeyboardDecoder naming burst by burst, as specs.md § 6 says"""

    kd = litpyglass.keyboard_decoder()

    ms_10 = 10 * 10**6
    assert litpyglass._10_MEGA_NANOS_ == ms_10, (litpyglass._10_MEGA_NANOS_, ms_10)

    slow = 750 * 10**6

    def nanobytes_of(waits: tuple[int, ...], data: bytes) -> tuple[tuple[int, bytes], ...]:
        assert len(waits) == len(data), (len(waits), len(data), data)
        nanobytes = tuple((wait, data[i:][:1]) for (i, wait) in enumerate(waits))
        return nanobytes

    # Pair up the waits and the Bytes with the Key Caps struck to send them

    j_acute = "j\u0301".encode()
    assert j_acute == b"j\314\201", (j_acute,)

    circumflex_p = "ˆp".encode()
    assert circumflex_p == b"\313\206p", (circumflex_p,)

    triples = (
        #
        ((), b"", ""),  # nothing struck
        #
        ((slow, 0, 0), circumflex_p, "⌥I P"),  # ⌥I P, as one read
        ((slow, 0, 72_791), circumflex_p, "⌥I P"),  # ⌥I P, as measured at macOS Terminal
        ((slow, 0, ms_10 - 1), circumflex_p, "⌥I P"),  # the slowest burst
        ((slow, 0, ms_10), circumflex_p, "⌥⇧I P"),  # the fastest two Chords
        ((slow, 0, 320_676_292), circumflex_p, "⌥⇧I P"),  # ⌥⇧I then P, as measured
        ((0, 0, 0), circumflex_p, "⌥I P"),  # a first wait of 0 cuts nothing
        ((slow, slow, 0), circumflex_p, "⌥I P"),  # a slow Byte inside the first Char cuts nothing
        ((slow, slow, slow), circumflex_p, "⌥⇧I P"),
        ((slow, 0, 0, slow), "ˆpq".encode(), "⌥I P Q"),  # a burst and then a Key
        ((slow, slow, 0, 0), "qˆp".encode(), "Q ⌥I P"),  # a Key and then a burst
        #
        ((slow, 0, 0), j_acute, "⌥EJ"),  # ⌥E J, as one read
        ((slow, ms_10 - 1, 0), j_acute, "⌥EJ"),  # the slowest burst
        ((slow, ms_10, 0), j_acute, ""),  # the fastest Combining Mark that came late
        ((slow, slow, 0), j_acute, ""),  # a Combining Mark that came slowly
        ((0, 0, 0), j_acute, "⌥EJ"),  # a first wait of 0 cuts nothing
        #
        ((slow, slow), "é".encode(), "⌥EE"),  # a slow Byte inside a Char cuts no Char in two
        ((slow, 0, slow), j_acute, ""),  # but makes its Char come late
        ((slow, ms_10 // 2, ms_10 // 2 - 1), j_acute, "⌥EJ"),  # the waits of a Char's Bytes add up
        ((slow, ms_10 // 2, ms_10 // 2), j_acute, ""),
        ((slow, ms_10 // 2, 0, ms_10 // 2), j_acute + b"a", "⌥EJ A"),  # but only inside one Char
        #
        ((slow, slow, slow), b"abc", "A B C"),  # Text struck slowly
        ((slow, 0, 0), b"abc", "A B C"),  # Text pasted
        #
        ((slow, slow, slow), b"\033[A", "↑"),  # ↑ typed slowly as ⎋ [ ⇧A
        ((slow, slow), b"\033[", "⎋["),
        ((slow, slow, slow), b"\033[1", "⎋ [ 1"),
        ((slow,), b"\377", ""),  # an Undecodable Byte
        #
    )

    for waits, data, want in triples:
        nanobytes = nanobytes_of(waits, data=data)
        caps = kd.nanobytes_to_key_caps_if(nanobytes)
        assert caps == want, (caps, want, waits, data)

    # Name the bursts of one read and of two reads 20ms apart, through the Strike Taker

    for chunks, want in (([j_acute], "⌥EJ"), ([b"j", "\u0301".encode()], "")):
        boss = typing.cast(litpyglass.TerminalBoss, FakeLateBoss(chunks))
        ts = litpyglass.TerminalShadow(boss)
        ist = litpyglass.InputStrikeTaker(ts, arrow_wait_nanos=0)

        strikes = list(ist.take_input_strikes_and_yield_each(stalwarts=()))
        taken_caps = list(_.caps for _ in strikes if _.taken)
        assert taken_caps == [want], (taken_caps, want, chunks)

        open_caps = list(_.caps for _ in strikes if not _.taken)
        assert open_caps[-1] == want, (open_caps, want, chunks)  # the Open Frame says the same

    # Name a Dead Key's burst of one read, and its Accent and Letter of two reads 20ms apart

    circumflex = "ˆ".encode()
    for chunks, want in (([circumflex_p], "⌥I P"), ([circumflex, b"p"], "⌥⇧I P")):
        boss = typing.cast(litpyglass.TerminalBoss, FakeLateBoss(chunks))
        ts = litpyglass.TerminalShadow(boss)
        ist = litpyglass.InputStrikeTaker(ts, arrow_wait_nanos=0)

        strikes = list(ist.take_input_strikes_and_yield_each(stalwarts=()))
        taken_caps = list(_.caps for _ in strikes if _.taken)
        assert taken_caps == [want], (taken_caps, want, chunks)

        open_caps = list(_.caps for _ in strikes if not _.taken)
        assert open_caps[-1] == want, (open_caps, want, chunks)  # the Open Frame says the same


def _try_terminal_frame_decoder_() -> None:
    """Try Replies to DSR6 and XTWINOPS_18 Asks, and Frames that aren't Replies"""

    assert litpyglass.XTWINOPS_18 == "\033[18t"
    assert litpyglass.DSR6 == "\033[6n"

    f = litpyglass.TerminalFrameDecoder.bytes_to_yx_or_hw_reply_else

    assert f(b"\033[8;24;80t") == ("HW", 24, 80)  # Rows then Columns
    assert f(b"\033[5;7R") == ("YX", 5, 7)  # Row then Column

    assert f(b"\033[A") is None  # an Arrow
    assert f(b"\033\033[5;7R") is None  # a Reply with a ⎋ stuck on the front
    assert f(b"\033[5;7R\033[5;7R") is None  # two Replies are two Frames
    assert f(b"\033[8;24t") is None  # too few Ints
    assert f(b"\033[;7R") is None  # an empty Int
    assert f(b"\033[007;5R") == ("YX", 7, 5)  # leading 0s, which ECMA-48 would not send
    assert f(b"") is None

    for data in (b"\033[0;7R", b"\033[5;0R", b"\033[8;0;80t", b"\033[8;24;0t"):  # a 0 Int
        try:
            f(data)
        except AssertionError:
            continue
        assert False, (data,)


def _try_terminal_byte_frame_() -> None:
    """Try TerminalByteFrame things"""

    assert "\u20ac" == "€"  # a popular Printable Character with a 3 Byte Encoding
    assert "\U0001f602" == "😂"  # a popular Printable Character with a 4 Byte Encoding

    try:
        decode = b"\xf4\x8f\xbf\xff".decode()
        assert False, (decode,)  # fails if Python accepts a Code above U+10FFFF
    except UnicodeDecodeError:
        pass

    _try_terminal_byte_frame_1_()

    _try_terminal_byte_frame_2_()


def _try_terminal_byte_frame_1_() -> None:
    """Run slow and quick Self-Test's of TerminalByteFrame"""

    _try_open_(b"")  # empty
    _try_headbook_()
    _try_ends_later_()  # ~300ms
    _try_one_more_kbyte_()
    _try_some_control_()
    _try_peeks_()


def _try_headbook_() -> None:
    """Accept the Bytes of any Head of the Headbook, without closing the Frame"""

    # Stay open for every Head of the real Headbook

    real_headbook = (
        b"\033",
        b"\033\033",
        b"\033\033O",
        b"\033\033[",
        b"\033O",
        b"\033[",
        b"\033[M",
        b"\033]",
    )  # ⎋ ⎋⎋ ⎋⎋⇧O ⎋⎋[ ⎋⇧O ⎋[ ⎋[⇧M ⎋]

    assert litpyglass.TerminalByteFrame.Headbook == real_headbook, (
        litpyglass.TerminalByteFrame.Headbook,
        real_headbook,
    )

    for head in real_headbook:
        _try_open_(head)

    # Try the 4 Heads that keep Tails, Extras, and closing, in more detail

    headbook = (b"\033", b"\033O", b"\033[", b"\033]")  # ⎋ ⎋⇧O ⎋[ ⎋]

    assert litpyglass.OSC == "\033]", (litpyglass.OSC,)

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
        assert litpyglass.TerminalByteFrame.bytes_to_later_decode_if(start), (start,)
        start_byte_set.add(start[:1])

    start_bytes = tuple(sorted(start_byte_set))
    assert start_bytes == litpyglass.StartBytes, (start_bytes, litpyglass.StartBytes)


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
    _try_extra_(b"Text", extra="\u00ad".encode())  # 2 Bytes, a Soft-Hyphen Control
    _try_extra_(b"Text", extra="\U0010ffff".encode())  # 4 Bytes, the last Code


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

    assert litpyglass._END_PASTE_ == "\033[" "201~", (litpyglass._END_PASTE_,)

    _try_close_(b"\x1b[", b"201", b"~")


def _try_peeks_() -> None:
    """Stay open for the Combining Mark already fetched, where a Printable Char would close"""

    peek = "\u0301"  # Combining Acute Accent, as ⌥E J sends it after the J
    encode = peek.encode()

    # Stay open after the Printable Char that would have closed, and then close on the Mark

    for data in (b"\033j", b"\033\033j", b"\033Oj", b"\033[A", b"\033[1;5A", b"\033[ q"):
        f = litpyglass.TerminalByteFrame(b"")
        extras = f.take_data_if(data, peek=peek)
        assert (not extras) and (not f.closed), (extras, f, data)

        extras = f.take_data_if(encode, peek="")
        assert (not extras) and f.closed, (extras, f, data)
        assert f.to_frame_bytes() == (data + encode), (f, data)

    # Close anyway, after an Unprintable Char, or after the 6 raw Bytes of ⎋[M

    for data in (b"\t", b"\033\t", b"\033[M /\xff"):
        f = litpyglass.TerminalByteFrame(b"")
        extras = f.take_data_if(data, peek=peek)
        assert (not extras) and f.closed, (extras, f, data)

    # Stay open anyway, as Text, or as ⎋] Osc, and take the Mark

    for data in (b"j", b"\033]0;x"):
        f = litpyglass.TerminalByteFrame(b"")
        extras = f.take_data_if(data, peek=peek)
        assert (not extras) and (not f.closed), (extras, f, data)

        extras = f.take_data_if(encode, peek="")
        assert (not extras) and (not f.closed), (extras, f, data)
        assert f.to_frame_bytes() == (data + encode), (f, data)


def _try_extra_(data: bytes, extra: bytes) -> None:
    """Require the Frame to bounce these Bytes, and to stay as it was"""

    f = litpyglass.TerminalByteFrame(data)
    closed = f.closed

    returned_extra = f.take_data_if(extra, peek="")
    assert returned_extra == extra, (returned_extra, extra, str(f))

    assert f.closed == closed, (f.closed, closed, extra, f)
    assert f == litpyglass.TerminalByteFrame(data), (f, litpyglass.TerminalByteFrame(data))


def _try_open_(*args: str | bytes) -> None:
    """Frame these Bytes, and require the Frame still open"""

    f = _try_bytes_(*args)
    assert not f.closed, (f,)


def _try_close_(*args: bytes) -> None:
    """Frame these Bytes, and require the Frame closed"""

    f = _try_bytes_(*args)
    assert f.closed, (f,)


def _try_bytes_(*args: str | bytes) -> litpyglass.TerminalByteFrame:
    """Frame these Bytes, and require the Str of the Frame to speak each Arg as given"""

    data_list = list()
    for arg in args:
        if isinstance(arg, str):
            data_list.append(arg.encode())
        else:
            data_list.append(arg)

    join = " ".join(
        (litpyglass.str_repr(_) if isinstance(_, str) else litpyglass.bytes_repr(_)) for _ in args
    )

    fdata = b""
    for data in data_list:
        fdata += data

    f = litpyglass.TerminalByteFrame(fdata)
    fbytes = f.to_frame_bytes()
    fstr = str(f)

    join_plus = join if f.closed else (join + " +")  # ' +' marks an Open Frame

    assert fbytes == fdata, (fbytes, fdata)
    assert fstr == join_plus, (fstr, join_plus)

    return f


def _try_terminal_byte_frame_2_() -> None:
    """Try some Frames: ↑ ⎋↑ ⎋[M and the ⎋\\ String Terminator"""

    assert litpyglass.DL_Y == "\033[" "{}M", (litpyglass.DL_Y,)
    assert litpyglass._CLICK3_ == "\033[M", (litpyglass._CLICK3_,)
    assert litpyglass._NorthArrow_ == "\033[A", (litpyglass._NorthArrow_,)
    assert litpyglass.ST == "\033\134", (litpyglass.ST,)

    # Do nothing with grace & elegance

    litpyglass.TerminalByteFrame(b"")

    # Speak well of ↑ and ⎋↑

    f = litpyglass.TerminalByteFrame(b"\033[A")
    assert f.to_frame_bytes() == b"\033[A", (f,)
    assert f.closed, (f,)

    f = litpyglass.TerminalByteFrame(b"\033\033[A")
    assert f.to_frame_bytes() == b"\033\033[A", (f,)
    assert f.closed, (f,)

    # Dance well with the _CLICK3_ clash into DL_Y without Pn

    f = litpyglass.TerminalByteFrame(b"\033[M")
    assert f.to_frame_bytes() == b"\033[M", (f,)
    assert not f.closed, (f,)  # because could be ⎋[⇧M{b}{x}{y}

    f = litpyglass.TerminalByteFrame(b"\033[Mabc")
    assert f.to_frame_bytes() == b"\033[Mabc", (f,)
    assert f.closed, (f,)

    f = litpyglass.TerminalByteFrame(b"\033[Mab\xff")
    assert f.to_frame_bytes() == b"\033[Mab\xff", (f,)
    assert f.closed, (f,)

    # Close a Csi Frame on a Final Char from outside 7-bit US Ascii, with or without Params

    for csi_decode in ("\033[↗", "\033[1;2↗", "\033[é", "\033[€"):
        csi_encode = csi_decode.encode()
        f = litpyglass.TerminalByteFrame(csi_encode)  # not yet standard
        assert f.to_frame_bytes() == csi_encode, (f,)
        assert f.closed, (f,)

    # Accept the ⎋\ String Terminator (ST) to close an ⎋] Osc Frame

    f = litpyglass.TerminalByteFrame(b"\033]11;?\033\\")
    assert f.to_frame_bytes() == b"\033]11;?\033\\", (f,)
    assert f.closed, (f,)


_TERMINAL_BOSS_TTY_CHILD_ = r"""
import os, select, sys, termios, tty
sys.path.insert(0, sys.argv[1])
import litpyglass


def slurp():
    data = b""
    while select.select([0], [], [], 0.1)[0]:
        data += os.read(0, 64)
    return data


sync_fileno = int(sys.argv[2])


events = []  # the order of flushes, tty.setraw calls, and termios.tcsetattr calls


class FlushSpy:  # stands in for sys.stdout and sys.stderr
    def __init__(self, name, stdio):
        self.name = name
        self.stdio = stdio
        self.flush_count = 0

    def flush(self):  # mimics TextIO.flush
        self.flush_count += 1
        events.append("flush " + self.name)
        self.stdio.flush()

    def write(self, text):  # mimics TextIO.write
        return self.stdio.write(text)


real_stdout = sys.stdout
spy_stdout = FlushSpy("out", sys.stdout)
spy_stderr = FlushSpy("err", sys.stderr)
sys.stdout, sys.stderr = spy_stdout, spy_stderr

real_setraw = tty.setraw
real_tcsetattr = termios.tcsetattr


def spy_setraw(*args, **kwargs):  # tty.setraw calls its own tcsetattr, so one event not two
    events.append("setraw")
    return real_setraw(*args, **kwargs)


def spy_tcsetattr(*args, **kwargs):
    events.append("tcsetattr")
    return real_tcsetattr(*args, **kwargs)


tty.setraw = spy_setraw
termios.tcsetattr = spy_tcsetattr

boss = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"")
print("READY1", file=real_stdout, flush=True)
os.read(sync_fileno, 1)  # 'ab' has been typed, and the Terminal still takes Cooked Input
with boss:
    saved_attributes = boss.tcgetattr
    entered_twice = (boss.__enter__() is boss) and (boss.tcgetattr is saved_attributes)
    flushes_at_enter = (spy_stdout.flush_count, spy_stderr.flush_count)
    events_at_enter = list(events)
    kept_at_enter = slurp()
    print("READY2", file=real_stdout, flush=True)
    os.read(sync_fileno, 1)  # 'xy' has been typed, and no one reads it
boss.__exit__()  # exits at most once
cleared_at_exit = boss.tcgetattr == []
flushes_at_exit = (spy_stdout.flush_count, spy_stderr.flush_count)
events_at_exit = list(events)
tty.setraw = real_setraw
termios.tcsetattr = real_tcsetattr
cooked_attributes = termios.tcgetattr(0)
tty.setraw(0, when=termios.TCSANOW)
left_at_exit = slurp()
termios.tcsetattr(0, termios.TCSANOW, cooked_attributes)
with boss:
    entered_afresh = bool(boss.tcgetattr)
result = (
    kept_at_enter,
    entered_twice,
    cleared_at_exit,
    left_at_exit,
    entered_afresh,
    flushes_at_enter,
    flushes_at_exit,
    events_at_enter,
    events_at_exit,
)
print("RESULT", repr(result), file=real_stdout, flush=True)
"""

_TERMINAL_BOSS_PIPE_CHILD_ = r"""
import sys
sys.path.insert(0, sys.argv[1])
import litpyglass

boss = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"")
with boss:
    inside = (boss.isatty, boss.tcgetattr)
    boss.tty_setraw_before_farewell()  # does nothing off a Terminal, farewell or not
print("RESULT", repr((inside, boss.tcgetattr)), flush=True)
"""


def _try_terminal_boss_() -> None:
    """Try TerminalBoss things, as specs.md § 1 says"""

    here = os.path.dirname(os.path.abspath(litpyglass.__file__))

    # Meet the Spec on a Terminal, with 'ab' typed before Enter and 'xy' typed inside

    sync_read_fileno, sync_write_fileno = os.pipe()
    os.set_inheritable(sync_read_fileno, True)  # lets the exec'd Child read it
    pid, master_fileno = pty.fork()
    if pid == 0:
        os.execv(
            sys.executable,
            [sys.executable, "-I", "-c", _TERMINAL_BOSS_TTY_CHILD_, here, str(sync_read_fileno)],
        )

    terminal_output = bytearray()

    def read_till_terminal_output(marker: bytes) -> None:
        deadline = time.monotonic() + 10
        while (marker not in terminal_output) and (time.monotonic() < deadline):
            if select.select([master_fileno], [], [], 0.05)[0]:
                try:
                    terminal_output.extend(os.read(master_fileno, 4096))
                except OSError:
                    break
        assert marker in terminal_output, (marker, bytes(terminal_output))

    read_till_terminal_output(b"READY1")
    os.write(master_fileno, b"ab")
    time.sleep(0.05)
    os.write(sync_write_fileno, b"g")

    read_till_terminal_output(b"READY2")
    os.write(master_fileno, b"xy")
    time.sleep(0.05)
    os.write(sync_write_fileno, b"g")

    read_till_terminal_output(b"RESULT (")
    read_till_terminal_output(b")\r\n")
    os.waitpid(pid, 0)
    os.close(master_fileno)
    os.close(sync_read_fileno)
    os.close(sync_write_fileno)

    tty_result_decoded = bytes(terminal_output).split(b"RESULT ")[1].split(b"\r\n")[0].decode()
    tty_result = ast.literal_eval(tty_result_decoded)
    enter_events = ["flush out", "flush err", "setraw"]  # no Farewell, so tty.setraw not setcbreak
    exit_events = enter_events + ["flush out", "flush err", "tcsetattr"]
    tty_expected = (b"ab", True, True, b"xy", True, (1, 1), (2, 2), enter_events, exit_events)
    # kept, twice, cleared, left, afresh, then the Stdout and Stderr flush counts after Enter and
    # after Exit, then the order of flushes before tty.setraw and before termios.tcsetattr
    assert tty_result == tty_expected, (tty_result, tty_expected)

    # Meet the Spec off a Terminal

    run = subprocess.run(
        [sys.executable, "-I", "-c", _TERMINAL_BOSS_PIPE_CHILD_, here],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=True,
    )
    pipe_result = ast.literal_eval(run.stdout.split("RESULT ")[1])
    pipe_expected: tuple[tuple[bool, list[int]], list[int]] = ((False, [20261010]), [])
    assert pipe_result == pipe_expected, (pipe_result, pipe_expected, run.stderr)


_TERMINAL_BOSS_FAREWELL_CHILD_ = r"""
import os, sys, termios
sys.path.insert(0, sys.argv[1])
import litpyglass

real_tcsetattr = termios.tcsetattr


def tcsetattr_after_marker(fd, when, attributes):
    os.write(1, b"<RESTORED>")
    real_tcsetattr(fd, when, attributes)


def lflag_has(bit):
    return bool(termios.tcgetattr(0)[3] & bit)


def setraw_asserts(boss):
    try:
        boss.tty_setraw_before_farewell()
    except AssertionError:
        return True
    return False


before_enter = setraw_asserts(litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"<FAREWELL>"))
mute = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"")
with mute:
    without_farewell = setraw_asserts(mute)

termios.tcsetattr = tcsetattr_after_marker

boss = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"<FAREWELL>")
with boss:
    cbreak = (lflag_has(termios.ISIG), lflag_has(termios.ICANON))
    boss.tty_setraw_before_farewell()
    raw = (lflag_has(termios.ISIG), lflag_has(termios.ICANON))
termios.tcsetattr = real_tcsetattr
print("RESULT", repr((cbreak, raw, before_enter, without_farewell)), flush=True)
"""


_TERMINAL_BOSS_RETURN_CHILD_ = r"""
import os, sys
sys.path.insert(0, sys.argv[1])
import litpyglass

farewell_bytes = sys.argv[2].encode()
sync_fileno = int(sys.argv[3])
boss = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=farewell_bytes)
print("READY1", flush=True)
os.read(sync_fileno, 1)  # a Return has been struck on the Terminal
with boss:
    queued = boss.read_one_byte()
    print("READY2", flush=True)
    entered = boss.read_one_byte()
    raw = entered
    if farewell_bytes:
        boss.tty_setraw_before_farewell()
        print("READY3", flush=True)
        raw = boss.read_one_byte()
print("RESULT", repr((queued, entered, raw)), flush=True)
"""


def _try_terminal_boss_return_() -> None:
    """Try which Bytes the Return Key sends, as specs.md § 1 says"""

    farewells = ("", "<F>")  # Enter with tty.setraw, and Enter with tty.setcbreak

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(farewells)) as executor:
        results = tuple(executor.map(_try_return_child_, farewells))

    # (queued before Enter, struck after Enter, struck after tty_setraw_before_farewell)

    assert results[0] == (b"\n", b"\r", b"\r"), results  # tty.setraw at Enter, so ⌃M after
    assert results[1] == (b"\n", b"\n", b"\r"), results  # tty.setcbreak keeps ⌃J till setraw


def _try_return_child_(farewell: str) -> object:
    """Run a Child on a Pty, striking Return before Enter and after each stage"""

    here = os.path.dirname(os.path.abspath(litpyglass.__file__))

    sync_read_fileno, sync_write_fileno = os.pipe()
    master_fileno, slave_fileno = pty.openpty()
    argv = [sys.executable, "-I", "-c", _TERMINAL_BOSS_RETURN_CHILD_, here, farewell]
    argv.append(str(sync_read_fileno))
    process = subprocess.Popen(
        argv,
        stdin=slave_fileno,
        stdout=slave_fileno,
        stderr=slave_fileno,
        pass_fds=(sync_read_fileno,),
    )
    os.close(slave_fileno)

    terminal_output = bytearray()

    _pty_read_till_marker_(master_fileno, terminal_output, b"READY1")
    os.write(master_fileno, b"\r")  # struck before Enter
    time.sleep(0.05)
    os.write(sync_write_fileno, b"g")

    _pty_read_till_marker_(master_fileno, terminal_output, b"READY2")
    os.write(master_fileno, b"\r")  # struck after Enter

    if farewell:
        _pty_read_till_marker_(master_fileno, terminal_output, b"READY3")
        os.write(master_fileno, b"\r")  # struck after tty_setraw_before_farewell

    _pty_read_till_marker_(master_fileno, terminal_output, b"RESULT (")
    _pty_read_till_marker_(master_fileno, terminal_output, b")\r\n")
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        process.kill()  # a Child that never printed its RESULT is still blocked reading Input
        process.wait()
    os.close(master_fileno)
    os.close(sync_read_fileno)
    os.close(sync_write_fileno)

    screen_decode = bytes(terminal_output).decode(errors="replace")
    assert "RESULT " in screen_decode, (screen_decode,)
    result_decode = screen_decode.split("RESULT ")[1].split("\r\n")[0]
    result: object = ast.literal_eval(result_decode)

    return result


def _try_terminal_boss_farewell_() -> None:
    """Try the TerminalBoss farewell, as specs.md § 1 says"""

    here = os.path.dirname(os.path.abspath(litpyglass.__file__))

    pid, master_fileno = pty.fork()
    if pid == 0:
        os.execv(
            sys.executable,
            [sys.executable, "-I", "-c", _TERMINAL_BOSS_FAREWELL_CHILD_, here],
        )

    terminal_output = bytearray()
    deadline = time.monotonic() + 10
    while (b")\r\n" not in terminal_output) and (time.monotonic() < deadline):
        if select.select([master_fileno], [], [], 0.05)[0]:
            try:
                terminal_output.extend(os.read(master_fileno, 4096))
            except OSError:
                break

    os.waitpid(pid, 0)
    os.close(master_fileno)

    heard = bytes(terminal_output)
    assert b"<FAREWELL><RESTORED>" in heard, (heard,)  # the farewell leaves before the restore

    tty_result = ast.literal_eval(heard.split(b"RESULT ")[1].split(b"\r\n")[0].decode())
    tty_expected = ((True, False), (False, False), True, True)  # (ISIG, ICANON) in cbreak, then
    # after setraw, then whether setraw asserted before Enter, and without a farewell
    assert tty_result == tty_expected, (tty_result, tty_expected)


_TERMINAL_BOSS_TYPEAHEAD_CHILD_ = r"""
import os, sys, time
sys.path.insert(0, sys.argv[1])
import litpyglass

sync_fileno = int(sys.argv[2])
boss = litpyglass.TerminalBoss(typeahead=b"ab", farewell_bytes=b"")
print("READY1", flush=True)
os.read(sync_fileno, 1)  # 'X' has been typed on the Terminal
with boss:
    first = boss.read_one_byte()
    second = boss.read_one_byte()
    selects_in_0ms = boss.stdio_select_select(timeout=0.0)
    start = time.monotonic()
    selects_in_1s = boss.stdio_select_select(timeout=1.0)
    waited_about_150ms = 0.1 <= (time.monotonic() - start) < 0.6
    third = boss.read_one_byte()
print(
    "RESULT",
    repr((first, second, selects_in_0ms, selects_in_1s, waited_about_150ms, third)),
    flush=True,
)
"""


def _try_terminal_boss_typeahead_() -> None:
    """Try TerminalBoss reading Typeahead, as specs.md § 9 says"""

    result = _pty_run_child_(_TERMINAL_BOSS_TYPEAHEAD_CHILD_, terminal_bytes=b"X")

    expected = (b"X", b"a", True, True, True, b"b")  # Terminal first, then Typeahead, and 2 selects
    assert result == expected, (result, expected)


_TERMINAL_BOSS_CHUNKS_CHILD_ = r"""
import os, sys
sys.path.insert(0, sys.argv[1])
import litpyglass

sync_fileno = int(sys.argv[2])
boss = litpyglass.TerminalBoss(typeahead=b"ab", farewell_bytes=b"")
print("READY1", flush=True)
os.read(sync_fileno, 1)  # 'XY' has been typed on the Terminal
with boss:
    chunks = tuple(boss.read_some_bytes_if() for _ in range(4))
print("RESULT", repr(chunks), flush=True)
"""


def _try_terminal_boss_chunks_() -> None:
    """Try TerminalBoss reading Typeahead in chunks, as specs.md § 9 says"""

    result = _pty_run_child_(_TERMINAL_BOSS_CHUNKS_CHILD_, terminal_bytes=b"XY")

    expected = (b"X", b"Y", b"a", b"b")  # each Byte alone, though 'XY' arrived all at once
    assert result == expected, (result, expected)


_TERMINAL_BOSS_KEEPS_CHILD_ = r"""
import os, sys
sys.path.insert(0, sys.argv[1])
import litpyglass

sync_fileno = int(sys.argv[2])
boss = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"")
boss2 = litpyglass.TerminalBoss(typeahead=b"abc", farewell_bytes=b"")
print("READY1", flush=True)
os.read(sync_fileno, 1)  # 'XYZ' has been typed on the Terminal
with boss:
    burst = boss.read_some_bytes_if()
with boss2:
    one = boss2.read_one_byte_if()
    chunk = boss2.read_some_bytes_if()
    two = boss2.read_one_byte_if()
print(
    "RESULT",
    repr(
        (
            (burst, bytes(boss.ibk.ba), boss.ibk.nano_list),
            (one, chunk, two, bytes(boss2.ibk.ba), boss2.ibk.nano_list),
        )
    ),
    flush=True,
)
"""


def _try_terminal_boss_keeps_input_() -> None:
    """Try TerminalBoss keeping each Byte read, and when, as specs.md § 1 says"""

    result = _pty_run_child_(_TERMINAL_BOSS_KEEPS_CHILD_, terminal_bytes=b"XYZ")

    (burst, burst_kept, burst_nanos), (one, chunk, two, typed_kept, typed_nanos) = typing.cast(
        tuple[tuple[bytes, bytes, list[int]], tuple[bytes, bytes, bytes, bytes, list[int]]], result
    )

    # a burst of Bytes read at once is kept once, all with one Nanos

    assert (burst, burst_kept) == (b"XYZ", b"XYZ"), (burst, burst_kept)
    assert len(burst_nanos) == 3 and len(set(burst_nanos)) == 1, burst_nanos

    # Typeahead Bytes are read through the same defs and kept once each, each with its own Nanos

    assert (one, chunk, two) == (b"a", b"b", b"c"), (one, chunk, two)
    assert typed_kept == b"abc", typed_kept
    assert len(typed_nanos) == 3, typed_nanos
    gaps = list(later - early for early, later in zip(typed_nanos, typed_nanos[1:]))
    assert all(_ >= 100_000_000 for _ in gaps), (gaps, typed_nanos)  # each waits about 150ms


def _pty_run_child_(child_code: str, terminal_bytes: bytes) -> object:
    """Run this Python on a Pty, type these Bytes when it says READY1, and return its RESULT"""

    here = os.path.dirname(os.path.abspath(litpyglass.__file__))

    sync_read_fileno, sync_write_fileno = os.pipe()
    master_fileno, slave_fileno = pty.openpty()
    argv = [sys.executable, "-I", "-c", child_code, here, str(sync_read_fileno)]
    process = subprocess.Popen(
        argv,
        stdin=slave_fileno,
        stdout=slave_fileno,
        stderr=slave_fileno,
        pass_fds=(sync_read_fileno,),
    )
    os.close(slave_fileno)

    terminal_output = bytearray()

    _pty_read_till_marker_(master_fileno, terminal_output, b"READY1")
    os.write(master_fileno, terminal_bytes)  # typed before the Child reads Input
    time.sleep(0.05)
    os.write(sync_write_fileno, b"g")

    _pty_read_till_marker_(master_fileno, terminal_output, b"RESULT (")
    _pty_read_till_marker_(master_fileno, terminal_output, b")\r\n")
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        process.kill()  # a Child that never printed its RESULT is still blocked reading Input
        process.wait()
    os.close(master_fileno)
    os.close(sync_read_fileno)
    os.close(sync_write_fileno)

    screen_decode = bytes(terminal_output).decode(errors="replace")
    assert "RESULT " in screen_decode, (screen_decode,)
    result_decode = screen_decode.split("RESULT ")[1].split("\r\n")[0]
    result: object = ast.literal_eval(result_decode)

    return result


def _try_typeahead_() -> None:
    """Try the --typeahead flag, as specs.md § 9 says"""

    master_fileno, slave_fileno = pty.openpty()
    argv = [sys.executable, "-I", litpyglass.__file__, "--egg=strikes", "--typeahead=\r\r\r"]
    with tempfile.TemporaryDirectory() as cwd:  # takes the files the egg writes at exit
        process = subprocess.Popen(
            argv, stdin=slave_fileno, stdout=slave_fileno, stderr=slave_fileno, cwd=cwd
        )
        os.close(slave_fileno)

        terminal_output = bytearray()

        deadline = time.monotonic() + 5
        while (process.poll() is None) and (time.monotonic() < deadline):
            _pty_read_once_(master_fileno, terminal_output)

        returncode = process.poll()
        if returncode is None:
            process.kill()
            process.wait()

    os.close(master_fileno)

    screen_decode = bytes(terminal_output).decode(errors="replace")
    assert returncode == 0, (returncode, screen_decode)


def _try_is_quitting_stalwarts_() -> None:
    """Try that a Stalwart is a Regex of the whole Bytes of a Frame, as specs.md § 4 says"""

    north = b"\033[A"
    mega = 10**6

    # Take three same Frames, 200 ms apart, the last one just now, which do tell us to quit

    fake = FakeKeeperBoss()
    boss = typing.cast(litpyglass.TerminalBoss, fake)
    tft = litpyglass.TerminalFrameTaker(boss)

    now_nano = time.perf_counter_ns()  # is_quitting_shape reads this same clock
    for i in range(3):
        nano = now_nano - ((2 - i) * 200 * mega)
        for code in north:
            b = bytes([code])
            fake.ibk.append_one_byte(b, nano=nano)
            tft.take_one_byte(b, peek="")

    datas = list(_.to_frame_bytes() for _ in tft.frames)
    assert datas == [north, north, north], (datas,)

    # Quit, or do not quit, by whether a Stalwart matches the whole Frame

    cases: tuple[tuple[tuple[bytes, ...], bool], ...] = (
        ((), True),  # no Stalwart
        ((rb"\033\[A",), False),  # the whole Frame, spelled out
        ((re.escape(north),), False),  # the whole Frame, escaped
        ((rb"\033\[[A-D]",), False),  # any of four Frames
        ((rb"\033\[[0-9]*A",), False),  # with a Pn or with none
        ((rb"\033\[",), True),  # only its start
        ((rb"\[A",), True),  # only its end
        ((rb"\033\[B", rb"\033\[A"), False),  # the second Stalwart of two
    )

    for stalwarts, want in cases:
        got = tft.is_quitting_frames(stalwarts=stalwarts)
        assert got is want, (got, want, stalwarts)


class FakeKeeperBoss:
    """Stand in for a TerminalBoss that only keeps Input Bytes and when they came"""

    def __init__(self) -> None:
        self.ibk = litpyglass.ByteKeeper()


def _try_is_quitting_frames_() -> None:
    """Try which strikes quit --egg=strikes, as specs.md § 4 says"""

    cases = (
        (b"\r", 3, True, ""),  # ⏎ ⏎ ⏎
        (b"\r", 2, False, ""),
        (b"\033[", 3, True, ""),  # ⎋[ ⎋[ ⎋[ with the 3rd still an Open Frame
        (b"\033", 3, False, "⎋⎋ '' b'\\033\\033' +"),  # ⎋ ⎋ ⎋ with the 2nd joined to the 1st
        (b"\033\033", 3, True, ""),  # ⎋⎋ ⎋⎋ ⎋⎋
        (b"\033", 6, True, ""),  # ⎋ ⎋ ⎋ ⎋ ⎋ ⎋ joined in pairs
        (b"x", 3, False, ""),  # Text
        (b"\r\r\r", 1, False, "⏎ '' b'\\r'\r\n\r\x1b[K" * 2 + "⏎ '' b'\\r'\r\n"),  # ⏎ ⏎ ⏎ pasted
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(cases)) as executor:
        results = tuple(
            executor.map(lambda case: _try_egg_quit_("strikes", (case[0],) * case[1], b""), cases)
        )

    for case, (quit, screen_decode) in zip(cases, results):
        data, count, want, shows = case
        assert quit == want, (quit, want, data, count)
        assert shows in screen_decode, (shows, data, count, screen_decode)


_SKATER_HAIL_ = "\033[m\033[?25h"  # reverts Text Styles, shows the Real Cursor
_SKATER_FAREWELL_ = "\r" + _SKATER_HAIL_ + "\033[32100B\033[A"  # the same, then parks the Cursor


def _skater_move_(warp: str) -> str:
    """Spell what --egg=skater writes to leave a Reverse Pair and move, away from every edge"""

    move_text = "\033[7m  \033[m\b\b" + warp
    return move_text


def _try_is_quitting_shape_() -> None:
    """Try that the quitting shape reads a list or a tuple of pairs alike, as specs.md § 4 says"""

    now = time.perf_counter_ns()
    ms = 10**6

    slow = ((now - 400 * ms, b"\r"), (now - 250 * ms, b"\r"), (now - 100 * ms, b"\r"))  # 150ms apart
    fast = ((now - 400 * ms, b"\r"), (now - 350 * ms, b"\r"), (now - 300 * ms, b"\r"))  # 50ms apart
    pair = slow[1:]  # two Bytes only

    for pairs, quits in ((slow, True), (fast, False), (pair, False)):
        assert litpyglass.is_quitting_shape(pairs) is quits, (pairs, quits)
        assert litpyglass.is_quitting_shape(list(pairs)) is quits, (pairs, quits)


def _try_skater_quits_() -> None:
    """Try which strikes quit --egg=skater, as specs.md § 8 says"""

    def reverse(*pairs: tuple[int, int]) -> dict[tuple[int, int], tuple[str, bool]]:
        """Say the Cells of each Reverse Pair at (Row, Column) of its left Cell"""

        reverse_by_yx = dict(
            ((row_y, column_x + dx), (" ", True)) for (row_y, column_x) in pairs for dx in (0, 1)
        )
        return reverse_by_yx

    # (steps, quits, the Cells marked, Cursor at Row Column, if the Cursor is hidden)

    cases = (
        ((b"\r",) * 3, True, {(1, 1): ("X", False)}, None, False),  # ⏎ ⏎ ⏎ quit, leaving the X
        ((b"\r",) * 2, False, {(1, 1): ("O", False)}, (1, 1), False),  # X then O, replaced in place
        ((b"\r\r\r",), False, {(1, 1): ("X", False)}, (1, 1), False),  # ⏎ ⏎ ⏎ pasted
        ((b"x\033[C",), False, reverse((1, 1)), (1, 3), False),  # x, then → undoes the X
        ((b"\033[C",) * 3, False, reverse((1, 1), (1, 3), (1, 5)), (1, 7), False),  # → → →
        ((b"\033[A",) * 3, False, reverse((1, 1)), (2, 1), True),  # ↑ ↑ ↑ bounce on a Reverse Pair
        ((b"\033[D",) * 3, False, reverse((1, 1)), (1, 3), True),  # ← ← ← bounce on a Reverse Pair
        ((b"\033[B",) * 3, False, reverse((1, 1), (2, 1), (3, 1)), (4, 1), False),  # ↓ ↓ ↓
        ((b"\033",), False, {(1, 1): ("1", False)}, (1, 1), False),  # ⎋ the Open Frame of 1 Byte
        ((b"\033[",), False, {(1, 1): ("2", False)}, (1, 1), False),  # ⎋[ 2 Bytes
        ((b"\033[12345678",), False, {(1, 1): ("0", False)}, (1, 1), False),  # 10 Bytes
        ((b"x\033[",), False, {(1, 1): ("3", False)}, (1, 1), False),  # x, then ⎋[
        (  # ⎋[C the Taken Arrow resets the count, so ⎋[ shows 2 again, a Cell east
            (b"x\033[C\033[",),
            False,
            {**reverse((1, 1)), (1, 3): ("2", False)},
            (1, 3),
            False,
        ),
        ((b"\033[1;2D\033[A",), False, reverse((1, 1)), (2, 3), False),  # ⇧↖ moves as ↖, to ↘
        ((b"\033[1;2C",), False, reverse((1, 1)), (1, 3), False),  # ⇧→ moves as →
        ((b"\033\033[A",), False, reverse((1, 1)), (2, 1), False),  # ⌥↑ bounces as ↑ does
        ((b"\033[1;2C",) * 3, False, reverse((1, 1), (1, 3), (1, 5)), (1, 7), False),  # ⇧→ x3
        ((b"\033\033[A\033[1;2C",), False, reverse((1, 1)), (1, 3), False),  # ⌥⇧↗ moves as ↗, to →
        ((b"\033\033[D\033[B",), False, reverse((1, 1)), (2, 1), False),  # ⎋⇧↙ moves as ↙, to ↓
        ((b"\033[6~",), False, reverse((1, 1)), (2, 1), False),  # ⇧Fn↓ moves as ↓
        ((b"\033[5~\033[F",), False, reverse((1, 1)), (1, 3), False),  # ⇧Fn↗ moves as ↗, to →
        ((b"\033[F\033[B",), False, reverse((1, 1)), (2, 3), False),  # ⇧Fn↘ moves as ↘
        (  # ↓ and → struck at once join as ↘, which moves 1 Row and 2 Columns
            (b"\033[B\033[C",),
            False,
            reverse((1, 1)),
            (2, 3),
            False,
        ),
        ((b"\033[A\033[C",), False, reverse((1, 1)), (1, 3), False),  # ↗ on the top Row moves as →
        ((b"\033[B\033[D",), False, reverse((1, 1)), (2, 1), False),  # ↙ at the West edge moves as ↓
        ((b"\033[A\033[D",), False, reverse((1, 1)), (2, 3), False),  # ↖ in the corner bounces to ↘
        (  # ↘ ↘ ↘ do not quit, since each pair moves the Cursor
            (b"\033[B\033[C",) * 3,
            False,
            reverse((1, 1), (2, 3), (3, 5)),
            (4, 7),
            False,
        ),
        ((b"\033[B", b"\033[C"), False, reverse((1, 1), (2, 1)), (2, 3), False),  # 150ms apart, ↓ →
        (  # ↘ ↘ then ↖ back onto the 2nd Pair, so a Plain Pair covers it and the Cursor hides
            (b"\033[B\033[C" * 2, b"\033[A\033[D"),
            False,
            reverse((1, 1), (3, 5)),
            (2, 3),
            True,
        ),
        (  # ↘ ↘ then ↗ one Row up and two Columns East of the 3rd Pair
            (b"\033[B\033[C" * 2, b"\033[A\033[C"),
            False,
            reverse((1, 1), (2, 3), (3, 5)),
            (2, 7),
            False,
        ),
        (  # ↘ ↘ then ↙ one Row down and two Columns West of the 3rd Pair
            (b"\033[B\033[C" * 2, b"\033[B\033[D"),
            False,
            reverse((1, 1), (2, 3), (3, 5)),
            (4, 3),
            False,
        ),
        ((b"\033",) + (b"\r",) * 4, True, {(1, 1): ("O", False)}, None, False),  # ⎋ then ⏎ x4
    )

    # Each Shifted Cardinal Arrow, struck 3 times, moves as its bare Arrow does and never quits

    bare_by_arrow = {  # (the Cells marked, Cursor at Row Column, if the Cursor is hidden) of 3 bare
        "←": (reverse((1, 1)), (1, 3), True),  # bounces on a Reverse Pair
        "↑": (reverse((1, 1)), (2, 1), True),
        "↓": (reverse((1, 1), (2, 1), (3, 1)), (4, 1), False),
        "→": (reverse((1, 1), (1, 3), (1, 5)), (1, 7), False),
    }
    shifted_frames = (  # each Frame and the bare arrow it moves as
        (b"\033[1;2D", "←"),  # ⇧←
        (b"\033b", "←"),  # ⌥←
        (b"\033f", "→"),  # ⌥→
        (b"\033\033[A", "↑"),  # ⌥↑
        (b"\033\033[B", "↓"),  # ⌥↓
        (b"\033\033[D", "←"),  # ⎋⇧←
        (b"\033\033[C", "→"),  # ⎋⇧→
        (b"\033[5~", "↑"),  # ⇧Fn↑
        (b"\033[6~", "↓"),  # ⇧Fn↓
        (b"\033[F", "→"),  # ⇧Fn→
        (b"\033[H", "←"),  # ⇧Fn←
    )
    shifted_cases = tuple(
        ((frame,) * 3, False, *bare_by_arrow[arrow]) for (frame, arrow) in shifted_frames
    )

    all_cases = cases + shifted_cases

    replies24x80 = b"\033[1;1R\033[8;24;80t"  # the Terminal replies with Row 1 Column 1, and 24 x 80

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(all_cases)) as executor:
        results = tuple(
            executor.map(lambda case: _try_egg_quit_("skater", case[0], replies24x80), all_cases)
        )

    for case, (quit, screen_decode) in zip(all_cases, results):
        strike_steps, want, want_mark_by_yx, want_cursor_yx, want_is_hidden = case
        assert quit == want, (quit, want, strike_steps, screen_decode)

        mark_by_yx, cursor_yx, is_hidden = _skater_state_(
            screen_decode, screen_width=80, screen_height=24
        )
        assert mark_by_yx == want_mark_by_yx, (
            mark_by_yx,
            want_mark_by_yx,
            strike_steps,
            screen_decode,
        )
        assert is_hidden == want_is_hidden, (is_hidden, want_is_hidden, strike_steps, screen_decode)
        if want_cursor_yx is not None:  # a Quit parks the Cursor, so only a still running case says
            assert cursor_yx == want_cursor_yx, (
                cursor_yx,
                want_cursor_yx,
                strike_steps,
                screen_decode,
            )

        launch = "\033[6n\033[18t" + _SKATER_HAIL_
        # writes the Asks, then shows the Cursor and goes West once the Screen is known
        assert launch in screen_decode, (launch, strike_steps, screen_decode)

        farewell = _SKATER_FAREWELL_
        assert (farewell in screen_decode) == quit, (farewell, quit, strike_steps, screen_decode)


def _skater_state_(
    screen_decode: str, screen_width: int, screen_height: int
) -> tuple[dict[tuple[int, int], tuple[str, bool]], tuple[int, int], bool]:
    """Replay the Bytes and say the Cells marked, where the Cursor sits, and if it is hidden"""

    screen_cells, row_y, column_x, _ = _screen_of_(
        screen_decode, screen_width=screen_width, screen_height=screen_height
    )

    # (Row, Column) of each Cell not plain

    mark_by_yx: dict[tuple[int, int], tuple[str, bool]] = dict()
    for cell_y, row in enumerate(screen_cells, start=1):
        for cell_x, cell in enumerate(row, start=1):
            if cell != (" ", False):
                mark_by_yx[(cell_y, cell_x)] = cell

    is_hidden = screen_decode.rfind("\033[?25l") > screen_decode.rfind("\033[?25h")
    cursor_yx = (row_y, column_x)
    return (mark_by_yx, cursor_yx, is_hidden)


def _try_skater_edge_() -> None:
    """Try --egg=skater at the far East Column, as specs.md § 8 says"""

    replies20 = b"\033[1;1R\033[8;5;20t"  # Row 1 Column 1, and a Screen 5 high, 20 wide
    replies21 = b"\033[1;1R\033[8;5;21t"  # the same, 21 wide

    cases = (
        (20, replies20, 9),  # → x 9 reaches the pixel at Columns 19 and 20
        (20, replies20, 10),  # → x 10 bounces off the East edge to the pixel at 17 and 18
        (21, replies21, 9),  # an odd Width acts as the even Width below it
        (21, replies21, 10),
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(cases)) as executor:
        results = tuple(
            executor.map(
                lambda case: _try_egg_quit_("skater", (b"\033[C",) * case[2], case[1]), cases
            )
        )

    for case, (quit, screen_decode) in zip(cases, results):
        screen_width, _, count = case
        assert not quit, (quit, screen_width, count, screen_decode)

        mark_by_yx, cursor_yx, is_hidden = _skater_state_(
            screen_decode, screen_width=screen_width, screen_height=5
        )

        want_x = 19 if (count == 9) else 17  # the left Cell of the pixel the Cursor sits on
        assert cursor_yx == (1, want_x), (cursor_yx, want_x, screen_width, count, screen_decode)

        # 9 Arrows leave 9 Reverse Pairs and the Cursor on a bare Cell, and 10 bounce onto the 9th
        want_inverse = list(range(1, 19)) if (count == 9) else (list(range(1, 17)) + [19, 20])
        inverse = list(column_x for ((row_y, column_x), cell) in mark_by_yx.items() if cell[1])
        assert inverse == want_inverse, (inverse, want_inverse, screen_width, count, screen_decode)

        spill = list(xy for xy in mark_by_yx.keys() if xy[0] != 1 or xy[1] > 20)
        assert not spill, (spill, screen_width, count, screen_decode)  # never Column 21, never Row 2

        want_is_hidden = count == 10  # the Cursor sits on a Reverse Pair, so a Plain Pair hides it
        assert is_hidden == want_is_hidden, (
            is_hidden,
            want_is_hidden,
            screen_width,
            count,
            screen_decode,
        )

    # Settle for the half of an Intercardinal Arrow that fits, else bounce to its opposite

    north_east = b"\033[A\033[C"  # ↑ and → struck at once join as ↗
    south = b"\033[B"
    pair = "\033[7m  \033[m"  # a Reverse Pair
    edge_cases = (  # (replies, the Bytes struck, the Bytes written to leave the Pair and move)
        (  # ↗ at the East edge moves as ↑
            b"\033[3;19R\033[8;5;20t",
            north_east,
            pair + "\b" + "\033[A",
        ),
        (  # ↗ bounces to ↙ in the top East corner
            b"\033[1;19R\033[8;5;20t",
            north_east,
            pair + "\b" + "\033[B" + "\033[D" * 2,
        ),
        (  # ↓ at the South edge bounces to ↑
            b"\033[5;1R\033[8;5;20t",
            south,
            pair + "\b\b" + "\033[A",
        ),
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(edge_cases)) as executor:
        edge_results = tuple(
            executor.map(lambda case: _try_egg_quit_("skater", (case[1],), case[0]), edge_cases)
        )

    for edge_case, (quit, screen_decode) in zip(edge_cases, edge_results):
        replies, _, want_text = edge_case
        assert not quit, (quit, edge_case, screen_decode)

        hail_at = screen_decode.index(_SKATER_HAIL_) + len(_SKATER_HAIL_)
        text = screen_decode[hail_at : hail_at + len(want_text)]
        assert text == want_text, (text, want_text, replies, screen_decode)


_SKATER_FUZZ_STEPS_ = 10  # steps per sequence, 150ms apart


def _try_skater_fuzz_() -> None:
    """Try --egg=skater against a model of specs.md § 8, on seeded random strikes"""

    cases = list()
    for seed in range(12):
        steps = _skater_steps_(seed)
        for screen_width in (20, 21):
            replies = f"\033[1;1R\033[8;5;{screen_width}t".encode()  # Row 1 Column 1
            cases.append((seed, steps, screen_width, replies))

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(cases)) as executor:
        outcomes = list(executor.map(lambda case: _try_egg_quit_("skater", case[1], case[3]), cases))

    for case, (quit, screen_decode) in zip(cases, outcomes):
        seed, steps, screen_width, _ = case
        assert not quit, (quit, seed, screen_width, steps, screen_decode)

        mark_by_yx, cursor_yx, is_hidden = _skater_state_(
            screen_decode, screen_width=screen_width, screen_height=5
        )

        # Never leave the Screen, never write the Column 21 that an odd Width leaves alone

        assert 1 <= cursor_yx[0] <= 5, (cursor_yx, seed, screen_width, steps, screen_decode)
        assert 1 <= cursor_yx[1] <= screen_width, (cursor_yx, seed, screen_width, screen_decode)
        spill = list(yx for yx in mark_by_yx.keys() if yx[1] > 20)
        assert not spill, (spill, seed, screen_width, steps, screen_decode)

        # Meet the model

        want = _skater_walk_(steps, screen_width=screen_width, screen_height=5)
        want_mark_by_yx, want_cursor_yx, want_is_hidden = want
        assert mark_by_yx == want_mark_by_yx, (
            mark_by_yx,
            want_mark_by_yx,
            seed,
            screen_width,
            steps,
            screen_decode,
        )
        assert cursor_yx == want_cursor_yx, (
            cursor_yx,
            want_cursor_yx,
            seed,
            screen_width,
            steps,
            screen_decode,
        )
        assert is_hidden == want_is_hidden, (
            is_hidden,
            want_is_hidden,
            seed,
            screen_width,
            steps,
            screen_decode,
        )


def _skater_steps_(seed: int) -> tuple[bytes, ...]:
    """Pick the strikes of one sequence, each a step 150ms apart, leaning on one Arrow"""

    rng = random.Random(seed)

    bytes_by_arrow = {"↑": b"\033[A", "↓": b"\033[B", "→": b"\033[C", "←": b"\033[D"}
    arrows = "→↑←↓"
    lean = arrows[seed % 4]  # the Arrow this sequence leans on
    lean_share = 0.95 if (seed < 4) else 0.40  # a runner leans on it, to run into its edge
    cross = "↑↓" if (lean in "→←") else "→←"  # the axis that a joined pair adds to the lean

    steps: list[bytes] = list()
    open_len = 0  # the Bytes of a ⎋ or ⎋[ Frame held open, 0 when none
    return_run = 0  # the ⏎ steps in a row, kept under three so as not to quit

    while len(steps) < _SKATER_FUZZ_STEPS_:
        if open_len == 1:
            steps.append(b"[")
            open_len = 2
            continue
        if open_len == 2:
            steps.append(rng.choice((b"A", b"B", b"C", b"D")))  # a tail closing ⎋[ as an Arrow
            open_len = 0
            continue

        roll = rng.random()
        rest = rng.random()  # picks among the other kinds of step
        if roll < lean_share:
            steps.append(bytes_by_arrow[lean])
        elif roll < (lean_share + 0.10):
            steps.append(bytes_by_arrow[rng.choice(arrows)])
        elif rest < 0.30:
            joined = [bytes_by_arrow[lean], bytes_by_arrow[rng.choice(cross)]]
            rng.shuffle(joined)  # either Arrow first
            steps.append(b"".join(joined))
        elif rest < 0.60:
            steps.append(rng.choice((b"x", b"y", b"z")))
        elif rest < 0.80 and return_run < 2:
            steps.append(b"\r")
        elif rest < 0.80:
            steps.append(b"x")
        else:
            steps.append(b"\033")
            open_len = 1

        return_run = (return_run + 1) if (steps[-1] == b"\r") else 0

    return tuple(steps)


def _skater_walk_(
    steps: tuple[bytes, ...], screen_width: int, screen_height: int
) -> tuple[dict[tuple[int, int], tuple[str, bool]], tuple[int, int], bool]:
    """Walk the rules of specs.md § 8 over the steps, and say the Cells, the Cursor, if hidden"""

    x_max = screen_width - (screen_width % 2)  # an odd Width acts as the even Width below it
    row_y = 1
    column_x = 1
    visited = list()  # the left Cell of each Reverse Pair written, in the order first written
    top_char = ""  # the one reply showing at the Cursor, else empty
    count = 0  # the Bytes of meaningless Frames taken since the last Arrow, mod 10
    xo = "X"
    open_len = 0  # the Bytes of a ⎋ or ⎋[ Frame held open, 0 when none
    text_len = 0  # the Bytes of a Text Frame held open, 0 when none

    for step in steps:
        if step in (b"x", b"y", b"z"):  # Text stays open and takes the next Char, and shows a Digit
            text_len += 1
            top_char = "0123456789"[(count + text_len) % 10]
            continue

        if text_len:  # any other step bounces off Text, which is then Taken, and draws X or O
            top_char = xo
            xo = "O" if (xo == "X") else "X"
            count = (count + text_len) % 10
            text_len = 0

        if step == b"\033":  # ⎋ stays open, and shows the count of its Bytes
            open_len = 1
            top_char = "0123456789"[(count + open_len) % 10]
            continue
        if open_len == 1 and step == b"[":
            open_len = 2
            top_char = "0123456789"[(count + open_len) % 10]
            continue

        if open_len == 2:  # a tail closes ⎋[ as an Arrow
            finals = list(step.decode())
            open_len = 0
        else:
            finals = re.findall(r"\033\[([ABCD])", step.decode())

        if not finals:  # a ⏎ draws X, then O, and counts its Byte
            top_char = xo
            xo = "O" if (xo == "X") else "X"
            count = (count + len(step)) % 10
            continue

        # Move 1 Row for each ↑ ↓ and 2 Columns for each ← →, else settle for the half that fits

        move_y = finals.count("B") - finals.count("A")
        move_x = 2 * (finals.count("C") - finals.count("D"))

        if (row_y, column_x) not in visited:
            visited.append((row_y, column_x))

        move = _skater_settle_(move_y, move_x, (row_y, column_x), x_max, screen_height)

        row_y += move[0]
        column_x += move[1]
        top_char = ""
        count = 0

    # The Plain Pair of a written Cell hides the Real Cursor, and covers its Reverse Pair

    is_hidden = (row_y, column_x) in visited

    mark_by_yx: dict[tuple[int, int], tuple[str, bool]] = dict()
    for cell_y, cell_x in visited:
        if (cell_y, cell_x) != (row_y, column_x):
            mark_by_yx[(cell_y, cell_x)] = (" ", True)
            mark_by_yx[(cell_y, cell_x + 1)] = (" ", True)
    if top_char:
        mark_by_yx[(row_y, column_x)] = (top_char, False)

    return (mark_by_yx, (row_y, column_x), is_hidden)


def _skater_settle_(
    move_y: int, move_x: int, yx: tuple[int, int], x_max: int, screen_height: int
) -> tuple[int, int]:
    """Settle for the half of a move that fits, else bounce to its opposite, as specs.md § 8 says"""

    def fits(dy: int, dx: int) -> bool:
        return (1 <= yx[0] + dy <= screen_height) and (1 <= yx[1] + dx <= x_max)

    if fits(move_y, move_x):
        return (move_y, move_x)
    if move_y and move_x and fits(move_y, 0):  # only the East or West half is too far
        return (move_y, 0)
    if move_y and move_x and fits(0, move_x):  # only the North or South half is too far
        return (0, move_x)

    assert fits(-move_y, -move_x), (move_y, move_x, yx)  # bounce to the opposite Arrow
    return (-move_y, -move_x)


class FakeWriteBoss:
    """Pretend to be a TerminalBoss that keeps the Bytes written"""

    def __init__(self) -> None:
        self.writes: list[bytes] = list()

    def bytes_write_flush(self, data: bytes) -> None:
        self.writes.append(data)


class FakeReadBoss:
    """Pretend to be a TerminalBoss that reads Replies and a Move at first, and then nothing"""

    def __init__(self) -> None:
        self.ibk = litpyglass.ByteKeeper()  # every Byte read, and when
        self.typeahead = bytearray()  # no Typeahead Bytes, ever
        self.reads = 0

    def read_some_bytes_if(self) -> bytes:
        self.reads += 1
        data = b"\033[1;1R\033[8;24;80t\033[B" if (self.reads == 1) else b""
        self.ibk.append_some_bytes(data, nano=time.perf_counter_ns())
        return data


class FakeSlowBoss:
    """Pretend to be a TerminalBoss that reads two chunks of Bytes, each after a 2ms wait"""

    def __init__(self) -> None:
        self.ibk = litpyglass.ByteKeeper()  # every Byte read, and when
        self.typeahead = bytearray()  # no Typeahead Bytes, ever
        self.chunks = [b"\033[B", b"q"]

    def read_some_bytes_if(self) -> bytes:
        time.sleep(0.002)
        data = self.chunks.pop(0) if self.chunks else b""
        self.ibk.append_some_bytes(data, nano=time.perf_counter_ns())
        return data


class FakeLateBoss:
    """Pretend to be a TerminalBoss that reads each given chunk of Bytes after a 20ms wait"""

    def __init__(self, chunks: list[bytes]) -> None:
        self.ibk = litpyglass.ByteKeeper()  # every Byte read, and when
        self.typeahead = bytearray()  # no Typeahead Bytes, ever
        self.chunks = list(chunks)

    def read_some_bytes_if(self) -> bytes:
        time.sleep(0.020)
        data = self.chunks.pop(0) if self.chunks else b""
        self.ibk.append_some_bytes(data, nano=time.perf_counter_ns())
        return data


class FakeChunkBoss:
    """Pretend to be a TerminalBoss that reads each given chunk of Bytes in turn, and then nothing"""

    def __init__(self, chunks: list[bytes]) -> None:
        self.ibk = litpyglass.ByteKeeper()  # every Byte read, and when
        self.typeahead = bytearray()  # no Typeahead Bytes, ever
        self.chunks = list(chunks)

    def read_some_bytes_if(self) -> bytes:
        data = self.chunks.pop(0) if self.chunks else b""
        self.ibk.append_some_bytes(data, nano=time.perf_counter_ns())
        return data


class FakeEndBoss:
    """Pretend to be a Tty TerminalBoss whose Input ends at once, with no Reply"""

    isatty = True

    def __init__(self) -> None:
        self.ibk = litpyglass.ByteKeeper()  # every Byte read, and when
        self.typeahead = bytearray()  # no Typeahead Bytes, ever

    def asks_write_flush(self, data: bytes) -> None:
        pass

    def bytes_write_flush(self, data: bytes) -> None:
        pass

    def str_print(self, text: str) -> None:
        print(text, end="\r\n")  # as a Boss entered ends its Line

    def read_some_bytes_if(self) -> bytes:
        return b""


class FakeJoinBoss:
    """Pretend to be a TerminalBoss that reads chunks of Bytes, and says if more are available"""

    def __init__(self, chunks: tuple[bytes, ...], typeahead: bytes, arrow_wait_nanos: int) -> None:
        self.arrow_wait_nanos = arrow_wait_nanos  # the Nanos the peek must ask us to wait
        self.chunks = list(chunks)  # the Bytes of each read, in order
        self.typeahead = bytearray(typeahead)  # the Bytes that come one per read, ahead of chunks
        self.events: list[str] = list()  # "idle", "read", "select", "yield", in the order met
        self.ibk = litpyglass.ByteKeeper()  # every Byte read, and when

    def read_some_bytes_if(self) -> bytes:
        self.events.append("read")
        data = b""
        if self.typeahead:
            data = bytes([self.typeahead.pop(0)])
        elif self.chunks:
            data = self.chunks.pop(0)

        self.ibk.append_some_bytes(data, nano=time.perf_counter_ns())
        return data

    def stdio_select_select(self, timeout: float | None) -> bool:
        assert timeout == self.arrow_wait_nanos / 1e9, (timeout, self.arrow_wait_nanos)
        self.events.append("select")
        hit = bool(self.chunks) or bool(self.typeahead)  # even a chunk of no Bytes is available
        return hit


def _try_skater_launch_edge_() -> None:
    """Try --egg=skater launched in the far East Columns, as specs.md § 8 says"""

    left = b"\033[D"
    right = b"\033[C"

    cases = (
        (b"\033[1;21R\033[8;5;21t", 2, left),  # Column 21 of 21 lies past x_max 20, so 2 steps West
        (b"\033[1;21R\033[8;5;21t", 2, right),
        (b"\033[1;20R\033[8;5;21t", 1, left),  # Column 20 of 21 has no room for a Pair, so 1 step
        (b"\033[1;20R\033[8;5;21t", 1, right),
        (b"\033[1;20R\033[8;5;20t", 1, left),  # Column 20 of 20, the same on an even Width
        (b"\033[1;20R\033[8;5;20t", 1, right),
        (b"\033[1;22R\033[8;5;22t", 1, left),
        (b"\033[1;23R\033[8;5;23t", 2, left),
        (b"\033[1;19R\033[8;5;21t", 0, left),  # Column 19 of 21 has room for a Pair, so no step
        (b"\033[1;10R\033[8;5;21t", 0, left),
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(cases)) as executor:
        results = tuple(
            executor.map(lambda case: _try_egg_quit_("skater", (case[2],), case[0]), cases)
        )

    for case, (quit, screen_decode) in zip(cases, results):
        assert not quit, (quit, case, screen_decode)  # no assert failed, no early exit
        assert "Traceback" not in screen_decode, (case, screen_decode)

        hail_at = screen_decode.index(_SKATER_HAIL_) + len(_SKATER_HAIL_)
        back_count = case[1]
        steps = screen_decode[hail_at : hail_at + back_count + 1]
        assert steps == ("\b" * back_count) + steps[-1:], (case, steps, screen_decode)
        assert steps[back_count:] != "\b", (case, steps, screen_decode)  # exactly as many as needed

        assert "\033[7m  \033[m" in screen_decode, (case, screen_decode)  # the Arrow left a Pair


def _try_input_file_() -> None:
    """Try the three files an egg writes at exit, as specs.md § 1, § 8, and § 9 say"""

    replies = b"\033[1;1R\033[8;24;80t"
    names_want = ["i.jsonl", "o.jsonl", "o.typescript"]

    cases = (  # (egg, Input piped in, then Stdin Eof)
        ("bytes", b"a\0\377\r"),
        ("bytes", b""),
        ("nanos", b"ab\r"),
        ("frames", b"x\033[A\r"),
        ("strikes", b"x\033[A\r"),
        ("skater", replies + b"\033[C" + b"x"),
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(cases)) as executor:
        futures = list(executor.submit(_try_egg_input_file_, egg, data) for (egg, data) in cases)

    for (egg, data), future in zip(cases, futures):
        returncode, (before, after), names, (i_decode, o_decode), (stdout, typescript) = (
            future.result()
        )
        assert returncode == 0, (egg, returncode)
        assert names == names_want, (egg, names)
        assert i_decode is not None, (egg,)
        assert o_decode is not None, (egg,)
        assert typescript is not None, (egg,)

        # Meet the Spec for each of the two Json Lines files

        i_pairs = _try_jsonl_pairs_(egg, i_decode)
        o_pairs = _try_jsonl_pairs_(egg, o_decode)

        i_codes = bytes(code for (nano, code) in i_pairs)
        assert i_codes == data, (egg, i_codes, data)  # every Byte typed, Replies included

        o_codes = bytes(code for (nano, code) in o_pairs)
        assert o_codes == typescript, (egg, o_codes, typescript)  # off a Terminal, no Asks

        # Meet the Spec for the Typescript, every Byte written, unchanged

        assert typescript == stdout, (egg, typescript, stdout)

        # Count the first wait of --egg=nanos from the first Nanos kept in the Output

        if egg == "nanos":
            launch_decode, _, waits_decode = typescript.decode().partition("to quit\n\n")
            first_wait_decode, _, _ = waits_decode.partition(" ")
            (first_nano, _), *_ = i_pairs
            assert int(first_wait_decode) == first_nano, (first_wait_decode, first_nano)

        # Count the Nanos of both files from one zero, the first Nanos kept in either

        i_nanos = list(nano for (nano, code) in i_pairs)
        o_nanos = list(nano for (nano, code) in o_pairs)
        assert o_nanos, (egg,)  # every egg writes Output
        assert min(i_nanos + o_nanos) == 0, (egg, i_nanos, o_nanos)

        for nanos in (i_nanos, o_nanos):
            assert nanos == sorted(nanos), (egg, nanos)
            assert all(_ <= (after - before) for _ in nanos), (egg, before, nanos, after)

    # Keep Bytes that arrived at once, and refuse to count from a zero later than a Nanos kept

    some = litpyglass.ByteKeeper()
    some.append_some_bytes(b"ab", nano=7)
    some.append_some_bytes(b"", nano=8)  # keeps nothing
    assert bytes(some.ba) == b"ab", (some.ba,)
    assert some.nano_list == [7, 7], (some.nano_list,)

    # Write the Bytes and Nanos kept, to the path given, and refuse to guess when they disagree

    nano_big = 10**30  # beyond 64 bits
    keeper = litpyglass.ByteKeeper()
    keeper.append_one_byte(b"\0", nano=nano_big)
    keeper.append_one_byte(b"\377", nano=nano_big + 1)

    with tempfile.TemporaryDirectory() as cwd:
        p_join = os.path.join(cwd, "p.jsonl")
        keeper.pairs_write_file(p_join, zero_nano=nano_big)
        with open(p_join, "rb") as f:
            p_decode = f.read().decode()
        want_decode = '["Nanos", "Bytes"]\n[0, 0]\n[1, 255]\n'  # counted from the zero given
        assert p_decode == want_decode, (p_decode, want_decode)

        keeper.pairs_write_file(p_join, zero_nano=(nano_big - 5))
        with open(p_join, "rb") as f:
            p_decode = f.read().decode()
        want_decode = '["Nanos", "Bytes"]\n[5, 0]\n[6, 255]\n'  # an earlier zero counts up
        assert p_decode == want_decode, (p_decode, want_decode)

        litpyglass.ByteKeeper().pairs_write_file(p_join, zero_nano=0)  # replaces it with a header
        with open(p_join, "rb") as f:
            p_decode = f.read().decode()
        assert p_decode == '["Nanos", "Bytes"]\n', (p_decode,)

        # Write an empty Typescript for a Boss who wrote nothing, over an older file

        t_join = os.path.join(cwd, "t.typescript")
        with open(t_join, "w") as f:
            f.write("older text\n")

        idle_boss = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"")
        assert not idle_boss.obk.nano_list, (idle_boss.obk.nano_list,)
        idle_boss.typescript_write_file(t_join)
        with open(t_join, "rb") as f:
            t_bytes = f.read()
        assert t_bytes == b"", (t_bytes,)

        with open(p_join, "w") as f:
            f.write("older text\n")

        later = None
        try:
            keeper.pairs_write_file(p_join, zero_nano=(nano_big + 1))  # later than the first Nanos
        except AssertionError as exc:
            later = exc
        assert later is not None, (nano_big,)

        with open(p_join) as f:
            older_text = f.read()
        assert older_text == "older text\n", (older_text,)  # never half written

        keeper.nano_list.pop()  # leaves 2 Bytes but 1 Nanos
        unequal = None
        try:
            keeper.pairs_write_file(p_join, zero_nano=nano_big)
        except AssertionError as exc:
            unequal = exc
        assert unequal is not None, (len(keeper.ba), len(keeper.nano_list))

        with open(p_join) as f:
            older_text = f.read()
        assert older_text == "older text\n", (older_text,)  # never half written

        no_directory = None
        try:
            keeper.nano_list.append(nano_big + 1)
            no_directory_join = os.path.join(cwd, "no_such_directory", "p.jsonl")
            keeper.pairs_write_file(no_directory_join, zero_nano=nano_big)
        except FileNotFoundError as exc:
            no_directory = exc
        assert no_directory is not None, (cwd,)

    # Write no file, for the Help or for a Launch that exits 1

    argvs = (
        [sys.executable, "-I", litpyglass.__file__],
        [sys.executable, "-I", litpyglass.__file__, "--egg=skater"],
    )
    for argv, returncode in zip(argvs, (0, 1)):
        with tempfile.TemporaryDirectory() as cwd:
            run = subprocess.run(
                argv, stdin=subprocess.DEVNULL, capture_output=True, timeout=10, cwd=cwd
            )
            assert run.returncode == returncode, (argv, run.returncode, run.stdout, run.stderr)
            names = os.listdir(cwd)
            assert not names, (argv, names)


def _try_jsonl_pairs_(egg: str, decode: str) -> list[tuple[int, int]]:
    """Check a Header Line, then one [Nanos, Byte] Line per Byte, and say each pair"""

    split = decode.split("\n")
    assert len(split) >= 2, (egg, split)
    header, *rows, end = split
    assert end == "", (egg, end)  # ends with "\n"
    assert header == '["Nanos", "Bytes"]', (egg, header)
    assert "\r" not in decode, (egg, decode)

    pairs = list(json.loads(_) for _ in rows)
    assert all(len(_) == 2 for _ in pairs), (egg, pairs)
    assert all(isinstance(n, int) and isinstance(c, int) for (n, c) in pairs), (egg, pairs)

    int_pairs = list((n, c) for (n, c) in pairs)
    return int_pairs


def _try_egg_input_file_(
    egg: str, data: bytes
) -> tuple[
    int, tuple[int, int], list[str], tuple[str | None, str | None], tuple[bytes, bytes | None]
]:
    """Run --egg= off a Terminal in a new directory, and say what it wrote there"""

    argv = [sys.executable, "-I", litpyglass.__file__, f"--egg={egg}"]
    with tempfile.TemporaryDirectory() as cwd:
        for name in ("i.jsonl", "o.jsonl", "o.typescript"):
            with open(os.path.join(cwd, name), "w") as f:
                f.write("older text, and longer than the header\n" * 9)  # an older file to replace

        before = time.perf_counter_ns()  # the Clock the Egg reads, shared across Processes
        run = subprocess.run(argv, input=data, capture_output=True, timeout=10, cwd=cwd)
        after = time.perf_counter_ns()

        names = sorted(os.listdir(cwd))

        decodes: list[str | None] = list()
        for name in ("i.jsonl", "o.jsonl"):
            decode = None
            if name in names:
                with open(os.path.join(cwd, name), "rb") as f:
                    decode = f.read().decode()  # no newline translation, so "\r" stays visible
            decodes.append(decode)

        typescript = None
        if "o.typescript" in names:
            with open(os.path.join(cwd, "o.typescript"), "rb") as f:
                typescript = f.read()

    i_decode, o_decode = decodes
    return (run.returncode, (before, after), names, (i_decode, o_decode), (run.stdout, typescript))


_BOSS_WRITES_CHILD_ = r"""
import json, os, sys
sys.path.insert(0, sys.argv[1])
import litpyglass

sys.stdout.reconfigure(encoding="latin-1")  # so that a Byte kept as Utf-8 would show as wrong

tb = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"")
tb.str_write("a")  # waits in the block buffer of Stdout, as off a Terminal
tb.str_print("bc")
with tb:
    tb.str_print("in")  # entered, so ends its Line as "\r\n"
tb.bytes_write_flush(b"<D>")
tb.str_write("é")
tb.asks_write_flush(b"<ASK>")

report = dict(
    ba=list(tb.obk.ba), nano_list=tb.obk.nano_list, typescript=list(tb.typescript),
)
with open(sys.argv[2], "w") as f:
    json.dump(report, f)

os._exit(0)  # exits without the flush of Stdout that a plain exit gives
"""


def _try_boss_writes_() -> None:
    """Try the TerminalBoss writers keep what they write, as specs.md § 1 and § 8 say"""

    here = os.path.dirname(os.path.abspath(litpyglass.__file__))
    with tempfile.TemporaryDirectory() as cwd:
        report_join = os.path.join(cwd, "report.json")
        argv = [sys.executable, "-I", "-c", _BOSS_WRITES_CHILD_, here, report_join]
        run = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, timeout=10)
        assert run.returncode == 0, (run.returncode, run.stdout, run.stderr)

        with open(report_join) as f:
            report = json.load(f)

    # Reach Stdout in order, the Ask at once, even with no exit flush after it

    written = b"abc\n" + b"in\r\n" + b"<D>" + b"\351"  # the é as Stdout encodes it, as Latin-1
    stdout_want = written + b"<ASK>"
    assert run.stdout == stdout_want, (run.stdout, stdout_want, run.stderr)

    # Keep every Byte in the Output, Asks too, and every Byte but the Asks in the Typescript

    ba = bytes(report["ba"])
    typescript = bytes(report["typescript"])
    assert ba == stdout_want, (ba, stdout_want)
    assert typescript == written, (typescript, written)

    # Stamp the Bytes of one write with one Nanos each, and never run the Nanos backwards

    nano_list = report["nano_list"]
    assert len(nano_list) == len(ba), (len(nano_list), len(ba))
    assert nano_list == sorted(nano_list), (nano_list,)

    lengths = (1, 3, 4, 3, 1, 5)  # "a", "bc\n", "in\r\n", "<D>", "é", "<ASK>"
    assert sum(lengths) == len(ba), (lengths, len(ba))

    here_index = 0
    for length in lengths:
        stamps = nano_list[here_index : (here_index + length)]
        assert len(set(stamps)) == 1, (here_index, length, stamps)
        here_index += length


def _try_output_routes_() -> None:
    """Try that no bare print or Stdout write escapes TerminalBoss, as specs.md § 8 says"""

    with open(litpyglass.__file__, "rb") as f:
        source_decode = f.read().decode()

    tree = ast.parse(source_decode)

    parents: dict[ast.AST, ast.AST] = dict()
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            shared = (ast.expr_context, ast.boolop, ast.operator, ast.unaryop, ast.cmpop)
            if isinstance(child, shared):
                continue
                # lists no Parent for a Load() or Store() or Add() etc, since many Parents share one

            assert child not in parents.keys(), (ast.dump(child)[:60],)
            parents[child] = node

    writers = ("print", "sys.stdout.write", "sys.stdout.buffer.write")

    found: list[tuple[str, str]] = list()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        call = ast.unparse(node.func)
        if call not in writers:
            continue

        # Name the Def that holds the Call, with its Class in front, if any

        holder = parents.get(node)
        while holder and not isinstance(holder, ast.FunctionDef):
            holder = parents.get(holder)
        assert isinstance(holder, ast.FunctionDef), (call, node.lineno)

        owner = parents.get(holder)
        prefix = f"{owner.name}." if isinstance(owner, ast.ClassDef) else ""
        found.append((f"{prefix}{holder.name}", call))

    want = [
        ("TerminalBoss._bytes_write_flush_", "sys.stdout.buffer.write"),
        ("TerminalBoss.str_write", "print"),
        ("main", "print"),  # the help prints 3 times, with no Boss
        ("main", "print"),
        ("main", "print"),
    ]
    assert sorted(found) == sorted(want), (sorted(found), sorted(want))


def _try_typescript_files_() -> None:
    """Try the o.jsonl and o.typescript files an egg writes on a Pty, as specs.md § 9 says"""

    asks = b"\033[6n\033[18t"
    replies = b"\033[1;1R\033[8;24;80t"
    arrows = (b"\033[C", b"\033[B")
    returns = (b"\r",) * 3

    cases = (  # (egg, steps struck 150ms apart, Replies sent, Bytes read in all)
        ("skater", arrows + returns, replies, replies + b"".join(arrows + returns)),
        ("strikes", (b"x",) + returns, b"", b"x" + b"".join(returns)),
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(cases)) as executor:
        futures = list(
            executor.submit(_try_egg_files_, egg, steps=steps, replies=replies)
            for (egg, steps, replies, typed) in cases
        )

    for (egg, steps, replies, typed), future in zip(cases, futures):
        quit, terminal_bytes, i_decode, o_decode, typescript = future.result()
        assert quit, (egg, len(terminal_bytes))
        assert i_decode is not None, (egg,)
        assert o_decode is not None, (egg,)
        assert typescript is not None, (egg,)

        i_pairs = _try_jsonl_pairs_(egg, i_decode)
        o_pairs = _try_jsonl_pairs_(egg, o_decode)

        i_codes = bytes(code for (nano, code) in i_pairs)
        assert i_codes == typed, (egg, i_codes, typed)

        # Meet the Spec for the Typescript, every Byte written except the Asks

        assert asks not in typescript, (egg, typescript)
        assert (asks in terminal_bytes) == (egg == "skater"), (egg, terminal_bytes)

        # The Terminal driver adds "\r" before each "\n" written while it still cooks Output
        # (the "\n" written in raw mode comes with its "\r" already)

        cooked_bytes = re.sub(rb"(?<!\r)\n", b"\r\n", typescript)
        want_bytes = (asks if (egg == "skater") else b"") + cooked_bytes
        assert terminal_bytes == want_bytes, (egg, terminal_bytes, want_bytes)

        # Meet the Spec for the Output, every Byte written, Asks too, so Asks only on a Terminal

        o_codes = bytes(code for (nano, code) in o_pairs)
        if egg == "skater":
            assert o_codes.count(asks) == 1, (egg, o_codes)
            assert o_codes.replace(asks, b"", 1) == typescript, (egg, o_codes, typescript)
        else:
            assert o_codes == typescript, (egg, o_codes, typescript)

        # Count the Nanos of both files from one zero

        i_nanos = list(nano for (nano, code) in i_pairs)
        o_nanos = list(nano for (nano, code) in o_pairs)
        assert min(i_nanos + o_nanos) == 0, (egg, i_nanos, o_nanos)
        assert i_nanos == sorted(i_nanos), (egg, i_nanos)
        assert o_nanos == sorted(o_nanos), (egg, o_nanos)

        if egg == "skater":  # writes the Farewell's "\n", from the Final Print after Exit
            assert typescript.endswith(_SKATER_FAREWELL_.encode() + b"\n"), (egg, typescript)
        else:  # writes what print() printed
            assert b"+ " in typescript, (egg, typescript)
            assert typescript.startswith(b"\nPress Return three times quickly, to quit\n\n")


def _try_egg_files_(
    egg: str, steps: tuple[bytes, ...], replies: bytes
) -> tuple[bool, bytes, str | None, str | None, bytes | None]:
    """Run --egg= on a Pty in a new directory, and say what it read, and wrote there"""

    with tempfile.TemporaryDirectory() as cwd:
        quit, terminal_bytes = _try_egg_pty_(egg, strike_steps=steps, replies=replies, cwd=cwd)

        decodes: list[str | None] = list()
        for name in ("i.jsonl", "o.jsonl"):
            decode = None
            name_join = os.path.join(cwd, name)
            if os.path.exists(name_join):
                with open(name_join, "rb") as f:
                    decode = f.read().decode()
            decodes.append(decode)

        typescript = None
        o_join = os.path.join(cwd, "o.typescript")
        if os.path.exists(o_join):
            with open(o_join, "rb") as f:
                typescript = f.read()

    i_decode, o_decode = decodes
    return (quit, terminal_bytes, i_decode, o_decode, typescript)


def _layer_after_(ts: litpyglass.TerminalShadow, text: str) -> litpyglass.TerminalLayer | None:
    """Write the Str into a new Layer over the Shadow, and say that Layer, else None"""

    forked_layer = ts.base.fork_layer()
    if not forked_layer._write_some_or_all_strs_(text):
        return None

    return forked_layer


def _try_shadow_layer_() -> None:
    """Try TerminalLayer, and the Layer inside a TerminalShadow, as specs.md § 10 says"""

    no_sgr_csi = "\033[m"
    reverse = "\033[7m"

    fake = FakeWriteBoss()
    boss = typing.cast(litpyglass.TerminalBoss, fake)
    ts = litpyglass.TerminalShadow(boss)
    ts.shadow_read_data_else(b"\033[2;3R")  # Row 2 Column 3
    ts.shadow_read_data_else(b"\033[8;5;20t")  # a Screen 5 high, 20 wide

    written = no_sgr_csi + reverse + "ab"  # a and b in Reverse, at Columns 3 and 4
    ts.str_write_base_tb(written)
    assert fake.writes == [written.encode()], fake.writes

    base_layer = ts.base

    # Layer 1: a Layer has its own .place, .text_styles, and .write_by_xy, and writes no Byte

    assert isinstance(base_layer, litpyglass.TerminalLayer), base_layer
    assert not hasattr(base_layer, "tb"), base_layer
    assert not hasattr(base_layer, "bytes_write_flush"), base_layer

    # Shadow 1: a TerminalShadow holds Layers, and forwards only .base_place and is_writeable_area

    for name in ("text_styles", "write_by_xy"):
        assert not hasattr(litpyglass.TerminalShadow, name), name

    assert isinstance(litpyglass.TerminalShadow.base_place, property), "base_place"

    # Layer 2: a new Layer starts with a copy of the Place and Text Styles, and no Writes

    forked_layer = base_layer.fork_layer()
    assert forked_layer.place == base_layer.place, forked_layer.place
    assert forked_layer.place is not base_layer.place, forked_layer.place
    assert forked_layer.text_styles == (no_sgr_csi, reverse), forked_layer.text_styles
    assert forked_layer.write_by_xy == {}, forked_layer.write_by_xy
    assert len(base_layer.write_by_xy) == 2, base_layer.write_by_xy

    # Layer 8: a Move that would leave the Screen chops at the edge, and the Layer counts the chop

    north_layer = base_layer.fork_layer()
    # a, b, then the 1st Move fits and the 2nd Move chops at the North edge
    north_written = north_layer._write_some_or_all_strs_("ab\033[A\033[A")
    north_xy = (north_layer.place.column_x, north_layer.place.row_y)
    occasion = (north_written, north_xy, north_layer.xy_chops, north_layer.place)
    assert north_written, occasion
    assert north_xy == (7, 1), occasion
    assert north_layer.xy_chops == 1, occasion
    assert north_layer.write_by_xy != {}, occasion  # keeps the Writes before it

    # Layer 11: a Write that cannot be made says so, and leaves the Layer half written

    edge_layer = base_layer.fork_layer()
    edge_layer.place.column_x = 20  # the last Column we write
    assert not edge_layer._write_some_or_all_strs_("ab")  # b would land in Column 21
    assert edge_layer.write_by_xy == {(20, 2): ((no_sgr_csi, reverse), "a")}, edge_layer.write_by_xy

    # Layer 12: the Shadow runs the one def on the Layer, and ships no second copy of the rules

    assert not hasattr(litpyglass.TerminalShadow, "_write_some_or_all_strs_")
    assert not hasattr(litpyglass.TerminalShadow, "text_styles_compress")

    # Layer 13: no Write into a Layer changes any other Layer, or the Terminal

    before = (
        dataclasses.astuple(base_layer.place),
        dict(base_layer.write_by_xy),
        tuple(base_layer.text_styles),
    )
    trial_layer = base_layer.fork_layer()
    assert trial_layer._write_some_or_all_strs_("xyz\033[m")
    after = (
        dataclasses.astuple(base_layer.place),
        dict(base_layer.write_by_xy),
        tuple(base_layer.text_styles),
    )
    assert after == before, (after, before)
    assert fake.writes == [written.encode()], fake.writes

    # Shadow 4: str_write_base_tb asserts the Write can be made, before any Byte goes out,
    # and takes a Move chopped at an edge, as the Terminal does

    fake.writes.clear()
    ts_north = litpyglass.TerminalShadow(boss)
    ts_north.shadow_read_data_else(b"\033[1;1R")
    ts_north.shadow_read_data_else(b"\033[8;5;20t")
    ts_north.str_write_base_tb("\033[A")  # chopped at the North edge
    north_xy = (ts_north.base_place.column_x, ts_north.base_place.row_y)
    occasion = (north_xy, ts_north.base.xy_chops, fake.writes)
    assert north_xy == (1, 1), occasion
    assert ts_north.base.xy_chops == 1, occasion
    assert fake.writes == [b"\033[A"], occasion

    fake.writes.clear()
    ts_north.shadow_read_data_else(b"\033[1;20R")
    try:
        ts_north.str_write_base_tb("ab")  # b would land in Column 21
        asserted = False
    except AssertionError:
        asserted = True
    assert asserted
    assert fake.writes == [], fake.writes

    # Shadow 5: is_writable_place_after_strs drops its Layer, and leaves the Shadow as it was

    shadow_before = (
        dataclasses.astuple(ts.base_place),
        dict(ts.base.write_by_xy),
        tuple(ts.base.text_styles),
    )
    assert ts.is_writable_place_after_strs(text="\b")
    assert not ts.is_writable_place_after_strs(text="\033[B" * 4)
    shadow_after = (
        dataclasses.astuple(ts.base_place),
        dict(ts.base.write_by_xy),
        tuple(ts.base.text_styles),
    )
    assert shadow_after == shadow_before, (shadow_after, shadow_before)


def _try_shadow_writes_() -> None:
    """Try TerminalLayer keeping the Writes made through a TerminalShadow, as specs.md § 10 says"""

    fake = FakeWriteBoss()
    boss = typing.cast(litpyglass.TerminalBoss, fake)
    ts = litpyglass.TerminalShadow(boss)
    assert ts.base.write_by_xy == {}, ts.base.write_by_xy

    ts.shadow_read_data_else(b"\033[2;3R")  # Row 2 Column 3
    ts.shadow_read_data_else(b"\033[8;5;20t")  # a Screen 5 high, 20 wide
    assert ts.base.write_by_xy == {}, ts.base.write_by_xy  # nothing written, so nothing known

    no_sgr_csi = "\033[m"  # ⎋[M, which starts the Text Styles in force
    reverse = "\033[7m"  # ⎋[7M

    ts.str_write_base_tb(no_sgr_csi + "ab")
    assert ts.base.write_by_xy == {
        (3, 2): ((no_sgr_csi,), "a"),
        (4, 2): ((no_sgr_csi,), "b"),
    }, ts.base.write_by_xy

    ts.str_write_base_tb(
        "\b\b" + reverse + "  " + no_sgr_csi + "\b\b"
    )  # two reverse Spaces over them
    assert ts.base.write_by_xy[(3, 2)] == ((no_sgr_csi, reverse), " "), ts.base.write_by_xy
    assert ts.base.write_by_xy[(4, 2)] == ((no_sgr_csi, reverse), " "), ts.base.write_by_xy
    assert ts.base.text_styles == (
        no_sgr_csi,
    ), ts.base.text_styles  # ⎋[M started the sequence again

    ts.str_write_base_tb("\033[B\033[Dz")  # move down and left, then write
    assert ts.base.write_by_xy[(2, 3)] == ((no_sgr_csi,), "z"), ts.base.write_by_xy
    assert len(ts.base.write_by_xy) == 3, ts.base.write_by_xy

    ts.str_write_base_tb(reverse + "q")  # leaves Reverse on
    assert tuple(ts.base.text_styles) == (
        no_sgr_csi,
        reverse,
    ), ts.base.text_styles  # tuple() blocks narrowing
    assert ts.base.write_by_xy[(3, 3)] == ((no_sgr_csi, reverse), "q"), ts.base.write_by_xy

    ts.str_write_base_tb(no_sgr_csi)  # ⎋[M starts the sequence again
    assert tuple(ts.base.text_styles) == (no_sgr_csi,), ts.base.text_styles

    # ⎋[7M said twice is kept once, and an SGR we do not spell fails loudly

    ts = litpyglass.TerminalShadow(boss)
    ts.shadow_read_data_else(b"\033[1;1R")
    ts.shadow_read_data_else(b"\033[8;5;20t")

    ts.str_write_base_tb(no_sgr_csi + reverse + reverse + "q")
    assert ts.base.write_by_xy[(1, 1)] == ((no_sgr_csi, reverse), "q"), ts.base.write_by_xy

    try:
        ts.str_write_base_tb("\033[1mr")  # Bold
        asserted = False
    except AssertionError:
        asserted = True
    assert asserted, ts.base.write_by_xy

    # Hiding or showing the Cursor keeps nothing and steers nothing, and any other Control fails

    ts = litpyglass.TerminalShadow(boss)
    ts.shadow_read_data_else(b"\033[2;3R")
    ts.shadow_read_data_else(b"\033[8;5;20t")

    shadow_before = (
        dataclasses.astuple(ts.base_place),
        dict(ts.base.write_by_xy),
        ts.base.text_styles,
    )
    ts.str_write_base_tb("\033[?25l\033[?25h")  # ⎋[⇧?25L ⎋[⇧?25H
    shadow_after = (
        dataclasses.astuple(ts.base_place),
        dict(ts.base.write_by_xy),
        ts.base.text_styles,
    )
    assert shadow_after == shadow_before, (shadow_after, shadow_before)

    try:
        ts.str_write_base_tb("\a")  # Bell
        asserted = False
    except AssertionError:
        asserted = True
    assert asserted, ts.base.write_by_xy

    # An odd Width W+1 acts as W: the Cursor may wait in Column W+1, but we write no Char there

    ts = litpyglass.TerminalShadow(boss)
    ts.shadow_read_data_else(b"\033[1;1R")
    ts.shadow_read_data_else(b"\033[8;5;21t")  # a Screen 5 high, 21 wide
    assert (ts.base_place.x_width, ts.base_place.x_max) == (21, 20), ts.base_place

    next_layer = _layer_after_(ts, text="\033[C" * 19)
    assert next_layer and (next_layer.place.column_x, next_layer.place.row_y) == (20, 1), next_layer
    assert ts.is_writable_place_after_strs(text="\033[C" * 19)
    next_layer = _layer_after_(ts, text="\033[C" * 20)  # in Column W, which is past x_max
    assert next_layer and (next_layer.place.column_x, next_layer.place.row_y) == (21, 1), next_layer
    assert next_layer.xy_chops == 0, next_layer
    assert not ts.is_writable_place_after_strs(text="\033[C" * 20)

    # A Char that would land in Column W+1 cannot be written, even if the Cursor then moves back,
    # and writing it fails an assert, since we write only inside Height x x_max

    inside = no_sgr_csi + "\033[C" * 19 + "a\b"  # a lands in Column 20, the last Column we write
    outside = no_sgr_csi + "\033[C" * 19 + "ab\b\b"  # b would land in Column 21
    next_layer = _layer_after_(ts, text=inside)
    assert next_layer and (next_layer.place.column_x, next_layer.place.row_y) == (20, 1), next_layer
    assert _layer_after_(ts, text=outside) is None

    before = (
        dataclasses.astuple(ts.base_place),
        dict(ts.base.write_by_xy),
        ts.base.text_styles,
        list(fake.writes),
    )

    try:
        ts.str_write_base_tb(outside)
        asserted = False
    except AssertionError:
        asserted = True
    assert asserted, ts.base.write_by_xy
    assert (21, 1) not in ts.base.write_by_xy, ts.base.write_by_xy

    # The Shadow finds the problem before the Terminal hears a Byte, and is left as it was

    after = (
        dataclasses.astuple(ts.base_place),
        dict(ts.base.write_by_xy),
        ts.base.text_styles,
        list(fake.writes),
    )
    assert after == before, (after, before)

    ts = litpyglass.TerminalShadow(boss)
    ts.shadow_read_data_else(b"\033[1;1R")
    ts.shadow_read_data_else(b"\033[8;5;20t")  # an even Width acts as itself
    assert (ts.base_place.x_width, ts.base_place.x_max) == (20, 20), ts.base_place

    # A Move that would leave the Screen chops at the North, West, South, and East edges

    # Row 1 Column 1 of a Screen 5 high, 20 wide
    for text in ("\033[A", "\033[D", "\b"):  # ↑ at the North edge, ← and Backspace at the West
        next_layer = _layer_after_(ts, text=text)
        assert next_layer, text
        next_xy = (next_layer.place.column_x, next_layer.place.row_y)
        assert next_xy == (1, 1), (text, next_xy, next_layer.xy_chops)
        assert next_layer.xy_chops == 1, (text, next_xy, next_layer.xy_chops)

    ts.shadow_read_data_else(b"\033[5;20R")  # Row 5 Column 20, the far South East
    for text in ("\033[B", "\033[C"):  # ↓ at the South edge, → at the East edge
        assert not ts.is_writable_place_after_strs(text=text), text
        next_layer = _layer_after_(ts, text=text)
        assert next_layer, text
        next_xy = (next_layer.place.column_x, next_layer.place.row_y)
        assert next_xy == (20, 5), (text, next_xy, next_layer.xy_chops)
        assert next_layer.xy_chops == 1, (text, next_xy, next_layer.xy_chops)

    next_layer = _layer_after_(ts, text="\033[A")  # ↑ back inside, with no chop
    assert next_layer and (next_layer.place.column_x, next_layer.place.row_y) == (20, 4), next_layer
    assert next_layer.xy_chops == 0, next_layer

    # A Return lands on Column 1, even with the wrap pending after a write into the last Column

    ts = litpyglass.TerminalShadow(boss)
    ts.shadow_read_data_else(b"\033[1;20R")
    ts.shadow_read_data_else(b"\033[8;5;20t")
    ts.str_write_base_tb("a\r")  # a lands in Column 20, the last, and then Return
    assert (ts.base_place.column_x, ts.base_place.row_y) == (1, 1), ts.base_place
    assert ts.base.write_by_xy[(20, 1)][1] == "a", ts.base.write_by_xy

    # A Char into the last Column of an even Width, with nothing after it, cannot be written,
    # since the Cursor would wait to wrap past x_max, but a Backspace after it can

    ts = litpyglass.TerminalShadow(boss)
    ts.shadow_read_data_else(b"\033[1;20R")
    ts.shadow_read_data_else(b"\033[8;5;20t")
    assert not ts.is_writable_place_after_strs(text="a")
    assert ts.is_writable_place_after_strs(text="a\b")
    next_layer = _layer_after_(ts, text="a\b")
    assert next_layer and (next_layer.place.column_x, next_layer.place.row_y) == (19, 1), next_layer

    # A Char into Column W+1 of an odd Width cannot be written, since only W Columns are ours

    ts = litpyglass.TerminalShadow(boss)
    ts.shadow_read_data_else(b"\033[1;21R")
    ts.shadow_read_data_else(b"\033[8;5;21t")
    assert _layer_after_(ts, text="a") is None

    # Before the Terminal replies, no write can be made, not even one of no Char

    early = FakeWriteBoss()
    ts = litpyglass.TerminalShadow(typing.cast(litpyglass.TerminalBoss, early))

    for text in (no_sgr_csi, "a"):
        try:
            ts.str_write_base_tb(text)
            asserted = False
        except AssertionError:
            asserted = True
        assert asserted, (text, ts.base.write_by_xy)

    assert early.writes == [], early.writes  # no Byte went out
    assert ts.base.write_by_xy == {}, ts.base.write_by_xy


def _try_shadow_chops_() -> None:
    """Try TerminalLayer chopping a Move or a Leap at each edge, as specs.md § 10 says"""

    fake = FakeWriteBoss()
    boss = typing.cast(litpyglass.TerminalBoss, fake)

    def new_shadow(yx_reply: bytes) -> litpyglass.TerminalShadow:
        """Start a Shadow of a Screen 5 high, 20 wide, with the Cursor at the Reply"""

        ts = litpyglass.TerminalShadow(boss)
        ts.shadow_read_data_else(yx_reply)
        ts.shadow_read_data_else(b"\033[8;5;20t")
        return ts

    def xy_count_after(ts: litpyglass.TerminalShadow, text: str) -> tuple[int, int, int]:
        """Say the Column, the Row, and the xy_chops after the Str, in a new Layer"""

        layer = _layer_after_(ts, text=text)
        assert layer, (text, ts.base_place)
        return (layer.place.column_x, layer.place.row_y, layer.xy_chops)

    # Layer 8: each Move stays at its edge, and counts 1, for each of A B C D and Backspace

    edge_cases = (
        (b"\033[1;1R", "\033[A", (1, 1, 1)),  # ↑ at the North edge
        (b"\033[1;1R", "\033[D", (1, 1, 1)),  # ← at the West edge
        (b"\033[1;1R", "\b", (1, 1, 1)),  # Backspace at the West edge
        (b"\033[5;20R", "\033[B", (20, 5, 1)),  # ↓ at the South edge
        (b"\033[5;20R", "\033[C", (20, 5, 1)),  # → at the East edge
    )
    for yx_reply, text, expect in edge_cases:
        got = xy_count_after(new_shadow(yx_reply), text)
        assert got == expect, (yx_reply, text, got, expect)

    # Layer 8: a Pn of 32100 stops at the edge, and counts 1

    far_cases = (
        ("\033[32100A", (10, 1, 1)),
        ("\033[32100B", (10, 5, 1)),
        ("\033[32100C", (20, 3, 1)),
        ("\033[32100D", (1, 3, 1)),
    )
    for text, expect in far_cases:
        got = xy_count_after(new_shadow(b"\033[3;10R"), text)
        assert got == expect, (text, got, expect)

    # Layer 8: a Move that fits counts 0

    fit_cases = (
        ("\033[A", (10, 2, 0)),
        ("\033[B", (10, 4, 0)),
        ("\033[C", (11, 3, 0)),
        ("\033[D", (9, 3, 0)),
        ("\b", (9, 3, 0)),
        ("\033[2A", (10, 1, 0)),  # a Pn that lands exactly on the North edge
        ("\033[10C", (20, 3, 0)),  # a Pn that lands exactly on the East edge
        ("\r", (1, 3, 0)),  # a Return never chops
    )
    for text, expect in fit_cases:
        got = xy_count_after(new_shadow(b"\033[3;10R"), text)
        assert got == expect, (text, got, expect)

    # Layer 8: a Move East from the last Column stays there, and the next Char lands there

    ts = new_shadow(b"\033[1;20R")
    layer = _layer_after_(ts, text="\033[Ca")
    assert layer, ts.base_place
    occasion = (layer.place, layer.write_by_xy, layer.xy_chops)
    assert list(layer.write_by_xy.keys()) == [(20, 1)], occasion
    assert (layer.place.column_x, layer.place.row_y) == (21, 1), occasion
    assert layer.xy_chops == 1, occasion
    assert _layer_after_(ts, text="\033[Cab") is None  # b would land in Column 21

    # Layer 8 and 10: from a Cursor waiting to wrap, a Move ends the wait in the last Column

    wait_cases = (
        ("a\033[A", (20, 2, 0)),
        ("a\033[B", (20, 4, 0)),
        ("a\033[C", (20, 3, 1)),
        ("a\b", (19, 3, 0)),
        ("a\r", (1, 3, 0)),
        ("a\033[D", (20, 3, 0)),  # ⎋[⇧D counts from Column W+1, so it lands in Column W
        ("a\033[2D", (19, 3, 0)),  # and ⎋[2⇧D lands in Column W-1
        ("a\033[1D", (20, 3, 0)),
    )
    for text, expect in wait_cases:
        got = xy_count_after(new_shadow(b"\033[3;20R"), text)
        assert got == expect, (text, got, expect)

    # Shadow 12: form_leap_back counts from Column W+1 while waiting, and lands on its target

    ts = new_shadow(b"\033[3;20R")
    ts.str_write_base_tb("a")  # waits to wrap past Column 20
    wait_place = ts.base_place
    assert 20 < wait_place.column_x <= 21, wait_place  # waits to wrap, one past the Width
    for target_x, want_leap in ((20, "\033[1D"), (19, "\033[2D"), (1, "\033[20D")):
        leap = litpyglass.TerminalShadow.form_leap_back(wait_place, column_x=target_x, row_y=3)
        got = xy_count_after(ts, leap)
        assert leap == want_leap, (leap, want_leap, target_x, wait_place)
        assert got == (target_x, 3, 0), (leap, got, target_x, wait_place)

    # Layer 14 and 15: a Leap past the Height or the Width counts 1, and a Pn of 0 counts 0

    leap_cases = (
        ("\033[32100d", (10, 5, 1)),
        ("\033[32100G", (20, 3, 1)),
        ("\033[6d", (10, 5, 1)),  # one Row past the Height
        ("\033[21G", (20, 3, 1)),  # one Column past the Width
        ("\033[5d", (10, 5, 0)),  # the last Row
        ("\033[20G", (20, 3, 0)),  # the last Column
        ("\033[0d", (10, 1, 0)),
        ("\033[0G", (1, 3, 0)),
    )
    for text, expect in leap_cases:
        got = xy_count_after(new_shadow(b"\033[3;10R"), text)
        assert got == expect, (text, got, expect)

    # Layer 8: a Pn of 0 moves 1 and counts 0, and a Pn of 003 moves 3, for A C D

    zero_cases = (
        ("\033[0A", (10, 3, 0)),
        ("\033[0B", (10, 5, 0)),
        ("\033[0C", (11, 4, 0)),
        ("\033[0D", (9, 4, 0)),
        ("\033[003A", (10, 1, 0)),
        ("\033[003C", (13, 4, 0)),
        ("\033[003D", (7, 4, 0)),
    )
    for text, expect in zero_cases:
        got = xy_count_after(new_shadow(b"\033[4;10R"), text)
        assert got == expect, (text, got, expect)

    # Layer 16 and 17: pn_to_at_plus_below_row_count gives the Rows from the Cursor Row down,
    # at most to the last

    for row_y, at_plus_below_rows in ((1, 5), (3, 3), (5, 1)):
        place = litpyglass.TerminalPlace(column_x=1, x_max=20, x_width=20, row_y=row_y, y_height=5)
        for pn, expect_count in (
            (0, 1),
            (1, 1),
            (at_plus_below_rows, at_plus_below_rows),  # exactly the Rows that fit
            (at_plus_below_rows + 1, at_plus_below_rows),  # one more
            (32100, at_plus_below_rows),
        ):
            row_count = place.pn_to_at_plus_below_row_count(pn)
            count_occasion = (row_y, at_plus_below_rows, pn, expect_count, row_count, place)
            assert row_count == expect_count, count_occasion

    # Shadow 5: is_writable_place_after_strs says no for a chopped Move, yes one step from the edge

    ts = new_shadow(b"\033[3;10R")
    for text, expect_fit in (
        ("\033[32100d", False),
        ("\033[5d", True),
        ("\033[6d", False),
        ("\033[3A", False),
        ("\033[2A", True),
        ("\033[C" * 11, False),
        ("\033[C" * 10, True),
    ):
        is_writable = ts.is_writable_place_after_strs(text=text)
        assert is_writable is expect_fit, (text, is_writable, expect_fit, ts.base_place)

    # Layer 8: .xy_chops is a log on the Layer, grows across writes, and a fork starts at 0

    ts = new_shadow(b"\033[3;10R")
    assert ts.base.xy_chops == 0, ts.base.xy_chops

    ts.str_write_base_tb("\033[32100A")
    count1 = ts.base.xy_chops
    ts.str_write_base_tb("\033[32100D")
    count2 = ts.base.xy_chops
    log_occasion = (count1, count2, ts.base_place)
    assert count1 == 1, log_occasion
    assert count2 == 2, log_occasion
    assert (ts.base_place.column_x, ts.base_place.row_y) == (1, 1), log_occasion

    fork_layer = ts.base.fork_layer()
    assert fork_layer.xy_chops == 0, (fork_layer.xy_chops, ts.base.xy_chops)
    assert ts.base.xy_chops == 2, (fork_layer.xy_chops, ts.base.xy_chops)

    # Shadow 8: clear_layer puts the count back to 0

    ts.base.clear_layer()
    assert ts.base.xy_chops == 0, (ts.base.xy_chops, ts.base.place)


def _try_shadow_row_leap_() -> None:
    """Try a TerminalShadow taking ⎋[D to leap to a Row, as specs.md § 10 says"""

    def asserts_for(write: typing.Callable[[str], None], text: str) -> bool:
        """Say if the Write fails an assert"""

        try:
            write(text)
        except AssertionError:
            return True
        return False

    def shadow_five_rows(fake: FakeWriteBoss, screen_width: int) -> litpyglass.TerminalShadow:
        """Write a, b, c, d, e into Column 1 of Rows 1 to 5, & leave the Cursor at Row 3 Column 5"""

        ts = litpyglass.TerminalShadow(typing.cast(litpyglass.TerminalBoss, fake))
        ts.shadow_read_data_else(b"\033[1;1R")
        ts.shadow_read_data_else(f"\033[8;5;{screen_width}t".encode())

        for y, char in enumerate("abcde", start=1):
            ts.shadow_read_data_else(f"\033[{y};1R".encode())
            ts.str_write_base_tb(char)

        ts.shadow_read_data_else(b"\033[3;5R")
        return ts

    # A leap lands on the Row it names, or the first Row, or the last Row, and keeps the Column

    row_by_text = {
        "\033[d": 1,
        "\033[0d": 1,
        "\033[1d": 1,
        "\033[3d": 3,
        "\033[003d": 3,
        "\033[5d": 5,
        "\033[6d": 5,
        "\033[32100d": 5,
    }

    for text, row_y in row_by_text.items():
        fake = FakeWriteBoss()
        ts = shadow_five_rows(fake, screen_width=20)
        write_by_xy_before = dict(ts.base.write_by_xy)

        ts.str_write_base_tb(text)

        occasion = (text, row_y, ts.base_place, fake.writes)
        assert fake.writes[-1] == text.encode(), occasion
        assert (ts.base_place.column_x, ts.base_place.row_y) == (5, row_y), occasion
        assert ts.base.write_by_xy == write_by_xy_before, (text, ts.base.write_by_xy)

        ts.str_write_base_tb("q")  # lands at the same Column of the new Row
        assert ts.base.write_by_xy[(5, row_y)] == ((), "q"), (text, row_y, ts.base.write_by_xy)
        assert (ts.base_place.column_x, ts.base_place.row_y) == (6, row_y), occasion

    # A Cursor waiting to wrap keeps waiting to wrap, as no Move does

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    ts.shadow_read_data_else(b"\033[3;20R")
    ts.str_write_base_tb("z")  # lands in Column 20, and then the Cursor waits in Column 21
    assert (ts.base_place.column_x, ts.base_place.row_y) == (21, 3), ts.base_place
    ts.str_write_base_tb("\033[2d")
    assert (ts.base_place.column_x, ts.base_place.row_y) == (21, 2), ts.base_place

    # A leap with more than one Pn, or with a Question Mark, fails an assert before any Byte goes out

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    writes_before = list(fake.writes)
    write_by_xy_before = dict(ts.base.write_by_xy)

    for text in ("\033[1;2d", "\033[?7d"):
        assert asserts_for(ts.str_write_base_tb, text), (text, ts.base_place)

    assert fake.writes == writes_before, (fake.writes, writes_before)
    assert ts.base.write_by_xy == write_by_xy_before, (ts.base.write_by_xy, write_by_xy_before)

    # A Writer may ask first if a leap to Row 3 keeps the Cursor in the Writable Area

    assert ts.is_writable_place_after_strs("\033[3d"), ts.base_place


def _try_shadow_column_leap_() -> None:
    """Try a TerminalShadow taking ⎋[⇧G to leap to a Column, as specs.md § 10 says"""

    def asserts_for(write: typing.Callable[[str], None], text: str) -> bool:
        """Say if the Write fails an assert"""

        try:
            write(text)
        except AssertionError:
            return True
        return False

    def shadow_five_rows(fake: FakeWriteBoss, screen_width: int) -> litpyglass.TerminalShadow:
        """Write a, b, c, d, e into Column 1 of Rows 1 to 5, & leave the Cursor at Row 3 Column 5"""

        ts = litpyglass.TerminalShadow(typing.cast(litpyglass.TerminalBoss, fake))
        ts.shadow_read_data_else(b"\033[1;1R")
        ts.shadow_read_data_else(f"\033[8;5;{screen_width}t".encode())

        for y, char in enumerate("abcde", start=1):
            ts.shadow_read_data_else(f"\033[{y};1R".encode())
            ts.str_write_base_tb(char)

        ts.shadow_read_data_else(b"\033[3;5R")
        return ts

    # A leap lands on the Column it names, or the first Column, or the last Column, and keeps the Row

    column_by_text = {
        "\033[G": 1,
        "\033[0G": 1,
        "\033[1G": 1,
        "\033[7G": 7,
        "\033[007G": 7,
        "\033[20G": 20,
        "\033[21G": 20,
        "\033[32100G": 20,
    }

    for text, column_x in column_by_text.items():
        fake = FakeWriteBoss()
        ts = shadow_five_rows(fake, screen_width=20)
        write_by_xy_before = dict(ts.base.write_by_xy)

        ts.str_write_base_tb(text)

        occasion = (text, column_x, ts.base_place, fake.writes)
        assert fake.writes[-1] == text.encode(), occasion
        assert (ts.base_place.column_x, ts.base_place.row_y) == (column_x, 3), occasion
        assert ts.base.write_by_xy == write_by_xy_before, (text, ts.base.write_by_xy)

        ts.str_write_base_tb("q")  # lands at the new Column of the same Row
        assert ts.base.write_by_xy[(column_x, 3)] == ((), "q"), (text, column_x, ts.base.write_by_xy)
        assert (ts.base_place.column_x, ts.base_place.row_y) == (column_x + 1, 3), occasion

    # An odd Width W+1 chops a leap at its real last Column, where the Cursor may sit but not write

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=21)
    ts.str_write_base_tb("\033[32100G")
    assert (ts.base_place.column_x, ts.base_place.row_y) == (21, 3), ts.base_place
    assert not ts.base_place.is_writable_place(), ts.base_place

    # A Cursor waiting to wrap stops waiting at a leap, even a leap to the last Column

    for text, column_x in (("\033[7G", 7), ("\033[20G", 20), ("\033[32100G", 20)):
        fake = FakeWriteBoss()
        ts = shadow_five_rows(fake, screen_width=20)
        ts.shadow_read_data_else(b"\033[3;20R")
        ts.str_write_base_tb("z")  # lands in Column 20, and then the Cursor waits in Column 21
        assert (ts.base_place.column_x, ts.base_place.row_y) == (21, 3), ts.base_place
        ts.str_write_base_tb(text)
        assert (ts.base_place.column_x, ts.base_place.row_y) == (column_x, 3), (text, ts.base_place)

    # A leap with more than one Pn, or with a Question Mark, fails an assert before any Byte goes out

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    writes_before = list(fake.writes)
    write_by_xy_before = dict(ts.base.write_by_xy)

    for text in ("\033[1;2G", "\033[?7G"):
        assert asserts_for(ts.str_write_base_tb, text), (text, ts.base_place)

    assert fake.writes == writes_before, (fake.writes, writes_before)
    assert ts.base.write_by_xy == write_by_xy_before, (ts.base.write_by_xy, write_by_xy_before)

    # A Writer may ask first if a leap keeps the Cursor in the Writable Area

    assert ts.is_writable_place_after_strs("\033[7G"), ts.base_place
    assert ts.is_writable_place_after_strs("\033[20G"), ts.base_place
    assert not ts.is_writable_place_after_strs("\033[20G" + "\033[C"), ts.base_place  # no Pair fits


def _try_shadow_yx_leap_() -> None:
    """Try a TerminalShadow taking ⎋[⇧H to leap to a Row and a Column, as specs.md § 10 says"""

    def asserts_for(write: typing.Callable[[str], None], text: str) -> bool:
        """Say if the Write fails an assert"""

        try:
            write(text)
        except AssertionError:
            return True
        return False

    def shadow_five_rows(fake: FakeWriteBoss, screen_width: int) -> litpyglass.TerminalShadow:
        """Write a, b, c, d, e into Column 1 of Rows 1 to 5, & leave the Cursor at Row 3 Column 5"""

        ts = litpyglass.TerminalShadow(typing.cast(litpyglass.TerminalBoss, fake))
        ts.shadow_read_data_else(b"\033[1;1R")
        ts.shadow_read_data_else(f"\033[8;5;{screen_width}t".encode())

        for y, char in enumerate("abcde", start=1):
            ts.shadow_read_data_else(f"\033[{y};1R".encode())
            ts.str_write_base_tb(char)

        ts.shadow_read_data_else(b"\033[3;5R")
        return ts

    # A leap lands on the Row and the Column it names, an empty or 0 Pn acting as 1, and counts chops

    xy_chops_by_text = {
        "\033[H": ((1, 1), 0),
        "\033[;H": ((1, 1), 0),
        "\033[0H": ((1, 1), 0),
        "\033[0;0H": ((1, 1), 0),
        "\033[1;1H": ((1, 1), 0),
        "\033[2H": ((1, 2), 0),
        "\033[2;H": ((1, 2), 0),
        "\033[;7H": ((7, 1), 0),
        "\033[0;7H": ((7, 1), 0),
        "\033[4;7H": ((7, 4), 0),
        "\033[004;007H": ((7, 4), 0),
        "\033[5;20H": ((20, 5), 0),
        "\033[6;7H": ((7, 5), 1),
        "\033[4;21H": ((20, 4), 1),
        "\033[;32100H": ((20, 1), 1),
        "\033[32100H": ((1, 5), 1),
        "\033[6;21H": ((20, 5), 2),
        "\033[32100;32100H": ((20, 5), 2),
    }

    for text, (xy, xy_chops) in xy_chops_by_text.items():
        fake = FakeWriteBoss()
        ts = shadow_five_rows(fake, screen_width=20)
        write_by_xy_before = dict(ts.base.write_by_xy)

        ts.str_write_base_tb(text)

        occasion = (text, xy, xy_chops, ts.base_place, ts.base.xy_chops, fake.writes)
        assert fake.writes[-1] == text.encode(), occasion
        assert (ts.base_place.column_x, ts.base_place.row_y) == xy, occasion
        assert ts.base.xy_chops == xy_chops, occasion
        assert ts.base.write_by_xy == write_by_xy_before, (text, ts.base.write_by_xy)

        column_x, row_y = xy
        ts.str_write_base_tb("q")  # lands at the new Column of the new Row
        assert ts.base.write_by_xy[(column_x, row_y)] == ((), "q"), (text, xy, ts.base.write_by_xy)

    # Chops add to the chops already counted

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    ts.str_write_base_tb("\033[32100;32100H")
    ts.str_write_base_tb("\033[32100;3H")
    assert ts.base.xy_chops == 3, (ts.base.xy_chops, ts.base_place)

    # An odd Width W+1 chops a leap at its real last Column, where the Cursor may sit but not write

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=21)
    ts.str_write_base_tb("\033[2;32100H")
    assert (ts.base_place.column_x, ts.base_place.row_y) == (21, 2), ts.base_place
    assert ts.base.xy_chops == 1, (ts.base.xy_chops, ts.base_place)
    assert not ts.base_place.is_writable_place(), ts.base_place

    # A Cursor waiting to wrap stops waiting at a leap, even a leap to the last Column

    for text, xy in (("\033[2;7H", (7, 2)), ("\033[2;20H", (20, 2)), ("\033[H", (1, 1))):
        fake = FakeWriteBoss()
        ts = shadow_five_rows(fake, screen_width=20)
        ts.shadow_read_data_else(b"\033[3;20R")
        ts.str_write_base_tb("z")  # lands in Column 20, and then the Cursor waits in Column 21
        assert (ts.base_place.column_x, ts.base_place.row_y) == (21, 3), ts.base_place
        ts.str_write_base_tb(text)
        assert (ts.base_place.column_x, ts.base_place.row_y) == xy, (text, ts.base_place)

        ts.str_write_base_tb("q")  # lands where the leap says, never in Column 21 or past it
        assert ts.base.write_by_xy[xy] == ((), "q"), (text, xy, ts.base.write_by_xy)

    # A leap with a third Pn, or with a Question Mark, fails an assert before any Byte goes out

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    writes_before = list(fake.writes)
    write_by_xy_before = dict(ts.base.write_by_xy)

    for text in ("\033[3;7;9H", "\033[;;H", "\033[?7H", "\033[?;7H"):
        assert asserts_for(ts.str_write_base_tb, text), (text, ts.base_place)

    assert fake.writes == writes_before, (fake.writes, writes_before)
    assert ts.base.write_by_xy == write_by_xy_before, (ts.base.write_by_xy, write_by_xy_before)
    assert ts.base.xy_chops == 0, (ts.base.xy_chops, ts.base_place)

    # A Writer may ask first if a leap keeps the Cursor in the Writable Area, and with no chop

    assert ts.is_writable_place_after_strs("\033[H"), ts.base_place
    assert ts.is_writable_place_after_strs("\033[2;7H"), ts.base_place
    assert ts.is_writable_place_after_strs("\033[5;20H"), ts.base_place
    assert not ts.is_writable_place_after_strs("\033[6;7H"), ts.base_place
    assert not ts.is_writable_place_after_strs("\033[2;21H"), ts.base_place
    assert not ts.is_writable_place_after_strs("\033[5;20H" + "\033[C"), ts.base_place  # no Pair
    assert ts.base.xy_chops == 0, (
        ts.base.xy_chops,
        ts.base_place,
    )  # a trial counts its chops in a fork, never in .base

    # The Top Layer takes a leap as the Base Layer does, and the Base Layer stays where it was

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    ts.str_write_top_tb("\033[2;7H")
    assert (ts.top.place.column_x, ts.top.place.row_y) == (7, 2), ts.top.place
    assert (ts.base_place.column_x, ts.base_place.row_y) == (5, 3), ts.base_place
    ts.str_write_top_tb("\033[32100;32100H")
    assert (ts.top.place.column_x, ts.top.place.row_y) == (20, 5), ts.top.place
    assert ts.top.xy_chops == 2, (ts.top.xy_chops, ts.top.place)
    assert ts.base.xy_chops == 0, (ts.base.xy_chops, ts.base_place)


def _try_shadow_insert_row_() -> None:
    """Try a TerminalShadow taking ⎋[⇧L to insert a Row, as specs.md § 10 says"""

    insert_row = "\033[L"  # ⎋[⇧L
    reverse = "\033[7m"  # ⎋[7M

    def asserts_for(write: typing.Callable[[str], None], text: str) -> bool:
        """Say if the Write fails an assert"""

        try:
            write(text)
        except AssertionError:
            return True
        return False

    def shadow_five_rows(fake: FakeWriteBoss, screen_width: int) -> litpyglass.TerminalShadow:
        """Write a, b, c, d, e into Column 1 of Rows 1 to 5, & leave the Cursor at Row 3 Column 5"""

        ts = litpyglass.TerminalShadow(typing.cast(litpyglass.TerminalBoss, fake))
        ts.shadow_read_data_else(b"\033[1;1R")
        ts.shadow_read_data_else(f"\033[8;5;{screen_width}t".encode())

        for y, char in enumerate("abcde", start=1):
            ts.shadow_read_data_else(f"\033[{y};1R".encode())
            ts.str_write_base_tb(char)

        ts.shadow_read_data_else(b"\033[3;5R")
        return ts

    # A Plain insert keeps Row 1 and Row 2, moves c and d down, drops e, and fills Row 3 plain

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    ts.str_write_base_tb(insert_row)

    assert fake.writes[-1] == insert_row.encode(), fake.writes
    assert ts.base.text_styles == (), ts.base.text_styles
    assert (ts.base_place.column_x, ts.base_place.row_y) == (5, 3), ts.base_place

    write_by_xy = ts.base.write_by_xy
    letter_by_xy = dict((xy, write[1]) for xy, write in write_by_xy.items() if write[1] != " ")
    assert letter_by_xy == {(1, 1): "a", (1, 2): "b", (1, 4): "c", (1, 5): "d"}, letter_by_xy

    row_cells = list(xy for xy in write_by_xy.keys() if xy[1] == 3)
    assert sorted(row_cells) == list((x, 3) for x in range(1, 21)), sorted(row_cells)
    assert all(write == ((), " ") for xy, write in write_by_xy.items() if xy[1] == 3), write_by_xy
    assert len(write_by_xy) == (20 + 4), write_by_xy

    # A Reverse insert fills the Cursor Row with Spaces in Reverse

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    ts.str_write_base_tb(reverse)
    ts.str_write_base_tb(insert_row)

    write_by_xy = ts.base.write_by_xy
    assert write_by_xy[(1, 3)] == ((), " "), write_by_xy  # plain, though ⎋[7M is in force
    assert write_by_xy[(20, 3)] == ((), " "), write_by_xy
    assert write_by_xy[(1, 4)] == ((), "c"), write_by_xy  # c keeps its own Text Styles
    assert (21, 3) not in write_by_xy.keys(), write_by_xy
    assert ts.base.text_styles == (reverse,), ts.base.text_styles
    assert (ts.base_place.column_x, ts.base_place.row_y) == (5, 3), ts.base_place

    # An odd Width W+1 fills Column W+1 too, since the real Terminal fills the whole Row

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=21)
    ts.str_write_base_tb(insert_row)

    write_by_xy = ts.base.write_by_xy
    assert write_by_xy[(21, 3)] == ((), " "), write_by_xy
    assert len(write_by_xy) == (21 + 4), write_by_xy

    # An insert on the last Row drops that Row and fills it, and moves nothing else

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    ts.shadow_read_data_else(b"\033[5;1R")
    ts.str_write_base_tb(insert_row)

    write_by_xy = ts.base.write_by_xy
    letter_by_xy = dict((xy, write[1]) for xy, write in write_by_xy.items() if write[1] != " ")
    assert letter_by_xy == {(1, 1): "a", (1, 2): "b", (1, 3): "c", (1, 4): "d"}, letter_by_xy
    assert len(write_by_xy) == (20 + 4), write_by_xy
    assert (ts.base_place.column_x, ts.base_place.row_y) == (1, 5), ts.base_place

    # An insert while waiting to wrap leaves the Cursor waiting to wrap, as no Move does

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    ts.shadow_read_data_else(b"\033[3;20R")
    ts.str_write_base_tb("z")  # lands in Column 20, and then the Cursor waits in Column 21
    assert (ts.base_place.column_x, ts.base_place.row_y) == (21, 3), ts.base_place
    ts.str_write_base_tb(insert_row)
    assert (ts.base_place.column_x, ts.base_place.row_y) == (21, 3), ts.base_place
    assert ts.base.write_by_xy[(20, 3)] == ((), " "), ts.base.write_by_xy  # replaced the z
    assert ts.base.write_by_xy[(20, 4)] == ((), "z"), ts.base.write_by_xy  # the z moved down

    # An insert with a Pn does the one-Row An insert that many times, and the Bytes go out once

    rows_from_cursor = 3  # Row 3 of 5
    for pn_text, pn_int in (
        ("", 1),
        ("0", 0),
        ("1", 1),
        ("3", 3),
        ("003", 3),
        ("4", 4),
        ("32100", 32100),
    ):
        text = f"\033[{pn_text}L"
        row_count = pn_int if pn_int else 1
        if row_count > rows_from_cursor:
            row_count = rows_from_cursor

        fake = FakeWriteBoss()
        ts = shadow_five_rows(fake, screen_width=20)
        writes_before = list(fake.writes)
        ts.str_write_base_tb(text)

        twin_fake = FakeWriteBoss()
        twin_ts = shadow_five_rows(twin_fake, screen_width=20)
        for row_index in range(row_count):
            twin_ts.str_write_base_tb("\033[L")

        occasion = (text, row_count, ts.base_place, ts.base.xy_chops, fake.writes, writes_before)
        assert ts.base.write_by_xy == twin_ts.base.write_by_xy, occasion
        assert ts.base_place == twin_ts.base_place, occasion
        assert ts.base.xy_chops == twin_ts.base.xy_chops, occasion
        assert ts.base.xy_chops == 0, occasion  # a chopped Pn counts no chop
        assert fake.writes == (writes_before + [text.encode()]), occasion

    # An insert or a delete with a Pn that is not decimal digits fails an assert before any Byte

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    writes_before = list(fake.writes)
    write_by_xy_before = dict(ts.base.write_by_xy)

    for text in ("\033[1;2L", "\033[?7L", "\033[1;2M", "\033[?7M"):
        assert asserts_for(ts.str_write_base_tb, text), (text, ts.base_place)

    assert fake.writes == writes_before, (fake.writes, writes_before)
    assert ts.base.write_by_xy == write_by_xy_before, (ts.base.write_by_xy, write_by_xy_before)

    # An insert through the Top Layer fails an assert before any Byte goes out, with a Pn too

    for text in (insert_row, "\033[3L", "\033[M", "\033[3M"):
        assert asserts_for(ts.str_write_top_tb, text), (text, ts.base_place)
    assert fake.writes == writes_before, (fake.writes, writes_before)
    assert not ts.top, ts.top.place

    # An insert through the Base Layer, while the Top Layer is on, fails an assert before any Byte

    ts.str_write_top_tb("X")
    writes_before = list(fake.writes)
    write_by_xy_before = dict(ts.base.write_by_xy)
    assert ts.top, ts.top.place

    for text in (insert_row, "\033[3L", "\033[M", "\033[3M"):
        assert asserts_for(ts.str_write_base_tb, text), (text, ts.top.place, ts.base_place)
    assert fake.writes == writes_before, (fake.writes, writes_before)
    assert ts.base.write_by_xy == write_by_xy_before, (ts.base.write_by_xy, write_by_xy_before)

    ts.str_write_base_tb("\b")  # other Base Writes while the Top is on go on as before
    assert fake.writes[-1] == b"\b", fake.writes


def _try_shadow_delete_row_() -> None:
    """Try a TerminalShadow taking ⎋[⇧M to delete a Row, as specs.md § 10 says"""

    insert_row = "\033[L"  # ⎋[⇧L
    delete_row = "\033[M"  # ⎋[⇧M
    reverse = "\033[7m"  # ⎋[7M

    def asserts_for(write: typing.Callable[[str], None], text: str) -> bool:
        """Say if the Write fails an assert"""

        try:
            write(text)
        except AssertionError:
            return True
        return False

    def shadow_five_rows(fake: FakeWriteBoss, screen_width: int) -> litpyglass.TerminalShadow:
        """Write a, b, c, d, e into Column 1 of Rows 1 to 5, & leave the Cursor at Row 3 Column 5"""

        ts = litpyglass.TerminalShadow(typing.cast(litpyglass.TerminalBoss, fake))
        ts.shadow_read_data_else(b"\033[1;1R")
        ts.shadow_read_data_else(f"\033[8;5;{screen_width}t".encode())

        for y, char in enumerate("abcde", start=1):
            ts.shadow_read_data_else(f"\033[{y};1R".encode())
            ts.str_write_base_tb(char)

        ts.shadow_read_data_else(b"\033[3;5R")
        return ts

    # A Plain delete keeps Row 1 and Row 2, drops c, moves d and e up, and fills Row 5 plain

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    ts.str_write_base_tb(delete_row)

    assert fake.writes[-1] == delete_row.encode(), fake.writes
    assert ts.base.text_styles == (), ts.base.text_styles
    assert (ts.base_place.column_x, ts.base_place.row_y) == (5, 3), ts.base_place

    write_by_xy = ts.base.write_by_xy
    letter_by_xy = dict((xy, write[1]) for xy, write in write_by_xy.items() if write[1] != " ")
    assert letter_by_xy == {(1, 1): "a", (1, 2): "b", (1, 3): "d", (1, 4): "e"}, letter_by_xy

    row_cells = list(xy for xy in write_by_xy.keys() if xy[1] == 5)
    assert sorted(row_cells) == list((x, 5) for x in range(1, 21)), sorted(row_cells)
    assert all(write == ((), " ") for xy, write in write_by_xy.items() if xy[1] == 5), write_by_xy
    assert len(write_by_xy) == (20 + 4), write_by_xy

    # A Reverse delete fills the last Row with plain Spaces, though Reverse stays in force

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    ts.str_write_base_tb(reverse)
    ts.str_write_base_tb(delete_row)

    write_by_xy = ts.base.write_by_xy
    assert write_by_xy[(1, 5)] == ((), " "), write_by_xy  # plain, though ⎋[7M is in force
    assert write_by_xy[(20, 5)] == ((), " "), write_by_xy
    assert write_by_xy[(1, 3)] == ((), "d"), write_by_xy  # d keeps its own Text Styles
    assert (21, 5) not in write_by_xy.keys(), write_by_xy
    assert ts.base.text_styles == (reverse,), ts.base.text_styles
    assert (ts.base_place.column_x, ts.base_place.row_y) == (5, 3), ts.base_place

    # An odd Width W+1 fills Column W+1 too, since the real Terminal fills the whole Row

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=21)
    ts.str_write_base_tb(delete_row)

    write_by_xy = ts.base.write_by_xy
    assert write_by_xy[(21, 5)] == ((), " "), write_by_xy
    assert len(write_by_xy) == (21 + 4), write_by_xy

    # A delete on the last Row drops that Row and fills it, and moves nothing else

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    ts.shadow_read_data_else(b"\033[5;1R")
    ts.str_write_base_tb(delete_row)

    write_by_xy = ts.base.write_by_xy
    letter_by_xy = dict((xy, write[1]) for xy, write in write_by_xy.items() if write[1] != " ")
    assert letter_by_xy == {(1, 1): "a", (1, 2): "b", (1, 3): "c", (1, 4): "d"}, letter_by_xy
    assert len(write_by_xy) == (20 + 4), write_by_xy
    assert (ts.base_place.column_x, ts.base_place.row_y) == (1, 5), ts.base_place

    # A delete on Row 1 drops a, moves every other Row up, and fills the last Row

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    ts.shadow_read_data_else(b"\033[1;1R")
    ts.str_write_base_tb(delete_row)

    write_by_xy = ts.base.write_by_xy
    letter_by_xy = dict((xy, write[1]) for xy, write in write_by_xy.items() if write[1] != " ")
    assert letter_by_xy == {(1, 1): "b", (1, 2): "c", (1, 3): "d", (1, 4): "e"}, letter_by_xy
    assert len(write_by_xy) == (20 + 4), write_by_xy
    assert (ts.base_place.column_x, ts.base_place.row_y) == (1, 1), ts.base_place

    # A delete while waiting to wrap leaves the Cursor waiting to wrap, as no Move does

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    ts.shadow_read_data_else(b"\033[3;20R")
    ts.str_write_base_tb("z")  # lands in Column 20, and then the Cursor waits in Column 21
    assert (ts.base_place.column_x, ts.base_place.row_y) == (21, 3), ts.base_place
    ts.str_write_base_tb(delete_row)
    assert (ts.base_place.column_x, ts.base_place.row_y) == (21, 3), ts.base_place
    assert (20, 3) not in ts.base.write_by_xy.keys(), ts.base.write_by_xy  # dropped the z

    # A delete with a Pn does the one-Row delete that many times, and the Bytes go out once

    rows_from_cursor = 3  # Row 3 of 5
    for pn_text, pn_int in (
        ("", 1),
        ("0", 0),
        ("1", 1),
        ("3", 3),
        ("003", 3),
        ("4", 4),
        ("32100", 32100),
    ):
        text = f"\033[{pn_text}M"
        row_count = pn_int if pn_int else 1
        if row_count > rows_from_cursor:
            row_count = rows_from_cursor

        fake = FakeWriteBoss()
        ts = shadow_five_rows(fake, screen_width=20)
        writes_before = list(fake.writes)
        ts.str_write_base_tb(text)

        twin_fake = FakeWriteBoss()
        twin_ts = shadow_five_rows(twin_fake, screen_width=20)
        for row_index in range(row_count):
            twin_ts.str_write_base_tb(delete_row)

        occasion = (text, row_count, ts.base_place, ts.base.xy_chops, fake.writes, writes_before)
        assert ts.base.write_by_xy == twin_ts.base.write_by_xy, occasion
        assert ts.base_place == twin_ts.base_place, occasion
        assert ts.base.xy_chops == twin_ts.base.xy_chops, occasion
        assert ts.base.xy_chops == 0, occasion  # a chopped Pn counts no chop
        assert fake.writes == (writes_before + [text.encode()]), occasion

    # A delete or an insert with a Pn that is not decimal digits fails an assert before any Byte

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    writes_before = list(fake.writes)
    write_by_xy_before = dict(ts.base.write_by_xy)

    for text in ("\033[1;2M", "\033[?7M", "\033[1;2L", "\033[?7L"):
        assert asserts_for(ts.str_write_base_tb, text), (text, ts.base_place)

    assert fake.writes == writes_before, (fake.writes, writes_before)
    assert ts.base.write_by_xy == write_by_xy_before, (ts.base.write_by_xy, write_by_xy_before)

    # A delete through the Top Layer fails an assert before any Byte goes out, with a Pn too

    for text in (delete_row, "\033[3M", insert_row, "\033[3L"):
        assert asserts_for(ts.str_write_top_tb, text), (text, ts.base_place)
    assert fake.writes == writes_before, (fake.writes, writes_before)
    assert not ts.top, ts.top.place

    # A delete through the Base Layer, while the Top Layer is on, fails an assert before any Byte

    ts.str_write_top_tb("X")
    writes_before = list(fake.writes)
    write_by_xy_before = dict(ts.base.write_by_xy)
    assert ts.top, ts.top.place

    for text in (delete_row, "\033[3M", insert_row, "\033[3L"):
        assert asserts_for(ts.str_write_base_tb, text), (text, ts.top.place, ts.base_place)
    assert fake.writes == writes_before, (fake.writes, writes_before)
    assert ts.base.write_by_xy == write_by_xy_before, (ts.base.write_by_xy, write_by_xy_before)

    ts.str_write_base_tb("\b")  # other Base Writes while the Top is on go on as before
    assert fake.writes[-1] == b"\b", fake.writes

    # An insert and then a delete at the same Cursor put back each Write above the last Row

    fake = FakeWriteBoss()
    ts = shadow_five_rows(fake, screen_width=20)
    write_by_xy_before = dict(ts.base.write_by_xy)

    ts.str_write_base_tb(insert_row)
    ts.str_write_base_tb(delete_row)

    write_by_xy = ts.base.write_by_xy
    above_by_xy = dict((xy, write) for xy, write in write_by_xy.items() if xy[1] < 5)
    above_by_xy_before = dict((xy, write) for xy, write in write_by_xy_before.items() if xy[1] < 5)
    assert above_by_xy == above_by_xy_before, (above_by_xy, above_by_xy_before)
    assert len(above_by_xy) == 4, above_by_xy
    assert (ts.base_place.column_x, ts.base_place.row_y) == (5, 3), ts.base_place


def _shadow_dump_cells_(
    layer: litpyglass.TerminalLayer,
) -> dict[tuple[int, int], tuple[object, str]]:
    """Give the Writes in the Writable Area, less the plain Spaces at the East end of each Row"""

    x_max = layer.place.x_max
    cells: dict[tuple[int, int], tuple[object, str]] = dict()
    for xy, (styles, char) in layer.write_by_xy.items():
        if xy[0] <= x_max:
            cells[xy] = (litpyglass.TerminalLayer.text_styles_in_force(styles), char)

    for y in sorted(set(y for _, y in cells.keys())):
        for x in sorted((x for x, cell_y in cells.keys() if cell_y == y), reverse=True):
            if cells[(x, y)] != ((), " "):
                break  # quits at the last Write of the Row that is more than a plain Space
            del cells[(x, y)]

    return cells


def _try_shadow_dump_() -> None:
    """Try a TerminalLayer dumping its Writes as a Str, and a TerminalShadow counting chops"""

    reverse = "\033[7m"  # ⎋[7M
    plain = "\033[m"  # ⎋[M

    def asserts_for(call: typing.Callable[[], object]) -> bool:
        """Say if the call fails an assert"""

        try:
            call()
        except AssertionError:
            return True
        return False

    def shadow_blank(
        fake: FakeWriteBoss, screen_width: int, screen_height: int, row_y: int, column_x: int
    ) -> litpyglass.TerminalShadow:
        """Start a Shadow that knows only a Screen and a Cursor, with no Write"""

        ts = litpyglass.TerminalShadow(typing.cast(litpyglass.TerminalBoss, fake))
        ts.shadow_read_data_else(b"\033[1;1R")
        ts.shadow_read_data_else(f"\033[8;{screen_height};{screen_width}t".encode())
        ts.shadow_read_data_else(f"\033[{row_y};{column_x}R".encode())
        return ts

    def layer_of(screen_width: int, screen_height: int, text: str) -> litpyglass.TerminalLayer:
        """Write the Text from Row 1 Column 1 of a blank Shadow, and give the Base Layer"""

        ts = shadow_blank(FakeWriteBoss(), screen_width, screen_height, row_y=1, column_x=1)
        ts.str_write_base_tb(text)
        return ts.base

    # Each case is a Width, a Height, and the Text that draws a Layer from Row 1 Column 1

    cases = (
        (20, 5, ""),  # empty
        (20, 5, "\033[3;4H" + reverse + "  " + plain + "\b\b\033[C\033[C" + reverse + "  "),
        (
            20,
            5,
            reverse + "  " + plain + "  " + reverse + "  " + plain + "\b\b",
        ),  # Plain among Reverse
        (
            20,
            5,
            "\033[2;1H" + reverse + "a" * 20 + "\b",
        ),  # a run to the last Column of an even Width
        (
            21,
            5,
            "\033[2;1H" + reverse + "ab\033[3;1H\033[L" + "\033[2;1H" + "cd",
        ),  # Column W+1 skipped
        (21, 5, "\033[2;3Hab\033[M\033[L" + reverse + "cd"),  # Row insert after Row delete
        (20, 5, "\033[2;3H" + reverse + "ab"),  # styles left in force as ⎋[7M
        (
            20,
            5,
            "\033[32100;32100H" + "\033[m" + reverse + "z\b",
        ),  # the Cursor in the far South East
        (21, 5, "\033[32100;32100H"),  # the Cursor in Column W+1 of an odd Width, with no Write
    )

    for screen_width, screen_height, text in cases:
        layer = layer_of(screen_width, screen_height, text)
        place = layer.place
        want_cells = _shadow_dump_cells_(layer)
        chops_before = layer.xy_chops

        for from_y, from_x in ((1, 1), (screen_height, screen_width), (2, 3)):
            dump = layer.form_dump_text(from_y=from_y, from_x=from_x)
            occasion = (text, from_y, from_x, dump, place)

            # The dump starts by leaping to the Row and the Column it was given, and then only moves
            # relatively, by Moves of 1 or more

            assert dump.startswith(f"\033[{from_y};{from_x}H"), occasion
            assert len(re.findall(r"\033\[[0-9;]*H", dump)) == 1, occasion
            assert "\r" not in dump, occasion
            assert "\n" not in dump, occasion
            for move_pn, _ in re.findall(r"\033\[([0-9]*)([ABCD])", dump):
                assert move_pn and int(move_pn) >= 1, (move_pn, occasion)

            # Replay from any start Cursor of a blank Shadow of the same Size: the same Cells
            # and the same Cursor, with no chop

            for start_y, start_x in ((1, 1), (screen_height, screen_width), (3, 2)):
                fake = FakeWriteBoss()
                ts = shadow_blank(fake, screen_width, screen_height, start_y, start_x)
                kept_text, drop_count = ts.str_drop_unwritable_chars(dump)
                assert (kept_text, drop_count) == (dump, 0), (drop_count, start_y, occasion)

                ts.str_write_base_tb(kept_text)
                replay_cells = _shadow_dump_cells_(ts.base)
                assert replay_cells == want_cells, (len(replay_cells), len(want_cells), occasion)
                assert ts.base_place == place, (ts.base_place, place, start_y, start_x, occasion)
                assert ts.base.xy_chops == 0, (ts.base.xy_chops, occasion)
                in_force = litpyglass.TerminalLayer.text_styles_in_force
                assert in_force(ts.base.text_styles) == in_force(layer.text_styles), occasion
                assert fake.writes[-1] == dump.encode(), (fake.writes, occasion)

        # The dump changes nothing in the Layer

        assert _shadow_dump_cells_(layer) == want_cells, (text, place)
        assert layer.xy_chops == chops_before, (layer.xy_chops, chops_before, text)

    # Layer 19: the dump keeps a plain Space between Pixels, and drops plain Spaces to the East of
    # the last Pixel of a Row, and drops a whole Row that ⎋[⇧L or ⎋[⇧M filled with plain Spaces

    east_layer = layer_of(20, 5, f"{reverse}  {plain}  {reverse}  {plain}    \033[4;1H\033[L")
    east_dump = east_layer.form_dump_text(from_y=1, from_x=1)
    east_occasion = (east_dump, sorted(east_layer.write_by_xy.keys()))
    assert len(east_layer.write_by_xy) == (10 + 20), east_occasion  # 10 Chars and the Row of ⎋[⇧L
    assert sorted(_shadow_dump_cells_(east_layer).keys()) == [
        (x, 1) for x in range(1, 7)
    ], east_occasion
    east_want = f"\033[1;1H{plain}{reverse}  {plain}  {plain}{reverse}  {plain}\033[6D\033[3B"
    assert east_dump == east_want, (east_want, east_occasion)

    # Cells that a dump redraws do not depend on the Row and the Column it was given

    layer = layer_of(20, 5, cases[1][2])
    dumps = list(layer.form_dump_text(from_y=y, from_x=x) for y, x in ((1, 1), (5, 20), (4, 7)))
    assert len(set(dumps)) == 3, dumps  # the leaps differ, so the Strs differ

    # The Column Move comes before the Row Move, then the Pixel, then Plain

    layer = layer_of(20, 5, "\033[2;3H" + reverse + "  " + plain)
    dump = layer.form_dump_text(from_y=1, from_x=1)
    assert dump == "\033[1;1H\033[2C\033[1B\033[m\033[7m  \033[m", (dump,)

    # A Row filled by ⎋[⇧L of an odd Width W+1, with a Pixel at its East end, skips its Space in
    # Column W+1, and the same Row with no Pixel dumps no Space at all

    layer = layer_of(21, 5, "\033[2;1H\033[L" + "\033[2;19H" + reverse + "  " + plain)
    assert (21, 2) in layer.write_by_xy.keys(), layer.write_by_xy
    dump = layer.form_dump_text(from_y=1, from_x=1)
    assert dump.count(" ") == 20, (dump.count(" "), dump)

    layer = layer_of(21, 5, "\033[2;1H\033[L")
    assert len(layer.write_by_xy) == 21, layer.write_by_xy
    dump = layer.form_dump_text(from_y=1, from_x=1)
    assert dump.count(" ") == 0, (dump.count(" "), dump)

    # A dump asserts, never silently answers, when it cannot spell the Layer

    layer = layer_of(20, 5, "a")
    assert not asserts_for(lambda: layer.form_dump_text(from_y=1, from_x=20)), layer.place
    for from_y, from_x in ((0, 1), (6, 1), (1, 0), (1, 21)):
        assert asserts_for(lambda: layer.form_dump_text(from_y=from_y, from_x=from_x)), (
            from_y,
            from_x,
        )

    layer = layer_of(20, 5, "a" * 20)  # the Cursor waits to wrap, in Column 21
    assert layer.place.column_x == 21, layer.place
    assert asserts_for(lambda: layer.form_dump_text(from_y=1, from_x=1)), layer.place

    layer = layer_of(20, 5, "a")
    layer.write_by_xy[(21, 1)] = ((), "b")  # a Write keyed off the Screen
    assert asserts_for(lambda: layer.form_dump_text(from_y=1, from_x=1)), layer.write_by_xy

    layer = layer_of(20, 5, "a")
    layer.write_by_xy[(2, 1)] = (("\033[1m",), "b")  # Text Styles that are not Plain or Reverse
    assert asserts_for(lambda: layer.form_dump_text(from_y=1, from_x=1)), layer.write_by_xy

    layer = layer_of(20, 5, "a")
    layer.write_by_xy[(2, 1)] = ((), "\n")  # a Char that cannot be written
    assert asserts_for(lambda: layer.form_dump_text(from_y=1, from_x=1)), layer.write_by_xy

    layer = layer_of(20, 5, "a")
    layer.write_by_xy[(2, 1)] = ((), "")  # no Char
    assert asserts_for(lambda: layer.form_dump_text(from_y=1, from_x=1)), layer.write_by_xy


def _try_shadow_drop_() -> None:
    """Try a TerminalShadow dropping each Char it cannot write from a Str, and counting the drops"""

    def shadow_blank(
        fake: FakeWriteBoss, screen_width: int, screen_height: int, row_y: int, column_x: int
    ) -> litpyglass.TerminalShadow:
        """Start a Shadow that knows only a Screen and a Cursor, with no Write"""

        ts = litpyglass.TerminalShadow(typing.cast(litpyglass.TerminalBoss, fake))
        ts.shadow_read_data_else(b"\033[1;1R")
        ts.shadow_read_data_else(f"\033[8;{screen_height};{screen_width}t".encode())
        ts.shadow_read_data_else(f"\033[{row_y};{column_x}R".encode())
        return ts

    fake = FakeWriteBoss()
    ts = shadow_blank(fake, 20, 5, 3, 5)
    ts.str_write_base_tb("ab\033[7m")
    ts.shadow_read_data_else(b"\033[3;5R")
    cells_before = dict(ts.base.write_by_xy)
    place_before = dataclasses.replace(ts.base_place)
    styles_before = ts.base.text_styles
    writes_before = list(fake.writes)

    # A Str of Controls and of Chars that fit comes back whole, with 0 drops, chops and all

    for text in (
        "",
        "\033[C\033[C",
        "x" * 16,
        "\033[7m  \033[m\b",
        "\033[32100C",
        "\033[32100;32100H",
    ):
        kept_text, drop_count = ts.str_drop_unwritable_chars(text)
        assert (kept_text, drop_count) == (text, 0), (text, kept_text, drop_count)

    # Each Char at a Place outside the Writable Area drops and counts, each Control stays

    texts_by_want = {
        "x" * 17: ("x" * 16, 1),  # the 17th Char would land in Column 21
        "x" * 20: ("x" * 16, 4),
        "x" * 17 + "\033[7m" + "y": ("x" * 16 + "\033[7m", 2),
        "x" * 17
        + "\033[2D"
        + "y": ("x" * 16 + "\033[2D" + "y", 1),  # the Cursor stayed in Column 20
    }
    for text, want in texts_by_want.items():
        got = ts.str_drop_unwritable_chars(text)
        assert got == want, (text, got, want)

    # A Shadow of a small Screen takes the kept Str in full, the Moves chopped, the Chars dropped

    drawing = "\033[3;3H" + "\033[7m" + "ab" * 20 + "\033[9B\033[40C" + "z"
    small = shadow_blank(FakeWriteBoss(), 20, 5, 1, 1)
    kept_text, drop_count = small.str_drop_unwritable_chars(drawing)
    assert drop_count > 0, (drop_count, kept_text)
    assert len(kept_text) < len(drawing), (len(kept_text), len(drawing))

    chops_before = small.base.xy_chops
    small.str_write_base_tb(kept_text)  # always succeeds now
    assert small.base.xy_chops > chops_before, (small.base.xy_chops, chops_before)
    assert small.base.write_by_xy, small.base_place

    # The question writes no Byte and changes neither Layer

    assert ts.base.write_by_xy == cells_before, (ts.base.write_by_xy, cells_before)
    assert ts.base_place == place_before, (ts.base_place, place_before)
    assert ts.base.xy_chops == 0, (ts.base.xy_chops,)
    assert ts.base.text_styles == styles_before, (ts.base.text_styles, styles_before)
    assert not ts.top, ts.top.place
    assert fake.writes == writes_before, (fake.writes, writes_before)

    # A Str that chops is kept, and is_writable_place_after_strs still says no to it

    assert not ts.is_writable_place_after_strs("\033[32100C"), ts.base_place

    # Layer 4: a Line Feed fails an assert, never skipped, in each walk of a Str, and no Byte goes out

    for line_feed_text in ("\n", "a\nb", "\033[C\n", "\r\n"):
        line_feed_writes_before = list(fake.writes)

        raises: list[str] = list()
        for write in (
            ts.str_drop_unwritable_chars,
            ts.str_write_base_tb,
            ts.is_writable_place_after_strs,
        ):
            try:
                write(line_feed_text)
            except AssertionError:
                raises.append(write.__name__)

        assert len(raises) == 3, (raises, line_feed_text)
        assert fake.writes == line_feed_writes_before, (fake.writes, line_feed_text)


def _try_shadow_top_layer_() -> None:
    """Try the Top Layer of a TerminalShadow keeping Writes to undo, as specs.md § 10 says"""

    fake = FakeWriteBoss()
    boss = typing.cast(litpyglass.TerminalBoss, fake)
    ts = litpyglass.TerminalShadow(boss)
    assert ts.top.write_by_xy == {}, ts.top.write_by_xy

    ts.shadow_read_data_else(b"\033[2;3R")  # Row 2 Column 3
    ts.shadow_read_data_else(b"\033[8;5;20t")  # a Screen 5 high, 20 wide

    no_sgr_csi = "\033[m"  # ⎋[M
    reverse = "\033[7m"  # ⎋[7M
    to_start = "\033[B\033[C\033[C"  # from Row 1 Column 1 to Row 2 Column 3, where the Shadow began

    def screen_after_writes() -> tuple[dict[tuple[int, int], tuple[str, bool]], tuple[int, int]]:
        """Replay every Write the Terminal has been given, and say the Cells marked and the Cursor"""

        decode = to_start + "".join(_.decode() for _ in fake.writes)
        mark_by_yx, cursor_yx, _ = _skater_state_(decode, screen_width=20, screen_height=5)
        return (mark_by_yx, cursor_yx)

    # Undo with nothing in the Top Layer writes nothing

    ts.undo_top_tb()
    assert fake.writes == [], fake.writes

    # A Reverse Pair written into the Base Layer, and the Cursor back on its left Cell

    ts.str_write_base_tb(no_sgr_csi + reverse + "  " + no_sgr_csi + "\b\b")
    assert ts.base.is_shadowed_area(area_width=2, area_height=1), ts.base_place
    base_writes = dict(ts.base.write_by_xy)
    assert set(base_writes.keys()) == {(3, 2), (4, 2)}, base_writes

    ts.str_write_base_tb("\033[C\033[C")  # a bare Cell east
    assert not ts.base.is_shadowed_area(area_width=2, area_height=1), ts.base_place
    ts.str_write_base_tb("\033[D\033[D")  # back on the Reverse Pair

    # A Plain Pair and then an X, written into the Top Layer, land only in the Top Layer

    ts.str_write_top_tb("  ")  # leaves the Top Layer's Cursor East of the Base Layer's
    assert (ts.top.place.column_x, ts.base_place.column_x) == (5, 3), (ts.top.place, ts.base_place)
    ts.str_write_top_tb("\b\b")
    ts.str_write_top_tb("X\b")
    assert ts.base.write_by_xy == base_writes, (ts.base.write_by_xy, base_writes)
    assert ts.top.write_by_xy == {
        (3, 2): ((no_sgr_csi,), "X"),  # the X replaced the Plain Pair's left Cell
        (4, 2): ((no_sgr_csi,), " "),
    }, ts.top.write_by_xy

    mark_by_yx, cursor_yx = screen_after_writes()
    assert mark_by_yx == {(2, 3): ("X", False)}, mark_by_yx  # the Plain Pair covers the Reverse Pair
    assert cursor_yx == (2, 3), (cursor_yx, mark_by_yx)
    assert dataclasses.astuple(ts.base_place) == dataclasses.astuple(ts.top.place)

    # Undo writes the Base Layer back over each Cell of the Top Layer, and forgets the Top Layer

    ts.undo_top_tb()
    assert ts.top.write_by_xy == {}, ts.top.write_by_xy
    assert ts.base.write_by_xy == base_writes, (ts.base.write_by_xy, base_writes)
    assert fake.writes[-1].endswith(b"\033[2D"), fake.writes[-1]  # one move only, West to the Base
    assert b"\r" not in fake.writes[-1], fake.writes[-1]

    mark_by_yx, cursor_yx = screen_after_writes()
    assert mark_by_yx == {
        (2, 3): (" ", True),
        (2, 4): (" ", True),
    }, mark_by_yx  # the Reverse Pair is back
    assert cursor_yx == (2, 3), (cursor_yx, mark_by_yx)  # and the Cursor sits where it began

    # Undo never guesses what a bare Cell held, and the Skater forgets a lone Char there first

    fake4 = FakeWriteBoss()
    ts4 = litpyglass.TerminalShadow(typing.cast(litpyglass.TerminalBoss, fake4))
    ts4.shadow_read_data_else(b"\033[2;3R")
    ts4.shadow_read_data_else(b"\033[8;5;20t")
    ts4.str_write_top_tb("Y\b")  # a lone Y over a bare Cell
    try:
        ts4.undo_top_tb()
        asserted = False
    except AssertionError:
        asserted = True
    assert asserted  # the Base Layer wrote nothing at the Y

    glass_worker = litpyglass.GlassWorker()
    glass_worker.ts_undo_enough_top_tb(ts4)  # forgets the lone Y, then undoes the Top
    assert not ts4.top, ts4.top.place
    assert ts4.base.write_by_xy == {}, ts4.base.write_by_xy  # Base never learns of the Y

    decode4 = to_start + "".join(_.decode() for _ in fake4.writes)
    mark_by_yx, cursor_yx, _ = _skater_state_(decode4, screen_width=20, screen_height=5)
    assert mark_by_yx == {(2, 3): ("Y", False)}, mark_by_yx  # the Y stays, as a Prompt Char does
    assert cursor_yx == (2, 3), (cursor_yx, mark_by_yx)

    fake5 = FakeWriteBoss()
    ts5 = litpyglass.TerminalShadow(typing.cast(litpyglass.TerminalBoss, fake5))
    ts5.shadow_read_data_else(b"\033[2;3R")
    ts5.shadow_read_data_else(b"\033[8;5;20t")
    ts5.str_write_top_tb("Y")  # a lone Y, with the Cursor one Cell past it
    try:
        glass_worker.ts_undo_enough_top_tb(ts5)
        asserted = False
    except AssertionError:
        asserted = True
    assert asserted  # the def forgets only a Char that the Cursor sits on

    # Undo reaches Cells further East on the Row, and puts the Cursor back West

    base_xy = dataclasses.astuple(ts.base_place)
    base_styles = ts.base.text_styles

    ts.str_write_top_tb("Z\b")  # a Z on the Reverse Pair's left Cell
    ts.str_write_top_tb("\033[C\033[7mW\b\033[D")  # a Reverse W on its right Cell, and back
    assert ts.top.text_styles == ("\033[m", "\033[7m"), ts.top.text_styles
    assert dataclasses.astuple(ts.base_place) == base_xy, ts.base_place  # Base keeps its Cursor
    assert ts.base.text_styles == base_styles, ts.base.text_styles  # and its Text Styles

    ts.undo_top_tb()
    assert not ts.top, ts.top.place  # the Top is off
    assert list(ts.top.text_styles) == list(), ts.top.text_styles  # and holds no Text Style
    mark_by_yx, cursor_yx = screen_after_writes()
    assert mark_by_yx == {(2, 3): (" ", True), (2, 4): (" ", True)}, mark_by_yx  # no Z, no W
    assert cursor_yx == (2, 3), (cursor_yx, mark_by_yx)  # back where the Base Layer has it

    # A Top Layer written in a Text Style only is on, so Undo still puts the Cursor and Styles back

    assert not ts.top, ts.top.place  # off, before any Top write
    base_xy = dataclasses.astuple(ts.base_place)
    base_styles = ts.base.text_styles

    ts.str_write_top_tb(reverse)
    assert ts.top, ts.top.place  # on, with no Cell written
    assert ts.top.write_by_xy == {}, ts.top.write_by_xy

    ts.undo_top_tb()  # writes the Base Style and the Base Cursor, though no Cell was written
    assert not ts.top, ts.top.place
    stay_put = (no_sgr_csi + "".join(base_styles)).encode()  # no move, the Cursor never left
    assert fake.writes[-1] == stay_put, fake.writes[-1]

    ts.str_write_top_tb(reverse)
    ts.str_write_top_tb("W\b")  # starts from the Top, so carries the Style written before it
    top_styles, top_text = ts.top.write_by_xy[(ts.base_place.column_x, ts.base_place.row_y)]
    assert (top_styles, top_text) == (base_styles + (reverse,), "W"), (top_styles, top_text)

    ts.undo_top_tb()
    assert not ts.top, ts.top.place  # off again
    assert dataclasses.astuple(ts.base_place) == base_xy, ts.base_place
    mark_by_yx, cursor_yx = screen_after_writes()
    assert cursor_yx == (ts.base_place.row_y, ts.base_place.column_x), (cursor_yx, mark_by_yx)

    ts.undo_top_tb()
    undone_writes = list(fake.writes)
    ts.undo_top_tb()
    assert fake.writes == undone_writes, fake.writes  # an Undo of an off Top writes nothing

    # A Reply from the Terminal goes where the Cursor sits, so to the Top once the Top is on

    fake2 = FakeWriteBoss()
    ts2 = litpyglass.TerminalShadow(typing.cast(litpyglass.TerminalBoss, fake2))
    ts2.shadow_read_data_else(b"\033[2;3R")
    ts2.shadow_read_data_else(b"\033[8;5;20t")

    ts2.shadow_read_data_else(b"\033[1;1R")  # Top off, so the Base takes the Cursor
    assert (ts2.base_place.row_y, ts2.base_place.column_x) == (1, 1), ts2.base_place
    assert not ts2.top, ts2.top.place

    ts2.shadow_read_data_else(b"\033[8;6;22t")  # Top off, so it stays off
    assert (ts2.base_place.y_height, ts2.base_place.x_width) == (6, 22), ts2.base_place
    assert not ts2.top, ts2.top.place

    ts2.str_write_top_tb(reverse)  # Top on
    ts2.shadow_read_data_else(b"\033[1;4R")  # on the same Row, so Undo needs no step up
    assert (ts2.top.place.row_y, ts2.top.place.column_x) == (1, 4), ts2.top.place
    assert (ts2.base_place.row_y, ts2.base_place.column_x) == (1, 1), ts2.base_place

    ts2.shadow_read_data_else(b"\033[8;7;24t")
    assert (ts2.top.place.y_height, ts2.top.place.x_width) == (7, 24), ts2.top.place
    assert (ts2.base_place.y_height, ts2.base_place.x_width) == (7, 24), ts2.base_place

    ts2.undo_top_tb()
    assert not ts2.top, ts2.top.place
    assert (ts2.base_place.row_y, ts2.base_place.column_x) == (1, 1), ts2.base_place

    # A move steps West along the Row, says nothing for no step, and asserts on any other step

    base_x = ts.base_place.column_x
    base_y = ts.base_place.row_y
    move_text = litpyglass.TerminalShadow.form_leap_back(
        ts.base_place, column_x=(base_x - 2), row_y=base_y
    )
    assert move_text == "\033[2D", move_text

    move_text = litpyglass.TerminalShadow.form_leap_back(
        ts.base_place, column_x=base_x, row_y=base_y
    )
    assert move_text == "", move_text  # no Pn of 0, which Terminals take as 1

    for column_x, row_y in ((base_x + 1, base_y), (base_x - 1, base_y + 1)):
        try:  # a step East, and a step South, each assert
            litpyglass.TerminalShadow.form_leap_back(ts.base_place, column_x=column_x, row_y=row_y)
            asserted = False
        except AssertionError:
            asserted = True
        assert asserted, (column_x, row_y)

    # The Shadow takes a step of 0 as a step of 1, as a Terminal does

    zero_place = dataclasses.replace(ts.base_place)
    one_place = dataclasses.replace(ts.base_place)
    zero_place.write_str_at_place("\033[0C")
    one_place.write_str_at_place("\033[C")
    assert zero_place == one_place, (zero_place, one_place, ts.base_place)

    # Undo at the right edge steps West from Column W+1, where a Cursor waiting to wrap sits

    fake3 = FakeWriteBoss()
    ts3 = litpyglass.TerminalShadow(typing.cast(litpyglass.TerminalBoss, fake3))
    ts3.shadow_read_data_else(b"\033[2;19R")  # Row 2 Column 19, the left Cell of the last Pair
    ts3.shadow_read_data_else(b"\033[8;5;20t")  # a Screen 5 high, 20 wide

    ts3.str_write_base_tb(reverse + "  " + no_sgr_csi + "\b")  # a Reverse Pair, waiting to wrap
    ts3.str_write_top_tb("  \b")  # a Plain Pair over it, with one step back
    ts3.undo_top_tb()

    decode = "\033[B" + (18 * "\033[C") + "".join(_.decode() for _ in fake3.writes)
    mark_by_yx, cursor_yx, _ = _skater_state_(decode, screen_width=20, screen_height=5)
    assert mark_by_yx == {(2, 19): (" ", True), (2, 20): (" ", True)}, mark_by_yx
    assert cursor_yx == (2, 19), (cursor_yx, mark_by_yx)  # not one Column further West

    # The Shadow says its Base Layer's Place and writeable Areas as its own

    assert ts.base_place is ts.base.place, (ts.base_place, ts.base.place)
    for area_width, area_height in ((1, 1), (2, 1), (1, 4), (1, 5), (20, 5), (21, 5)):
        want = ts.base.is_writeable_area(area_width=area_width, area_height=area_height)
        got = ts.is_writeable_base_area(area_width=area_width, area_height=area_height)
        assert got == want, (area_width, area_height, got, want)

    # An Area is writeable only when every Cell of it lies in the Writable Area

    area_layer = ts.base.fork_layer()
    for column_x, row_y, area_width, area_height, x_width, want in (
        (19, 1, 2, 1, 20, True),  # the last Pair of a Screen 20 wide
        (20, 1, 2, 1, 20, False),  # its right Cell would be Column 21
        (20, 1, 1, 1, 20, True),
        (21, 1, 1, 1, 21, False),  # Column 21 of 21 lies past x_max 20
        (1, 5, 1, 1, 20, True),  # the last Row of a Screen 5 high
        (1, 5, 1, 2, 20, False),  # its lower Cell would be Row 6
        (1, 1, 20, 5, 20, True),  # the whole Screen
        (1, 1, 21, 5, 20, False),
    ):
        area_layer.place = dataclasses.replace(
            area_layer.place, column_x=column_x, row_y=row_y, x_width=x_width
        )
        writeable = area_layer.is_writeable_area(area_width=area_width, area_height=area_height)
        assert writeable == want, (column_x, row_y, area_width, area_height, x_width, writeable)

    # A written Cell is a shadowed Cell, whether written plain or in Reverse

    ts.str_write_base_tb("\033[C\033[C")  # a bare Cell east of the Reverse Pair

    assert not ts.base.is_shadowed_area(area_width=1, area_height=1), ts.base_place  # a bare Cell
    ts.str_write_base_tb("a\b")  # a plain a, and back
    assert ts.base.is_shadowed_area(area_width=1, area_height=1), ts.base_place

    # A Cell is shadowed only when every Cell of the whole Area is written

    assert not ts.base.is_shadowed_area(
        area_width=2, area_height=1
    ), ts.base_place  # the next Cell is bare
    assert not ts.base.is_shadowed_area(
        area_width=1, area_height=2
    ), ts.base_place  # the Cell below is bare

    ts.str_write_base_tb("\033[Ba\b\033[A")  # a plain a one Row down, and back up
    assert ts.base.is_shadowed_area(area_width=1, area_height=2), ts.base_place
    assert not ts.base.is_shadowed_area(area_width=2, area_height=2), ts.base_place

    # todo: look at a Plain Pair over a written Cell in a real Terminal window


def _try_screen_replay_() -> None:
    """Try the Screen replay that the Tests of specs.md § 8 use, and its assert on a Byte not modeled"""

    for decode in ("\033[2J", "\033[1;2A", "\033[5m", "\t", "\033"):
        try:
            _screen_of_(decode, screen_width=20, screen_height=5)
            asserted = False
        except AssertionError:
            asserted = True
        assert asserted, (decode,)

    cells, row_y, column_x, wrap_pending = _screen_of_(
        "ab\033[3C\033[2D\n\033[?25h", screen_width=20, screen_height=5
    )
    assert cells[0][0] == ("a", False), cells[0][:3]  # models what it claims
    assert (row_y, column_x, wrap_pending) == (2, 4, False), (row_y, column_x, wrap_pending)


def _screen_of_(
    screen_decode: str, screen_width: int, screen_height: int
) -> tuple[list[list[tuple[str, bool]]], int, int, bool]:
    """Replay the Bytes onto a Screen that waits to wrap, as macOS Terminal does, from Row 1"""

    screen_cells = list(
        list((" ", False) for _ in range(screen_width)) for _ in range(screen_height)
    )
    row_y = 1
    column_x = 1
    wrap_pending = False  # true after a write into the last Column, till the next write or move
    inverse = False

    pattern = re.compile(r"\033\[([?0-9;]*)([ -/]*[@-~])|.", re.DOTALL)
    for match in pattern.finditer(screen_decode):
        text = match.group(0)
        if text.startswith("\033["):
            ps = match.group(1)
            final = text[-1]
            n = max(1, int(ps)) if ps.isdigit() else 1  # a Pn of 0 acts as 1

            # The Show, the Hide, and the two Asks mark no Cell and move no Cursor

            quiet_list = ("\033[?25h", "\033[?25l", "\033[6n", "\033[18t")
            if text in quiet_list:
                pass
            elif final == "m":
                assert ps in ("", "7"), repr(text)  # models only no Style and Reverse
                inverse = ps == "7"
            else:
                assert final in "ABCD", repr(text)  # models no other Csi
                assert ps.isdigit() or (not ps), repr(text)  # models only a lone Pn
                if final == "A":
                    row_y = max(1, row_y - n)
                    wrap_pending = False  # ⎋[⇧A ends the wait, in the last Column
                elif final == "B":
                    row_y = min(screen_height, row_y + n)
                    wrap_pending = False  # ⎋[⇧B ends the wait, in the last Column
                elif final == "C":
                    column_x = min(screen_width, column_x + n)
                    wrap_pending = False
                else:
                    assert final == "D", (final,)
                    wait_x = 1 if wrap_pending else 0  # ⎋[⇧D counts from Column W+1
                    column_x = max(1, column_x + wait_x - n)
                    wrap_pending = False
            continue

        if text == "\r":
            column_x = 1
            wrap_pending = False
        elif text == "\b":
            column_x = max(1, column_x - 1)
            wrap_pending = False
        elif text == "\n":
            wrap_pending = False
            if row_y >= screen_height:
                screen_cells.pop(0)  # scrolls
                screen_cells.append(list((" ", False) for _ in range(screen_width)))
            else:
                row_y += 1
        else:
            assert text.isprintable(), repr(text)  # models only \r \b \n and printable Chars
            if wrap_pending:
                column_x = 1
                row_y = min(screen_height, row_y + 1)
                wrap_pending = False

            screen_cells[row_y - 1][column_x - 1] = (text, inverse)
            if column_x >= screen_width:
                wrap_pending = True
            else:
                column_x += 1

    return (screen_cells, row_y, column_x, wrap_pending)


_PLACED_CHILD_ = r"""
import dataclasses, os, sys
sys.path.insert(0, sys.argv[1])
import litpyglass

sync_fileno = int(sys.argv[2])
boss = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"<FAREWELL>")
ts = litpyglass.TerminalShadow(boss)
ist = litpyglass.InputStrikeTaker(ts, arrow_wait_nanos=0)
print("READY1", flush=True)
os.read(sync_fileno, 1)  # ↑, a Reply, a lookalike Reply, a Reply, and ↓ are typed
places = list()
with boss:
    ist.pull_yx_hw_from_ts_else(stalwarts=())
    for isap in ist.take_input_strikes_and_yield_each_placed(stalwarts=()):
        if not isap.strike.taken:
            continue  # the Open Frame comes before each Read, and says nothing yet
        place = isap.place and dataclasses.astuple(isap.place)
        places.append((isap.strike.caps, place))
        if len(places) == 2:
            break
print("RESULT", repr(tuple(places)), flush=True)
"""

_PLACED_OFF_TERMINAL_CHILD_ = r"""
import dataclasses, sys
sys.path.insert(0, sys.argv[1])
import litpyglass

boss = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"")
ts = litpyglass.TerminalShadow(boss)
ist = litpyglass.InputStrikeTaker(ts, arrow_wait_nanos=0)
places = list()
with boss:
    ist.pull_yx_hw_from_ts_else(stalwarts=())
    for isap in ist.take_input_strikes_and_yield_each_placed(stalwarts=()):
        if not isap.strike.taken:
            continue  # the Open Frame comes before each Read, and says nothing yet
        place = isap.place and dataclasses.astuple(isap.place)
        places.append((isap.strike.caps, place))
print("RESULT", repr(tuple(places)), flush=True)
"""


def _try_frame_reader_quits_midbatch_() -> None:
    """Try that a Caller who quits mid-batch leaves the later Taken Frames, as specs.md § 5 says"""

    read_fake = FakeReadBoss()
    boss = typing.cast(litpyglass.TerminalBoss, read_fake)
    tfr = litpyglass.TerminalFrameReader(boss)

    taken_count = 0
    for taken, frame, _ in tfr.take_frames_and_yield_each(stalwarts=()):
        taken_count += int(taken)
        if taken_count == 2:
            break  # quits at the second Frame of three

    assert read_fake.reads == 1, (read_fake.reads,)

    shows = list()
    for taken, frame, _ in tfr.take_frames_and_yield_each(stalwarts=()):
        shows.append((taken, frame.to_frame_bytes(), read_fake.reads))

    # the third Frame comes first, before the Open Frame, and before any second read

    expected = [(True, b"\033[B", 1), (False, b"", 1)]
    assert shows == expected, (shows, expected)


def _try_frame_reader_nanobytes_() -> None:
    """Try that each Taken Frame has its Nanos waited and Bytes read, as specs.md § 5 says"""

    slow_fake = FakeSlowBoss()
    boss = typing.cast(litpyglass.TerminalBoss, slow_fake)
    tfr = litpyglass.TerminalFrameReader(boss)

    shows = list()
    for taken, frame, frame_nanobytes in tfr.take_frames_and_yield_each(stalwarts=()):
        assert isinstance(frame_nanobytes, tuple), (taken, frame_nanobytes)  # Open Frames too
        if taken:
            shows.append((frame.to_frame_bytes(), frame_nanobytes))

    (data1, nanobytes1), (data2, nanobytes2) = shows
    assert (data1, data2) == (b"\033[B", b"q"), (data1, data2)

    # one (Nanos waited, Byte read) pair for each Byte, in order

    assert list(b for _, b in nanobytes1) == [b"\033", b"[", b"B"], nanobytes1
    assert list(b for _, b in nanobytes2) == [b"q"], nanobytes2

    # the Nanos waited are 0 for every Byte of a read but the first

    assert list(w for w, _ in nanobytes1)[1:] == [0, 0], nanobytes1
    assert nanobytes1[0][0] >= 1_000_000 and nanobytes2[0][0] >= 1_000_000, (nanobytes1, nanobytes2)


def _try_frame_reader_peek_() -> None:
    """Try that the Reader peeks for a Combining Mark in the same read, as specs.md § 5 says"""

    acute = b"\314\201"  # U+0301 Combining Acute Accent, category Mn, 2 Bytes
    spacing = b"\340\244\203"  # U+0903 Devanagari Sign Visarga, category Mc, 3 Bytes
    enclosing = b"\342\203\235"  # U+20DD Combining Enclosing Circle, category Me, 3 Bytes
    stem = b"\360\235\205\245"  # U+1D165 Musical Symbol Combining Stem, category Mc, 4 Bytes
    printable = b"\303\251"  # U+00E9 Latin Small Letter E With Acute, category Ll, not a Mark
    marks = (acute, spacing, enclosing, stem)

    # Hold one Frame open across one read, for each Category of Mark and for each Byte count

    for mark in marks:
        taken, opened = _frames_of_([b"\033j" + mark])
        assert taken == [b"\033j" + mark], (taken, mark)
        assert opened == [b"", b""], (opened, mark)

    # Close the Frame at the j, and start another at the Mark, across two reads

    for mark in marks:
        taken, opened = _frames_of_([b"\033j", mark])
        assert taken == [b"\033j", mark], (taken, mark)
        assert opened == [b"", b"", mark], (opened, mark)

    # Close the Frame at the j, when the Char after is not a Mark

    for plain in (b"x", printable):
        taken, opened = _frames_of_([b"\033j" + plain])
        assert taken == [b"\033j", plain], (taken, plain)
        assert opened == [b"", plain], (opened, plain)

    # Take Text, a j and then a Mark, as one Frame left open, whether in one read or in two

    taken, opened = _frames_of_([b"j" + acute])
    assert taken == [b"j" + acute], (taken,)
    assert opened == [b"", b"j" + acute], (opened,)

    taken, opened = _frames_of_([b"j", acute])
    assert taken == [b"j" + acute], (taken,)
    assert opened == [b"", b"j", b"j" + acute], (opened,)


def _try_frame_reader_tilt_() -> None:
    """Try that a typed ⎋[⇧M closes at once as Delete Row, as specs.md § 5 says"""

    # Close a ⎋[⇧M typed slowly, one Byte per read

    fake = FakeTiltBoss([(15, b"\033"), (15, b"["), (15, b"M")], typeahead=b"")
    taken, frames = _tilt_taken_(fake)
    occasion = (fake.chunks, fake.opens, taken, frames)
    (frame,) = frames
    assert taken == [b"\033[M"], occasion
    shape = (frame.closed, bytes(frame.head), bytes(frame.neck), bytes(frame.backtail))
    assert shape == (True, b"\033[", b"", b"M"), (shape, frame, occasion)
    assert fake.opens[-1] == b"", occasion  # the Open Frame after is empty

    # Leave it open for {b}{x}{y}, when a whole Mouse Report comes in one read

    fake = FakeTiltBoss([(15, b"\033[M !!")], typeahead=b"")
    taken, frames = _tilt_taken_(fake)
    occasion = (fake.chunks, fake.opens, taken, frames)
    assert taken == [b"\033[M !!"], occasion

    # Leave it open, when the ⇧M comes last in its read but not first, so not slowly

    fake = FakeTiltBoss([(0, b"\033[M"), (15, b" !!")], typeahead=b"")
    taken, frames = _tilt_taken_(fake)
    occasion = (fake.chunks, fake.opens, taken, frames)
    assert taken == [b"\033[M !!"], occasion

    # Leave it open, when the ⇧M comes slowly but not alone, as a Mouse Report cut before its ⇧M

    fake = FakeTiltBoss([(0, b"\033["), (15, b"M !!")], typeahead=b"")
    taken, frames = _tilt_taken_(fake)
    occasion = (fake.chunks, fake.opens, taken, frames)
    assert taken == [b"\033[M !!"], occasion

    # Leave it open, when the ⇧M comes alone but fast, with no sleep so under 10 ms

    fake = FakeTiltBoss([(0, b"\033["), (0, b"M"), (0, b" !!")], typeahead=b"")
    taken, frames = _tilt_taken_(fake)
    occasion = (fake.chunks, fake.opens, taken, frames)
    assert taken == [b"\033[M !!"], occasion
    assert fake.opens[2] == b"\033[M", occasion  # stayed open after the M

    # Leave it open while Typeahead waits, and take it cut off at the end of Input

    fake = FakeTiltBoss([], typeahead=b"\033[M")
    taken, frames = _tilt_taken_(fake)
    occasion = (fake.chunks, fake.opens, taken, frames)
    (frame,) = frames
    assert taken == [b"\033[M"], occasion
    shape = (frame.closed, bytes(frame.head), bytes(frame.neck), bytes(frame.backtail))
    assert shape == (False, b"\033[M", b"", b""), (shape, frame, occasion)

    # Close the ordinary ⎋[1⇧M as ever, when typed slowly

    fake = FakeTiltBoss([(15, b"\033"), (15, b"["), (15, b"1"), (15, b"M")], typeahead=b"")
    taken, frames = _tilt_taken_(fake)
    occasion = (fake.chunks, fake.opens, taken, frames)
    (frame,) = frames
    assert taken == [b"\033[1M"], occasion
    shape = (frame.closed, bytes(frame.head), bytes(frame.neck), bytes(frame.backtail))
    assert shape == (True, b"\033[", b"1", b"M"), (shape, frame, occasion)


class FakeTiltBoss:
    """Pretend to be a TerminalBoss that reads each chunk after its ms wait, Typeahead first"""

    def __init__(self, chunks: list[tuple[int, bytes]], typeahead: bytes) -> None:
        self.ibk = litpyglass.ByteKeeper()  # every Byte read, and when
        self.chunks = list(chunks)  # (ms to wait, Bytes of the read), in order
        self.typeahead = bytearray(typeahead)  # Bytes that come one per read, each after 15 ms
        self.opens: list[bytes] = list()  # the Open Frame yielded before each read

    def read_some_bytes_if(self) -> bytes:
        data = b""
        if self.typeahead:
            time.sleep(0.015)
            data = bytes([self.typeahead.pop(0)])
        elif self.chunks:
            ms, data = self.chunks.pop(0)
            time.sleep(ms / 1e3)

        self.ibk.append_some_bytes(data, nano=time.perf_counter_ns())
        return data


def _tilt_taken_(fake: FakeTiltBoss) -> tuple[list[bytes], list[litpyglass.TerminalByteFrame]]:
    """Read every chunk of the fake, and return the Taken Frames as Bytes, and as Frames"""

    boss = typing.cast(litpyglass.TerminalBoss, fake)
    tfr = litpyglass.TerminalFrameReader(boss)

    takens: list[bytes] = list()
    frames: list[litpyglass.TerminalByteFrame] = list()
    for taken, frame, _ in tfr.take_frames_and_yield_each(stalwarts=()):
        if taken:
            takens.append(frame.to_frame_bytes())
            frames.append(frame)
        else:
            fake.opens.append(frame.to_frame_bytes())

    return (takens, frames)


def _frames_of_(chunks: list[bytes]) -> tuple[list[bytes], list[bytes]]:
    """Read each chunk in turn, and return the Taken Frames and the Open Frames yielded"""

    boss = typing.cast(litpyglass.TerminalBoss, FakeChunkBoss(chunks))
    tfr = litpyglass.TerminalFrameReader(boss)

    takens: list[bytes] = list()
    opens: list[bytes] = list()
    for taken, frame, _ in tfr.take_frames_and_yield_each(stalwarts=()):
        (takens if taken else opens).append(frame.to_frame_bytes())

    return (takens, opens)


def _try_frame_print_() -> None:
    """Try that a Frame prints its first wait, and later waits if not 0ns, as specs.md § 8 says"""

    glass_worker = litpyglass.GlassWorker()
    start = "\r\033[K"  # from the start of the Line
    esc = b"\033"

    def printed(data: bytes, frame_nanobytes: tuple[tuple[int, bytes], ...]) -> str:
        boss = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"")

        captured_bytes = io.BytesIO()
        captured = io.TextIOWrapper(captured_bytes, encoding="utf-8", newline="")  # as Stdout is
        with contextlib.redirect_stdout(captured):
            glass_worker.frame_print(data, nanobytes=frame_nanobytes, end="\r\n", tb=boss)
            captured.flush()

        captured_data = captured_bytes.getvalue()
        assert bytes(boss.typescript) == captured_data, (boss.typescript, captured_data)
        return captured_data.decode()

    prefix = start + "↑ '\\033[A' b'\\033[A' = "

    # a first wait of 750ms prints, and the later waits of 0ns drop

    got = printed(b"\033[A", frame_nanobytes=((750_000_000, esc), (0, b"["), (0, b"A")))
    assert got == prefix + "750ms b'\\033' b'[' b'A'\r\n", got

    # a first wait of 0ns still prints, once

    got = printed(b"\033[A", frame_nanobytes=((0, esc), (0, b"["), (0, b"A")))
    assert got == prefix + "0ns b'\\033' b'[' b'A'\r\n", got

    # a later wait of more than 0ns prints too

    got = printed(b"\033[A", frame_nanobytes=((750_000_000, esc), (3_000_000, b"["), (0, b"A")))
    assert got == prefix + "750ms b'\\033' 3.00ms b'[' b'A'\r\n", got

    # a burst of j before Combining Acute prints as ⌥EJ, and the same Bytes 320ms apart as no Key Caps

    j_acute = "j\u0301".encode()
    b1, b2, b3 = b"j", b"\314", b"\201"
    assert j_acute == b1 + b2 + b3, (j_acute,)

    got = printed(j_acute, frame_nanobytes=((750_000_000, b1), (0, b2), (0, b3)))
    assert got == start + "⌥EJ j\u0301 b'j\\314\\201' = 750ms b'j' b'\\314' b'\\201'\r\n", got

    got = printed(j_acute, frame_nanobytes=((750_000_000, b1), (320_000_000, b2), (0, b3)))
    want = start + "j\u0301 b'j\\314\\201' = 750ms b'j' 320ms b'\\314' b'\\201'\r\n"
    assert got == want, (got, want)

    # a Dead Key's burst prints as ⌥I P, and the same Bytes struck 320ms apart as ⌥⇧I P

    circumflex_p = "ˆp".encode()
    b1, b2, b3 = b"\313", b"\206", b"p"
    assert circumflex_p == b1 + b2 + b3, (circumflex_p,)

    got = printed(circumflex_p, frame_nanobytes=((750_000_000, b1), (0, b2), (0, b3)))
    assert got == start + "⌥I P ˆp b'\\313\\206p' = 750ms b'\\313' b'\\206' b'p'\r\n", got

    got = printed(circumflex_p, frame_nanobytes=((750_000_000, b1), (0, b2), (320_000_000, b3)))
    want = start + "⌥⇧I P ˆp b'\\313\\206p' = 750ms b'\\313' b'\\206' 320ms b'p'\r\n"
    assert got == want, (got, want)


def _try_pull_ends_without_replies_() -> None:
    """Try that Input ending before both Replies fails loudly, as specs.md § 7 says"""

    boss = typing.cast(litpyglass.TerminalBoss, FakeEndBoss())
    ist = litpyglass.InputStrikeTaker(litpyglass.TerminalShadow(boss), arrow_wait_nanos=0)

    heard = io.StringIO()
    with contextlib.redirect_stdout(heard):
        try:
            ist.pull_yx_hw_from_ts_else(stalwarts=())
            code = None
        except SystemExit as exc:
            code = exc.code

    complaint = "Input ended before Y X H W replies to ⎋[6N and ⎋[18T"
    assert code == 1, (code, heard.getvalue())
    assert complaint in heard.getvalue(), (complaint, heard.getvalue())


def _try_placed_input_strikes_() -> None:
    """Try the Place each Strike takes, as specs.md § 7 says"""

    typed = b"\033[A" + b"\033[5;7R" + b"\033[9;9R" + b"\033[8;24;81t" + b"\033[B"
    result = _pty_run_child_(_PLACED_CHILD_, terminal_bytes=typed)

    place = (9, 80, 81, 9, 24)  # column_x, x_max, x_width, row_y, y_height: the last ⎋[9;9⇧R
    expected = (("↑", place), ("↓", place))  # the Replies are no Strikes
    assert result == expected, (result, expected)

    here = os.path.dirname(os.path.abspath(litpyglass.__file__))
    argv = [sys.executable, "-I", "-c", _PLACED_OFF_TERMINAL_CHILD_, here]
    complaint = b"Input ended before Y X H W replies to"
    yx, hw, arrows = b"\033[1;1R", b"\033[8;24;80t", b"\033[A\033[B"
    place = (1, 80, 80, 1, 24)  # column_x, x_max, x_width, row_y, y_height from those Replies
    taken = "RESULT (('↑', %s), ('↓', %s))" % (place, place)

    cases = (  # off a Terminal, nothing asks, so the Input must volunteer both Replies
        (arrows, None),  # both Replies absent
        (yx + arrows, None),  # only YX present
        (yx + hw + arrows, taken),  # ordered
        (hw + yx + arrows, taken),  # disordered
    )

    for data, want in cases:
        run = subprocess.run(argv, input=data, capture_output=True, timeout=10)
        if want is None:
            assert run.returncode == 1, (run.returncode, run.stdout, run.stderr, data)
            assert complaint in run.stdout, (run.stdout, data)
        else:
            assert run.returncode == 0, (run.returncode, run.stdout, run.stderr, data)
            assert want in run.stdout.decode(), (run.stdout, want, data)


def _intercardinal_taken_(chunks: tuple[bytes, ...]) -> tuple[list[tuple[str, bytes]], list[str]]:
    """Take Strikes from fake reads, and say each taken Strike as Key Caps and Bytes, and events"""

    wait_50ms = litpyglass._50_MEGA_NANOS_
    return _intercardinal_taken_ahead_(chunks, typeahead=b"", arrow_wait_nanos=wait_50ms)


def _intercardinal_taken_ahead_(
    chunks: tuple[bytes, ...], typeahead: bytes, arrow_wait_nanos: int
) -> tuple[list[tuple[str, bytes]], list[str]]:
    """Take Strikes from fake Typeahead and then fake reads, and say the same of them"""

    join_fake = FakeJoinBoss(chunks, typeahead=typeahead, arrow_wait_nanos=arrow_wait_nanos)
    boss = typing.cast(litpyglass.TerminalBoss, join_fake)
    ts = litpyglass.TerminalShadow(boss)
    ist = litpyglass.InputStrikeTaker(ts, arrow_wait_nanos=arrow_wait_nanos)

    pairs: list[tuple[str, bytes]] = list()
    for strike in ist.take_input_strikes_and_yield_each(stalwarts=()):
        if strike.taken:
            pairs.append((strike.caps, strike.to_strike_bytes()))
            join_fake.events.append("yield")
        elif not strike.to_strike_bytes():
            join_fake.events.append("idle")  # the empty Open Frame, yielded before a read
        else:
            join_fake.events.append("grow")  # the Open Frame that holds Bytes, yielded after a read

    return (pairs, join_fake.events)


_TYPEAHEAD_ARROWS_CHILD_ = r"""
import os, sys
sys.path.insert(0, sys.argv[1])
import litpyglass

sync_fileno = int(sys.argv[2])
boss = litpyglass.TerminalBoss(typeahead=b"\033[A\033[C\r", farewell_bytes=b"")
ist = litpyglass.InputStrikeTaker(litpyglass.TerminalShadow(boss), arrow_wait_nanos=50000000)
print("READY1", flush=True)
os.read(sync_fileno, 1)
caps_list = list()
with boss:
    for strike in ist.take_input_strikes_and_yield_each(stalwarts=()):
        if strike.taken:
            caps_list.append(strike.caps)
            if len(caps_list) >= 2:
                break
print("RESULT", repr(tuple(caps_list)), flush=True)
"""


def _try_intercardinal_strikes_() -> None:
    """Try that two Cardinal Arrows at once join into one, as specs.md § 7 says"""

    east, north, west, south = b"\033[C", b"\033[A", b"\033[D", b"\033[B"
    arrows = {"→": east, "↑": north, "←": west, "↓": south}
    diagonal_by_straights = {
        "↑←": "↖",
        "↑→": "↗",
        "↓→": "↘",
        "↓←": "↙",
        "←↑": "↖",
        "→↑": "↗",
        "→↓": "↘",
        "←↓": "↙",
    }

    # Join each pair on different axes, struck in one read or in two reads

    for straights, diagonal in diagonal_by_straights.items():
        first, second = arrows[straights[0]], arrows[straights[1]]
        want = [(diagonal, first + second)]  # the two Frames catenated in order

        pairs, events = _intercardinal_taken_((first + second,))
        assert pairs == want, (pairs, want, straights)

        pairs, events = _intercardinal_taken_((first, second))
        assert pairs == want, (pairs, want, straights, events)
        assert events == ["idle", "read", "select", "idle", "read", "yield", "idle", "read"], (
            events,
            straights,
        )

    # Never join two Arrows on one axis, and yield both in order

    for straights in ("↑↑", "↑↓", "↓↑", "←→", "→←", "→→"):
        first, second = arrows[straights[0]], arrows[straights[1]]
        pairs, events = _intercardinal_taken_((first + second,))
        want = [(straights[0], first), (straights[1], second)]
        assert pairs == want, (pairs, want, straights)

    # Yield a lone Arrow once the peek says no Byte is available, before the last read

    pairs, events = _intercardinal_taken_((north,))
    assert pairs == [("↑", north)], (pairs, events)
    assert events == ["idle", "read", "select", "yield", "idle", "read"], (events,)

    # Yield an Arrow held at End of Input

    pairs, events = _intercardinal_taken_((north, b""))
    assert pairs == [("↑", north)], (pairs, events)
    assert events == ["idle", "read", "select", "idle", "read", "yield"], (events,)

    # Never join an Arrow with a Strike that is no Cardinal Arrow, and yield the Arrow first

    pairs, events = _intercardinal_taken_((north + b"x",))
    assert list(data for _, data in pairs) == [north, b"x"], (pairs, events)

    pairs, events = _intercardinal_taken_((b"x" + north,))
    assert list(data for _, data in pairs) == [b"x", north], (pairs, events)

    pairs, events = _intercardinal_taken_((north + b"J",))  # ⇧J is shifted, and no Arrow
    assert pairs == [("↑", north), ("⇧J", b"J")], (pairs, events)

    for lone_data in (b"\r", b"\x80"):  # yields at once, with no peek, since none is held
        pairs, events = _intercardinal_taken_((lone_data,))
        assert list(data for _, data in pairs) == [lone_data], (pairs, events)
        assert events == ["idle", "read", "yield", "idle", "read"], (events, lone_data)

    pairs, events = _intercardinal_taken_((b"x\r",))  # x, then ⏎, each yielded as it is taken
    assert list(data for _, data in pairs) == [b"x", b"\r"], (pairs, events)
    assert events == ["idle", "read", "yield", "yield", "idle", "read"], (events,)

    pairs, events = _intercardinal_taken_((north, b"\x80"))  # a Strike with no Key Caps at all
    assert pairs == [("↑", north), ("", b"\x80")], (pairs, events)
    want_events = ["idle", "read", "select", "idle", "read", "yield", "yield", "idle", "read"]
    assert events == want_events, (events,)

    # Join each Shifted Arrow too, keeping every shift of both Arrows, each once, in the order
    # ⎋ ⌃ ⌥ ⇧ ⌘ Fn, and catenate the two Frames in order

    shift_left, shift_right = b"\033[1;2D", b"\033[1;2C"
    alt_up, escape_shift_left = b"\033\033[A", b"\033\033[D"
    fn_up, fn_down, fn_right, fn_left = b"\033[5~", b"\033[6~", b"\033[F", b"\033[H"

    cases = (
        (north + shift_right, "⇧↗"),  # ↑ ⇧→
        (shift_right + north, "⇧↗"),
        (shift_left + north, "⇧↖"),
        (north + shift_left, "⇧↖"),
        (alt_up + shift_right, "⌥⇧↗"),  # ⌥↑ ⇧→
        (shift_right + alt_up, "⌥⇧↗"),
        (b"\033b" + north, "⌥↖"),  # ⌥← ↑
        (escape_shift_left + south, "⎋⇧↙"),  # ⎋⇧← ↓
        (south + escape_shift_left, "⎋⇧↙"),
        (fn_up + fn_right, "⇧Fn↗"),  # ⇧Fn↑ ⇧Fn→
        (fn_right + fn_up, "⇧Fn↗"),
        (fn_up + east, "⇧Fn↗"),  # ⇧Fn↑ →
        (east + fn_up, "⇧Fn↗"),
        (south + fn_left, "⇧Fn↙"),
        (fn_down + shift_right, "⇧Fn↘"),  # ⇧ on both is written once
        (alt_up + fn_right, "⌥⇧Fn↗"),  # ⌥↑ ⇧Fn→
    )
    for data, want_caps in cases:
        pairs, events = _intercardinal_taken_((data,))
        assert pairs == [(want_caps, data)], (pairs, want_caps, data)  # the two Frames in order

    pairs, events = _intercardinal_taken_((shift_left, north))  # two reads, as for bare Arrows
    assert pairs == [("⇧↖", shift_left + north)], (pairs, events)
    assert events == ["idle", "read", "select", "idle", "read", "yield", "idle", "read"], (events,)

    pairs, events = _intercardinal_taken_((shift_right + north + b"x",))  # then the Strike after
    assert list(data for _, data in pairs) == [shift_right + north, b"x"], (pairs, events)

    pairs, events = _intercardinal_taken_((shift_right,))  # a lone ⇧→ is yielded after the peek
    assert pairs == [("⇧→", shift_right)], (pairs, events)
    assert events == ["idle", "read", "select", "yield", "idle", "read"], (events,)


def _try_intercardinal_joins_() -> None:
    """Try that a join catenates the two Frames in order, as specs.md § 7 says"""

    east, north = b"\033[C", b"\033[A"
    shift_left, shift_right = b"\033[1;2D", b"\033[1;2C"
    fn_up, fn_down, fn_right, fn_left = b"\033[5~", b"\033[6~", b"\033[F", b"\033[H"

    # Join each Shifted pair spoken by Key Caps, in either order,

    def shifted_strike(caps: str, data: bytes) -> litpyglass.InputStrike:
        """Make a taken Strike of these Key Caps, which the Frame need not match"""

        frame = litpyglass.TerminalByteFrame(data)
        strike = litpyglass.InputStrike(taken=True, caps=caps, printables="", frames=(frame,))
        return strike

    def taken_strike(caps: str, data: bytes) -> litpyglass.InputStrike:
        """Make a taken Strike of these Key Caps and these Bytes"""

        strike = shifted_strike(caps, data)
        return strike

    join_cases = (
        ("⇧←", "↑", "⇧↖"),
        ("Fn↑", "→", "Fn↗"),
        ("⌥←", "↑", "⌥↖"),
        ("⌃←", "↑", "⌃↖"),
        ("⌘→", "↓", "⌘↘"),
        ("⎋→", "↓", "⎋↘"),
        ("⇧↑", "⌥←", "⌥⇧↖"),  # ⇧ then ⌥ arrive, ⌥ then ⇧ in order
        ("⌘⌃↑", "⌥⇧→", "⌃⌥⇧⌘↗"),
        ("⎋⌃↑", "⎋→", "⎋⌃↗"),  # a shift on both Arrows is written once
        ("⇧↑", "⇧→", "⇧↗"),
    )
    for first_caps, second_caps, want_caps in join_cases:
        for caps_pair in ((first_caps, second_caps), (second_caps, first_caps)):
            first_strike = shifted_strike(caps_pair[0], north)
            second_strike = shifted_strike(caps_pair[1], east)
            joined = litpyglass.InputStrikeTaker.arrows_join_else(first_strike, second_strike)
            assert joined is not None, (caps_pair,)
            assert joined.caps == want_caps, (joined.caps, want_caps, caps_pair)
            assert joined.to_strike_bytes() == north + east, (joined.frames, caps_pair)
            assert joined.taken, (joined,)

    # Catenate in order of arrival, so one Intercardinal Arrow has two Frames

    north_east = litpyglass.InputStrikeTaker.arrows_join_else(
        taken_strike("↑", north), taken_strike("→", east)
    )
    east_north = litpyglass.InputStrikeTaker.arrows_join_else(
        taken_strike("→", east), taken_strike("↑", north)
    )
    assert north_east is not None and east_north is not None, (north_east, east_north)
    assert (north_east.caps, north_east.to_strike_bytes()) == ("↗", b"\033[A\033[C")
    assert (east_north.caps, east_north.to_strike_bytes()) == ("↗", b"\033[C\033[A")

    # Hold two Frames in a joined Strike, each one Cardinal Arrow's, and one Frame in an ordinary Strike

    first_strike = taken_strike("↑", north)
    second_strike = taken_strike("→", east)
    joined = litpyglass.InputStrikeTaker.arrows_join_else(first_strike, second_strike)
    assert joined is not None, (joined,)
    assert len(first_strike.frames) == 1 and len(second_strike.frames) == 1, (first_strike,)
    assert len(joined.frames) == 2, (joined,)
    joined_first, joined_second = joined.frames
    assert joined_first.closed and joined_second.closed, (joined,)
    assert joined_first.to_frame_bytes() == north, (joined_first,)
    assert joined_second.to_frame_bytes() == east, (joined_second,)
    assert joined.to_strike_bytes() == north + east, (joined,)

    # Never hold a Frame with Bytes other than one Cardinal Arrow's, in a joined Strike

    for first_caps, second_caps, first_data, second_data in (
        ("↑", "→", north, east),
        ("→", "↑", east, north),
        ("⇧←", "↑", shift_left, north),
        ("↑", "⇧→", north, shift_right),
    ):
        pair_strike = litpyglass.InputStrikeTaker.arrows_join_else(
            taken_strike(first_caps, first_data), taken_strike(second_caps, second_data)
        )
        assert pair_strike is not None, (first_caps, second_caps)
        for pair_frame, pair_data in zip(pair_strike.frames, (first_data, second_data)):
            assert pair_frame.to_frame_bytes() == pair_data, (pair_frame, pair_data)

    # Refuse an Arrow whose Frame has no Bytes or is not closed, since its Key Caps then lie

    east_strike = taken_strike("→", east)
    for lying_data in (b"", b"\033[", b"x"):
        lying_strike = shifted_strike("↑", lying_data)
        for pair in ((lying_strike, east_strike), (east_strike, lying_strike)):
            try:
                litpyglass.InputStrikeTaker.arrows_join_else(*pair)
                refusal = None
            except AssertionError as exc:
                refusal = exc.args
            assert refusal is not None, (pair, lying_data)

    # Never join two Shifted Arrows on one axis, nor an Arrow with a Strike that is no Cardinal Arrow

    for first_caps, second_caps in (("⇧←", "⇧→"), ("⌥↑", "⇧↓"), ("⇧←", "←"), ("↑", "↑")):
        first_strike = shifted_strike(first_caps, north)
        second_strike = shifted_strike(second_caps, east)
        assert litpyglass.InputStrikeTaker.arrows_join_else(first_strike, second_strike) is None, (
            first_caps,
        )

    for first_caps, second_caps in (("⇧↑", "⇧A"), ("⇧A", "→"), ("↑", ""), ("↑", "⎋["), ("↑", "↗")):
        first_strike = shifted_strike(first_caps, north)
        second_strike = shifted_strike(second_caps, east)
        assert litpyglass.InputStrikeTaker.arrows_join_else(first_strike, second_strike) is None, (
            first_caps,
        )

    # Never join a Strike not taken, since it is no Arrow yet

    taken_north = shifted_strike("↑", north)
    taken_east = shifted_strike("→", east)
    open_north = litpyglass.InputStrike(
        taken=False, caps="↑", printables="", frames=taken_north.frames
    )
    open_east = litpyglass.InputStrike(
        taken=False, caps="→", printables="", frames=taken_east.frames
    )

    early_join = litpyglass.InputStrikeTaker.arrows_join_else(open_north, taken_east)
    late_join = litpyglass.InputStrikeTaker.arrows_join_else(taken_north, open_east)
    assert early_join is None, (early_join,)
    assert late_join is None, (late_join,)

    pairs, events = _intercardinal_taken_((shift_left + shift_right,))  # ⇧← ⇧→ on one axis
    assert list(data for _, data in pairs) == [shift_left, shift_right], (pairs, events)

    for first_data, second_data in ((fn_up, fn_down), (fn_left, fn_right), (fn_up, fn_up)):
        pairs, events = _intercardinal_taken_((first_data + second_data,))  # one axis, both ⇧Fn
        assert list(data for _, data in pairs) == [first_data, second_data], (pairs, events)


def _try_intercardinal_ahead_() -> None:
    """Try that an Arrow joins across reads and Typeahead, as specs.md § 7 says"""

    east, north = b"\033[C", b"\033[A"
    shift_left = b"\033[1;2D"

    # Yield an Arrow before the Strike after it, when the Arrow joins and when it does not

    pairs, events = _intercardinal_taken_((north + east + b"x",))
    assert list(data for _, data in pairs) == [north + east, b"x"], (pairs, events)

    # Take three Arrows ↑ → ↑ as ↗ and then ↑

    pairs, events = _intercardinal_taken_((north + east + north,))
    assert pairs == [("↗", north + east), ("↑", north)], (pairs, events)

    # Give up at once when the first read ends mid-Frame, and yield both Arrows in order

    pairs, events = _intercardinal_taken_((north + b"\033[", b"C"))
    assert pairs == [("↑", north), ("→", east)], (pairs, events)
    want_events = ["idle", "read", "yield", "grow", "read", "select", "yield", "idle", "read"]
    assert events == want_events, (events,)

    # Give up when the second read brings only part of an Arrow, and yield both in order

    pairs, events = _intercardinal_taken_((north, b"\033[", b"C"))
    assert pairs == [("↑", north), ("→", east)], (pairs, events)
    want_events = [
        "idle",
        "read",
        "select",
        "idle",
        "read",
        "yield",
        "grow",
        "read",
        "select",
        "yield",
        "idle",
        "read",
    ]
    assert events == want_events, (events,)

    # Join Arrows typed ahead, as if all the Typeahead were available at once

    result = _pty_run_child_(_TYPEAHEAD_ARROWS_CHILD_, terminal_bytes=b"")
    assert result == ("↗", "⏎"), (result,)  # the trailing ⏎ shows the Typeahead ran dry

    wait_50ms = litpyglass._50_MEGA_NANOS_
    typeahead_cases = (
        (north + east, [("↗", north + east)]),
        (b"x" + north + east, [("X", b"x"), ("↗", north + east)]),
        (north + east + north, [("↗", north + east), ("↑", north)]),
        (north + north + east, [("↑", north), ("↗", north + east)]),
        (shift_left + north, [("⇧↖", shift_left + north)]),
        (north + b"x", [("↑", north), ("X", b"x")]),
        (north, [("↑", north)]),  # the peek says no once the Typeahead runs dry
        (north + b"\033[", [("↑", north), ("⎋[", b"\033[")]),  # runs dry mid-Frame, so gives up
    )
    for typeahead, want in typeahead_cases:
        pairs, events = _intercardinal_taken_ahead_(
            (), typeahead=typeahead, arrow_wait_nanos=wait_50ms
        )
        assert pairs == want, (pairs, want, typeahead, events)

    # Yield every Open Frame of the Typeahead, even while holding an Arrow, and ask no select

    pairs, events = _intercardinal_taken_ahead_(
        (), typeahead=north + east, arrow_wait_nanos=wait_50ms
    )
    want_events = ["idle", "read", "grow", "read", "grow", "read"]  # ⎋ [ ⇧A
    want_events += ["idle", "read", "grow", "read", "grow", "read"]  # ⎋ [ ⇧C
    want_events += ["yield", "idle", "read"]
    assert events == want_events, (events,)

    # Peek once the Typeahead has run dry

    pairs, events = _intercardinal_taken_ahead_((), typeahead=north, arrow_wait_nanos=wait_50ms)
    want_events = ["idle", "read", "grow", "read", "grow", "read", "select", "yield", "idle", "read"]
    assert events == want_events, (events,)

    # Join an Arrow typed ahead to an Arrow read next, and give up once the Typeahead has run dry

    pairs, events = _intercardinal_taken_ahead_((east,), typeahead=north, arrow_wait_nanos=wait_50ms)
    assert pairs == [("↗", north + east)], (pairs, events)

    pairs, events = _intercardinal_taken_ahead_(
        (b"\033[", b"C"), typeahead=north, arrow_wait_nanos=wait_50ms
    )
    assert pairs == [("↑", north), ("→", east)], (pairs, events)


def _try_intercardinal_splits_() -> None:
    """Try that Key Caps split into shifts and one Arrow, as specs.md § 7 says"""

    split_cases = (
        ("←", ((), "←")),
        ("⇧←", (("⇧",), "←")),
        ("⌥⇧↗", (("⌥", "⇧"), "↗")),
        ("⎋⌃⌥⇧⌘Fn↓", (("⎋", "⌃", "⌥", "⇧", "⌘", "Fn"), "↓")),
        ("Fn↑", (("Fn",), "↑")),
        ("⇧Fn↑", (("⇧", "Fn"), "↑")),
        ("", None),
        ("⇧", None),
        ("⇧A", None),
        ("A", None),
        ("⎋[", None),
        ("←←", None),
        ("⇧←x", None),
        ("↑←", None),
        ("⌃⇧F5", None),
    )
    for caps, want_split in split_cases:
        split = litpyglass.InputStrikeTaker.caps_split_arrow_else(caps)
        assert split == want_split, (split, want_split, caps)


_ARROW_WAIT_CHILD_ = r"""
import os, sys, time
sys.path.insert(0, sys.argv[1])
import litpyglass

sync_fileno = int(sys.argv[2])
boss = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"")
ts = litpyglass.TerminalShadow(boss)
ist = litpyglass.InputStrikeTaker(ts, arrow_wait_nanos=<WAIT>)
print("READY1", flush=True)
os.read(sync_fileno, 1)  # a lone ↑ is typed
waited_ms = -1
with boss:
    start = None
    for strike in ist.take_input_strikes_and_yield_each(stalwarts=()):
        if start is None:
            start = time.perf_counter_ns()  # the first Open Frame comes before the first read
        if strike.taken:
            waited_ms = (time.perf_counter_ns() - start) // 10**6
            break
print("RESULT", repr((waited_ms,)), flush=True)
"""


def _try_arrow_wait_() -> None:
    """Try that the wait for the second Arrow is the Caller's, as specs.md § 7 says"""

    east, north = b"\033[C", b"\033[A"
    wait_50ms = 50 * 10**6

    # Ask the peek to wait the Nanos given, and join two Arrows read apart

    pairs, events = _intercardinal_taken_ahead_(
        (north, east), typeahead=b"", arrow_wait_nanos=wait_50ms
    )
    assert pairs == [("↗", north + east)], (pairs, events)  # the Fake asserts timeout == 0.05
    assert events == ["idle", "read", "select", "idle", "read", "yield", "idle", "read"], (events,)

    # Yield a lone Arrow after a peek that waits

    pairs, events = _intercardinal_taken_ahead_((north,), typeahead=b"", arrow_wait_nanos=wait_50ms)
    assert pairs == [("↑", north)], (pairs, events)
    assert events == ["idle", "read", "select", "yield", "idle", "read"], (events,)

    # Hold nothing and join nothing at a wait of 0, in one read, in two reads, and in Typeahead

    want_unjoined = [("↑", north), ("→", east)]
    for chunks, typeahead in (((north + east,), b""), ((north, east), b""), ((), north + east)):
        pairs, events = _intercardinal_taken_ahead_(chunks, typeahead=typeahead, arrow_wait_nanos=0)
        assert pairs == want_unjoined, (pairs, events, chunks, typeahead)
        assert "select" not in events, (events, chunks, typeahead)

    # Pin the event streams at a wait of 0, the stream before any holding existed

    pairs, events = _intercardinal_taken_ahead_((north + east,), typeahead=b"", arrow_wait_nanos=0)
    assert events == ["idle", "read", "yield", "yield", "idle", "read"], (events,)

    pairs, events = _intercardinal_taken_ahead_((north, east), typeahead=b"", arrow_wait_nanos=0)
    want_events = ["idle", "read", "yield", "idle", "read", "yield", "idle", "read"]
    assert events == want_events, (events,)

    pairs, events = _intercardinal_taken_ahead_((), typeahead=north + east, arrow_wait_nanos=0)
    want_events = ["idle", "read", "grow", "read", "grow", "read", "yield"]  # ⎋ [ ⇧A
    want_events += ["idle", "read", "grow", "read", "grow", "read", "yield"]  # ⎋ [ ⇧C
    want_events += ["idle", "read"]
    assert events == want_events, (events,)

    pairs, events = _intercardinal_taken_ahead_((north,), typeahead=b"", arrow_wait_nanos=0)
    assert pairs == [("↑", north)], (pairs, events)
    assert events == ["idle", "read", "yield", "idle", "read"], (events,)

    # Ask no select of Typeahead, even with a wait of 50ms

    pairs, events = _intercardinal_taken_ahead_(
        (), typeahead=north + east, arrow_wait_nanos=wait_50ms
    )
    assert pairs == [("↗", north + east)], (pairs, events)
    assert "select" not in events, (events,)

    # Refuse a negative wait, saying the value

    boss = typing.cast(litpyglass.TerminalBoss, FakeJoinBoss((), typeahead=b"", arrow_wait_nanos=0))
    ts = litpyglass.TerminalShadow(boss)
    try:
        litpyglass.InputStrikeTaker(ts, arrow_wait_nanos=-1)
        refusal = None
    except AssertionError as exc:
        refusal = exc.args
    assert refusal == ((-1,),), (refusal,)

    # Spell a wait of 50ms in --egg=strikes and in --egg=skater

    with open(litpyglass.__file__, "rb") as f:
        source_decode = f.read().decode()

    waits_by_egg: dict[str, list[str]] = dict()
    for node in ast.walk(ast.parse(source_decode)):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("show_"):
            for inner in ast.walk(node):
                if isinstance(inner, ast.Call) and ast.unparse(inner.func) == "InputStrikeTaker":
                    waits = list(ast.unparse(_.value) for _ in inner.keywords)

                    assert node.name not in waits_by_egg.keys(), (node.name,)
                    waits_by_egg[node.name] = waits

    want_waits_by_egg = dict(show_strikes=["_50_MEGA_NANOS_"], show_skater=["_50_MEGA_NANOS_"])
    assert waits_by_egg == want_waits_by_egg, (waits_by_egg, want_waits_by_egg)
    assert litpyglass._50_MEGA_NANOS_ == wait_50ms, (litpyglass._50_MEGA_NANOS_, wait_50ms)

    # Wait in real time on a Pty, for about the Nanos given and for none when 0

    wait_0_replace = _ARROW_WAIT_CHILD_.replace("<WAIT>", "0")
    wait_50_replace = _ARROW_WAIT_CHILD_.replace("<WAIT>", str(wait_50ms))
    result_0 = typing.cast(tuple[int], _pty_run_child_(wait_0_replace, terminal_bytes=north))
    result_50 = typing.cast(tuple[int], _pty_run_child_(wait_50_replace, terminal_bytes=north))

    (waited_0ms,), (waited_50ms,) = result_0, result_50
    assert waited_0ms < 40, (result_0, result_50)
    assert 40 <= waited_50ms < 1000, (result_0, result_50)


def _try_skater_entry_() -> None:
    """Try how --egg=skater waits for the Replies to its Asks, as specs.md § 8 says"""

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        mute = executor.submit(_try_egg_entry_, b"", b"")  # no Replies
        half = executor.submit(_try_egg_entry_, b"", b"\033[1;1R")  # only the Cursor Reply
        other = executor.submit(_try_egg_entry_, b"", b"\033[8;24;80t")  # only the Size Reply
        ahead = executor.submit(_try_egg_entry_, b"\033[C", b"\033[1;1R\033[8;24;80t")  # → typed
        swapped = executor.submit(_try_egg_entry_, b"", b"\033[8;24;80t\033[1;1R")  # Size first

    complaint = "Input ended before Y X H W replies to ⎋[6N and ⎋[18T"

    for future in (mute, half, other):
        screen_decode, isig, returncode = future.result()
        replace_decode = screen_decode.replace(_SKATER_FAREWELL_, "")  # which ends in a hail
        assert _SKATER_HAIL_ not in replace_decode, (screen_decode,)  # no hail while it hangs
        assert isig, (isig, screen_decode)  # ⌃C ⌃Z ⌃\ still signal while the hang lasts
        assert returncode == 1, (returncode, screen_decode)  # ⌃D ends the hang
        assert complaint in screen_decode, (complaint, screen_decode)

    screen_decode, isig, returncode = ahead.result()
    assert _SKATER_HAIL_ in screen_decode, (screen_decode,)
    assert screen_decode.index("\033[6n") < screen_decode.index(_SKATER_HAIL_), (screen_decode,)
    assert not isig, (isig, screen_decode)
    assert returncode is None, (returncode, screen_decode)

    moved = _skater_move_("\033[C\033[C")  # the → typed before the Replies came, kept
    assert screen_decode.index(_SKATER_HAIL_) < screen_decode.index(moved), (moved, screen_decode)

    screen_decode, isig, returncode = swapped.result()
    assert screen_decode.index("\033[6n") < screen_decode.index(_SKATER_HAIL_), (screen_decode,)
    assert not isig, (isig, screen_decode)  # the Replies take either order
    assert returncode is None, (returncode, screen_decode)

    argv = [sys.executable, "-I", litpyglass.__file__, "--egg=skater"]
    with tempfile.TemporaryDirectory() as cwd:  # takes the files the egg writes at exit
        run = subprocess.run(
            argv, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=10, cwd=cwd
        )
        assert run.returncode == 1, (run.returncode, run.stdout, run.stderr)  # no Screen, no skating
        assert "Input ended before Y X H W replies to" in run.stdout, (run.stdout,)
        assert "\033[6n" not in run.stdout, (run.stdout,)  # asks no Terminal, off a Terminal

        replies = b"\033[1;1R\033[8;24;80t"  # Input volunteers a Cursor and a Screen of 24 x 80
        run_bytes = subprocess.run(
            argv, input=replies + b"\r\r\r", capture_output=True, timeout=10, cwd=cwd
        )
        assert run_bytes.returncode == 0, (run_bytes.returncode, run_bytes.stdout, run_bytes.stderr)
        assert b"X\b" in run_bytes.stdout, (run_bytes.stdout,)  # skates on the Input's Replies
        assert b"\033[6n" not in run_bytes.stdout, (run_bytes.stdout,)  # and still asks no Terminal


def _try_egg_entry_(typed_data: bytes, replies: bytes) -> tuple[str, bool, int | None]:
    """Run --egg=skater on a Pty, reply to its Asks as told, and say how it waits"""

    master_fileno, slave_fileno = pty.openpty()
    argv = [sys.executable, "-I", litpyglass.__file__, "--egg=skater"]
    with tempfile.TemporaryDirectory() as cwd:  # takes the files the egg writes at exit
        process = subprocess.Popen(
            argv, stdin=slave_fileno, stdout=slave_fileno, stderr=slave_fileno, cwd=cwd
        )
        os.close(slave_fileno)

        terminal_output = bytearray()
        _pty_read_till_marker_(master_fileno, terminal_output, b"\033[6n\033[18t")
        os.write(master_fileno, typed_data + replies)
        _pty_read_for_seconds_(master_fileno, terminal_output, 0.5)

        isig = bool(termios.tcgetattr(master_fileno)[3] & termios.ISIG)  # ⌃C ⌃Z ⌃\ signal, or not

        returncode = None
        if isig:
            # still waiting, since the Terminal takes ⌃C ⌃Z ⌃\ as Signals till both Replies come
            os.write(master_fileno, b"\004")  # ⌃D
            _pty_read_for_seconds_(master_fileno, terminal_output, 0.5)
            returncode = process.poll()

        if process.poll() is None:
            process.kill()
        process.wait()
    os.close(master_fileno)

    screen_decode = bytes(terminal_output).decode(errors="replace")
    return (screen_decode, isig, returncode)


def _try_egg_quit_(egg: str, strike_steps: tuple[bytes, ...], replies: bytes) -> tuple[bool, str]:
    """Run --egg= on a Pty, strike each step 150ms apart, and say if it quit, as specs.md § 8 says"""

    with tempfile.TemporaryDirectory() as cwd:  # takes the files the egg writes at exit
        quit, terminal_bytes = _try_egg_pty_(
            egg, strike_steps=strike_steps, replies=replies, cwd=cwd
        )

    screen_decode = terminal_bytes.decode(errors="replace")
    return (quit, screen_decode)


def _try_egg_pty_(
    egg: str, strike_steps: tuple[bytes, ...], replies: bytes, cwd: str
) -> tuple[bool, bytes]:
    """Run --egg= on a Pty in a directory, strike each step 150ms apart, and say if it quit"""

    master_fileno, slave_fileno = pty.openpty()
    argv = [sys.executable, "-I", litpyglass.__file__, f"--egg={egg}"]
    process = subprocess.Popen(
        argv, stdin=slave_fileno, stdout=slave_fileno, stderr=slave_fileno, cwd=cwd
    )
    os.close(slave_fileno)

    terminal_output = bytearray()

    if egg == "skater":  # replies to the Asks, as a Terminal does
        _pty_read_till_marker_(master_fileno, terminal_output, b"\033[6n\033[18t")
        os.write(master_fileno, replies)

    prompt = _SKATER_HAIL_.encode() if (egg == "skater") else b"+ "
    _pty_read_till_marker_(
        master_fileno, terminal_output, prompt
    )  # waits for the Prompt, since Bytes read too soon count as too fast
    assert prompt in terminal_output, (prompt, bytes(terminal_output))

    if egg == "skater":  # the Replies count as Frames in the quit rule, so strike after the gap
        _pty_read_for_seconds_(master_fileno, terminal_output, 0.15)

    isig = termios.tcgetattr(master_fileno)[3] & termios.ISIG  # ⌃C ⌃Z ⌃\ signal, or else not
    assert not isig, (isig, egg, bytes(terminal_output))

    for data in strike_steps:
        try:
            os.write(master_fileno, data)
        except OSError:
            break  # the Child has already exited, so the Pty is closed
        _pty_read_for_seconds_(master_fileno, terminal_output, 0.15)  # over the 100ms gap

    _pty_read_for_seconds_(master_fileno, terminal_output, 0.5)  # long enough for a quit to show
    quit = process.poll() is not None
    if not quit:
        process.kill()
    process.wait()
    os.close(master_fileno)

    return (quit, bytes(terminal_output))


def _try_strikes_spill_() -> None:
    """Try what --egg=strikes leaves unread in the Input after it quits, as specs.md § 8 says"""

    cases = (
        (b"", b""),  # nothing struck after the 3rd ⏎, so nothing left
        (b"zz", b"zz"),  # 'zz' struck after the exit, so left for the next program
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(cases)) as executor:
        lefts = tuple(executor.map(lambda case: _try_strikes_left_(case[0]), cases))

    wants = tuple(case[1] for case in cases)
    assert lefts == wants, (lefts, wants, cases)


_STRIKES_LEFT_CHILD_ = r"""
import os, select, subprocess, sys, termios, tty
subprocess.run([sys.executable, "-I", sys.argv[1], "--egg=strikes"])
print("DEMO_EXITED", flush=True)
tty.setraw(0, when=termios.TCSANOW)
left = b""
while select.select([0], [], [], 0.3)[0]:
    left += os.read(0, 64)
print("LEFT", repr(left), flush=True)
"""


def _try_strikes_left_(extra: bytes) -> bytes:
    """Run --egg=strikes on a Pty, quit it, strike these Bytes after, and say what Stdin holds"""

    master_fileno, slave_fileno = pty.openpty()
    argv = [sys.executable, "-I", "-c", _STRIKES_LEFT_CHILD_, litpyglass.__file__]
    with tempfile.TemporaryDirectory() as cwd:  # takes the files the egg writes at exit
        process = subprocess.Popen(
            argv, stdin=slave_fileno, stdout=slave_fileno, stderr=slave_fileno, cwd=cwd
        )
        os.close(slave_fileno)

        terminal_output = bytearray()

        _pty_read_till_marker_(master_fileno, terminal_output, b"+ ")  # waits for the Prompt
        assert b"+ " in terminal_output, (bytes(terminal_output),)

        for _ in range(3):
            os.write(master_fileno, b"\r")
            _pty_read_for_seconds_(master_fileno, terminal_output, 0.15)  # over the 100ms gap

        if extra:
            os.write(master_fileno, extra)

        _pty_read_till_marker_(master_fileno, terminal_output, b"LEFT ")
        _pty_read_for_seconds_(master_fileno, terminal_output, 0.1)
        process.wait()
    os.close(master_fileno)

    screen_decode = bytes(terminal_output).decode(errors="replace")
    lines = list(_ for _ in screen_decode.split("\r\n") if _.startswith("LEFT "))
    assert len(lines) == 1, (lines, screen_decode)

    left = ast.literal_eval(lines[0].removeprefix("LEFT "))
    assert isinstance(left, bytes), (left,)

    return left


def _pty_read_till_marker_(master_fileno: int, terminal_output: bytearray, marker: bytes) -> None:
    """Take the Bytes arriving from the Pty till the Marker, else till 10s"""

    deadline = time.monotonic() + 10
    while (time.monotonic() < deadline) and (marker not in terminal_output):
        if not _pty_read_once_(master_fileno, terminal_output):
            return


def _pty_read_for_seconds_(master_fileno: int, terminal_output: bytearray, seconds: float) -> None:
    """Take the Bytes arriving from the Pty for this long"""

    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not _pty_read_once_(master_fileno, terminal_output):
            return


def _pty_read_once_(master_fileno: int, terminal_output: bytearray) -> bool:
    """Take the Bytes waiting, and say if the Pty is still open"""

    if select.select([master_fileno], [], [], 0.02)[0]:
        try:
            terminal_output.extend(os.read(master_fileno, 4096))
        except OSError:
            return False

    return True


# ⚠️ ↑↑↑ Above written by Claude·Ai, reviewed by almost no living people


# 3456789_123456789_123456789_123456789 123456789_123456789_123456789_123456789 123456789_123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/pylitglass/tests.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
