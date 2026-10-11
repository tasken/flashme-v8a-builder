#!/usr/bin/env python3
"""Compare built FlashMe Lite images (v6 base vs v7 base) with their stock firmware.

Optional manual check, not part of ./docker-build.sh. Needs a CHECK_DIR (default out/check)
holding {v6,v7} (stock parts) and img/{v6,v7}<variant> (parts extracted from the built
images with dsfwtool, from out/firmware). It proves that, per variant:
  * P4/P5 are unchanged stock data,
  * P3 differs from stock only at the three patch sites,
  * the retained P1 inside FP1 differs from stock only at the patch sites,
  * the retained P2 inside FP2 is byte for byte stock,
  * the patched bytes written on the v7 base equal the ones on the v6 base,
  * the FlashMe-owned stubs (primary P1/P2, FP1/FP2 prefixes) are identical on both bases.
"""
import os
import sys
from pathlib import Path

import verify_base as v

ROOT = Path(__file__).resolve().parent.parent
CHK = Path(os.environ.get("CHECK_DIR", ROOT / "out" / "check"))
PREFIX = 0x400
VARIANTS = ["", "_noauto", "_stealth", "_stealth_noauto"]


def rd(p):
    return Path(p).read_bytes()


def diffs(a, b):
    n = min(len(a), len(b))
    return {i: b[i] for i in range(n) if a[i] != b[i]}


def site_ranges(syms, sites, base, stealth):
    out = {}
    for label, extra, patched, _ in sites:
        if stealth and label.startswith("BootDisplayFade_") or (stealth and label == "BootStateDispatch"):
            continue
        off = syms[label] + extra - syms[base]
        out[label] = range(off, off + patched)
    return out


def main():
    s6 = v.load_symbols(v.INC / "official_v6_sym.inc")
    s7 = v.load_symbols(v.INC / "official_v7_sym.inc")
    stock = {"v6": v.load_parts(CHK / "v6"), "v7": v.load_parts(CHK / "v7")}
    syms = {"v6": s6, "v7": s7}
    ok = True

    def check(cond, msg):
        nonlocal ok
        ok &= bool(cond)
        print(("  PASS " if cond else "  FAIL ") + msg)

    for suf in VARIANTS:
        stealth = "stealth" in suf
        print(f"== variant '{suf or 'normal'}'")
        parts = {}
        patched = {}
        for k in ("v6", "v7"):
            d = CHK / "img" / f"{k}{suf}"
            p = {n: rd(d / f"p{n}.bin") for n in (1, 2, 3, 4, 5)}
            p["fp1"], p["fp2"], p["fh"] = rd(d / "fp1.bin"), rd(d / "fp2.bin"), rd(d / "fh.bin")
            parts[k] = p
            st = stock[k]
            check(p[4] == st[4], f"{k}: P4 equals stock")
            check(p[5] == st[5], f"{k}: P5 equals stock")

            p3d = diffs(st[3], p[3])
            r3 = site_ranges(syms[k], v.P3_SITES, "RetailP3RamAddress", stealth)
            allowed = {i for r in r3.values() for i in r}
            check(len(p[3]) == len(st[3]) and set(p3d) <= allowed,
                  f"{k}: P3 differs from stock only at the 3 patch sites ({len(p3d)} bytes)")

            fp1 = p["fp1"][PREFIX:]
            p1d = diffs(st[1], fp1)
            r1 = site_ranges(syms[k], v.P1_SITES, "RetailP1RamAddress", stealth)
            allowed = {i for r in r1.values() for i in r}
            check(len(fp1) == len(st[1]) and set(p1d) <= allowed,
                  f"{k}: retained P1 differs from stock only at the patch sites ({len(p1d)} bytes)")
            check(p["fp2"][PREFIX:] == st[2], f"{k}: retained P2 is byte for byte stock")

            patched[k] = {
                "p3": {lab: bytes(p[3][o] for o in r) for lab, r in site_ranges(syms[k], v.P3_SITES, "RetailP3RamAddress", stealth).items()},
                "p1": {lab: bytes(fp1[o] for o in r) for lab, r in site_ranges(syms[k], v.P1_SITES, "RetailP1RamAddress", stealth).items()},
            }

        check(patched["v6"] == patched["v7"], "patched bytes identical on v6 and v7 base")
        for key in (1, 2):
            check(parts["v6"][key] == parts["v7"][key], f"primary P{key} stub identical on both bases")
        check(parts["v6"]["fp1"][:PREFIX] == parts["v7"]["fp1"][:PREFIX], "FP1 stub identical on both bases")
        check(parts["v6"]["fp2"][:PREFIX] == parts["v7"]["fp2"][:PREFIX], "FP2 stub identical on both bases")
        for lab, b in patched["v7"]["p3"].items():
            print(f"    P3 {lab}: {b.hex()}")
        for lab, b in patched["v7"]["p1"].items():
            print(f"    P1 {lab}: {b.hex()}")

    print("RESULT:", "all checks pass" if ok else "FAILURES, do not flash")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
