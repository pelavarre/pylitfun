#!/usr/bin/env python3

"""
usage: emacs.py [-h] [-Q] [-q] [--no-splash] [-nw] [--script PROFILE] [--eval COMMAND]
                [FILE ...]

read files, accept edits, write files, in the way of classic Gnu Emacs

positional arguments:
  FILE                     a file to edit (default: None)

options:
  -h, --help               show this help message and exit
  -Q, --quick              run as if --no-init-file --no-splash etc
  -q, --no-init-file       don't default to run '~/.emacs' after args
  --no-splash              start with an empty file, not a file of help
  -nw, --no-window-system  stay inside this terminal, don't open another terminal
  --script PROFILE         edit after running a file after args (default: ~/.emacs)
  --eval COMMAND           another elisp command to run after args and after --script

examples:
  emacs --no-splash -nw --eval '(menu-bar-mode -1)'  # run on an Empty Buffer with less Spam
  emacs -Q -nw --eval '(menu-bar-mode -1)' "$@"  # run with less Local Reconfiguration & Spam
  emacs ~/.emacs  # show that the Local Reconfiguration loads well enough to let you edit it
  pbpaste >./pb && emacs ... ./pb && pbcopy <./pb  # run on a Proxy of the Paste Buffer
"""


import sys

import litnotes


print("NotImplementedError: emacs.py ...", file=sys.stderr)
sys.exit(2)


# solve
#
#    % bash -c emacs </dev/null
#    Emacs: standard input is not a tty
#    Zsh: exit 1     bash -c emacs < /dev/null
#    %
#


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/sh/emacs.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
