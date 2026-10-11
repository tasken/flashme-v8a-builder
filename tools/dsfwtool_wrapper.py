#!/usr/bin/python3
"""Drop-in dsfwtool for dscfw's FlashMe Makefiles, backed by the native dsfwtool.

dscfw's Makefiles were written for the dsfwtool.exe shipped in dscfw, which has a
--layout option and a few implicit behaviours the public native tool lacks. This
wrapper accepts the exact command lines those Makefiles use:

  extract: dsfwtool -x IN -h ... -pN -decrypt -uncomp OUT ...   (passed through)
  pack:    dsfwtool -c OUT --layout L -h H -p1 -comp -encrypt F ... -s 256K --fill FF

and for packing it reproduces what the old tool did:
  * places the parts in the order given by the layout file, honouring "align";
  * pads every part to the layout alignment, with zeros (the old tool never left FF
    in the gaps between parts);
  * keeps P1/P2 encryption tails as zeros;
  * keeps the stock P3/P4 CRC-16 from the base header (the native tool recalculates it).
Any other pack command line is rejected instead of guessed.
"""
import os
import subprocess
import sys
import tempfile

NATIVE = os.environ.get("DSFWTOOL_NATIVE", "/usr/local/libexec/dsfwtool-native")
ORDER = ["P1", "P2", "P5", "P4", "P3", "FP2", "FP1"]
FH_OFFSET = 0x3F680


def run(*args):
    r = subprocess.run([NATIVE, *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit("dsfwtool failed: %s\n%s%s" % (" ".join(args), r.stdout, r.stderr))


def pad(data, n):
    return data + b"\0" * (-len(data) % n)


def read(path):
    with open(path, "rb") as f:
        return f.read()


def write(path, data):
    with open(path, "wb") as f:
        f.write(data)


def parse_layout(path):
    align = {}
    with open(path) as f:
        for line in f:
            w = line.split("#")[0].split()
            if len(w) >= 4 and w[1] == "auto" and w[2] == "align":
                align[w[0]] = int(w[3], 0)
    return align


def parse_pack(argv):
    """Return (out, layout, parts); parts maps H/P1../FH/FP1/FP2 to (flags, path)."""
    out = layout = None
    parts = {}
    size = fill = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "-c":
            out = argv[i + 1]
            i += 2
        elif a == "--layout":
            layout = argv[i + 1]
            i += 2
        elif a == "-s":
            size = argv[i + 1]
            i += 2
        elif a == "--fill":
            fill = argv[i + 1]
            i += 2
        elif a in ("-h", "-fh", "-p1", "-p2", "-p3", "-p4", "-p5", "-fp1", "-fp2"):
            flags = []
            i += 1
            while argv[i].startswith("-") and argv[i] not in ("-h",):
                flags.append(argv[i])
                i += 1
            parts[a[1:].upper()] = (flags, argv[i])
            i += 1
        else:
            sys.exit("dsfwtool wrapper: unsupported pack argument %r" % a)
    if size != "256K" or (fill or "").upper() != "FF":
        sys.exit("dsfwtool wrapper: only '-s 256K --fill FF' is supported")
    expect = {
        "P1": ["-comp", "-encrypt"], "P2": ["-comp", "-encrypt"],
        "P3": ["-comp", "-flashme"], "P4": ["-comp", "-flashme"], "P5": ["-comp", "-flashme"],
        "FP1": ["-comp"], "FP2": ["-comp"], "FH": [], "H": [],
    }
    if out is None or layout is None or set(parts) != set(expect):
        sys.exit("dsfwtool wrapper: pack needs -c, --layout and all of H P1-P5 FH FP1 FP2")
    for name, flags in expect.items():
        if parts[name][0] != flags:
            sys.exit("dsfwtool wrapper: unsupported flags for %s: %s" % (name, parts[name][0]))
    return out, layout, parts


def pack(argv):
    out, layout, parts = parse_pack(argv)
    align = parse_layout(layout)
    with tempfile.TemporaryDirectory() as tmp:
        w = lambda n: os.path.join(tmp, n)
        files = {}
        for p in ("P1", "P2"):
            run("-" + p.lower(), "-comp", parts[p][1], "-o", w(p + ".c"))
            files[p] = pad(read(w(p + ".c")), 8)
        for p in ("P3", "P4", "P5"):
            run("-" + p.lower(), "-comp", "-flashme", parts[p][1], "-o", w(p + ".c"))
            files[p] = read(w(p + ".c"))
        for p in ("FP1", "FP2"):
            run("-" + p.lower(), "-comp", parts[p][1], "-o", w(p + ".c"))
            files[p] = pad(read(w(p + ".c")), 8)

        pos, off = {}, 0x180
        for n in ORDER:
            a = align.get(n, 8)
            files[n] = pad(files[n], a)
            off = (off + a - 1) // a * a
            pos[n] = off
            off += len(pad(files[n], 8))
            off = (off + a - 1) // a * a
        if off > FH_OFFSET:
            sys.exit("dsfwtool wrapper: layout overflow (0x%X)" % off)

        args = ["-c", out, "-h", parts["H"][1]]
        for n in ORDER:
            path = w(n + ".padded")
            write(path, files[n])
            flags = ["-encrypt"] if n in ("P1", "P2") else []
            args += ["-" + n.lower(), *flags, "--offset", hex(pos[n]), path]
        args += ["-fh", "--offset", hex(FH_OFFSET), parts["FH"][1], "-s", "256K", "--fill", "FF"]
        run(*args)

    image = bytearray(read(out))
    stock_crc = read(parts["H"][1])[4:6]
    image[4:6] = stock_crc
    image[FH_OFFSET + 4:FH_OFFSET + 6] = stock_crc
    write(out, bytes(image))


def main():
    argv = sys.argv[1:]
    if "-c" in argv:
        pack(argv)
    else:
        os.execv(NATIVE, [NATIVE, *argv])


if __name__ == "__main__":
    main()
