#!/usr/bin/env python3

"""
usage: sed.py ...

copy to output from input, without much buffer, and edit it all on the fly

options:
  -i EXT  add or replace backup copies of the Files edited in place

quirks:
  speaks of Stream EDit as S E D

examples:

  sed -i.bak 's,old,new,g' FILE ...  # edits File's in place

  git show --pretty= --name-only |sed "s,\",$'," |sed "s,\",'," |sed 's,^,echo ,'  # unescapes
  pbpaste |awk '{print $NF}' |sed 's,^,-- ,' |sed 's,$, --,' |pbcopy  # f"-- {line} --" for each

  |sed 's,^  *,,' |sed 's,  *$,,'  # drops Space's from start and end of each line  # |pb strip
  |sed 's,  *, ,g'  # collapses each run of Space's into a single Space  # |pb split join
  |sed "s,.*,'&',"  # enclose each Line inside two ' Apostrophe's  # |pb repr
  |sed 's,^.*$,& = self.&,'  # replaces each Line with Itself and some Text and Itself again
"""

# unescapes tested with:  touch å∫ç && git add å∫ç


import sys

import litnotes

litnotes.print_doc_and_exit_zero_if("examples:")

print("NotImplementedError: sed.py ...", file=sys.stderr)
sys.exit(2)


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/sh/sed.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
