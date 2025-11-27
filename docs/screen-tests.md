# screen-tests.md

## Context

Try our tests, for the fun of it  : -)

Launch a loop-back test to write your Keyboard Input Bytes back into your Screen

    % python3 ./litglass.py --

## Tests

Apple macOS Keycap Symbols are ⎋ Esc, ⌃ Control, ⌥ Option/ Alt, ⇧ Shift, ⌘ Command/ Os

    ⌃G ⌃H ⌃J mean \a \b \n, and ⌃[ means \e, also known as ⎋ Esc
    ⇥ Tab means ⌃I \t, and ⏎ Return means ⌃M \r, and ⌫ ⌃? Delete means \b

The famous Esc ⎋ Byte Pairs are ⎋ 7 8 C L ⇧D ⇧E ⇧M

    ⎋C terminal-reset  ⎋L terminal-confuse
    ⎋7 cursor-checkpoint  ⎋8 cursor-revert (defaults to Y 1 X 1)
    ⎋⇧D \n  ⎋⇧E \r↓ else \r\n  ⎋⇧M ↑ else south-row-delete

The famous Csi ⎋[ Outputs are ⎋[ ⇧ @ ABCDEFGHIJKLM P ST Z and ⎋[ D F H LM Q

    ⎋[⇧A ↑  ⎋[⇧B ↓  ⎋[⇧C →  ⎋[⇧D ←  ⎋[⇧E \r ↓  ⎋[⇧F \r ↑
    ⎋[I ⌃I  ⎋[⇧Z ⇧Tab
    ⎋[D row-leap  ⎋[⇧G column-leap  ⎋[⇧H row-column-leap  ⎋[F row-column-leap

    ⎋[1⇧M rows-delete  ⎋[⇧L rows-insert  ⎋[⇧P chars-delete  ⎋[⇧@ chars-insert
    ⎋[⇧J after-erase  ⎋[1⇧J before-erase  ⎋[2⇧J screen-erase  ⎋[3⇧J scrollback-erase
    ⎋[⇧K row-tail-erase  ⎋[1⇧K row-head-erase  ⎋[2⇧K row-erase
    ⎋[⇧T south-rows-delete  ⎋[⇧S north-rows-delete
    ⎋['⇧} cols-insert  ⎋['⇧~ cols-delete

    ⎋[4H insert  ⎋[4L replace
    ⎋[?25H cursor-show  ⎋[?25L cursor-hide  ⎋[6 Q bar  ⎋[4 Q skid  ⎋[ Q unstyled

    ⎋[1M bold  ⎋[4M underline  ⎋[7M reverse/inverse
    ⎋[31M red  ⎋[32M green  ⎋[34M blue  ⎋[38;5;130M orange
    ⎋[M plain

    ⎋[⇧?1049H screen-alt  ⎋[⇧?1049L screen-main
    ⎋[⇧?2004H paste-on  ⎋[⇧?2004L paste-off

The famous Csi ⎋[ and Osc ⎋] Output Calls and Reply Inputs are

    ⎋[5N call for reply ⎋[0N
    ⎋[6N call for reply ⎋[{y};{x}⇧R  ⎋[18T call for reply ⎋[8;{rows};{columns}T
    ⎋]11;?⌃G call for ⎋]11;RGB⇧:{r}/{g}/{b}⌃G

The famous Csi ⎋[ Inputs, apart from the Reply Inputs, are

    ⎋[>{f};{x};{y}⇧M press  ⎋[>{f};{x};{y}M release  ⎋[⇧M{b}{x}{y} press/release

## Results

Our results shown above are as seen at macOS Terminal. The Terminal Emulations of macOS iTerm2 and Google Cloud Shell are different

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

<!--

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/screen-tests.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
