#!/usr/bin/env python3
"""Stamp the installer CRC-16 into the built images and build installers.

usage: finalize.py [--update]
  default   Phat v3 and Lite v6 images -> out/installers/flashme_v8a<variant>.nds
  --update  Phat v5 and Lite v7 images -> out/installers/flashme_v8a_update<variant>.nds

Steps (host side, no Docker needed):
1. For every image in out/firmware, write CRC-16 (init 0xFFFF, poly 0xA001) of
   bytes [0, 0x3FDFE) as a little-endian u16 at 0x3FDFE. The FlashMe installer
   (arm7.c) refuses images whose stored value does not match.
2. Replace the embedded Phat and Lite images inside the matching installer from the
   public FlashMe v8a release (inputs/flashme/FlashMe_v8a.zip) with ours.
   The installers keep their images at fixed offsets, and each slot must already
   hold a valid stamped image before it is replaced.
"""
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
FW = OUT / "firmware"
INST = OUT / "installers"
ZIP = ROOT / "inputs" / "flashme" / "FlashMe_v8a.zip"

CRC_OFFSET = 0x3FDFE
EMBED_LEN = 0x3FE00
SLOTS = {"phat": 0x1434, "lite": 0x41234}
VARIANTS = {
    "": "flashme.nds",
    "_noauto": "flashme_noauto.nds",
    "_stealth": "flashme_stealth.nds",
    "_stealth_noauto": "flashme_stealth_noauto.nds",
}


def crc16(buf):
    c = 0xFFFF
    for x in buf:
        c ^= x
        for _ in range(8):
            c = (c >> 1) ^ 0xA001 if c & 1 else c >> 1
    return c


def check_slot(installer, start, what):
    end = start + CRC_OFFSET
    stored = int.from_bytes(installer[end:end + 2], "little")
    if start + EMBED_LEN > len(installer) or crc16(installer[start:end]) != stored:
        sys.exit(f"{what} slot at {start:#x} does not hold a valid image; is this the public FlashMe v8a release?")


def main():
    update = sys.argv[1:] == ["--update"]
    if sys.argv[1:] not in ([], ["--update"]):
        sys.exit(__doc__)
    models = ("phat_v5", "lite_v7") if update else ("phat_v3", "lite_v6")
    prefix = "flashme_v8a_update" if update else "flashme_v8a"

    images = {}
    for model in models:
        for suf in VARIANTS:
            p = FW / f"flashme_v8a_{model}{suf}.bin"
            if not p.is_file():
                sys.exit(f"missing {p}; run ./docker-build.sh build first")
            d = bytearray(p.read_bytes())
            crc = crc16(d[:CRC_OFFSET])
            d[CRC_OFFSET:CRC_OFFSET + 2] = crc.to_bytes(2, "little")
            p.write_bytes(d)
            images[(model, suf)] = bytes(d[:EMBED_LEN])
            print(f"stamped {p.name}: CRC-16 0x{crc:04X}")

    if not ZIP.is_file():
        sys.exit(f"missing {ZIP.relative_to(ROOT)}; the installers need the public FlashMe v8a release")

    INST.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP) as z:
        for suf, nds in VARIANTS.items():
            data = bytearray(z.read(nds))
            for slot, model in zip(SLOTS, models):
                check_slot(bytes(data), SLOTS[slot], slot)
                img = images[(model, suf)]
                data[SLOTS[slot]:SLOTS[slot] + EMBED_LEN] = img
            out = INST / f"{prefix}{suf}.nds"
            out.write_bytes(data)
            note = "" if update else f", identical to the public installer: {bytes(data) == z.read(nds)}"
            print(f"built {out.relative_to(ROOT)} ({len(data)} bytes){note}")


if __name__ == "__main__":
    main()
