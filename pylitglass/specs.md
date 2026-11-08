# Specs of litpyglass.py

Each section is one Spec. Its first line says what it covers, `We meet spec as tested by` names the Tests in tests.py that prove it, and a Measured line, when there is one, comes last and says which items it measures.

## § 1 TerminalBoss

```
Spec of TerminalBoss, and how it chooses TCSADRAIN vs TCSAFLUSH in its __enter__ and __exit__.

Choice: Keep TCSADRAIN at Enter and at Exit of TerminalBoss.

    Enter keeps the Keyboard Input typed before launch.

    Exit leaves the Keyboard Input the person typed during the run for the next Terminal App to read.

    TCSAFLUSH would destroy the Input without a backup and without a trace.

We meet spec as tested by _try_terminal_boss_, _try_terminal_boss_return_, and
_try_terminal_boss_farewell_:

    1. Save the Terminal attributes once at Enter, then call tty.setraw with TCSADRAIN,
       so queued Output leaves, but Input already typed stays to be read.
       With a Farewell, call tty.setcbreak at Enter and not tty.setraw, so ⌃C ⌃Z ⌃\ still signal.
       Expect queued Strikes of the Return Key to arrive as ⌃J,
       until tty.setraw makes new Strikes arrive as ⌃M.

    2. At Enter on a Stdin that is not a Terminal, save a stand-in list, and touch no termios.

    3. At Enter when already entered, change nothing, and return the same TerminalBoss.

    4. At Exit, restore the saved attributes with TCSADRAIN, so Input not yet read stays
       for the next Terminal App to read.

    5. At Exit when not entered, change nothing. At Exit, clear the save, so the next Enter
       saves afresh.

    6. At Enter and at Exit, flush Stdout and Stderr first, before tty.setraw or termios.tcsetattr.

    7. At Exit, write the Farewell Bytes, flushed, before restoring the saved attributes.

    8. Call tty.setraw in tty_setraw_before_farewell, so ⌃C ⌃Z ⌃\ stop signalling.

    9. Fail an assert when tty_setraw_before_farewell runs on a Terminal before Enter, and fail
       an assert when it runs without a Farewell. Do nothing at all on a Stdin that is not a
       Terminal.

Measured 24/Oct/2026 on a macOS pty, 2 runs each, 'ab' typed before Enter and 'xy' inside,
for the Choice:

    TCSADRAIN, our choice:    Enter keeps 'ab'        Exit leaves 'xy' for the next program
    TCSAFLUSH, not chosen:    Enter drops 'ab'        Exit drops 'xy'
```

## § 2 TerminalByteFrame

```
Spec of TerminalByteFrame.take_data_if.

Bytes go in, and the Frame closes, stays open, or bounces back the Bytes it won't take.

We meet spec as tested by _try_terminal_byte_frame_ and its helpers:

    1. Leave an empty Frame open. Bounce every Byte offered to a closed Frame, and leave the
       Frame as it was after any bounce.

    2. Leave each Head of the Headbook open: ⎋ ⎋⎋ ⎋⎋⇧O ⎋⎋[ ⎋⇧O ⎋[ ⎋[⇧M and ⎋].
       Bounce a 3rd ⎋ from ⎋⎋.

    3. Leave each Start of any UTF-8 Encoding open, and start it with exactly C2 .. F4.

    4. Close alone on a Control Byte, or a Char Unprintable by itself, or 1 to 4 Undecodable Bytes.

    5. Close Esc ⎋ on a Printable or Control Tail, and close Ss3 ⎋O on a Printable or Control Tail.

    6. Close Csi ⎋[ on a Multi-Byte Char, and bounce ⎋ and Tab and Undecodable Bytes.

    7. Close a Csi Frame on its Tail:  ⎋[⇧A  ⎋⎋[⇧A  ⎋[1⇧M  ⎋[3;5⇧H  and on the ⎋[ q ending in
       b" q", and close b'\033[201~' as _END_PASTE_.

    8. Leave Mouse ⎋[⇧M open, since ⎋[⇧M{b}{x}{y} could be a Frame of 6 Bytes,
       and then take 6 Bytes undecoded and bounce the rest.

    9. Leave Osc ⎋] open until Bel or ⎋\ closes it, and bounce Tab, ⎋ before a Multi-Byte Char,
       and before itself again.

    10. Leave Text open, and bounce 1 to 4 Unprintable Bytes after it.

    11. Keep a Frame open past a Printable Char that would close it, when a Combining Mark is
        already fetched,  ⎋j́  ⎋⎋j́  ⎋⇧Oj́  ⎋[j́  ⎋[1;5j́, then close on the Mark.
        Close Tab and ⎋Tab and raw ⎋[M anyway, while Text and Osc stay open and take the Mark.

    12. Speak each Byte as given in str(Frame), and end it in ' +' while the Frame is open.

    13. Close ⎋[↗ as an Intercardinal Arrow, all while no merely public standard names these.
```

