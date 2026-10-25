#!/usr/bin/env python3
"""Write "FlashMe v8a" and VERSION over message 163 ("settings lost") in every P5 language table.

usage: about_text.py P5.bin VERSION

Message ids are 0-based; each message keeps its byte length.
"""
import struct
import sys
from pathlib import Path

MAGIC = b"MESGbmg1"
MESSAGE = 163
# Confirms MESSAGE is the expected one.
ENGLISH_PREFIX = b"System settings have been lost. Tap "


def messages(data, base):
    """Return (start, end) byte ranges of every message in the BMG at base."""
    sections = struct.unpack_from("<I", data, base + 0x0C)[0]
    pos = base + 0x20
    inf = dat = None
    for _ in range(sections):
        magic = data[pos:pos + 4]
        size = struct.unpack_from("<I", data, pos + 4)[0]
        if magic == b"INF1":
            inf = pos
        elif magic == b"DAT1":
            dat = pos + 8
        pos += size
    if inf is None or dat is None:
        sys.exit(f"about_text: BMG at offset {base:#x} lacks INF1 or DAT1")
    count, entry_size = struct.unpack_from("<HH", data, inf + 8)
    ranges = []
    for i in range(count):
        start = dat + struct.unpack_from("<I", data, inf + 16 + i * entry_size)[0]
        ranges.append((start, data.index(b"\x00", start)))
    return ranges


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    path, version = Path(sys.argv[1]), sys.argv[2]
    text = f"FlashMe v8a\n{version}".encode("utf-8")

    data = bytearray(path.read_bytes())
    bases = []
    pos = data.find(MAGIC)
    while pos >= 0:
        bases.append(pos)
        pos = data.find(MAGIC, pos + 1)
    if not bases:
        sys.exit(f"about_text: no BMG message tables found in {path}")

    slots = []
    for base in bases:
        ranges = messages(data, base)
        if len(ranges) <= MESSAGE:
            sys.exit(f"about_text: BMG at offset {base:#x} has no message {MESSAGE}")
        start, nul = ranges[MESSAGE]
        total = nul - start + 1  # message bytes including the terminator
        if len(text) + 1 > total:
            sys.exit(
                f"about_text: build string too long for BMG at offset {base:#x} "
                f"({len(text) + 1} bytes > {total} available)"
            )
        slots.append((start, nul, total))
    if not any(data[start:nul].startswith(ENGLISH_PREFIX) for start, nul, _ in slots):
        sys.exit(f"about_text: message {MESSAGE} is not the expected settings-lost message")

    for start, nul, total in slots:
        data[start:nul + 1] = text + b"\x00" * (total - len(text))
        print(f"injected {text!r} at offset {start:#x}")
    path.write_bytes(data)


if __name__ == "__main__":
    main()
