#!/usr/bin/env python3

"""
usage: sed.py ...

copy to output from input, without much buffer, and edit it all on the fly

options:
  -i EXT  add or replace backup copies of the Files edited in place

quirks:
  speaks of Stream EDit as S E D

examples:

  pbpaste |awk '{print $NF}' |sed 's,^,-- ,' |sed 's,$, --,' |pbcopy  # f"-- {line} --" for each

  sed -i.bak 's,old,new,g' FILE ...  # edits File's in place
  git show --pretty= --name-only |sed "s,\",$'," |sed "s,\",'," |sed 's,^,echo ,'  # unescapes

  |sed 's,^  *,,' |sed 's,  *$,,'  # drops Space's from start and end of each line  # |pf strip
  |sed 's,  *, ,g'  # collapses each run of Space's into a single Space  # |pf split join
  |sed "s,.*,'&',"  # enclose each Line inside two ' Apostrophe's  # |pf repr
  |sed 's,^.*$,& = self.&,'  # replaces each Line X with XYXZ
"""

# unescapes tested with:  touch å∫ç && git add å∫ç


import sys

import litnotes

litnotes.print_doc_and_exit_zero_if("examples:")

print("NotImplementedError: sed.py ...", file=sys.stderr)
sys.exit(2)

# vs tradition of 'sed.py --' meaning:  pbpaste |awk '{print $NF}' |sed 's,^,-- ,' |etc etc etc


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/py/sed.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
