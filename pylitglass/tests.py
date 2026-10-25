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
import os
import pty
import select
import subprocess
import sys
import termios
import time
import unicodedata

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

    _try_terminal_byte_frame_()  # ~330ms, mostly ~327ms _try_ends_later_ over every Char
    _try_keyboard_decoder_()  # ~1ms
    _try_terminal_boss_()  # ~490ms, 2 child Pythons
    _try_terminal_boss_farewell_()  # ~100ms, 1 child Python
    _try_is_quitting_frames_()  # ~1600ms, 7 Ptys at once, the slowest 6 ⎋ at 150ms apart + 500ms
    _try_strikes_spill_()  # ~1000ms, 3 ⏎ at 150ms apart, then 300ms of reading what is left
    _try_terminal_boss_typeahead_()  # ~600ms, 150ms per Typeahead Byte
    _try_terminal_boss_chunks_()  # ~460ms, 150ms per Typeahead Byte
    _try_typeahead_()  # ~550ms, 3 Typeahead ⏎ at 150ms each
    _try_skater_quits_()  # ~1100ms, 8 Ptys at once, the slowest 3 ⏎ at 150ms apart + 500ms

    print("tests ok")


def _try_keyboard_decoder_() -> None:
    """Try KeyboardDecoder things"""

    dead_key_echo_by_combining = litpyglass.KeyboardDecoder.DeadKeyEchoByCombining

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

    for t in dead_key_echo_by_combining.keys():
        assert unicodedata.combining(t), (t,)


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

    for data in (b"\t", b"\033\t", b"\033[M !\xff"):
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
    """Try some Frames: ↑ ⎋↑ ⎋[M ⎋[↗ and the ⎋\\ String Terminator"""

    assert litpyglass.DL_Y == "\033[" "{}M", (litpyglass.DL_Y,)
    assert litpyglass._CLICK3_ == "\033[M", (litpyglass._CLICK3_,)
    assert litpyglass._NorthArrow_ == "\033[A", (litpyglass._NorthArrow_,)
    assert litpyglass.ST == "\033\134", (litpyglass.ST,)
    assert litpyglass._NortheastArrow_ == "\033[↗", (litpyglass._NortheastArrow_,)

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

    # Accept ↖↗↘↙ Intercardinal Arrows, not just ←↑→↓ Cardinal Arrows

    f = litpyglass.TerminalByteFrame("\033[↗".encode())  # not yet standard
    assert f.to_frame_bytes() == "\033[↗".encode(), (f,)
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


class FlushSpy:
    def __init__(self, stdio):
        self.stdio = stdio
        self.flush_count = 0

    def flush(self):
        self.flush_count += 1
        self.stdio.flush()

    def write(self, text):
        return self.stdio.write(text)


real_stdout = sys.stdout
spy_stdout = FlushSpy(sys.stdout)
spy_stderr = FlushSpy(sys.stderr)
sys.stdout, sys.stderr = spy_stdout, spy_stderr

boss = litpyglass.TerminalBoss(typeahead=b"", farewell=b"")
print("READY1", file=real_stdout, flush=True)
os.read(sync_fileno, 1)  # 'ab' has been typed, and the Terminal still takes Cooked Input
with boss:
    saved_attributes = boss.tcgetattr
    entered_twice = (boss.__enter__() is boss) and (boss.tcgetattr is saved_attributes)
    flushes_at_enter = (spy_stdout.flush_count, spy_stderr.flush_count)
    kept_at_enter = slurp()
    print("READY2", file=real_stdout, flush=True)
    os.read(sync_fileno, 1)  # 'xy' has been typed, and no one reads it
boss.__exit__()  # exits at most once
cleared_at_exit = boss.tcgetattr == []
flushes_at_exit = (spy_stdout.flush_count, spy_stderr.flush_count)
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
)
print("RESULT", repr(result), file=real_stdout, flush=True)
"""

_TERMINAL_BOSS_PIPE_CHILD_ = r"""
import sys
sys.path.insert(0, sys.argv[1])
import litpyglass

boss = litpyglass.TerminalBoss(typeahead=b"", farewell=b"")
with boss:
    inside = (boss.isatty, boss.tcgetattr)
    boss.tty_setraw_before_farewell()  # does nothing off a Terminal, farewell or not
