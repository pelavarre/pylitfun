# Specs of litpyglass.py

Each section is one Spec. Its first line says what it covers, `We meet spec as tested by` names the Tests in tests.py that prove it, and a Measured line, when there is one, comes last and says which items it measures.

## § 1 TerminalBoss

```
Spec of TerminalBoss, and how it chooses TCSADRAIN vs TCSAFLUSH in its __enter__ and __exit__.

Choice: Keep TCSADRAIN at Enter and at Exit of TerminalBoss.

    Enter keeps the Keyboard Input typed before launch.

    Exit leaves the Keyboard Input the person typed during the run for the next Terminal App to
    read.

    TCSAFLUSH would destroy the Input without a backup and without a trace.

We meet spec as tested by _try_terminal_boss_, _try_terminal_boss_return_, and
_try_terminal_boss_farewell_:

    1. Save the Terminal attributes once at Enter, then call tty.setraw with TCSADRAIN, so queued
       Output leaves, but Input already typed stays to be read. With a Farewell, call tty.setcbreak
       at Enter and not tty.setraw, so ⌃C ⌃Z ⌃\ still signal. Expect queued Strikes of the Return
       Key to arrive as ⌃J, until tty.setraw makes new Strikes arrive as ⌃M.

    2. At Enter on Input that is not a Terminal, save a stand-in list, and touch no termios.

    3. At Enter when already entered, change nothing, and return the same TerminalBoss.

    4. At Exit, restore the saved attributes with TCSADRAIN, so Input not yet read stays for the
       next Terminal App to read.

    5. At Exit when not entered, change nothing. At Exit, clear the save, so the next Enter saves
       afresh.

    6. At Enter and at Exit, flush the Output written so far, before tty.setraw or
       termios.tcsetattr.

    7. At Exit, write the Farewell Bytes, flushed, before restoring the saved attributes.

    8. Call tty.setraw in tty_setraw_before_farewell, so ⌃C ⌃Z ⌃\ stop signalling.

    9. Fail an assert when tty_setraw_before_farewell runs on a Terminal before Enter, and fail an
       assert when it runs without a Farewell. Do nothing at all on Input that is not a Terminal.

We meet spec as tested by _try_boss_writes_ and _try_input_file_:

    10. Start .obk and .typescript empty. Keep in .obk every Byte written, the Asks too, each with
        its Nanos. Keep in .typescript every Byte written but the Asks.

    11. In str_write, encode the Text in the encoding the Output takes, such as Latin-1 when the
        Output is Latin-1, so the Bytes kept are the Bytes the Terminal gets. Then take one Nanos,
        and write the Text with nothing added to end the last Line of the Text. Keep the Bytes in
        .obk with that one Nanos, and in .typescript. Keep nothing, and write nothing, for a Text
        that will not encode.

    12. In str_print, call str_write for the Text and the end of its Line. End the Line as "\r\n"
        while the Boss is entered, since then the Terminal adds no "\r" to a "\n". End it as "\n"
        before the Boss is entered and after it exits.

    13. Say str_print when the Boss's present end of Line is wanted. Say str_write when nothing is
        to be added to end the last Line of the Text, as in a Prompt that stays on its Line.

    14. In bytes_write_flush, take one Nanos, flush, write the Bytes, and flush. Then keep the
        Bytes in .obk with that Nanos, and in .typescript.

    15. In asks_write_flush, write exactly as bytes_write_flush does, and keep the Bytes in .obk
        only, never in .typescript, since an Ask replayed from a Typescript would make the
        Terminal reply.

    16. In _bytes_write_flush_, flush, write the Bytes, and flush, and keep nothing.

    17. In typescript_write_file, write the Bytes of .typescript, unchanged, into the file at the
        path given, and replace any older file. Write an empty file when the Boss wrote nothing.

We meet spec as tested by _try_terminal_boss_keeps_input_ and _try_input_file_:

    18. Start .ibk empty. Keep in .ibk every Byte read through the TerminalBoss, Typeahead Bytes
        too, each Byte once and each with its Nanos.

    19. In read_one_byte_if, take one Nanos after the read returns. Keep the Input, or b'' at
        End-of-Input, in .ibk with that one Nanos.

    20. In read_some_bytes_if, take one Nanos after the burst is read. Keep the Input, or b'' at
        End-of-Input, in .ibk with that one Nanos.

    21. In _read_one_byte_if_, read one Byte and keep nothing, so read_some_bytes_if keeps a burst
        once and not Byte by Byte.

Measured 24/Oct/2026 on a macOS pty, 2 runs each, 'ab' typed before Enter and 'xy' inside, for the
Choice:

    TCSADRAIN, our choice:    Enter keeps 'ab'        Exit leaves 'xy' for the next program
    TCSAFLUSH, not chosen:    Enter drops 'ab'        Exit drops 'xy'
```

