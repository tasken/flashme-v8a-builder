#!/usr/bin/env python3
"""Check built installers against the public FlashMe v8a release.

usage: check_installers.py <default out dir> <update out dir>
Default installers must equal the public ones. Update installers must differ
only inside the Phat and Lite image slots.
Optional manual check, not part of ./docker-build.sh.
"""
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLOTS = (0x1434, 0x41234)
EMBED_LEN = 0x3FE00
VARIANTS = ["", "_noauto", "_stealth", "_stealth_noauto"]


def in_slot(i):
    return any(s <= i < s + EMBED_LEN for s in SLOTS)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    default_dir, update_dir = (Path(a) for a in sys.argv[1:])
    ok = True
    with zipfile.ZipFile(ROOT / "inputs/flashme/FlashMe_v8a.zip") as z:
        for suf in VARIANTS:
            pub = z.read(f"flashme{suf}.nds")
            dflt = (default_dir / "installers" / f"flashme_v8a{suf}.nds").read_bytes()
            upd = (update_dir / "installers" / f"flashme_v8a_update{suf}.nds").read_bytes()
            same = dflt == pub
            outside = len(upd) != len(pub) or any(a != b and not in_slot(i) for i, (a, b) in enumerate(zip(pub, upd)))
            print(f"{suf or 'normal':16} default equals public: {same}   update changes only the image slots: {not outside}")
            ok = ok and same and not outside
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