print("RESULT", repr((inside, boss.tcgetattr)), flush=True)
"""


def _try_terminal_boss_() -> None:
    """Try TerminalBoss things, as the Spec at the bottom of this file says"""

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
    tty_expected = (b"ab", True, True, b"xy", True, (1, 1), (2, 2))  # kept, twice, cleared, left,
    # afresh, then the Stdout and Stderr flush counts after Enter and after Exit
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


before_enter = setraw_asserts(litpyglass.TerminalBoss(typeahead=b"", farewell=b"<FAREWELL>"))
mute = litpyglass.TerminalBoss(typeahead=b"", farewell=b"")
with mute:
    without_farewell = setraw_asserts(mute)

termios.tcsetattr = tcsetattr_after_marker

boss = litpyglass.TerminalBoss(typeahead=b"", farewell=b"<FAREWELL>")
with boss:
    cbreak = (lflag_has(termios.ISIG), lflag_has(termios.ICANON))
    boss.tty_setraw_before_farewell()
    raw = (lflag_has(termios.ISIG), lflag_has(termios.ICANON))
termios.tcsetattr = real_tcsetattr
print("RESULT", repr((cbreak, raw, before_enter, without_farewell)), flush=True)
"""


def _try_terminal_boss_farewell_() -> None:
    """Try the TerminalBoss farewell, as the Spec at the bottom of this file says"""

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
boss = litpyglass.TerminalBoss(typeahead=b"ab", farewell=b"")
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
    """Try TerminalBoss reading Typeahead, as _6_ at the bottom of this file says"""

    result = _pty_run_child_(_TERMINAL_BOSS_TYPEAHEAD_CHILD_, terminal_bytes=b"X")

    expected = (b"X", b"a", True, True, True, b"b")  # Terminal first, then Typeahead, and 2 selects
    assert result == expected, (result, expected)


_TERMINAL_BOSS_CHUNKS_CHILD_ = r"""
import os, sys
sys.path.insert(0, sys.argv[1])
import litpyglass

sync_fileno = int(sys.argv[2])
boss = litpyglass.TerminalBoss(typeahead=b"ab", farewell=b"")
print("READY1", flush=True)
os.read(sync_fileno, 1)  # 'XY' has been typed on the Terminal
with boss:
    chunks = tuple(boss.read_some_bytes_if() for _ in range(4))
print("RESULT", repr(chunks), flush=True)
"""


def _try_terminal_boss_chunks_() -> None:
    """Try TerminalBoss reading Typeahead in chunks, as _6_ at the bottom of this file says"""

    result = _pty_run_child_(_TERMINAL_BOSS_CHUNKS_CHILD_, terminal_bytes=b"XY")

    expected = (b"X", b"Y", b"a", b"b")  # each Byte alone, though 'XY' arrived all at once
    assert result == expected, (result, expected)


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
    """Try the --typeahead flag, as _6_ at the bottom of this file says"""

    master_fileno, slave_fileno = pty.openpty()
    argv = [sys.executable, "-I", litpyglass.__file__, "--egg=strikes", "--typeahead=\r\r\r"]
    process = subprocess.Popen(argv, stdin=slave_fileno, stdout=slave_fileno, stderr=slave_fileno)
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


def _try_is_quitting_frames_() -> None:
    """Try which strikes quit --egg=strikes, as _3_ at the bottom of this file says"""

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
            executor.map(lambda case: _try_egg_quit_("strikes", case[0], case[1]), cases)
        )

    for case, (quit, screen_decode) in zip(cases, results):
        data, count, want, shows = case
        assert quit == want, (quit, want, data, count)
        assert shows in screen_decode, (shows, data, count, screen_decode)


def _try_skater_quits_() -> None:
    """Try which strikes quit --egg=skater, as _5_ at the bottom of this file says"""

    cases = (
        (b"\r", 3, True, ""),  # ⏎ ⏎ ⏎
        (b"\r", 2, False, ""),
        (b"\r\r\r", 1, False, ""),  # ⏎ ⏎ ⏎ pasted
        (b"\033[C", 3, False, "+\b\b\033[C\033[C + \b\b"),  # → → →
        (b"\033[A", 3, False, "+\b\b\033[A + \b\b"),  # ↑ ↑ ↑
        (b"\033[D", 3, False, "+\b\b\033[D\033[D + \b\b"),  # ← ← ←
        (b"\033[B", 3, False, "+\b\b\033[B + \b\b"),  # ↓ ↓ ↓
        ("\033[↗".encode(), 3, True, ""),  # ↗ ↗ ↗, an Intercardinal Arrow, not yet a Stalwart
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(cases)) as executor:
        results = tuple(executor.map(lambda case: _try_egg_quit_("skater", case[0], case[1]), cases))

    for case, (quit, screen_decode) in zip(cases, results):
        data, count, want, shows = case
        assert quit == want, (quit, want, data, count, screen_decode)
        assert shows in screen_decode, (shows, data, count, screen_decode)

        launch = "\033[4 q + \b\b"  # sets Cursor Style 4, then writes the first Prompt
        assert launch in screen_decode, (launch, data, count, screen_decode)

        farewell = "\r\033[ q\033[32100B\033[A"  # parks the Cursor, and reverts the Cursor Style
        assert (farewell in screen_decode) == quit, (farewell, quit, data, count, screen_decode)


