# Specs of litpyglass.py

Each section is one Spec, and `We meet spec as tested by` names the Tests in tests.py that prove it.

## § 1 TerminalBoss

```
Spec of how TerminalBoss chooses TCSADRAIN vs TCSAFLUSH in its __enter__ and __exit__

Choice: Keep TCSADRAIN at Enter and at Exit of TerminalBoss.

    Enter keeps the Keyboard Input typed before launch.

    Exit leaves the Keyboard Input the person typed during the run for the next Terminal App to read.

    TCSAFLUSH would destroy the Input without a backup and without a trace.

Measured 24/Oct/2026 on a macOS pty, 2 runs each, 'ab' typed before Enter and 'xy' inside:

    TCSADRAIN, our choice:    Enter keeps 'ab'        Exit leaves 'xy' for the next program
    TCSAFLUSH, not chosen:    Enter drops 'ab'        Exit drops 'xy'

We meet spec as tested by _try_terminal_boss_ and _try_terminal_boss_return_:

    1. Enter saves the Terminal attributes once, then calls tty.setraw with TCSADRAIN
       so queued Output leaves, but Input already typed stays to be read.
       Enter with a Farewell calls tty.setcbreak not tty.setraw, so ⌃C ⌃Z ⌃\ still signal.
       Queued Strikes of the Return Key arrive as ⌃J,
       until tty.setraw makes new Strikes arrive as ⌃M.

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
```

## § 2 TerminalByteFrame

```
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
```

## § 3 TerminalFrameDecoder

```
Spec of TerminalFrameDecoder.bytes_to_yx_or_hw_else, as _try_terminal_frame_decoder_ tests it.

We meet spec as tested by _try_terminal_frame_decoder_:

    1. The Frame ⎋[8;24;80T, the Result of the Query ⎋[18T, decodes as ("HW", 24, 80),
       Row Height then Column Width.

    2. The Frame ⎋[5;7⇧R, the Result of the Query ⎋[6N, decodes as ("YX", 5, 7),
       Row Number then Column Number.

    3. Any other Frame decodes as None, such as the Arrow ⎋[⇧A, or a Result with a ⎋ stuck on
       its front, or two Results as one Frame, or a Result with too few Ints, or an empty Int,
       or no Bytes.

    4. A Frame shaped like a Result but with a 0 Int is no other Frame, so it fails an assert,
       since Rows, Columns, Row Numbers, and Column Numbers all count from 1.

    5. A Result whose Ints start with 0s, such as ⎋[007;5⇧R, decodes as ("YX", 7, 5).
```

## § 4 TerminalFrameTaker

```
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
```

## § 5 TerminalFrameReader

```
Spec of TerminalFrameReader.take_frames_and_yield_each, as _try_frame_reader_quits_midbatch_
tests it.

We meet spec as tested by _try_frame_reader_quits_midbatch_:

    1. A Caller who quits after the second of three Taken Frames of one read leaves the third
       Taken Frame for the next pass.

    2. The next pass yields that third Taken Frame first, before the Open Frame and before
       any further read.
```

## § 6 KeyboardDecoder

