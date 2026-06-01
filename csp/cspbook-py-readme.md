# pylitfun / ... / cspbook-py-readme.md

What should the CLI be for speaking with a CSP Program, when you've got Python on your desk in place of Lisp?

How about like this?

Fourteen Demos.

1

Ask what you can do.

    % ./csp/cspbook.py

    cspbook.py
    cspbook.py --help
    cspbook.py -c CTR
    cspbook.py -c CLOCK1
    cspbook.py -c CH5B
    cspbook.py --

    %

2

Ask for more of a man page.

    % ./csp/cspbook.py --help
    usage: cspbook.py [-h] [-i] [-c CSP]

    exec some lines of csp code

    options:
    -h, --help  show this help message and exit
    -i          prompt and reply, loop loop till quit
    -c CSP      one line of csp code to exec

    quirks:
      trusts you to press Return to continue, ⌃C to cancel, ⌃D to quit
      trusts your Terminal Shell tab to understand ⎋[⇧A ⎋[⇧K
      works like Python works:
        cspbook.py --help
        cspbook.py --
        cspbook.py -i -c ''
          dir()
          dir(__builtins__)

    examples:
      cspbook.py
      cspbook.py --help
      cspbook.py -c STOP
      cspbook.py -c CTR
      cspbook.py -c CLOCK1
      cspbook.py -c CH5B
    %

3

Ask what version you're working with, and quit.

    % ./csp/cspbook.py --
    Csp Python 0.5.67 (main, 2026-05-31)
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
    ['__doc__', 'STOP', 'X1A', 'X2A', 'CTR', 'CLOCK1', 'CLOCK2', 'VMS1', 'VMS2', 'CH5A', 'CH5B', 'X1B', 'CH5C', 'VMCT', 'VMC']
    csp>
    csp> __builtins__.__doc__
    'Built-in procs, and other objects.'
    csp>
    csp> __doc__
    csp>
    csp> ^D
    %

5

Chat to show the source, and run the source.

Run a Csp Process of 1 Event.

    % ./csp/cspbook.py -i -c ''
    csp>
    csp> dir(__builtins__)
    ['__doc__', 'STOP', 'X1A', 'X2A', 'CTR', 'CLOCK1', 'CLOCK2', 'VMS1', 'VMS2', 'CH5A', 'CH5B', 'X1B', 'CH5C', 'VMCT', 'VMC']
    csp>
    csp> U1??
    ["coin", "STOP"]
    csp> U1
    coin
    STOP
    csp>

6

Run a Csp Process through 4 Events.

    csp> U2??
    ["coin", ["choc", ["coin", ["choc", "STOP"]]]]
    csp>
    csp> U2
    coin
    choc
    coin
    choc
    STOP
    csp>

7

Run another Csp Process through 4 Events.

    csp> CTR??
    ["right", "up", "right", "right", "STOP"]
    csp> CTR
    right
    up
    right
    right
    STOP
    csp>

8

Run a Csp Process that loops.

    csp> CLOCK1??
    ["tick", "CLOCK1"]
    csp> CLOCK1
    tick

    tick

    tick
    > ^C
    KeyboardInterrupt
    csp>

9

Run another Csp Process that loops, but defined in terms of a local name "X" for the Process.

    csp> CLOCK2??
    {"X": ["tick", "X"]}
    csp> CLOCK2
    tick

    tick

    tick
    > ^C
    KeyboardInterrupt
    csp>
    csp>

10

Run a Csp Process that loops through more than one Event.

    csp> VMS1??
    ["coin", ["choc", "VMS1"]]
    csp> VMS1
    coin
    choc

    coin
    choc
    > ^C
    KeyboardInterrupt
    csp>

11

Run another Csp Process that loops through more than one Event, and defined in terms of a local name "X" for the Process.

    csp> VMS2??
    {"X": ["coin", ["choc", "X"]]}
    csp> VMS2
    coin
    choc

    coin
    choc

    coin
    > ^C
    KeyboardInterrupt
    csp>

12

Run a Csp Process that loops through four Events.

    csp> CH5A
    in5p
    > ^C
    KeyboardInterrupt
    csp> CH5A??
    ["in5p", "out2p", "out1p", "out2p", "CH5A"]
    csp> CH5A
    in5p
    out2p
    out1p
    out2p

    in5p
    > ^C
    KeyboardInterrupt
    csp>

13

Run another Csp Process that loops through four Events.

    csp> CH5B??
    ["in5p", "out1p", "out1p", "out1p", "out2p", "CH5B"]
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

14

Run an empty Csp Process, and quit chatting.

    csp>
    csp> STOP
    csp>
    csp> ^C
    KeyboardInterrupt
    csp>
    csp> ^D
    %

15

Todo: Run Csp Processes that make choices: X1B, CH5C, VMCT, VMC, etc

<!--

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/cspbook-py-readme.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
