#!/usr/bin/env python3
"""Stamp the installer CRC-16 into the firmware images and build the installers.

usage: finalize.py [--update] [--about] [--firmware-only]
  default          Phat v3 and Lite v6 -> out/installers/flashme_v8a<variant>.nds
  --update         Phat v5 and Lite v7 -> out/installers/flashme_v8a_update<variant>.nds
  --about          the built images carry the About stamp, so they are not
                   compared with the public release
  --firmware-only  stop after out/firmware and build no installers

Each model uses the images ./docker-build.sh built into out/firmware. A model
with none there (its dump was not supplied) uses the public image from
inputs/flashme/FlashMe_v8a.zip instead: Phat v3 or Lite v6.

Steps (host side, no Docker needed):
1. Write the public images of every model that was not built to out/firmware,
   padded with FF to 256K.
2. For every image in out/firmware, write CRC-16 (init 0xFFFF, poly 0xA001) of
   bytes [0, 0x3FDFE) as a little-endian u16 at 0x3FDFE. The FlashMe installer
   (arm7.c) refuses images whose stored value does not match.
3. Default build without --about: every built image must equal the public one.
   This runs whenever the FlashMe release is present, even with --firmware-only.
4. Unless --firmware-only, replace the embedded Phat and Lite images inside the
   matching installer from the public release with ours. The installers keep
   their images at fixed offsets, and each slot must already hold a valid
   stamped image before it is replaced.
"""
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
FW = OUT / "firmware"
INST = OUT / "installers"
ZIP = ROOT / "inputs" / "flashme" / "FlashMe_v8a.zip"

IMAGE_LEN = 0x40000
CRC_OFFSET = 0x3FDFE
EMBED_LEN = 0x3FE00
SLOTS = {"phat": 0x1434, "lite": 0x41234}
NAMES = {"phat": "Phat", "lite": "Lite"}
PUBLIC_VERSIONS = {"phat": "v3", "lite": "v6"}
UPDATE_VERSIONS = {"phat": "v5", "lite": "v7"}
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


def was_built(model):
    found = [(FW / f"flashme_v8a_{model}{suf}.bin").is_file() for suf in VARIANTS]
    if any(found) and not all(found):
        sys.exit(f"out/firmware holds only some {model} images; run ./docker-build.sh build again")
    return all(found)


def main():
    args = sys.argv[1:]
    if not set(args) <= {"--update", "--about", "--firmware-only"} or len(set(args)) != len(args):
        sys.exit(__doc__)
    update = "--update" in args
    about = "--about" in args
    firmware_only = "--firmware-only" in args
    versions = UPDATE_VERSIONS if update else PUBLIC_VERSIONS
    built = {slot: was_built(f"{slot}_{versions[slot]}") for slot in SLOTS}

    if (not firmware_only or not all(built.values())) and not ZIP.is_file():
        sys.exit(f"missing {ZIP.relative_to(ROOT)}; the installers and the public images need the FlashMe v8a release")
    public = {}
    if ZIP.is_file():
        with zipfile.ZipFile(ZIP) as z:
            public = {suf: z.read(nds) for suf, nds in VARIANTS.items()}
        for data in public.values():
            for slot, start in SLOTS.items():
                check_slot(data, start, slot)

    FW.mkdir(parents=True, exist_ok=True)
    images = {}
    for slot, start in SLOTS.items():
        name = NAMES[slot]
        if built[slot]:
            model = f"{slot}_{versions[slot]}"
            stamp = " with the About stamp" if about else ""
            print(f"{name}: built from inputs/official_{versions[slot]}.bin{stamp}")
        else:
            model = f"{slot}_{PUBLIC_VERSIONS[slot]}"
            print(f"{name}: public {name} {PUBLIC_VERSIONS[slot]} image (no inputs/official_{versions[slot]}.bin)")
            if update:
                print(f"warning: the {name} slot stays on official {PUBLIC_VERSIONS[slot]}; "
                      f"installing it on a {name} {versions[slot]} console downgrades it")
        for suf in VARIANTS:
            p = FW / f"flashme_v8a_{model}{suf}.bin"
            if not built[slot]:
                image = bytearray(b"\xff" * IMAGE_LEN)
                image[:EMBED_LEN] = public[suf][start:start + EMBED_LEN]
                p.write_bytes(image)
            d = bytearray(p.read_bytes())
            crc = crc16(d[:CRC_OFFSET])
            d[CRC_OFFSET:CRC_OFFSET + 2] = crc.to_bytes(2, "little")
            p.write_bytes(d)
            images[(slot, suf)] = bytes(d[:EMBED_LEN])
            print(f"stamped {p.name}: CRC-16 0x{crc:04X}")
            if built[slot] and not update and not about and public:
                if images[(slot, suf)] != public[suf][start:start + EMBED_LEN]:
                    sys.exit(f"{p.name} differs from the image in the public release; see logs/build.log")

    if firmware_only:
        print("--firmware-only: no installers built")
        return

    INST.mkdir(parents=True, exist_ok=True)
    prefix = "flashme_v8a_update" if update else "flashme_v8a"
    for suf, nds in VARIANTS.items():
        data = bytearray(public[suf])
        for slot, start in SLOTS.items():
            data[start:start + EMBED_LEN] = images[(slot, suf)]
        out = INST / f"{prefix}{suf}.nds"
        out.write_bytes(data)
        note = "" if update else f", identical to the public installer: {bytes(data) == public[suf]}"
        print(f"built {out.relative_to(ROOT)} ({len(data)} bytes){note}")


if __name__ == "__main__":
    main()
