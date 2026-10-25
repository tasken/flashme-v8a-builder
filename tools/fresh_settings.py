#!/usr/bin/env python3
"""Write blank user settings into firmware images, so they start first-boot setup.

usage: fresh_settings.py IMAGE.bin [...]

Both 0x100-byte blocks at 0x3FE00 are zero except the version and the CRC-16
(init 0xFFFF, poly 0xA001) of the first 0x70 bytes at 0x72.
"""
import sys
from pathlib import Path

from finalize import crc16

SETTINGS_OFFSET = 0x3FE00
SETTINGS_SIZE = 0x100
CRC_DATA_SIZE = 0x70
CRC_OFFSET = 0x72
VERSION = 5


def fresh_block():
    block = bytearray(SETTINGS_SIZE)
    block[0:2] = VERSION.to_bytes(2, "little")
    block[CRC_OFFSET:CRC_OFFSET + 2] = crc16(block[:CRC_DATA_SIZE]).to_bytes(2, "little")
    return bytes(block)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for name in sys.argv[1:]:
        path = Path(name)
        image = bytearray(path.read_bytes())
        if len(image) < SETTINGS_OFFSET + 2 * SETTINGS_SIZE:
            sys.exit(f"{path.name}: image is too small; need at least {SETTINGS_OFFSET + 2 * SETTINGS_SIZE} bytes")
        image[SETTINGS_OFFSET:SETTINGS_OFFSET + 2 * SETTINGS_SIZE] = fresh_block() * 2
        path.write_bytes(image)
        print(f"wrote fresh user settings to {path.name}")


if __name__ == "__main__":
    main()