## § 3 TerminalFrameDecoder

```
Spec of TerminalFrameDecoder.bytes_to_yx_or_hw_else.

We meet spec as tested by _try_terminal_frame_decoder_:

    1. Decode the Frame ⎋[8;24;80T, the Result of the Query ⎋[18T, as ("HW", 24, 80),
       Row Height then Column Width.

    2. Decode the Frame ⎋[5;7⇧R, the Result of the Query ⎋[6N, as ("YX", 5, 7),
       Row Number then Column Number.

    3. Decode any other Frame as None, such as the Arrow ⎋[⇧A, or a Result with a ⎋ stuck on
       its front, or two Results as one Frame, or a Result with too few Ints, or an empty Int,
       or no Bytes.

    4. Fail an assert on a Frame shaped like a Result but with a 0 Int, since it is no other
       Frame, and since Rows, Columns, Row Numbers, and Column Numbers all count from 1.

    5. Decode a Result whose Ints start with 0s, such as ⎋[007;5⇧R, as ("YX", 7, 5).
```

## § 4 TerminalFrameTaker

```
Spec of TerminalFrameTaker.is_quitting_frames.

We meet spec as tested by _try_is_quitting_frames_:

    1. Quit on the triple of ⏎ ⏎ ⏎.

    2. Do not quit on the pair of ⏎ ⏎.

    3. Quit on the triple of ⎋[ ⎋[ ⎋[, since the 2 Frames Taken and the 3rd still Open
       are the same Frame.

    4. Do not quit on the triple of ⎋ ⎋ ⎋, since the 2nd ⎋ joins the 1st in the Frame ⎋⎋
       and the 3rd bounces. Show ⎋⎋ '' b'\033\033' + on the screen the moment the 2nd ⎋ arrives.

    5. Quit on the triple of ⎋⎋ ⎋⎋ ⎋⎋, and on 6 ⎋ struck 150 ms apart, since those join
       in pairs as 3 Frames.

    6. Do not quit on the triple of x x x, since repeated Text never quits.

    7. Do not quit on the triple of ⏎ ⏎ ⏎ pasted, or struck all at once, and show 3 closed
       Frames, each ⏎ '' b'\r', since they are under 100 ms apart, so pasting blank lines
       is safe.

Items 1 to 7 measured 24/Oct/2026 on a macOS pty running --egg=strikes, with the strikes
150 ms apart.
```

```
Spec of is_quitting_shape.

We meet spec as tested by _try_is_quitting_shape_:

    1. Make the quitting shape of three same Bytes, each 100 ms or more after the one before,
       all within 3 s. Do not make it of two Bytes, nor of Bytes under 100 ms apart.

    2. Give the same answer for a list or a tuple of (Nanos, Bytes) pairs.
```

## § 5 TerminalFrameReader

```
Spec of TerminalFrameReader.take_frames_and_yield_each.

We meet spec as tested by _try_frame_reader_quits_midbatch_ and _try_frame_reader_nanobytes_:

    1. Leave the third Taken Frame of one read for the next pass, when a Caller quits after the
       second of three.

    2. Yield that third Taken Frame first in the next pass, before the Open Frame and before
       any further read.

    3. Give each Taken Frame with one (Nanos waited, Byte read) pair for each of its Bytes, in
       order, in a tuple, so that no Caller changes what the Reader keeps. Make the Nanos waited
       0 for every Byte of a read but the first.
```

## § 6 KeyboardDecoder