def _try_egg_quit_(egg: str, data: bytes, count: int) -> tuple[bool, str]:
    """Run --egg= on a Pty, strike these Bytes this often 150ms apart, and say if it quit"""

    master_fileno, slave_fileno = pty.openpty()
    argv = [sys.executable, "-I", litpyglass.__file__, f"--egg={egg}"]
    process = subprocess.Popen(argv, stdin=slave_fileno, stdout=slave_fileno, stderr=slave_fileno)
    os.close(slave_fileno)

    terminal_output = bytearray()

    _pty_read_till_marker_(
        master_fileno, terminal_output, b"+ "
    )  # waits for the Prompt, since Bytes read too soon count as too fast
    assert b"+ " in terminal_output, (bytes(terminal_output),)

    isig = termios.tcgetattr(master_fileno)[3] & termios.ISIG  # ⌃C ⌃Z ⌃\ signal, or else not
    assert not isig, (isig, egg, bytes(terminal_output))

    for _ in range(count):
        try:
            os.write(master_fileno, data)
        except OSError:
            break  # the Child has already exited, so the Pty is closed
        _pty_read_for_seconds_(master_fileno, terminal_output, 0.15)  # over the 100ms too-fast gap

    _pty_read_for_seconds_(master_fileno, terminal_output, 0.5)  # long enough for a quit to show
    quit = process.poll() is not None
    if not quit:
        process.kill()
    process.wait()
    os.close(master_fileno)

    screen_decode = bytes(terminal_output).decode(errors="replace")
    return (quit, screen_decode)


def _try_strikes_spill_() -> None:
    """Try what --egg=strikes leaves in Stdin after it quits, as _5_ says at the bottom"""

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
    process = subprocess.Popen(argv, stdin=slave_fileno, stdout=slave_fileno, stderr=slave_fileno)
    os.close(slave_fileno)

    terminal_output = bytearray()

    _pty_read_till_marker_(master_fileno, terminal_output, b"+ ")  # waits for the Prompt
    assert b"+ " in terminal_output, (bytes(terminal_output),)

    for _ in range(3):
        os.write(master_fileno, b"\r")
        _pty_read_for_seconds_(master_fileno, terminal_output, 0.15)  # over the 100ms too-fast gap

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


#
# Specs, presented bottom-up (as a reverse of our top-down Code)
#


# class ByteKeeper


# class TerminalBoss:

_1_ = r"""
Spec of how TerminalBoss chooses TCSADRAIN vs TCSAFLUSH in its __enter__ and __exit__

Choice: Keep TCSADRAIN at Enter and at Exit of TerminalBoss.

    Enter keeps the Keyboard Input typed before launch.

    Exit leaves the Keyboard Input the person typed during the run for the next Terminal App to read.

    TCSAFLUSH would destroy the Input without a backup and without a trace.

Measured 24/Oct/2026 on a macOS pty, 2 runs each, 'ab' typed before Enter and 'xy' inside:

    TCSADRAIN, our choice:    Enter keeps 'ab'        Exit leaves 'xy' for the next program
    TCSAFLUSH, not chosen:    Enter drops 'ab'        Exit drops 'xy'

We meet spec as tested by _try_terminal_boss_:

    1. Enter saves the Terminal attributes once, then calls tty.setraw with TCSADRAIN
       so queued Output leaves, but Input already typed stays to be read.
       Enter with a Farewell calls tty.setcbreak not tty.setraw, so ⌃C ⌃Z ⌃\ still signal.

    2. Enter on a Stdin that is not a Terminal saves a stand-in list, and touches no termios.

    3. Enter when already entered changes nothing, and returns the same TerminalBoss.

    4. Exit restores the saved attributes with TCSADRAIN, so Input not yet read stays
       for the next Terminal App to read.

    5. Exit when not entered changes nothing, and Exit clears the save, so next Enter saves afresh.

    6. Enter and Exit each flush Stdout and Stderr first, before tty.setraw/ termios.tcsetattr.

    7. The Farewell Bytes write at Exit, flushed, before Exit restores the saved attributes.

    8. The tty_setraw_before_farewell stops ⌃C ⌃Z ⌃\ from signalling, by calling tty.setraw.

    9. The tty_setraw_before_farewell on a Terminal fails an assert before Enter, and fails
       an assert without a Farewell, and does nothing at all on a Stdin that is not a Terminal.
"""


