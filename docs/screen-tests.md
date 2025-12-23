# screen-tests.md


## Context

Try our tests, for the fun of it  : -)

Launch a loop-back test to write your Keyboard Input Bytes back into your Screen

    % python3 ./litglass.py --


## Tests

Apple macOS Keycap Symbols are ⎋ Esc, ⌃ Control, ⌥ Option/ Alt, ⇧ Shift, ⌘ Command/ Os

However
+ U+005E ^ Circumflex Accent ... is not U+2303 ⌃ Up Arrowhead ... is not U+2191 ↑ Upwards Arrow
+ U+21EA ⇪ Upwards White Arrow From Bar ... is not U+21E7 ⇧ Upwards White Arrow

The famous Control Characters are

    ⌃⇧@ ⌃G ⌃H ⌃J mean \0 \a \b \n, and ⌃[ means \e, also known as ⎋ Esc
    ⇥ Tab means ⌃I \t, and ⏎ Return means ⌃M \r, and ⌫ ⌃? Delete means \b
    ⌃␢ means ⌃⇧@ means \0, and ⌥␢ means \302\240 U+00A0 No-Break Space

The famous Esc ⎋ Byte Pairs are ⎋ 7 8 C L ⇧D ⇧E ⇧M

    ⎋C terminal-reset  ⎋L terminal-confuse
    ⎋7 cursor-checkpoint  ⎋8 cursor-revert (defaults to Y 1 X 1)
    ⎋⇧D \n  ⎋⇧E \r↓ else \r\n  ⎋⇧M ↑ else south-row-delete

The famous Csi ⎋[ Outputs are ⎋[ ⇧ @ ABCDEFGHIJKLM P ST Z and ⎋[ D F H LM Q

    ⎋[⇧A ↑  ⎋[⇧B ↓  ⎋[⇧C →  ⎋[⇧D ←  ⎋[⇧E \r ↓  ⎋[⇧F \r ↑
    ⎋[I ⌃I  ⎋[⇧Z ⇧Tab
    ⎋[D row-leap  ⎋[⇧G column-leap  ⎋[⇧H row-column-leap  ⎋[F row-column-leap

    ⎋[1⇧M rows-delete  ⎋[⇧L rows-insert  ⎋[⇧P chars-delete  ⎋[⇧@ chars-insert
    ⎋[⇧J after-erase  ⎋[1⇧J before-erase  ⎋[2⇧J screen-erase  ⎋[3⇧J scroll-erase
    ⎋[⇧K row-tail-erase  ⎋[1⇧K row-head-erase  ⎋[2⇧K row-erase
    ⎋[⇧S south-rows-insert  ⎋[⇧T north-rows-insert
    ⎋['⇧} cols-insert  ⎋['⇧~ cols-delete

    ⎋[4H inserting  ⎋[4L replacing  ⎋[⇧?2004H paste-wrap  ⎋[⇧?2004L paste-unwrap
    ⎋[?25H cursor-show  ⎋[?25L -hide  ⎋[6 Q -bar  ⎋[4 Q -skid  ⎋[ Q -unstyled
    ⎋[⇧?1049H screen-alt  ⎋[⇧?1049L screen-main

    ⎋[1M bold  ⎋[2M dim  ⎋[4M underline  ⎋[7M reverse  ⎋[44M on-blue  ⎋[103M on-yellow
    ⎋[91M red  ⎋[34M blue  ⎋[32M green  ⎋[38;5;130M orange  ⎋[48;5;130M on-orange
    ⎋[M plain  ⎋[22M bold-not-dim-not  ⎋[39M color-not  ⎋[49M on-not

<!-- ⎋[1M "bold", "increased intensity" -->
<!-- ⎋[2M "faint", "decreased intensity", "second colour" -->
<!-- ⎋[7M "reverse video", "inverse video", "negative image" -->
<!-- ⎋[27M "positive image" -->

The famous Csi ⎋[ and Osc ⎋] Outputs sent for reply as Inputs are

    ⎋[5N send for reply ⎋[0N
    ⎋[6N send for reply ⎋[{y};{x}⇧R  ⎋[18T send for reply ⎋[8;{rows};{columns}T
    ⎋]11;⇧?⌃G send for {r}/{g}/{b}  # 11 On-Backlight  # 10 Color  # 12 Cursor

The famous Csi ⎋[ Inputs, apart from the Reply Inputs, are

    ⎋[>{f};{x};{y}⇧M press  ⎋[>{f};{x};{y}M release  ⎋[⇧M{b}{x}{y} press/release

<!-- todo: Say more of Osc Ps 12 112, esp Ps 12 crashes of Terminal Tabs at Google Cloud Shell -->
<!-- todo: Beware of printf '\033]12;''#ff0000''\007' && sleep 1 && printf '\033]112\007' -->


## Results

Our results shown above are as seen at macOS Terminal. Results at macOS iTerm2 and Google Cloud Shell are different

We run four kinds of loop-back for Terminal Inputs

a ) Echoes without writing, for negative repeat counts <br>
b ) Echoes and lots of details, for a repeat count of exactly -1 <br>
c ) Echoes and writes, for a repeat count of 0 <br>
d ) Echoes and cooks and writes, for positive repeat counts and for no repeat count<br>

| Input   | Cooked Form             | Platforms |
|---------|-------------------------|-----------|
|  ⎋C     |  ⎋[3⇧J ⎋[⇧H ⎋[2⇧J       | (all)     |
|  ⎋L     |  ⎋[⇧H                   | (all)     |
|  ⎋['⇧}  |  one ⎋[D ⎋[⇧@ per row   | (all)     |
|  ⎋['⇧~  |  one ⎋[⇧P ⎋[⇧@ per row  | (all)     |

⎋ [ ' 4 ⇧} is what you type to get four of our Csi ⇧} emulations.
⎋ [ ' 8 ⇧~ is what you type to get eight of our Csi ⇧~ emulations


## Eggs

  --egg=enter to launch loop back with no setup

  --egg=exit to quit loop back with no teardown

  --egg=repr to loop the Repr, not the Str

  --egg=scroll to scroll into Scrollback. Also launches in Alt Screen, not Main Screen

  --egg=sigint for ⌃C to raise KeyboardInterrupt. Also defines the ⏎ Return Key to work like ⌃J rather than like ⌃M


<!--

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/screen-tests.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