```
Spec of KeyboardDecoder.bytes_to_key_caps_if, as _try_keyboard_decoder_ tests it

The Bytes of one Strike go in, and the Key Caps struck to send them come out, else an Empty Str:

    1. Sending in nothing gives Empty Str out, and so do an Undecodable Byte, a lone Combining Mark,
       and 2 Combining Marks on 1 Char.

    2. A Control Byte gives its Key Cap: ⇥ for Tab, ⏎ for Return, ⌃A for b'\001', ⎋ for b'\033'.

    3. A closed Csi or Ss3 Frame gives its Key Cap: ↑, ⇧→, F1.

    4. A Frame still open gives the Keys struck so far: b'\033[' gives ⎋[, b'\033[1' gives ⎋ [ 1,
       since no Chord sends those Bytes, and a Frame closed by b'a' gives ⎋ [ A.

    5. Printable Chars give their Key Cap: ␢ J ⇧J, and a Paste of b'ABC' gives ⇧A ⇧B ⇧C.

    6. A Dead Key Echo gives the Option Chord: è é ê ñ ë give ⌥`E ⌥EE ⌥IE ⌥NN ⌥UE, j + Acute gives
       ⌥EJ, ´ gives ⌥⇧E.

    7. Where several Key Chords send the same Bytes, one reading wins:
       F6 over ⌥F1 and ⎋F1, F12 over ⌥F7 and ⎋F7, ⇧F5 over ⌥F8 and ⎋F8, ⎋⌃P over ⎋⇧F1 .. ⎋⌃⇧F12.

    8. b'\033[23~' gives ⌥F6, since macOS Mission Control often steals F11.

    9. b'\033[22~' gives ⎋ [ 2 2 ⇧~, since no F Key sends 22 (F10 sends 21 and F11 sends 23).

    10. Each Dead Key Echo names a Unicode Combining Mark, so Apple accents the Char struck next.
        litpyglass.py asserts this itself as it loads.
```

## § 7 InputStrikeTaker

```
Spec of InputStrikeTaker.pull_yx_hw_from_ts_else and .take_input_strikes_and_yield_each_placed, as
_try_placed_input_strikes_ and _try_pull_ends_without_answers_ test it.

We meet spec as tested by _try_placed_input_strikes_ and _try_pull_ends_without_answers_:

    1. On a Terminal, the Results ⎋[5;7⇧R and ⎋[8;24;81T place each Strike at column_x 7,
       x_max 80, x_width 81, row_y 5, and y_height 24: Columns come from the Cursor X and the
       Screen W, Rows from the Cursor Y and the Screen H, and the odd Width W+1 acts as 80.

    2. The Strike typed before the Results come waits in a queue for them, and then takes that
       same Place, as does each Strike typed after.

    3. Each Result is taken as an answer and not yielded as a Strike. A later Result of the same
       kind, such as a second ⎋[9;9⇧R pasted before the Size Result, replaces the earlier.

    4. Off a Terminal, nothing asks, and both Results must arrive in the Input, in either order,
       before any Strike takes its Place.

    5. When Input ends, or ⌃D quits the wait, before both Results have come, it prints "Input
       ended before Y X H W replies to ⎋[6N and ⎋[18T" and exits 1, on a Terminal or off one.
```

## § 8 GlassWorker

```
Spec of GlassWorker, the demos that --egg= picks.

Measured 24/Oct/2026 on a macOS pty running --egg=strikes, with the 3 ⏎ 150 ms apart,
we meet spec as tested by _try_strikes_spill_:

    1. When nothing is struck after the 3rd ⏎, Stdin holds nothing.

    2. Keys struck 150 ms after the 3rd ⏎ stay in Stdin for the next program to read.

On a macOS pty running --egg=skater, we meet spec as tested by _try_skater_quits_:

    3. The triple of ⏎ ⏎ ⏎ struck 150 ms apart quits, as it does --egg=strikes.

    4. The pair of ⏎ ⏎ does not quit.

    5. The triple of ⏎ ⏎ ⏎ pasted, or struck all at once, does not quit.

    6. Each Cardinal Arrow moves the Cursor, leaves an inverse pair of Spaces behind it, and
       draws a plain pair of Spaces ahead of it: → and ← move 2 Columns, and ↑ and ↓ move 1 Row.

    7. The triple of → → → does not quit, and nor do the triples of ↑ ← ↓, since an Arrow
       moves the Cursor.

    8. The triple of ⎋[↗ quits, since the Intercardinal Arrows are declared and not yet used.

    9. Launch sets the Cursor Style to Skid, a solid underline similar to a _ skid mark,
       and hides the Cursor, once both Results have come and before it writes the first Prompt.

    10. Quit parks the Cursor at the leftmost Column of the next-to-last Row, shows the Cursor,
        and reverts the Cursor Style to the default. No writes of a choice of Cursor Style
        between Launch and Quit.

    11. Launch takes ⌃C ⌃Z ⌃\ as Input and not as Signals, once both Results have come.

    12. Each Byte of an Open Frame cycles the Prompt through the Digits 1234567890.
        Such as ⎋ shows 1, and ⎋[ shows 2, and ⎋[ after a Taken Frame of 1 Byte shows 3,
        and an Open Frame of 10 or 20 Bytes shows 0.

    13. A Taken Arrow Frame resets the count of Bytes to 0, so ⎋[ shows 2 again after it.

    14. Launch on a Terminal writes the first Prompt, then the Queries ⎋[6N and ⎋[18T, and
        waits however long it takes for both Results.

    15. While waiting, ⌃C ⌃Z ⌃\ still signal, and ⌃D ends Input with a brief complaint and exit 1.

    16. The keys typed before the Results come are kept, and take effect once both Results
        have come.

    17. Launch off a Terminal writes no Queries and takes the Results from the Input, else prints
        the same complaint as on a Terminal and exits 1.

    18. Each Taken Frame that is no Arrow draws X, then O, then X again, in the left Cell of the
        Cursor's pair of Spaces. Such as ⏎ ⏎ shows X then O, and x then → shows X before the move.

    19. On a Screen 20 or 21 Columns wide, → fills the Row to Column 20 and then bounces back
        off the East edge. It never writes Column 21, and never wraps to the next Row.
```

## § 9 main

```
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
```

## § 10 TerminalShadow

```
Spec of TerminalShadow.write_by_xy, as _try_shadow_cells_ tests it.

We meet spec as tested by _try_shadow_cells_:

    1. No Cell is kept before any write, and none after only the Terminal's answers.

    2. Each Printable Char written through the Shadow is kept at the (Column, Row) it lands on,
       with the Text Styles in force then, and a later write there replaces it.

    3. A Move or a Backspace keeps nothing, but steers where the next Char lands. Hiding or
       showing the Cursor, ⎋[?25L or ⎋[?25H, keeps nothing and steers nothing. Any other Control
       fails an assert, not silently.

    4. The Text Styles in force start over at ⎋[M and carry to the next write. ⎋[7M joins them
       once however often said. Any other SGR, such as ⎋[27M or ⎋[1M, fails an assert, not
       silently.

    5. An odd Width W+1 is real but acts as W, since a Square Pixel is 2 Columns wide and cannot
       fit in Column W+1: no Char can be written into Column W+1, though the Cursor may wait
       there. The wait to wrap is judged by the real Width W+1.

    6. Writes land only inside the rectangle of Height by x_max: a Char that would land outside it
       cannot be written, even if the Cursor then moves back inside, and a write that lands outside
       it anyway fails an assert.

    7. A Move or a Backspace that would leave the Screen cannot be written, at the North, West,
       and South edges. A Move East from the last Column waits in Column W+1, still on the Screen.

    8. A Return lands the Cursor on Column 1 of the same Row, even with the wrap pending after a
       write into the last Column.

    9. A write that cannot be written fails its assert before any Byte goes to the Terminal, and
       leaves the Shadow as it was.

    10. A Char into the last Column, with nothing after it, leaves the Cursor waiting to wrap
        past x_max, so is_writable_place_after_strs says no: an even Width has no Column W+1 for
        it, and an odd Width acts as W. A Backspace or a Return after it says yes.

    11. Before the Terminal answers, no write can be made, not even one of no Char: it fails its
        assert before any Byte goes out.
```