# class TerminalByteFrame

_2_ = r"""
Spec of TerminalByteFrame.take_data_if, as _try_terminal_byte_frame_ and its helpers test it

Bytes go in, and the Frame closes, stays open, or bounces back the Bytes it won't take:

    1. An empty Frame is open, and a closed Frame bounces every Byte offered after.
       A bounce always leaves the Frame as it was.

    2. Each Head of the Headbook stays open: ⎋ ⎋⎋ ⎋⎋⇧O ⎋⎋[ ⎋⇧O ⎋[ ⎋[⇧M and ⎋].
       ⎋⎋ bounces a 3rd ⎋.

    3. Each Start of any UTF-8 Encoding stays open, and starts with exactly C2 .. F4.

    4. A Control Byte, or a Char Unprintable by itself, or 1 to 4 Undecodable Bytes, closes alone.

    5. Esc ⎋ closes on a Printable or Control Tail, & Ss3 ⎋O closes on a Printable or Control Tail.

    6. Csi ⎋[ closes on a Multi-Byte Char, and bounces ⎋ and Tab and Undecodable Bytes.

    7. A Csi Frame closes on its Tail:  ⎋[⇧A  ⎋⎋[⇧A  ⎋[1⇧M  ⎋[3;5⇧H  and the ⎋[ q ending in b" q"
       and b'\033[201~' closes as _END_PASTE_.

    8. Mouse ⎋[⇧M stays open, since ⎋[⇧M{b}{x}{y} could be a Frame of 6 Bytes,
       and then takes 6 Bytes undecoded and bounces the rest.

    9. Osc ⎋] stays open until Bel or ⎋\ closes it, and bounces Tab, ⎋ before a Multi-Byte Char,
       and before itself again.

    10. Text stays open, and bounces 1 to 4 Unprintable Bytes after it.

    11. A Combining Mark already fetched keeps a Frame open past a Printable Char that would
        close it,  ⎋j́  ⎋⎋j́  ⎋⇧Oj́  ⎋[j́  ⎋[1;5j́, then closes on the Mark;
        Tab and ⎋Tab and raw ⎋[M close anyway, while Text and Osc stay open and take the Mark.

    12. The str(Frame) speaks each Byte as given, and ends in ' +' while the Frame is open.

    13. The ⎋[↗ closes as an Intercardinal Arrow, all while no merely public standard names these.
"""


# class TerminalFrameTaker

_3_ = r"""
Spec of TerminalFrameTaker.is_quitting_frames, as _try_is_quitting_frames_ tests it.

Measured 24/Oct/2026 on a macOS pty running --egg=strikes, with the strikes 150 ms apart:

    1. The triple of ⏎ ⏎ ⏎ quits.

    2. The pair of ⏎ ⏎ does not quit.

    3. The triple of ⎋[ ⎋[ ⎋[ quits, since the 2 Frames Taken and the 3rd still Open
       are the same Frame.

    4. The triple of ⎋ ⎋ ⎋ does not quit, since the 2nd ⎋ joins the 1st in the Frame ⎋⎋
       and the 3rd bounces. The screen shows ⎋⎋ '' b'\033\033' + the moment the 2nd ⎋ arrives.

    5. The triple of ⎋⎋ ⎋⎋ ⎋⎋ quits, and so do 6 ⎋ struck 150 ms apart, since those join
       in pairs as 3 Frames.

    6. The triple of x x x does not quit, since repeated Text never quits.

    7. The triple of ⏎ ⏎ ⏎ pasted, or struck all at once, shows 3 closed Frames, each ⏎ '' b'\r',
       and does not quit, since they are under 100 ms apart. So pasting blank lines is safe.
"""


# class TerminalFrameReader


# class KeyboardDecoder