## § 2 TerminalByteFrame

```
Spec of TerminalByteFrame.take_data_if.

Bytes go in, and the Frame closes, stays open, or bounces back the Bytes it won't take.

We meet spec as tested by _try_terminal_byte_frame_ and its helpers:

    1. Leave an empty Frame open. Bounce every Byte offered to a closed Frame, and leave the Frame
       as it was after any bounce.

    2. Leave each Head of the Headbook open: ⎋ ⎋⎋ ⎋⎋⇧O ⎋⎋[ ⎋⇧O ⎋[ ⎋[⇧M and ⎋]. Bounce a 3rd ⎋ from
       ⎋⎋.

    3. Leave each Start of any UTF-8 Encoding open, and start it with exactly C2..F4.

    4. Close alone on a Control Byte, or a Char Unprintable by itself, or 1 to 4 Undecodable Bytes.

    5. Close Esc ⎋ on a Printable or Control Tail, and close Ss3 ⎋O on a Printable or Control Tail.

    6. Close Csi ⎋[ on a Multi-Byte Char, and bounce ⎋ and Tab and Undecodable Bytes.

    7. Close a Csi Frame on its Tail:  ⎋[⇧A  ⎋⎋[⇧A  ⎋[1⇧M  ⎋[3;5⇧H  and on the ⎋[ q ending in b" q",
       and close b'\033[201~' as _END_PASTE_.

    8. Leave Mouse ⎋[⇧M open, since ⎋[⇧M{b}{x}{y} could be a Frame of 6 Bytes, and then take 6 Bytes
       undecoded and bounce the rest.

    9. Leave Osc ⎋] open until Bel or ⎋\ closes it, and bounce Tab, ⎋ before a Multi-Byte Char, and
       before itself again.

    10. Leave Text open, and bounce 1 to 4 Unprintable Bytes after it.

    11. Keep a Frame open past a Printable Char that would close it, when a Combining Mark is
        already fetched,  ⎋j́  ⎋⎋j́  ⎋⇧Oj́  ⎋[j́  ⎋[1;5j́, then close on the Mark. Close Tab and
        ⎋Tab and raw ⎋[M anyway, while Text and Osc stay open and take the Mark.

    12. Speak each Byte as given in str(Frame), and end it in ' +' while the Frame is open.

    13. Close a Csi Frame on a printable Final Char from outside 7-bit US Ascii, such as ⎋[↗ or
        ⎋[1;2↗ or ⎋[€, though no public standard names these, and nothing here sends them yet.
```

## § 3 TerminalFrameDecoder

```
Spec of TerminalFrameDecoder.bytes_to_yx_or_hw_reply_else.

We meet spec as tested by _try_terminal_frame_decoder_:

    1. Decode the Frame ⎋[5;7⇧R, the Reply to the Ask ⎋[6N, as ("YX", 5, 7), Row Number then
       Column Number.

    2. Decode the Frame ⎋[8;24;80T, the Reply to the Ask ⎋[18T, as ("HW", 24, 80), Row Height
       then Column Width.

    3. Decode any other Frame as None, such as the Arrow ⎋[⇧A, or a Reply with a ⎋ stuck on its
       front, or two Replies as one Frame, or a Reply with too few Ints, or an empty Int, or no
       Bytes.

    4. Fail an assert on a Frame shaped like a Reply but with a 0 Int, since it is no other Frame,
       and since Rows, Columns, Row Numbers, and Column Numbers all count from 1.

    5. Decode a Reply whose Ints start with 0s, such as ⎋[007;5⇧R, as ("YX", 7, 5).
```

## § 4 TerminalFrameTaker

```
Spec of TerminalFrameTaker.is_quitting_frames.

We meet spec as tested by _try_is_quitting_frames_:

    1. Quit on the triple of ⏎ ⏎ ⏎.

    2. Do not quit on the pair of ⏎ ⏎.

    3. Quit on the triple of ⎋[ ⎋[ ⎋[, since the 2 Frames Taken and the 3rd still Open are the same
       Frame.

    4. Do not quit on the triple of ⎋ ⎋ ⎋, since the 2nd ⎋ joins the 1st in the Frame ⎋⎋ and the 3rd
       bounces. Show ⎋⎋ '' b'\033\033' + on the screen the moment the 2nd ⎋ arrives.

    5. Quit on the triple of ⎋⎋ ⎋⎋ ⎋⎋, and on 6 ⎋ struck 150 ms apart, since those join in pairs as
       3 Frames.

    6. Do not quit on the triple of x x x, since repeated Text never quits.

    7. Do not quit on the triple of ⏎ ⏎ ⏎ pasted, or struck all at once, and show 3 closed Frames,
       each ⏎ '' b'\r', since they are under 100 ms apart, so pasting blank lines is safe.

Items 1 to 7 measured 24/Oct/2026 on a macOS pty running --egg=strikes, with the strikes 150 ms
apart.

We meet spec as tested by _try_terminal_boss_keeps_input_:

    8. Build the TerminalFrameTaker with its TerminalBoss, and read the Bytes and their Nanos from
       the Input Keeper of that Boss.
```

