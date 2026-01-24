#!/usr/bin/env python3

"""
usage: vim.py [--help] [-u PROFILE]

read files, accept edits, write files, in the way of classic Vim

options:
  -h, --help  show this help message and exit
  -u VIMRC    edit after running a file before args (default: ~/.vimrc)

quirks:
  classic Vim declines ':n' when asked at the last File

examples:
  emacs --no-splash -nw --eval '(menu-bar-mode -1)'  # run with less Spam
  emacs -Q -nw --eval '(menu-bar-mode -1)' "$@"  # run with less Local Reconfiguration & Spam
  emacs ~/.emacs  # show that the Local Reconfiguration loads well enough to let you edit it

examples:

  vim  # run on an Empty Buffer with less Spam
  vim -u /dev/null  # run with less Local Reconfiguration
  vim ~/.vimrc  # show that the Local Reconfiguration loads well enough to let you edit it
  pbpaste >./pb && vim ./pb && pbcopy <./pb  # run on a Proxy of the Paste Buffer

  vim +$ Makefile  # open up at end of file, not start of file
  vim +':set background=light' Makefile  # choose Lightmode, when they didn't
  vim +':set background=dark' Makefile  # choose Darkmode, when they didn't

  printf '\033]11;?\007' && cat - >/dev/null  # ask the Terminal to disclose Darkmode/ Lightmode
"""

# todo: surface Vim options akin to |less -FIRX
# todo: run 'vim.py ...' to mean correct to fit Lightmode/ Darkmode


import sys

import litnotes


print("NotImplementedError: vim.py ...", file=sys.stderr)
sys.exit(2)


# :helpgrep
# :helpgrep CTRL-U
# :cnext

# demo +123
# demo +:123
# demo +startinsert
# vim.py to take:  pathname:123
# vim.py to take:  pathname:123:4


# solve
#
#    % bash -c vim </dev/null
#    Vim: Warning: Input is not from a terminal
#    :q%
#    %
#


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/sh/vim.py
# copied from:  git clone https://github.com/pelavarre/byoverbs.git