_4_ = r"""
Spec of KeyboardDecoder.bytes_to_key_caps_if, as _try_keyboard_decoder_ tests it

The Bytes of one Strike go in, and the Key Caps struck to send them come out, else an Empty Str:

    1. Sending in nothing gives Empty Str out, and so do an Undecodable Byte, a lone Combining Mark,
       and 2 Combining Marks on 1 Char.

    2. A Control Byte gives its Key Cap: ⇥ for Tab, ⏎ for Return, ⌃A for b'\001', ⎋ for b'\033'.

    3. A closed Csi or Ss3 Frame gives its Key Cap: ↑, ⇧→, F1.

    4. A Frame still open gives the Keys struck so far: b'\033[' gives ⎋[, b'\033[1' gives ⎋ [ 1,
       since no Chord sends those Bytes, and a Frame closed by b'a' gives ⎋ [ A.

    5. Printable Chars give their Key Cap: ␢ J ⇧J, and a Paste of b'ABC' gives ⇧A ⇧B ⇧C.

    6. A Dead Key Echo gives the Option Chord: é gives ⌥EE, j + Acute gives ⌥EJ, ´ gives ⌥⇧E.

    7. Where several Key Chords send the same Bytes, one reading wins:
       F6 over ⌥F1 and ⎋F1, F12 over ⌥F7 and ⎋F7, ⇧F5 over ⌥F8 and ⎋F8, ⎋⌃P over ⎋⇧F1 .. ⎋⌃⇧F12.

    8. b'\033[23~' gives ⌥F6, since macOS Mission Control often steals F11.

    9. b'\033[22~' gives ⎋ [ 2 2 ⇧~, since no F Key sends 22 (F10 sends 21 and F11 sends 23).

    10. Each Dead Key Echo names a Unicode Combining Mark, so Apple accents the Char struck next.
"""


# class InputStrikeTaker


# class GlassWorker

_5_ = r"""
Spec of GlassWorker, the demos that --egg= picks.

Measured 24/Oct/2026 on a macOS pty running --egg=strikes, with the 3 ⏎ 150 ms apart,
we meet spec as tested by _try_strikes_spill_:

    1. When nothing is struck after the 3rd ⏎, Stdin holds nothing.

    2. Keys struck 150 ms after the 3rd ⏎ stay in Stdin for the next program to read.

On a macOS pty running --egg=skater, we meet spec as tested by _try_skater_quits_:

    3. The triple of ⏎ ⏎ ⏎ struck 150 ms apart quits, as it does --egg=strikes.

    4. The pair of ⏎ ⏎ does not quit.

    5. The triple of ⏎ ⏎ ⏎ pasted, or struck all at once, does not quit.

    6. Each Cardinal Arrow moves the Cursor and redraws the '+' behind it: → and ← move
       2 Columns, and ↑ and ↓ move 1 Row.

    7. The triple of → → → does not quit, and nor do the triples of ↑ ← ↓, since an Arrow
       moves the Cursor.

    8. The triple of ⎋[↗ quits, since the Intercardinal Arrows are declared and not yet used.

    9. Launch sets the Cursor Style to Skid, a solid underline similar to a _ skid mark,
       before it writes the first Prompt.

    10. Quit parks the Cursor at the leftmost Column of the next-to-last Row, and reverts the
        Cursor Style to the default. No writes of a choice of Cursor Style between Launch and Quit.

    11. Launch takes ⌃C ⌃Z ⌃\ as Input and not as Signals, by the time it writes the first Prompt.
"""


# def main

_6_ = r"""
Spec of the --typeahead flag of litpyglass.py, from the flag down into TerminalBoss.

Measured 24/Oct/2026 on a macOS pty running --egg=strikes, with no key struck.

We meet spec as tested by _try_typeahead_:

    1. The flag --typeahead of ⏎ ⏎ ⏎ quits it, since each ⏎ comes 150 ms after the last.

We meet spec as tested by _try_terminal_boss_typeahead_ and _try_terminal_boss_chunks_:

    2. Typeahead Bytes read as if the Terminal sent them, but only after 150 ms in which
       the Terminal sends nothing, so a Byte the Terminal already sent comes first.

    3. While Typeahead is waiting, asking if a Byte is coming always gets the answer yes.
       The answer waits up to 150 ms for the Terminal to speak first, or only as long as
       the caller will wait, when that is less.

    4. Reading Typeahead always takes each Typeahead Byte alone, never as if pasted
       as a burst.
"""


_ = _1_, _2_, _3_, _4_, _5_, _6_


# 3456789_123456789_123456789_123456789 123456789_123456789_123456789_123456789 123456789_123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/pylitglass/tests.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
