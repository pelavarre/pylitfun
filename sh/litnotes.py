#!/usr/bin/env python3

"""
usage: import litnotes

print examples if no Shell Args, else Help if asked for, else return from import
"""


import __main__
import sys
import textwrap


def print_doc_and_exit_zero_if(indexable: str) -> None:
    "Print Examples if no Shell Args, else Help if asked for, else return"

    doc = __main__.__doc__
    assert doc, (doc,)

    helpdoc = textwrap.dedent(doc).strip()

    testdoc = doc[doc.index(indexable) :]
    testdoc = testdoc.removeprefix(indexable)
    testdoc = textwrap.dedent(testdoc).strip()

    for sharg in sys.argv[1:]:
        if sharg == "--":
            break
        if sharg.startswith("--h") and "--help".startswith(sharg):

            print(helpdoc)

            sys.exit(0)

    if not sys.argv[1:]:

        print()
        print(testdoc)
        print()

        sys.exit(0)


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/sh/litnotes.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
