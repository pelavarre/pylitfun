import bdb
import pdb
import signal
import subprocess
import sys
import traceback
import types
import unicodedata


def main() -> None:
    try:
        try_main()
    except BaseException:  # KeyboardInterrupt  # SystemExit
        # TerminalBoss.selves[-1].__exit__()  # todo6:
        excepthook(*sys.exc_info())


def try_main() -> None:  # noqa  # C901 too complex

    trial = 2

    if trial == 1:

        for code in range(0x80, 0xFF + 1):
            obytes = bytes([code])

            try:
                obytes.decode()
                assert False, (code,)
            except UnicodeDecodeError:
                pass

            subprocess.run(["pbcopy"], input=obytes, check=True)

            run = subprocess.run(["pbpaste"], check=True, stdout=subprocess.PIPE)

            stdout = run.stdout
            decode = stdout.decode()
            u_nnnn = f"U+{ord(decode):04X}"

            if decode == "\uf8ff":
                utitle = "Apple Logo = Last of Private Use Area (PUA)"
                isprintableish = True
            else:
                isprintableish = decode.isprintable()
                try:
                    utitle = unicodedata.name(decode).title()
                except ValueError:
                    utitle = "(no title)"

            assert len(decode) == 1, (len(decode), decode, hex(code))

            text = rf"printf '\{code:02X}' | pbcopy && pbpaste |hexdump -C"

            mode = 0

            if mode == 1:
                if isprintableish:
                    print(f"{text}  # ==> {stdout!r} {u_nnnn} {decode} {utitle}")
                else:
                    print(f"{text}  # ==> {stdout!r} {u_nnnn} (unprintable) {utitle}")

            if mode == 2:
                print(decode)

    if trial == 2:

        # decode_by_obyte = dict()
        #
        # for code in range(0x00, 0xFF + 1):
        #     obyte = bytes([code])
        #     print(obyte)
        #
        #     subprocess.run(["pbcopy"], input=obyte, check=True)
        #     run = subprocess.run(["pbpaste"], check=True, stdout=subprocess.PIPE)
        #     stdout = run.stdout
        #     decode = stdout.decode()
        #
        #     assert obyte not in decode_by_obyte, (obyte, hex(code))
        #     decode_by_obyte[obyte] = decode
        #
        # pprint.pprint(decode_by_obyte)
        # sys.exit(2)

        decode_by_obyte = {
            b"\x80": "Ä",
            b"\x81": "Å",
            b"\x82": "Ç",
            b"\x83": "É",
            b"\x84": "Ñ",
            b"\x85": "Ö",
            b"\x86": "Ü",
            b"\x87": "á",
            b"\x88": "à",
            b"\x89": "â",
            b"\x8a": "ä",
            b"\x8b": "ã",
            b"\x8c": "å",
            b"\x8d": "ç",
            b"\x8e": "é",
            b"\x8f": "è",
            b"\x90": "ê",
            b"\x91": "ë",
            b"\x92": "í",
            b"\x93": "ì",
            b"\x94": "î",
            b"\x95": "ï",
            b"\x96": "ñ",
            b"\x97": "ó",
            b"\x98": "ò",
            b"\x99": "ô",
            b"\x9a": "ö",
            b"\x9b": "õ",
            b"\x9c": "ú",
            b"\x9d": "ù",
            b"\x9e": "û",
            b"\x9f": "ü",
            b"\xa0": "†",
            b"\xa1": "°",
            b"\xa2": "¢",
            b"\xa3": "£",
            b"\xa4": "§",
            b"\xa5": "•",
            b"\xa6": "¶",
            b"\xa7": "ß",
            b"\xa8": "®",
            b"\xa9": "\ufffd",  # 'Replacement Character'
            b"\xaa": "™",
            b"\xab": "´",
            b"\xac": "¨",
            b"\xad": "≠",
            b"\xae": "Æ",
            b"\xaf": "Ø",
            b"\xb0": "∞",
            b"\xb1": "±",
            b"\xb2": "≤",
            b"\xb3": "≥",
            b"\xb4": "¥",
            b"\xb5": "µ",
            b"\xb6": "∂",
            b"\xb7": "∑",
            b"\xb8": "∏",
            b"\xb9": "π",
            b"\xba": "∫",
            b"\xbb": "ª",
            b"\xbc": "º",
            b"\xbd": "Ω",
            b"\xbe": "æ",
            b"\xbf": "ø",
            b"\xc0": "¿",
            b"\xc1": "¡",
            b"\xc2": "¬",
            b"\xc3": "√",
            b"\xc4": "ƒ",
            b"\xc5": "≈",
            b"\xc6": "∆",
            b"\xc7": "«",
            b"\xc8": "»",
            b"\xc9": "…",
            b"\xca": "\xa0",
            b"\xcb": "À",
            b"\xcc": "Ã",
            b"\xcd": "Õ",
            b"\xce": "Œ",
            b"\xcf": "œ",
            b"\xd0": "–",
            b"\xd1": "—",
            b"\xd2": "“",
            b"\xd3": "”",
            b"\xd4": "‘",
            b"\xd5": "’",
            b"\xd6": "÷",
            b"\xd7": "◊",
            b"\xd8": "ÿ",
            b"\xd9": "Ÿ",
            b"\xda": "⁄",
            b"\xdb": "€",
            b"\xdc": "‹",
            b"\xdd": "›",
            b"\xde": "ﬁ",
            b"\xdf": "ﬂ",
            b"\xe0": "‡",
            b"\xe1": "·",
            b"\xe2": "‚",
            b"\xe3": "„",
            b"\xe4": "‰",
            b"\xe5": "Â",
            b"\xe6": "Ê",
            b"\xe7": "Á",
            b"\xe8": "Ë",
            b"\xe9": "È",
            b"\xea": "Í",
            b"\xeb": "Î",
            b"\xec": "Ï",
            b"\xed": "Ì",
            b"\xee": "Ó",
            b"\xef": "Ô",
            b"\xf0": "\uf8ff",
            b"\xf1": "Ò",
            b"\xf2": "Ú",
            b"\xf3": "Û",
            b"\xf4": "Ù",
            b"\xf5": "ı",
            b"\xf6": "ˆ",
            b"\xf7": "˜",
            b"\xf8": "¯",
            b"\xf9": "˘",
            b"\xfa": "˙",
            b"\xfb": "˚",
            b"\xfc": "¸",
            b"\xfd": "˝",
            b"\xfe": "˛",
            b"\xff": "ˇ",
        }

        for code in range(0x00, 0x7F + 1):
            obyte = bytes([code])
            assert obyte not in decode_by_obyte, (obyte, hex(code))
            decode_by_obyte[obyte] = obyte.decode()

        for code in range(0, 0xFFFF + 1):

            obytes = bytes([code // 0x100, code % 0x100])
            print(obytes)

            h = obytes[:1]
            t = obytes[-1:]

            if (code // 0x100) >= 0x80:
                try:
                    obytes.decode()
                    continue
                except UnicodeDecodeError:
                    pass

            subprocess.run(["pbcopy"], input=obytes, check=True)
            run = subprocess.run(["pbpaste"], check=True, stdout=subprocess.PIPE)
            stdout = run.stdout
            decode = stdout.decode()

            assert len(decode) == 2, (len(decode), decode, hex(code))

            dh = decode_by_obyte[h]
            dt = decode_by_obyte[t]
            if code != 0xA9A9:
                if (code // 0x100) == 0xA9:
                    if (code % 0x100) >= 0x80:
                        dh = "\u00a9"  # b"\xc2\xa9".decode()
                if (code % 0x100) == 0xA9:
                    if (code // 0x100) >= 0x80:
                        dt = "\u00a9"  # b"\xc2\xa9".decode()

                # U+00A9 © 'Copyright Sign'

            assert decode[0] == dh, (decode[0], decode, dh, h, hex(code))
            assert decode[-1] == dt, (decode[1], decode, dt, t, hex(code))


#
# Amp up Import Traceback
#


assert sys.__stderr__ is not None  # refuses to run headless
with_stderr = sys.stderr


assert int(0x80 + signal.SIGINT) == 130  # discloses the Nonzero Exit Code for after ⌃C SigInt


def excepthook(  # ) -> ...:
    exc_type: type[BaseException] | None,  # aka .type
    exc_value: BaseException | None,  # aka .exc_obj aka .value
    exc_traceback: types.TracebackType | None,  # aka .exc_tb aka .traceback aka .tb
) -> None:
    """Run at Process Exit"""

    if exc_type is SystemExit:
        return

        # consciously no traceback.print_exception
        # happens without sys.flags.interactive when not called via sys.excepthook

    # Quit loudly for KeyboardInterrupt

    if exc_type is KeyboardInterrupt:
        pass

    # Quit quietly, early now, if BdbQuit

    if exc_type is bdb.BdbQuit:
        with_stderr.write("BdbQuit\n")
        sys.exit(130)  # 0x80 + signal.SIGINT  # same as for KeyboardInterrupt

    # Print the usual 'Traceback (most recent call last):', & Traceback, & Assert

    print(file=with_stderr)
    print(file=with_stderr)  # twice

    traceback.print_exception(exc_type, value=exc_value, tb=exc_traceback, file=with_stderr)

    print(file=with_stderr)
    print(file=with_stderr)  # twice

    # Launch the Post-Mortem Debugger

    if exc_value is not None:
        if not hasattr(sys, "last_exc"):
            setattr(sys, "last_exc", exc_value)  # ducks out of confusing pdb.pm()

            # todo: figure out when this does and doesn't happen

    if exc_traceback is not None:
        if not hasattr(sys, "last_traceback"):
            setattr(sys, "last_traceback", exc_traceback)  # ducks out of confusing pdb.pm()

            # todo: figure out when this does and doesn't happen

    print(">" ">" "> pdb.pm()", file=with_stderr)  # (3 * ">") spelled unlike a Git Conflict
    pdb.pm()


main()
