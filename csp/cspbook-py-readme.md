<!-- omit in toc -->
# pylitfun / ... / cspbook-py-readme.md

What should the CLI be for speaking with a CSP Program, when you've got Python on your desk in place of Lisp?

How about like this?

- [1. Processes](#1-processes)
  - [1.1 Introduction](#11-introduction)
    - [1.1.1 Prefix](#111-prefix)
    - [1.1.2 Recursion](#112-recursion)
    - [1.1.3 Choice](#113-choice)
    - [1.1.4 Mutual recursion](#114-mutual-recursion)

## 1. Processes

### 1.1 Introduction

Five examples.

<!-- The /cspbook.pdf has no numbered examples inside its '1.1 Introduction'. We have these. -->

**X1**

Ask what you can do.

    % ./csp/cspbook.py

    cspbook.py --
      dir()
      dir(__builtins__)
      __builtins__.__doc__

    cspbook.py -c CTR
    cspbook.py -c CLOCK
    cspbook.py -c VMC

    %

**X2**

Ask for more of a man page.

    % ./csp/cspbook.py --help
    usage: cspbook.py [-h] [-V] [-i] [-c CODELINE] [--make-tests]

    exec some lines of csp code

    options:
      -h, --help     show this help message and exit
      -V, --version  print the version and exit
      -i             prompt and reply, loop loop till quit
      -c CODELINE    one line of csp code to exec
      --make-tests   update:  git diff csp/cspbook-py-readme.md

    quirks:
      trusts you to press Return to continue, ⌃C to cancel, ⌃D to quit
      trusts your Terminal Shell tab to understand ⎋[⇧A ⎋[⇧K
      lots works like Python works:
        cspbook.py --help
        cspbook.py -i -c ''

    examples:

      cspbook.py --
        dir()
        dir(__builtins__)
        __builtins__.__doc__

      cspbook.py -c CTR
      cspbook.py -c CLOCK
      cspbook.py -c VMC
    %

**X3**

Ask what version you're working with, and quit.

    % ./csp/cspbook.py --
    Csp Python 0.12.28 (main, 2026-06-30)
    csp>
    csp> ^D
    %

**X4**

Chat without showing the version, and look at the built-in globals, but then quit.

    % ./csp/cspbook.py -i -c ''
    csp>
    csp> dir()
    ['__builtins__', '__doc__']
    csp>
    csp> dir(__builtins__)
    ['__doc__', 'STOP', 'X1', 'X1.A', 'X2', 'CTR', 'CLOCK', 'CLOCK.A', 'CLOCK.B', 'VMS', 'VMS.A', 'VMS.B', 'CH5A', 'CH5B', 'X1.B', 'CH5C', 'VMCT', 'VMC', 'VMCRED', 'VMS2', 'COPYBIT', 'RUN', 'DD', 'O', 'L']
    csp>
    csp> __builtins__.__doc__
    'Built-in procs, and other objects.'
    csp>
    csp> __doc__
    csp>
    csp> ^D
    %

**X5**

Run an empty Csp Process, and quit chatting.

    % ./csp/cspbook.py -i -c ''
    csp>
    csp> STOP
    STOP
    csp>
    csp> ^C
    KeyboardInterrupt
    csp>
    csp> ^D
    %

#### 1.1.1 Prefix

**X1**

Chat to show the source, and run the source.

Run a Csp Process of 1 Event.

    csp> X1.A??
    ["coin", "STOP"]
    csp>

    csp> X1.A
    coin
    STOP
    csp>

**X2**

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

**X3**

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

#### 1.1.2 Recursion

<!-- The /cspbook.pdf presents this example without numbering it, before its example numbered as 'X1'. -->

**X0**

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

**X1**

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

**X2**

<!-- The /cspbook.pdf presents these two examples as two parts of its 'X2'. -->

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
    > ^C
    csp>

**X3**

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
    out1p
    out2p

    in5p
    > ^C
    csp>

**X4**

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
    out1p
    out1p
    out2p

    in5p
    > ^C
    csp>

#### 1.1.3 Choice

**X1**

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

**X2**

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
    > ^C
    csp>

**X3**

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
    choc

    coin
    toffee

    coin
    > ^C
    csp>

**X4**

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

**X5**

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
    choc

    choc
    coin

    coin
    > ^C
    csp>

**X6**

Run a Csp Process that sets up another Csp Process.

    csp> VMS2??
    ["coin", "VMCRED"]
    csp>

    csp> VMS2
    coin

    choc
    coin

    coin
    choc

    choc
    coin

    coin
    choc

    choc
    > ^C
    csp>

**X7**

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
    out.0

    in.1
    out.1

    in.0
    > ^C
    csp>

**X8**

Show again a Process walking through indefinitely many indistinguishable variations on an Event.

    csp> RUN??
    ["x", "RUN"]
    csp>

    csp> RUN
    x

    x

    x
    > ^C
    csp>

Speak of the empty Csp Process as a Choice between no Events.

    csp> STOP??
    {}
    csp>

    csp> STOP
    STOP
    csp>

#### 1.1.4 Mutual recursion

todo1: Tests of 1.1.4 Mutual recursion

<!--

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/cspbook-py-readme.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