```
Spec of is_quitting_shape.

We meet spec as tested by _try_is_quitting_shape_:

    1. Make the quitting shape of three same Bytes, each 100 ms or more after the one before, all
       within 3 s. Do not make it of two Bytes, nor of Bytes under 100 ms apart.

    2. Give the same answer for a list or a tuple of (Nanos, Bytes) pairs.
```

## § 5 TerminalFrameReader

```
Spec of TerminalFrameReader.take_frames_and_yield_each.

We meet spec as tested by _try_frame_reader_quits_midbatch_, _try_frame_reader_nanobytes_, and
_try_frame_reader_peek_:

    1. Leave the third Taken Frame of one read for the next pass, when a Caller quits after the
       second of three.

    2. Yield that third Taken Frame first in the next pass, before the Open Frame and before any
       further read.

    3. Give each Taken Frame with one (Nanos waited, Byte read) pair for each of its Bytes, in
       order, in a tuple, so that no Caller changes what the Reader keeps. Make the Nanos waited 0
       for every Byte of a read but the first.

    4. Build the Reader with its TerminalBoss, and read every Byte of its Frames through that Boss.

    5. Peek at the Bytes of the same read that follow each Byte taken. When they begin a Char of 1 to
       4 Bytes that is a Combining Mark, of Category Mn, Mc, or Me, keep the Frame open for it, as
       § 3 item 11 says. Close the Frame at once when the Char is no Mark, and when the Mark comes
       in a later read.
```

## § 6 KeyboardDecoder

