#!/usr/bin/env python3
"""Check the firmware dumps and the FlashMe v8a release in inputs/.

usage: check_inputs.py official_v3.bin [...]
usage: check_inputs.py --print official_v3.bin [...]
usage: check_inputs.py --release

Firmware dumps are checked against tools/inputs.sha256. Their hash covers only
the valid firmware range, with the private header bytes (0x28..0x170: MAC
address, Wi-Fi calibration and similar) set to FF, so a dump that differs only
in console-private data gives the same hash. The range ends are the same ones
dscfw uses for its official CRC-32 check.

The release is the four public installers in inputs/, either inside a ZIP or as
loose .nds files. Each installer is found by its own SHA-256, so file
names, ZIP layout and compression do not matter.
"""
import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = (0x28, 0x170)
RANGE_END = {
    "official_v3.bin": 0x3F6F8,
    "official_v5.bin": 0x3F7B8,
    "official_v6.bin": 0x3F9B8,
    "official_v7.bin": 0x3F760,
}
RELEASE_DIR = ROOT / "inputs"
RELEASE = {
    "flashme.nds": "34185b496ec3775d007bfd572158f78fb14c041b86041330efda65f9d61ad500",
    "flashme_noauto.nds": "3c090be0efe17f011d50cf235920af840b12381db4f52eb7b29397e3246f8d6f",
    "flashme_stealth.nds": "30eca61737385f4c192109cad68e8ba476a78b8cf898164a9ac075ad2bc4c163",
    "flashme_stealth_noauto.nds": "3fda81e5d1a9e30306f978e0e6c64fd178ff13512dcddaa618780f9ae562e48a",
}


def release_files():
    if not RELEASE_DIR.is_dir():
        return []
    return sorted(p for p in RELEASE_DIR.iterdir() if p.suffix.lower() in (".zip", ".nds"))


def release_installers():
    """Return the four public installers, by name, from the files in inputs/."""
    names = {digest: name for name, digest in RELEASE.items()}
    found = {}

    def accept(data):
        name = names.get(hashlib.sha256(data).hexdigest())
        if name:
            found[name] = data

    for path in release_files():
        if path.suffix.lower() == ".nds" and path.stat().st_size <= 2 * 1024 * 1024:
            accept(path.read_bytes())
        elif path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as archive:
                for entry in archive.infolist():
                    if entry.filename.lower().endswith(".nds") and entry.file_size <= 2 * 1024 * 1024:
                        accept(archive.read(entry))
    missing = sorted(set(RELEASE) - found.keys())
    if missing:
        sys.exit("inputs/ needs the FlashMe v8a release (ZIP or .nds files); missing: "
                 + ", ".join(missing))
    return found


def digest(name):
    end = RANGE_END.get(name)
    if end is None:
        sys.exit(f"{name} is not one of: {', '.join(RANGE_END)}")
    data = (ROOT / "inputs" / name).read_bytes()
    if len(data) < end:
        sys.exit(f"inputs/{name} is too short to be this firmware")
    blob = bytearray(data[:end])
    blob[PRIVATE[0]:PRIVATE[1]] = b"\xff" * (PRIVATE[1] - PRIVATE[0])
    return hashlib.sha256(blob).hexdigest()


def main():
    args = sys.argv[1:]
    if args == ["--release"]:
        release_installers()
        print("FlashMe v8a release: all four installers found.")
        return
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
