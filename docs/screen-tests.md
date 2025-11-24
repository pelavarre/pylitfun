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

    ⎋7 cursor-checkpoint  ⎋8 cursor-revert (defaults to Y 1 X 1)
    ⎋C terminal-reset  ⎋L terminal-confuse
    ⎋⇧D \n  ⎋⇧E \r↓ else \r\n  ⎋⇧M ↑ else south-row-delete

The famous Csi ⎋[ Outputs are ⎋[ ⇧ @ ABCDE GHIJKLM P ST Z and ⎋[ D H LM Q

    ⎋[⇧A ↑  ⎋[⇧B ↓  ⎋[⇧C →  ⎋[⇧D ←
    ⎋[I ⌃I  ⎋[⇧Z ⇧Tab
    ⎋[D row-leap  ⎋[⇧G column-leap  ⎋[⇧H row-column-leap

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

The famous Osc ⎋] and Csi ⎋[ Output Calls and Input Replies are

    ⎋]11;?⌃G call for ⎋]11;RGB⇧:{r}/{g}/{b}⌃G

    ⎋[5N call for reply ⎋[0N
    ⎋[6N call for reply ⎋[{y};{x}⇧R  ⎋[18T call for reply ⎋[8;{rows};{columns}T

The famous Csi ⎋[ Inputs, apart from the Replies, are

    ⎋[>{f};{x};{y}⇧M release  ⎋[>{f};{x};{y}M press  ⎋[⇧M{b}{x}{y} press/release

## Results

Our results shown above are as seen at macOS Terminal. The Terminal Emulations of macOS iTerm2 and Google Cloud Shell are different

Our loop-back is impure on purpose. If you type out a repeat count before your Input, then we'll repeat your Input that many times, and write it purely. So when you need to see pure effects, you can type a digit 1 and then your Input and you do test the pure effects. But when you don't type out repeat count, we more guess what you mean, try to help you out

| Input   | Emulation               | Platforms |
|---------|-------------------------|-----------|
|  ⎋C     |  ⎋[3⇧J ⎋[⇧H ⎋[2⇧J       | (all)     |
|  ⎋L     |  ⎋[⇧H                   | (all)     |
|  ⎋['⇧}  |  one ⎋[D ⎋[⇧@ per row   | (all)     |
|  ⎋['⇧~  |  one ⎋[⇧P ⎋[⇧@ per row  | (all)     |

<!--

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/screen-tests.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
