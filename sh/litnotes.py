#!/usr/bin/env python3

"""
usage: import litnotes

print examples if no Shell Args, else Help if asked for, else return from import
"""


import __main__
import textwrap
import sys


doc = __main__.__doc__
assert doc, (doc,)

helpdoc = textwrap.dedent(doc).strip()

testdoc = doc[doc.index("examples:"):]
testdoc = testdoc.removeprefix("examples:")
testdoc = textwrap.dedent(testdoc).strip()


for sharg in sys.argv[1:]:
    if sharg == "--":
        break
    if sharg.startswith("--h") and "--help".startswith(sharg):

        print(helpdoc)

        sys.exit()


if not sys.argv[1:]:

    print()
    print(testdoc)
    print()

    sys.exit()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/sh/litnotes.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

