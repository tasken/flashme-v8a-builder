#!/usr/bin/env python3
"""Check input files against tools/inputs.sha256.

usage: check_inputs.py <file under inputs/> [...]
usage: check_inputs.py --print <file under inputs/> [...]

Firmware dumps hash only the valid firmware range, with the private header
bytes (0x28..0x170: MAC address, Wi-Fi calibration and similar) set to FF, so a
dump that differs only in console-private data gives the same hash. The range
ends are the same ones dscfw uses for its official CRC-32 check. Any other file
(the FlashMe release zip) is hashed whole.
"""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = (0x28, 0x170)
RANGE_END = {
    "official_v3.bin": 0x3F6F8,
    "official_v5.bin": 0x3F7B8,
    "official_v6.bin": 0x3F9B8,
    "official_v7.bin": 0x3F760,
}


def digest(name):
    data = (ROOT / "inputs" / name).read_bytes()
    end = RANGE_END.get(name)
    if end is None:
        return hashlib.sha256(data).hexdigest()
    if len(data) < end:
        sys.exit(f"inputs/{name} is too short to be this firmware")
    blob = bytearray(data[:end])
    blob[PRIVATE[0]:PRIVATE[1]] = b"\xff" * (PRIVATE[1] - PRIVATE[0])
    return hashlib.sha256(blob).hexdigest()


def main():
    args = sys.argv[1:]
    show = args[:1] == ["--print"]
    names = args[1:] if show else args
    if not names:
        sys.exit(__doc__)
    expected = {}
    for line in (ROOT / "tools" / "inputs.sha256").read_text().splitlines():
        if line.strip():
            h, n = line.split(None, 1)
            expected[n.strip()] = h
    ok = True
    for name in names:
        got = digest(name)
        if show:
            print(f"{got}  {name}")
        elif got != expected.get(name):
            print(f"inputs/{name} does not match the expected SHA-256 in tools/inputs.sha256.", file=sys.stderr)
            ok = False
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
