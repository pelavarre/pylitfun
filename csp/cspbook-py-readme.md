# pylitfun / ... / cspbook-py-readme.md

What should the CLI be for speaking with a CSP Program, when you've got Python on your desk in place of Lisp?

How about like this?

Twenty-two Demos.

1

Ask what you can do.

    % ./csp/cspbook.py

    cspbook.py -i
    cspbook.py -c CTR
    cspbook.py -c CLOCK
    cspbook.py -c VMC

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
    Csp Python 0.4.196 (main, 2026-06-24)
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
    ['__doc__', 'STOP', 'X1', 'X1.A', 'X2', 'CTR', 'CLOCK', 'CLOCK.A', 'CLOCK.B', 'VMS', 'VMS.A', 'VMS.B', 'CH5A', 'CH5B', 'X1.B', 'CH5C', 'VMCT', 'VMC', 'VMCRED', 'VMS2', 'COPYBIT']
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
    ['__doc__', 'STOP', 'X1', 'X1.A', 'X2', 'CTR', 'CLOCK', 'CLOCK.A', 'CLOCK.B', 'VMS', 'VMS.A', 'VMS.B', 'CH5A', 'CH5B', 'X1.B', 'CH5C', 'VMCT', 'VMC', 'VMCRED', 'VMS2', 'COPYBIT']
    csp>

    csp> X1.A??
    ["coin", "STOP"]
    csp>

    csp> X1.A
    coin
    STOP
    csp>

7

Run a Csp Process through 4 Events.

    csp> X2??
    ["coin", ["choc", ["coin", ["choc", "STOP"]]]]
    csp>

    csp> X2
    coin
    choc
    coin
    choc
    STOP
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
    STOP
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
    csp>

10

Run another Csp Process that loops, but defined in terms of a local name "X" for the Process.

    csp> CLOCK.B??
    {"X": ["tick", "X"]}
    csp>

    csp> CLOCK.B
    tick

    tick

    tick
    > ^C
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

    coin
    > ^C
    csp>

12

Run another Csp Process that loops through more than one Event, but while defined in terms of a local name "X" for the Process.

    csp> VMS.B??
    {"X": ["coin", ["choc", "X"]]}
    csp>

    csp> VMS.B
    coin
    choc

    coin
    choc

    coin
    choc
    > ^C
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
    out2p
    > ^C
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
    out1p
    > ^C
    csp>

15

Speak of the empty Csp Process as a Choice between no Events.

    csp> STOP??
    {}
    csp>

    csp> STOP
    STOP
    csp>

16

Run a Csp Process that stops in a couple of different ways.

    csp> X1.B??
    {"up": "STOP", "right": ["right", "up", "STOP"]}
    csp>

    csp> X1.B
    up
    STOP
    csp>

    csp> X1.B
    right
    right
    up
    STOP
    csp>

17

Run a Csp Process that loops over a choice of a couple of sequences.

    csp> CH5C??
    ["in5p", {"out1p": ["out1p", "out1p", "out2p", "CH5C"], "out2p": ["out1p", "out2p", "CH5C"]}]
    csp>

    csp> CH5C
    in5p
    out1p
    out1p
    out1p
    out2p

    in5p
    out2p
    out1p
    out2p

    in5p
    out1p
    out1p
    out1p
    > ^C
    csp>

18

Run another Csp Process that loops through a choice of two sequences, but while defined in terms of a local name "X" for the Process.

    csp> VMCT??
    {"X": ["coin", {"choc": "X", "toffee": "X"}]}
    csp>

    csp> VMCT
    coin
    choc

    coin
    toffee

    coin
    > ^C
    csp>

19

Run a Csp Process that loops through choices and choices of many of sequences, indeed even a sequence that ends with a STOP process.`

    csp> VMC??
    {"in2p": {"large": "VMC", "small": ["out1p", "VMC"]}, "in1p": {"small": "VMC", "in1p": {"large": "VMC", "in1p": "STOP"}}}
    csp>

    csp> VMC
    in2p
    large

    in1p
    small

    in2p
    small
    out1p

    in1p
    in1p
    large

    in2p
    large

    in1p
    small

    in2p
    small
    out1p

    in1p
    in1p
    in1p
    STOP
    csp>

20

Run a Csp Process that chooses up front between two sequences, again while defined in terms of a local name "X" for the Process.

    csp> VMCRED??
    {"X": {"coin": ["choc", "X"], "choc": ["coin", "X"]}}
    csp>

    csp> VMCRED
    coin
    choc

    choc
    coin

    coin
    > ^C
    csp>

21

Run a Csp Process that sets up another Csp Process.

    csp> VMS2??
    ["coin", "VMCRED"]
    csp>

    csp> VMS2
    coin

    coin
    choc

    choc
    coin
    > ^C
    csp>

22

Show how looping over a choice of two sequences copies one bit and another and another.

    csp> COPYBIT??
    {"X": {"in.0": ["out.0", "X"], "in.1": ["out.1", "X"]}}
    csp>

    csp> COPYBIT
    in.0
    out.0

    in.1
    out.1

    in.0
    > ^C
    csp>

<!--

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/cspbook-py-readme.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