```
Spec of KeyboardDecoder._burst_bytes_to_key_caps_if_ and .nanobytes_to_key_caps_if.

The Bytes of one burst go in, and the Key Caps struck to send them come out, else an Empty Str.

We meet spec as tested by _try_keyboard_decoder_:

    1. Give Empty Str out for nothing in, and for an Undecodable Byte, a lone Combining Mark, and 2
       Combining Marks on 1 Char. Give Empty Str out for a Letter under a Combining Mark that no
       Key sends: q + Acute, p + Tilde, x + Diaeresis, j + Grave, and ĵ. Give Empty Str out for
       e + Acute as 2 Chars, since ⌥E E sends é as 1 Char, and for ˆ + j + Acute, since ⌥I J sends
       ˆj and then no Key sends the Acute alone.

    2. Give a Control Byte its Key Cap: ⇥ for Tab, ⏎ for Return, ⌃A for b'\001', ⎋ for b'\033'.

    3. Give a closed Csi or Ss3 Frame its Key Cap: ↑, ⇧→, F1.

    4. Give a Frame still open the Keys struck so far: b'\033[' gives ⎋[, b'\033[1' gives ⎋ [ 1,
       since no Chord sends those Bytes, and a Frame closed by b'a' gives ⎋ [ A.

    5. Give Printable Chars their Key Cap: ␢ J ⇧J, and give a Paste of b'ABC' ⇧A ⇧B ⇧C, and of aå
       A ⌥A.

    6. Give a Dead Key Echo the Option Chord: è é ê ñ ë give ⌥`E ⌥EE ⌥IE ⌥NN ⌥UE, É gives ⌥E⇧E,
       j + Acute gives ⌥EJ, J + Acute gives ⌥E⇧J, ´ gives ⌥⇧E.

    7. Pick one reading where several Key Chords send the same Bytes: F6 over ⌥F1 and ⎋F1, F12 over
       ⌥F7 and ⎋F7, ⇧F5 over ⌥F8 and ⎋F8, ⎋⌃P over ⎋⇧F1 .. ⎋⌃⇧F12.

    8. Give b'\033[22~' ⎋ [ 2 2 ⇧~, since no F Key sends 22 (F10 sends 21 and F11 sends 23).

    9. Give b'\033[23~' ⌥F6, since macOS Mission Control often steals F11.

    10. Assert in litpyglass.py, as it loads, that the three tables of Dead Keys speak of the same
        five: ⌥` ⌥E ⌥I ⌥N ⌥U. Assert that 5 Dead Keys before 52 Letters, 10 Digits, and 32 Punctuation Marks make 470 pairs.

    11. Name the Frames b'\033[5~' b'\033[6~' b'\033[F' b'\033[H' as the Key Caps ⇧Fn↑ ⇧Fn↓ ⇧Fn→
        ⇧Fn←, in that order, as macOS Terminal sends them.

    12. Name the ⌥ Dead Key, when its Accent comes ahead of a Letter A..Z or a..z that it does not
        accent: ˆp gives ⌥I P, and `p ´q ˜p ¨x ˆP give ⌥` P, ⌥E Q, ⌥N P, ⌥U X, ⌥I ⇧P. Name 210 such
        pairs of Accent and Letter, as the U.S. Layout of macOS sends them. Name 210 more pairs of
        Accent and Digit or Punctuation Mark, such as `- ´_ ˆ1 ˜~ ¨`, giving ⌥` - ⌥E ⇧_ ⌥I 1 ⌥N ⇧~
        ⌥U `.

    13. Name the ⌥⇧ Chord of the Accent, when no Dead Key sends the pair: ˆe gives ⌥⇧I E since ⌥I E
        sends ê, ´j gives ⌥⇧E J since ⌥E J sends j before a Combining Acute Accent, and ˆ before a
        Space, itself, or a Letter under a Dead Key's own Mark stays ⌥⇧I, as in ˜Ï giving
        ⌥⇧N ⌥U⇧I.

We meet spec as tested by _try_keyboard_decoder_bursts_ and _try_frame_print_:

    14. Take (Nanos waited, Byte read) pairs in. Cut Text into bursts, before each Char whose last
        Byte came 10 ms or more after the Char before, adding up the waits of its Bytes. Name each
        burst, and join the names with a Space: ˆp gives ⌥I P when the p waited less than 10 ms, and
        ⌥⇧I P when it waited 10 ms. Likewise j + Acute gives ⌥EJ when the Acute waited less than
        10 ms, and Empty Str when it waited 10 ms, since no Key sends a lone Combining Mark.

    15. Cut no Char in two, no matter how slowly its Bytes came, and cut no Frame that is not all
        Printable Text: ⎋ [ ⇧A struck slowly still gives ↑.

    16. Give Empty Str out for no pairs in, and for Text with a burst that has no name, such as a
        Combining Mark that came slowly.

    17. Name each Frame burst by burst in --egg=frames, and in every Strike of the InputStrikeTaker,
        Open or Taken: ˆp of one read gives ⌥I P, and ˆ and p of two reads 20 ms apart give ⌥⇧I P.
        Likewise j + Acute of one read gives ⌥EJ, and of two reads 20 ms apart gives Empty Str.

Measured, items 12 to 14 and 17: at macOS Terminal, the p of ⌥I P came less than 1 ms after its
Accent, and the p of ⌥⇧I then P struck fast came 320 ms to 333 ms after, in four tries.
```

## § 7 InputStrikeTaker

```
Spec of InputStrikeTaker.pull_yx_hw_from_ts_else, .take_input_strikes_and_yield_each_placed, and
.take_input_strikes_and_yield_each.

We meet spec as tested by _try_placed_input_strikes_, _try_pull_ends_without_replies_,
_try_intercardinal_strikes_, _try_intercardinal_joins_, _try_intercardinal_ahead_, and
_try_intercardinal_splits_:

    1. On a Terminal, place each Strike at column_x 7, x_max 80, x_width 81, row_y 5, and y_height
       24, given the Replies ⎋[5;7⇧R and ⎋[8;24;81T: take Columns from the Cursor X and the Screen
       W, Rows from the Cursor Y and the Screen H, and act as 80 for the odd Width W+1.

    2. Queue the Strike typed before the Replies come, and then give it that same Place, as for each
       Strike typed after.

    3. Take each Reply as the Reply to our Ask, and do not yield it as a Strike. Let a later Reply
       of the same kind, such as a second ⎋[9;9⇧R pasted before the Size Reply, replace the
       earlier.

    4. Off a Terminal, ask nothing, and require both Replies in the Input, in either order, before
       any Strike takes its Place.

    5. When Input ends, or ⌃D quits the wait, before both Replies have come, write "Input ended
       before Y X H W replies to ⎋[6N and ⎋[18T" and exit 1, on a Terminal or off one.

    6. Take as a Cardinal Arrow each Taken Strike whose Key Caps are zero or more of ⎋ ⌃ ⌥ ⇧ ⌘ Fn
       and then one of ← ↑ → ↓, such as ← or ⇧← or ⌥↑ or ⎋⇧→ or ⇧Fn↑.

    7. Join two Cardinal Arrows on different axes into one Intercardinal Arrow Strike, whether
       Shifted or not, when the second is available soon: its Bytes came in the same read as the
       first, or come in the very next read within the wait of item 14. Join them in either order of
       arrival, such as ↑ → and → ↑ both joined as ↗, and ⇧← ↑ joined as ⇧↖, and ⇧Fn↑ → joined as ⇧Fn↗.

    8. Give a joined Strike the Key Caps of every Shift of both Arrows, each once, in the order ⎋
       ⌃ ⌥ ⇧ ⌘ Fn, and then the diagonal ↖ ↗ ↘ ↙, such as ⇧← with ↑ giving ⇧↖, and ⌥↑ with ⇧→
       giving ⌥⇧↗.

    9. Give a joined Strike the two Frames of its Arrows, in the order they arrived. Give it their
       Bytes catenated, such as ↑ then → giving ⎋[A⎋[C, and → then ↑ giving ⎋[C⎋[A, both with the
       Key Caps ↗. So one Intercardinal Arrow has two Frames, and ⇧← then ↑ gives ⎋[1;2D⎋[A.

    10. Do not join two Cardinal Arrows on one axis, such as ↑ ↓ or ⇧← ⇧→ or ⇧Fn↑ ⇧Fn↓, nor an Arrow
        with a Strike that is no Cardinal Arrow, such as ⇧A.

    11. When arrow_wait_nanos is above 0, hold the first Arrow, and peek once, at the first empty
        Open Frame after it, to ask if a first Byte is available. Wait for one at most
        arrow_wait_nanos. Yield the held Arrow unjoined when no Byte is available by then, and
        likewise when the next read brings anything but a whole second Arrow that joins. When
        arrow_wait_nanos is 0, hold nothing, peek never, and join nothing: yield each Strike as it
        comes, whether two Arrows arrive in one read, in two reads, or in Typeahead.

    12. Yield a held Arrow before the Strike that ends the hold, and when Input ends. Yield a Strike
        for each empty Open Frame as ever, one before each read, even while holding an Arrow.

    13. Join Arrows typed ahead by --typeahead as if all the Typeahead were available at once,
        though each Byte arrives alone: ⎋[A⎋[C gives ↗. While holding an Arrow, and while Typeahead
        Bytes remain, read on past each Open Frame, empty or not, without asking if a Byte is
        available, and yield a Strike for it as ever. Once the Typeahead runs dry, apply the rules
        above: yield a lone Arrow after the peek says no, and give up at once on a partial Frame.
        Never wait on Typeahead, whatever arrow_wait_nanos says.

    14. Take the wait of item 11 from the constructor, as arrow_wait_nanos, an int of 0 or more,
        with no default, so each caller spells it. Refuse a negative wait, with the value in the
        message.
```

## § 8 GlassWorker

```
Spec of GlassWorker, the demos that --egg= picks. The Tests of the Skater read the Screen back
through a Screen replay, and _try_screen_replay_ is the Test of that replay.

We meet spec as tested by _try_strikes_spill_, running --egg=strikes on a macOS pty:

    1. Leave no unread Input when nothing is struck after the 3rd ⏎.

    2. Leave Keys struck 150 ms after the 3rd ⏎ as unread Input for the next program to read.

We meet spec as tested by _try_skater_quits_, _try_skater_entry_, _try_skater_edge_,
_try_skater_fuzz_, and _try_skater_launch_edge_, running --egg=skater on a macOS pty:

    3. At Launch on a Terminal, write the Asks ⎋[6N and ⎋[18T, and wait however long it takes
       for both Replies.

    4. While waiting, let ⌃C ⌃Z ⌃\ still signal, and let ⌃D end Input with a brief complaint and
       exit 1.

    5. Keep the keys typed before the Replies come, and let them take effect once both Replies have
       come.

    6. At Launch off a Terminal, write no Asks and take the Replies from the Input, else write
       the same complaint as on a Terminal and exit 1.

    7. At Launch, once both Replies have come, revert the Text Styles and show the Real Cursor.
       Step the Cursor West by Backspaces only as far as a Pair of 2 Columns needs, so that it sits
       at or West of Column x_max less 1, and move nowhere else. Assert that a Pair then fits at the
       Cursor. Item 9 says when to hide it and show it again.

    8. At Launch, take ⌃C ⌃Z ⌃\ as Input and not as Signals, once both Replies have come.

    9. On each Cardinal Arrow, bare or Shifted, write a Reverse Pair of Spaces into the Base Layer
       where the Cursor was, then move the Cursor: → and ← move 2 Columns, and ↑ and ↓ move 1 Row.
       Write a visible Prompt at nearly every input into the Top Layer, never into the Base Layer:
       the Cursor, the X and O, and the Digits. A later Prompt in the same Cell replaces the earlier.
       Undo the write through the Top Layer when an Arrow moves the Cursor and at Quit, and let it
       stand otherwise. Before each Undo, if the Top Layer holds one lone Char, forget it and do not
       undo it, since Undo guesses nothing of a Cell the Base Layer never wrote. The next Reverse
       Pair covers it at an Arrow, and it stays at Quit. While the Cursor sits on a Cell already
       written, write a Plain Pair of Spaces over it into the Top Layer, and hide the Real Cursor.
       Otherwise show the Real Cursor. Do ask to show the Real Cursor at exit.

    10. On each Intercardinal Arrow, bare or Shifted, write the same Reverse Pair, then move the
        Cursor 1 Row and 2 Columns, such as ↗ moving 1 Row up and 2 Columns East. At an edge,
        settle for the half of the move that fits, so as to make a visible change: ↗ on the top
        Row moves as →, and ↗ at the East edge moves as ↑. Bounce to the opposite Arrow only when
        neither half fits, such as ↗ in the top East corner moving as ↙.

    11. Move on every Shifted Arrow, Cardinal or joined, as its bare Arrow moves, such as ⇧← moving
        as ←, and ⌥⇧↗ moving as ↗. Never quit on a Shifted Cardinal Arrow: the stalwarts are ← ↑ → ↓
        and ⇧← ⇧→ ⌥← ⌥→ ⌥↑ ⌥↓ ⎋⇧← ⎋⇧→ ⇧Fn↑ ⇧Fn↓ ⇧Fn→ ⇧Fn←, each by its Bytes.

    12. On a Screen 20 or 21 Columns wide, fill the Row with → to Column 20 and then bounce back off
        the East edge. Never write Column 21, and never wrap to the next Row. Bounce likewise off
        each other edge, each of ↑ ↓ ← → to its opposite.

    13. Cycle the Prompt through the Digits 1234567890 with each Byte of an Open Frame, in the Top
        Layer. Such as ⎋ shows 1, and ⎋[ shows 2, and ⎋[ after a Taken Frame of 1 Byte shows 3, and
        an Open Frame of 10 or 20 Bytes shows 0.

    14. Reset the count of Bytes to 0 at a Taken Arrow Frame, so ⎋[ shows 2 again after it.

    15. Draw X, then O, then X again, in the Top Layer, in the left Cell of the Cursor's pair of
        Spaces, for each Taken Frame that is no Arrow. Such as ⏎ ⏎ shows X then O, and x then →
        shows X before the move.

    16. Quit on the triple of ⏎ ⏎ ⏎ struck 150 ms apart, as --egg=strikes does.

    17. Do not quit on the pair of ⏎ ⏎.

    18. Do not quit on the triple of ⏎ ⏎ ⏎ pasted, or struck all at once.

    19. Do not quit on the triple of → → →, nor on the triples of ↑ ← ↓, nor on the triples of ⇧→
        ⌥↑ or ⎋⇧←, or any other Shifted Arrow, since an Arrow moves the Cursor.

    20. Do not quit on the triple of ↓ → struck together, since each pair is one Intercardinal Arrow
        that moves the Cursor.

    21. At Quit, at the last moment, undo the write through the Top Layer, then revert the Text
        Styles, show the Real Cursor, and park it at the leftmost Column of the next-to-last Row.
        Leave the Base Layer as the Arrows wrote it. Before any Arrow, leave only a lone last
        Prompt Char, if any.

We meet spec as tested by _try_frame_print_, running --egg=frames:

    22. Print a Frame's Bytes after "=", each Byte after the Nanos it waited. Print the first wait
        even when 0ns, and print each later wait only when more than 0ns.

We meet spec as tested by _try_boss_writes_ and _try_output_routes_:

    23. Write the Asks of item 3 by asks_write_flush, after flushing the Output written before
        them, so they leave at once and never wait in a buffer.

    24. Write every other Byte through the TerminalBoss, never around it by a print or a write of
        its own, except the three prints of the help.

We meet spec as tested by _try_input_file_, running every --egg= off a Terminal:

    25. In every egg, build the TerminalBoss before the first print, enter it later with `with tb:`,
        print through it, and return only the Boss, which holds the Input Keeper and the Output
        Keeper. Give frame_print the Boss as tb=. Print the first Lines, in the eggs that print any, before entering the Boss,
        so they end as "\n".

    26. In --egg=nanos, count the first wait from the first Nanos kept in the Output, since no Input
        has come yet. So the first wait printed is the first Nanos of i.jsonl.

We meet spec as tested by _try_arrow_wait_:

    27. In --egg=strikes and in --egg=skater, wait up to 50 ms for a second Arrow, since the second
        Arrow of two struck together came within 50 ms in 69 of 69 strikes measured on a Terminal,
        while a held Key repeats no faster than 80 ms.

Items 1 and 2 measured 24/Oct/2026 on a macOS pty running --egg=strikes, with the 3 ⏎ 150 ms apart.
```

## § 9 main

```
Spec of the --typeahead flag of litpyglass.py, from the flag down into TerminalBoss.

We meet spec as tested by _try_typeahead_:

    1. Quit on the flag --typeahead of ⏎ ⏎ ⏎, since each ⏎ comes 150 ms after the last.

We meet spec as tested by _try_terminal_boss_typeahead_ and _try_terminal_boss_chunks_:

    2. Read Typeahead Bytes as if the Terminal sent them, but only after 150 ms in which the
       Terminal sends nothing, so a Byte the Terminal already sent comes first.

    3. While Typeahead is waiting, answer yes to asking if a Byte is coming. Wait up to 150 ms for
       the Terminal to speak first, or only as long as the caller will wait, when that is less.

    4. Read each Typeahead Byte alone, never as if pasted as a burst.

Item 1 measured 24/Oct/2026 on a macOS pty running --egg=strikes, with no key struck.
```

```
Spec of the Files that main writes at the end of an egg run.

We meet spec as tested by _try_input_file_, running every --egg= off a Terminal, and running no
args and --egg=skater off a Terminal with no Replies, and as tested by _try_typescript_files_,
running --egg=skater and --egg=strikes on a macOS pty:

    1. At the end of an egg run, write every Input Byte that the Boss kept, with its Nanos, to
       i.jsonl in the current directory. Write a first line ["Nanos", "Bytes"], then one [Nanos, Byte] line per Byte, in
       the order the Bytes arrived, the Byte as an Int and the Nanos counted from a zero shared with
       o.jsonl, so the first Nanos across both files is 0. End each line with "\n".

    2. Write every Byte written through the TerminalBoss, the Asks too, to o.jsonl in the
       same line format. Take the Nanos from just before the write, and give the Bytes of one write
       the one Nanos.

    3. Write every Byte written except the Asks to o.typescript, unchanged and in order,
       so that cat o.typescript draws the same Screen and types nothing into the Shell.

    4. Replace any older file of those three names.

    5. Cope with an egg that read no Input, or wrote no Output, or neither: write only the first
       line into i.jsonl or o.jsonl for no Bytes, and write an empty o.typescript for no Output.

    6. Count the Nanos of both files from the earlier of the first Nanos kept in the Input Keeper
       and the first Nanos kept in the Output Keeper. Count from 0 when neither kept any.

    7. In pairs_write_file, assert in the one loop over the Bytes that no Nanos is less than the
       zero given, so a Nanos never counts below 0. Do that before opening the file, so a refusal
       leaves any older file as it was. Assert too that Bytes and Nanos agree in count.

    8. Write the three files after the last Output, which is the empty Line that main writes through
       the TerminalBoss once the egg returns.

    9. Write no file for the help, nor when the egg exits before it returns, such as exit 1 for
       Input that ended before the Replies.
```

## § 10 TerminalLayer and TerminalShadow

```
Spec of TerminalLayer.

We meet spec as tested by _try_shadow_layer_, _try_shadow_writes_, and _try_shadow_insert_row_:

    1. Give a Layer its own .place, .text_styles, and .write_by_xy, and write no Byte anywhere from
       it.

    2. Start a new Layer with a copy of the Place and the Text Styles of the Layer it is made from,
       and with no Writes.

    3. Keep each Printable Char written into a Layer at the (Column, Row) it lands on, with the Text
       Styles in force then, and let a later write there replace it.

    4. Keep nothing for a Move or a Backspace, but steer where the next Char lands. Keep nothing and
       steer nothing for hiding or showing the Cursor, ⎋[⇧?25L or ⎋[⇧?25H. Fail an assert on any
       other Control, not silently. Insert a Row at the Cursor on ⎋[⇧L, as item 14 says.

    5. Start the Text Styles in force over at ⎋[M, and carry them to the next write. Join them once
       on ⎋[7M however often said. Fail an assert on any other SGR, such as ⎋[27M or ⎋[1M, not
       silently.

    6. Act as W for an odd Width W+1, though it is real, since a Square Pixel is 2 Columns wide and
       cannot fit in Column W+1: write no Char into Column W+1, though let the Cursor wait there.
       Judge the wait to wrap by the real Width W+1.

    7. Write only inside the rectangle of Height by x_max: refuse a Char that would land outside it,
       even if the Cursor then moves back inside.

    8. Refuse a Move or a Backspace that would leave the Screen, at the North, West, and South
       edges. Let a Move East from the last Column wait in Column W+1, still on the Screen.

    9. Land a Return on Column 1 of the same Row, even with the wrap pending after a write into the
       last Column.

    10. After a Char into the last Column, with nothing after it, leave the Cursor waiting to wrap
        past x_max: an even Width has no Column W+1 for it, and an odd Width acts as W. After a
        Backspace or a Return after it, leave the Cursor inside the Writable Area.

    11. Say so when a Write cannot be made, and leave the Layer half written. Let the caller drop
        that Layer.

    12. Do the work of items 3 to 11 in one def on the Layer, _write_some_or_all_strs_. Run that one
        def in the Shadow, and ship no second copy of the rules.

    13. Change no other Layer on any Write into a Layer. Never write through unasked.

    14. Insert a Row at the Cursor on ⎋[⇧L, the 3 Chars "\e[L", in _write_some_or_all_strs_ and in
        this order. Drop the Writes of the last Row. Move down one Row each Write of each Row at or
        below the Cursor, and leave each Write above the Cursor where it is. Write the Cursor Row
        full of plain Spaces, from Column 1 to the real Width W+1 of an odd Width, and plain even
        while ⎋[7M is in force, as macOS Terminal paints it: Reverse is no Background Colour. Leave
        the Cursor where it is, and leave it waiting to wrap while it waits, as macOS Terminal
        does and as no Move does. Do the work in the same dict of Writes, never a copy. Fail an
        assert on ⎋[2⇧L or any other Pn, not silently.
```

```
Spec of TerminalShadow.

We meet spec as tested by _try_shadow_layer_, _try_shadow_writes_, _try_shadow_top_layer_, and
_try_shadow_insert_row_:

    1. Hold a Terminal, a Base Layer named .base, and a Top Layer named .top. Read everything
       known of the Screen from .base. Forward .base_place by property and is_writeable_base_area
       by def, each from .base, and forward nothing else of a Layer.

    2. Keep no Write before any write, and none after only the Terminal's Replies.

    3. Fail an assert before any Byte goes out, on any write made before the Terminal replies, even
       one of no Char.

    4. In str_write_base_tb, take each Write through a new Layer made from .base as a trial.
       Assert the Write can be made, then take the same Write into .base itself, and only then
       write the Bytes to the Terminal. Fail an assert before any Byte goes out on a Write that
       cannot be made, and leave the Shadow as it was.

    5. In is_writable_place_after_strs, take the Write through a new Layer, drop that Layer, and say
       yes only when the Cursor ends inside the Writable Area. Say no to a Char into the last Column
       with nothing after it, and yes to a Backspace or a Return after it.

    6. Call .top off when its Place is 1 by 1, as at the start, and on once str_write_top_tb has
       written through it. In str_write_top_tb, take each Write through a new Layer made from .top
       while .top is on, else from .base, as a trial. Assert the Write can be made. Turn .top on
       at the Place and Text Styles of .base while it is off, then take the same Write into .top
       itself. Leave .base as it was, its Place and its Text Styles too.

    7. In undo_top_tb, write nothing while .top is off. Else walk the Terminal Cursor from where
       .top has it over each Cell of .top, row by row, assert that .base wrote that Cell, and write
       the Base Layer's Char there, and guess nothing. Then put the Terminal Cursor and the Text
       Styles where .base has them, even when .top holds no Cell, and turn .top off by clear_layer.

    8. In clear_layer, forget the Layer's Writes and Text Styles, and shrink its Place to 1 by 1.

    9. Say a Layer is_writeable_area only when every Cell of the Area, from the Cursor east for the
       width and south for the height that the caller gives, is a Cell where a Char may be written.

    10. Say a Layer is_shadowed_area only when the Layer has written every Cell of the Area, from
        the Cursor east for the width and south for the height that the caller gives.

    11. In shadow_read_data_else, take a Cursor Reply into .top while .top is on, else into .base.
        Take a Screen size Reply into .base, and into .top too while .top is on. Never turn an
        off .top on by a Reply.

    12. In form_leap_back, spell a step West by CUB_X along the Row, never a Return, counted from the
        last Column while the Cursor waits to wrap. Spell nothing for a step of 0. Assert that the
        step is 0 or more and that the Row matches. Let the Shadow cope with a Pn after ⎋[ and
        before A B C D, and assert on a Pn of 0.

    13. Refuse ⎋[⇧L through the Top Layer, since the Top Layer as yet cannot undo a Row Insert. In
        str_write_top_tb, fail an assert before any Byte goes out on a Str holding ⎋[⇧L. In
        str_write_base_tb, fail an assert before any Byte goes out on a Str holding ⎋[⇧L while .top
        is on, and take every other Write as before.
```