```
Spec of KeyboardDecoder.bytes_to_key_caps_if.

The Bytes of one Strike go in, and the Key Caps struck to send them come out, else an Empty Str.

We meet spec as tested by _try_keyboard_decoder_:

    1. Give Empty Str out for nothing in, and for an Undecodable Byte, a lone Combining Mark,
       and 2 Combining Marks on 1 Char.

    2. Give a Control Byte its Key Cap: ⇥ for Tab, ⏎ for Return, ⌃A for b'\001', ⎋ for b'\033'.

    3. Give a closed Csi or Ss3 Frame its Key Cap: ↑, ⇧→, F1.

    4. Give a Frame still open the Keys struck so far: b'\033[' gives ⎋[, b'\033[1' gives ⎋ [ 1,
       since no Chord sends those Bytes, and a Frame closed by b'a' gives ⎋ [ A.

    5. Give Printable Chars their Key Cap: ␢ J ⇧J, and give a Paste of b'ABC' ⇧A ⇧B ⇧C.

    6. Give a Dead Key Echo the Option Chord: è é ê ñ ë give ⌥`E ⌥EE ⌥IE ⌥NN ⌥UE, j + Acute gives
       ⌥EJ, ´ gives ⌥⇧E.

    7. Pick one reading where several Key Chords send the same Bytes:
       F6 over ⌥F1 and ⎋F1, F12 over ⌥F7 and ⎋F7, ⇧F5 over ⌥F8 and ⎋F8, ⎋⌃P over ⎋⇧F1 .. ⎋⌃⇧F12.

    8. Give b'\033[23~' ⌥F6, since macOS Mission Control often steals F11.

    9. Give b'\033[22~' ⎋ [ 2 2 ⇧~, since no F Key sends 22 (F10 sends 21 and F11 sends 23).

    10. Name a Unicode Combining Mark in each Dead Key Echo, so Apple accents the Char struck
        next. Assert this in litpyglass.py as it loads.
```

## § 7 InputStrikeTaker

```
Spec of InputStrikeTaker.pull_yx_hw_from_ts_else and .take_input_strikes_and_yield_each_placed.

We meet spec as tested by _try_placed_input_strikes_ and _try_pull_ends_without_answers_:

    1. On a Terminal, place each Strike at column_x 7, x_max 80, x_width 81, row_y 5, and
       y_height 24, given the Results ⎋[5;7⇧R and ⎋[8;24;81T: take Columns from the Cursor X
       and the Screen W, Rows from the Cursor Y and the Screen H, and act as 80 for the odd
       Width W+1.

    2. Queue the Strike typed before the Results come, and then give it that same Place, as for
       each Strike typed after.

    3. Take each Result as an answer and do not yield it as a Strike. Let a later Result of the
       same kind, such as a second ⎋[9;9⇧R pasted before the Size Result, replace the earlier.

    4. Off a Terminal, ask nothing, and require both Results in the Input, in either order,
       before any Strike takes its Place.

    5. When Input ends, or ⌃D quits the wait, before both Results have come, print "Input
       ended before Y X H W replies to ⎋[6N and ⎋[18T" and exit 1, on a Terminal or off one.
```

## § 8 GlassWorker

```
Spec of GlassWorker, the demos that --egg= picks.

We meet spec as tested by _try_strikes_spill_, running --egg=strikes on a macOS pty:

    1. Leave nothing in Stdin when nothing is struck after the 3rd ⏎.

    2. Leave Keys struck 150 ms after the 3rd ⏎ in Stdin for the next program to read.

We meet spec as tested by _try_skater_quits_, _try_skater_entry_, and _try_skater_edge_,
running --egg=skater on a macOS pty:

    3. Quit on the triple of ⏎ ⏎ ⏎ struck 150 ms apart, as --egg=strikes does.

    4. Do not quit on the pair of ⏎ ⏎.

    5. Do not quit on the triple of ⏎ ⏎ ⏎ pasted, or struck all at once.

    6. Move the Cursor on each Cardinal Arrow, leave an inverse pair of Spaces behind it, and
       draw a plain pair of Spaces ahead of it: → and ← move 2 Columns, and ↑ and ↓ move 1 Row.

    7. Do not quit on the triple of → → →, nor on the triples of ↑ ← ↓, since an Arrow
       moves the Cursor.

    8. Quit on the triple of ⎋[↗, since the Intercardinal Arrows are declared and not yet used.

    9. At Launch, set the Cursor Style to Skid, a solid underline similar to a _ skid mark,
       and hide the Cursor, once both Results have come and before writing the first Prompt.

    10. At Quit, park the Cursor at the leftmost Column of the next-to-last Row, show the Cursor,
        and revert the Cursor Style to the default. Write no choice of Cursor Style
        between Launch and Quit.

    11. At Launch, take ⌃C ⌃Z ⌃\ as Input and not as Signals, once both Results have come.

    12. Cycle the Prompt through the Digits 1234567890 with each Byte of an Open Frame.
        Such as ⎋ shows 1, and ⎋[ shows 2, and ⎋[ after a Taken Frame of 1 Byte shows 3,
        and an Open Frame of 10 or 20 Bytes shows 0.

    13. Reset the count of Bytes to 0 at a Taken Arrow Frame, so ⎋[ shows 2 again after it.

    14. At Launch on a Terminal, write the first Prompt, then the Queries ⎋[6N and ⎋[18T, and
        wait however long it takes for both Results.

    15. While waiting, let ⌃C ⌃Z ⌃\ still signal, and let ⌃D end Input with a brief complaint
        and exit 1.

    16. Keep the keys typed before the Results come, and let them take effect once both Results
        have come.

    17. At Launch off a Terminal, write no Queries and take the Results from the Input, else
        print the same complaint as on a Terminal and exit 1.

    18. Draw X, then O, then X again, in the left Cell of the Cursor's pair of Spaces, for each
        Taken Frame that is no Arrow. Such as ⏎ ⏎ shows X then O, and x then → shows X before
        the move.

    19. On a Screen 20 or 21 Columns wide, fill the Row with → to Column 20 and then bounce back
        off the East edge. Never write Column 21, and never wrap to the next Row.

We meet spec as tested by _try_frame_print_, running --egg=frames:

    20. Print a Frame's Bytes after "=", each Byte after the Nanos it waited. Print the first
        wait even when 0ns, and print each later wait only when more than 0ns.

Items 1 and 2 measured 24/Oct/2026 on a macOS pty running --egg=strikes, with the 3 ⏎ 150 ms
apart.
```

## § 9 main

```
Spec of the --typeahead flag of litpyglass.py, from the flag down into TerminalBoss.

We meet spec as tested by _try_typeahead_:

    1. Quit on the flag --typeahead of ⏎ ⏎ ⏎, since each ⏎ comes 150 ms after the last.

We meet spec as tested by _try_terminal_boss_typeahead_ and _try_terminal_boss_chunks_:

    2. Read Typeahead Bytes as if the Terminal sent them, but only after 150 ms in which
       the Terminal sends nothing, so a Byte the Terminal already sent comes first.

    3. While Typeahead is waiting, answer yes to asking if a Byte is coming. Wait up to 150 ms
       for the Terminal to speak first, or only as long as the caller will wait, when that
       is less.

    4. Read each Typeahead Byte alone, never as if pasted as a burst.

Item 1 measured 24/Oct/2026 on a macOS pty running --egg=strikes, with no key struck.
```

## § 10 TerminalLayer and TerminalShadow

```
Spec of TerminalLayer.

We meet spec as tested by _try_shadow_layer_ and _try_shadow_writes_:

    1. Give a Layer its own .place, .text_styles, and .write_by_xy, and write no Byte anywhere
       from it.

    2. Start a new Layer with a copy of the Place and the Text Styles of the Layer it is made
       from, and with no Writes.

    3. Keep each Printable Char written into a Layer at the (Column, Row) it lands on, with the
       Text Styles in force then, and let a later write there replace it.

    4. Keep nothing for a Move or a Backspace, but steer where the next Char lands. Keep nothing
       and steer nothing for hiding or showing the Cursor, ⎋[?25L or ⎋[?25H. Fail an assert on
       any other Control, not silently.

    5. Start the Text Styles in force over at ⎋[M, and carry them to the next write. Join them
       once on ⎋[7M however often said. Fail an assert on any other SGR, such as ⎋[27M or
       ⎋[1M, not silently.

    6. Act as W for an odd Width W+1, though it is real, since a Square Pixel is 2 Columns wide
       and cannot fit in Column W+1: write no Char into Column W+1, though let the Cursor wait
       there. Judge the wait to wrap by the real Width W+1.

    7. Write only inside the rectangle of Height by x_max: refuse a Char that would land outside
       it, even if the Cursor then moves back inside.

    8. Refuse a Move or a Backspace that would leave the Screen, at the North, West, and South
       edges. Let a Move East from the last Column wait in Column W+1, still on the Screen.

    9. Land a Return on Column 1 of the same Row, even with the wrap pending after a write into
       the last Column.

    10. After a Char into the last Column, with nothing after it, leave the Cursor waiting to
        wrap past x_max: an even Width has no Column W+1 for it, and an odd Width acts as W.
        After a Backspace or a Return after it, leave the Cursor inside the Writable Area.

    11. Say so when a Write cannot be made, and leave the Layer half written. Let the caller
        drop that Layer.

    12. Do the work of items 3 to 11 in one def on the Layer, _write_some_or_all_strs_. Run that
        one def in the Shadow, and ship no second copy of the rules.

    13. Change no other Layer on any Write into a Layer. Never write through unasked.

    14. Give a Layer's Place, Text Styles, and Writes to another Layer when asked, by
        shadow_screen_into. Let each Write replace the Write at the same (Column, Row), leave
        each other Write as it was, and leave the Layer that gives as it was.
```

```
Spec of TerminalShadow.

We meet spec as tested by _try_shadow_layer_ and _try_shadow_writes_:

    1. Hold a Terminal and one Layer, named .layer, and read everything known of the Screen
       from .layer. Forward none of the three by property.

    2. Keep no Write before any write, and none after only the Terminal's answers.

    3. Fail an assert before any Byte goes out, on any write made before the Terminal answers,
       even one of no Char.

    4. In str_write_tb, take each Write through a new Layer made from .layer. Assert the Write
       can be made, call shadow_screen_into to update .layer, and only then write the Bytes to
       the Terminal. Fail an assert before any Byte goes out on a Write that cannot be made,
       and leave the Shadow as it was.

    5. In is_writable_place_after_strs, take the Write through a new Layer, drop that Layer, and
       say yes only when the Cursor ends inside the Writable Area. Say no to a Char into the
       last Column with nothing after it, and yes to a Backspace or a Return after it.
```
