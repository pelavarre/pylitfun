# pylitfun / ... / cspbook-py-readme.md

What should the CLI be for speaking with a CSP Program, when you've got Python on your desk in place of Lisp?

How about like this?

Fourteen Demos.

1

Ask what you can do.

    % ./csp/cspbook.py

    cspbook.py -i
    cspbook.py -c CTR
    cspbook.py -c CLOCK.B
    cspbook.py -c CH5B

    %

2

Ask for more of a man page.

    % ./csp/cspbook.py --help
    usage: cspbook.py [-h] [-i] [-c CSP] [--make-tests]

    exec some lines of csp code

    options:
    -h, --help    show this help message and exit
    -i            prompt and reply, loop loop till quit
    -c CSP        one line of csp code to exec
    --make-tests  update:  git diff csp/cspbook-py-readme.md

    quirks:
      trusts you to press Return to continue, ⌃C to cancel, ⌃D to quit
      trusts your Terminal Shell tab to understand ⎋[⇧A ⎋[⇧K
      works like Python works:
        cspbook.py --help
        cspbook.py --
        cspbook.py -i -c ''
          dir()

    examples:
      cspbook.py
      cspbook.py --help
      cspbook.py -c CTR
      cspbook.py -c CLOCK.B
      cspbook.py -c CH5B
    %

3

Ask what version you're working with, and quit.

    % ./csp/cspbook.py --
    Csp Python 0.6.33 (main, 2026-06-07)
    csp>
    csp> ^D
    %

4

Chat without showing the version, and look at the built-in globals, but then quit.

    % ./csp/cspbook.py -i -c ''
    csp>
    csp> dir()
    ['__builtins__', '__doc__']
    csp>
    csp> dir(__builtins__)
    ['__doc__', 'STOP', 'X1.A', 'X2.A', 'CTR', 'CLOCK.A', 'CLOCK.B', 'VMS.A', 'VMS.B', 'CH5A', 'CH5B', 'X1.B', 'CH5C', 'VMCT', 'VMC', 'VMCRED', 'VMS2', 'COPYBIT']
    csp>
    csp> __builtins__.__doc__
    'Built-in procs, and other objects.'
    csp>
    csp> __doc__
    csp>
    csp> ^D
    %

5

Run an empty Csp Process, and quit chatting.

    csp> STOP
    STOP
    csp>

    csp> ^C
    KeyboardInterrupt
    csp>

    csp> ^D
    %

6

Chat to show the source, and run the source.

Run a Csp Process of 1 Event.

    % ./csp/cspbook.py -i -c ''
    csp>
    csp> dir(__builtins__)
    ['__doc__', 'STOP', 'X1.A', 'X2.A', 'CTR', 'CLOCK.A', 'CLOCK.B', 'VMS.A', 'VMS.B', 'CH5A', 'CH5B', 'X1.B', 'CH5C', 'VMCT', 'VMC', 'VMCRED', 'VMS2', 'COPYBIT']
    csp>

    csp> X1.A??
    ["coin", "STOP"]
    csp>

    csp> X1.A
    coin

    csp>

7

Run a Csp Process through 4 Events.

    csp> X2.A??
    ["coin", ["choc", ["coin", ["choc", "STOP"]]]]
    csp>

    csp> X2.A
    coin
    choc
    coin
    choc

    csp>

8

Run another Csp Process through 4 Events.

    csp> CTR??
    ["right", "up", "right", "right", "STOP"]
    csp>

    csp> CTR
    right
    up
    right
    right

    csp>

9

Run a Csp Process that loops.

    csp> CLOCK.A??
    ["tick", "CLOCK.A"]
    csp>

    csp> CLOCK.A
    tick

    tick

    tick
    > ^C
    KeyboardInterrupt
    csp>

10

Run another Csp Process that loops, but defined in terms of a local name "X" for the Process.

    csp> CLOCK.B??
    {"CLOCK.B": {"X": ["tick", "X"]}}
    csp>

    csp> CLOCK.B
    tick

    tick

    tick
    > ^C
    KeyboardInterrupt
    csp>

11

Run a Csp Process that loops through more than one Event.

    csp> VMS.A??
    ["coin", ["choc", "VMS.A"]]
    csp>

    csp> VMS.A
    coin
    choc

    coin
    choc
    > ^C
    KeyboardInterrupt
    csp>

12

Run another Csp Process that loops through more than one Event, and defined in terms of a local name "X" for the Process.

    csp> VMS.B??
    {"VMS.B": {"X": ["coin", ["choc", "X"]]}}
    csp>

    csp> VMS.B
    coin
    choc

    coin
    choc

    coin
    > ^C
    KeyboardInterrupt
    csp>

13

Run a Csp Process that loops through four Events.

    csp> CH5A??
    ["in5p", "out2p", "out1p", "out2p", "CH5A"]
    csp>

    csp> CH5A
    in5p
    out2p
    out1p
    out2p

    in5p
    > ^C
    KeyboardInterrupt
    csp>

14

Run another Csp Process that loops through four Events.

    csp> CH5B??
    ["in5p", "out1p", "out1p", "out1p", "out2p", "CH5B"]
    csp>

    csp> CH5B
    in5p
    out1p
    out1p
    out1p
    out2p

    in5p
    > ^C
    KeyboardInterrupt
    csp>

15

Speak of the empty Csp Process as a Choice between no Events.

    csp> STOP??
    []
    csp>

    csp> STOP
    STOP
    csp>

16

Todo: Run more Csp Processes that make choices: X1.B, CH5C, VMCT, VMC, VMCRED, VMS2, COPYBIT etc

<!--

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/cspbook-py-readme.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
