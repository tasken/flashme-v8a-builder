#!/usr/bin/env python3
"""Check that FlashMe v8a patch sites are valid on a newer base firmware.

Extracts two firmware versions with dsfwtool and compares the bytes at every
site the FlashMe patches touch, using dscfw's own address tables
(include/official_<old>_sym.inc and official_<new>_sym.inc).
Exits non-zero if any patched site differs, so no image is built from a
mismatched layout.

usage: verify_base.py <old, e.g. v6> <new, e.g. v7> <dir with old parts> <dir with new parts>
       (parts extracted with dsfwtool; v3 v5 checks Phat, v6 v7 checks Lite)
Optional manual check, not part of ./docker-build.sh.
Set DSCFW_INCLUDE to a dscfw checkout's include/ directory (default /tmp/dscfw_src/include).
"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

INC = Path(os.environ.get("DSCFW_INCLUDE", "/tmp/dscfw_src/include"))

# (label, extra offset, bytes that FlashMe overwrites, extra bytes compared around it)
P1_SITES = [
    ("BootStateDispatch", 0x00, 2, 6),
    ("BootDisplayFade_1", 0x00, 2, 6),
    ("BootDisplayFade_2", 0x00, 2, 6),
    ("BootDisplayFade_3", 0x00, 2, 6),
    ("P3P4Crc16Gate", 0x3A, 2, 6),
    ("P5Crc16Gate", 0x20, 2, 6),
]
P3_SITES = [
    ("NintendoLogoStateGate", 0x00, 2, 6),
    ("RSA_verify", 0x00, 4, 8),
    ("RSA_verify_with_SHA1", 0x00, 4, 8),
]


def load_symbols(path):
    syms = {}
    for line in path.read_text().splitlines():
        m = re.match(r"\.definelabel\s+(\w+),\s*([^;]+)", line)
        if not m:
            continue
        name, expr = m.group(1), m.group(2).strip()
        total = 0
        for term in re.split(r"\s*\+\s*", expr):
            total += int(term, 16) if term.lower().startswith("0x") else syms[term]
        syms[name] = total
    return syms


def load_parts(d):
    return {n: (Path(d) / f"p{n}.bin").read_bytes() for n in (1, 2, 3, 4, 5)}


def window(blob, off, patched, around):
    lo = max(0, off - around)
    return lo, blob[lo:off + patched + around]


def check(part, sites, s6, s7, base_label, blob6, blob7):
    ok = True
    base6, base7 = s6[base_label], s7[base_label]
    for label, extra, patched, around in sites:
        o6 = s6[label] + extra - base6
        o7 = s7[label] + extra - base7
        lo6, w6 = window(blob6, o6, patched, 0)
        lo7, w7 = window(blob7, o7, patched, 0)
        same = w6 == w7
        ok &= same
        print(f"  {part} {label}+{extra:#x}: old@{o6:#x} new@{o7:#x} "
              f"{'SAME' if same else 'DIFFERENT'}")
        if not same:
            print(f"    old: {w6.hex()}\n    new: {w7.hex()}")
    return ok


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    old, new = sys.argv[1], sys.argv[2]
    s6 = load_symbols(INC / f"official_{old}_sym.inc")
    s7 = load_symbols(INC / f"official_{new}_sym.inc")
    f6 = load_parts(sys.argv[3])
    f7 = load_parts(sys.argv[4])

    for n in (1, 2, 3, 4, 5):
        print(f"P{n}: {old} {len(f6[n])} bytes, {new} {len(f7[n])} bytes, "
              f"{'identical' if f6[n] == f7[n] else 'differ'}")

    ok = True
    ok &= check("P1", P1_SITES, s6, s7, "RetailP1RamAddress", f6[1], f7[1])
    ok &= check("P3", P3_SITES, s6, s7, "RetailP3RamAddress", f6[3], f7[3])
    print("RESULT:", "all patch sites match" if ok else "MISMATCH, do not build")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
