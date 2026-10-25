# Building

You need Python 3. Building from a firmware dump also needs Docker with `sudo`.

## Getting started

1. Put the FlashMe v8a release in `inputs/flashme/`. Dumps are optional: put any you have in `inputs/`, named as in the table below.
1. Run `./docker-build.sh build`, or `./docker-build.sh build --update` for the latest firmware.
1. Find the installers in `out/installers/` and the firmware images in `out/firmware/`.

```shell
git clone https://github.com/tasken/flashme-v8a-builder.git
cd flashme-v8a-builder/
./docker-build.sh build
```

> [!WARNING]
> Flash the installers, not the images in `out/firmware/`. An installer keeps your console's own data: MAC address, Wi-Fi calibration, Wi-Fi settings and user settings. A raw image has none of it. See [Firmware only](#firmware-only).

| File in `inputs/` | What it is | SHA-256 |
|---|---|---|
| `official_v3.bin` | Phat, 2005/02/28 | `c8eefb282b96fc6e86c8957dbab95fef5fd3fbd72afd6faaa5b9f0e9bc59bd92` |
| `official_v5.bin` | Phat, 2005/12/07 | `ef4583cc7d1b670f156d0bd63185113c7ef1985077b46bea1d1b483399f6f3d4` |
| `official_v6.bin` | Lite, 2006/02/05 | `414ba292764d085fabccf62d4f9d5dfc497365ef7175154ef3c1c6c64588479d` |
| `official_v7.bin` | Lite, 2006/03/08 | `28c285959d12e3f1ac0980bccd7aa13823f9ff8000b76c83c118bbfff0abcf46` |
| `flashme/FlashMe_v8a.zip` | FlashMe v8a release | `6bb7efdba869a0d8887f176770d2f6c2c3ae880dec94f436bb9f6a8c879c16be` |

The build stops if a file doesn't match its hash. Dump hashes skip each console's private data (header bytes `0x28` to `0x16F`), so any console's dump of the same firmware matches.

## What gets built

Each installer holds a Phat image and a Lite image. Each image is built from your dump if you have it, or else taken from the FlashMe release.

*   `build`: Phat v3 and Lite v6, the same as the public installers. No dumps needed. With `official_v3.bin` or `official_v6.bin`, it rebuilds that image and stops if it differs from the public one.
*   `build --update`: Phat v5 and Lite v7. Experimental. Needs `official_v5.bin`, `official_v7.bin` or both. A missing dump keeps the public v3 or v6 image, so that installer downgrades the other model. The build warns you.

`build` always cleans first. `./docker-build.sh clean` removes `out/` and `logs/`. The first build from a dump needs internet to set up Docker.

## Variants

Every installer comes in four variants:

*   `flashme_v8a`: starts a Slot-2 (GBA slot) flash cart on its own when the cart is a DS loader (`PASS` or `DSBooter`). Hold A+B+X+Y at power-on to force it, or Select to start the normal firmware
*   `_noauto`: never starts Slot-2 on its own. Hold Select at power-on to start it
*   `_stealth`: no backlight fade when the normal firmware starts
*   `_stealth_noauto`: both of the above

FlashMe has no menu. It runs whatever DS code the Slot-2 cart holds, such as a flash cart's menu. With nothing to run (empty slot or a GBA game), the screen stays white. Hold power to switch off; nothing is written.

To check that the update installers change only the firmware images: copy `out/` aside after `build`, run `build --update`, then run `python3 tools/check_installers.py <copy> out`.

## Firmware only

`--firmware-only` builds only `out/firmware/`, without installers. You must type `yes` to start it.

The images in `out/firmware/` have blank user settings, so they start first-boot setup. Never flash one whole: it would break Wi-Fi and reset your settings. Use [CFW-Suite](https://github.com/Wokann/CFW-Suite) `fwManager`, keep its default `Reserve old ...` options, and do not choose `Flash Complete Firmware`. See [fwManager safety details](WOKANN-TOOLSET.md#fwmanager-safety-details).

## About stamp

`--about` marks the images built from your dumps, so it needs at least one. On the Settings page, Select shows `FlashMe v8a` and the commit, such as `e2279a8` (`-dirty` with local changes). The stamp reuses the "settings have been lost" message, so that message shows the stamp instead.

## Version numbers

> [!NOTE]
> `v3`, `v5`, `v6` and `v7` are community names, used here and in [dscfw](https://github.com/Wokann/dscfw), ordered by firmware build date. They are not Nintendo's versions (Phat v5 is `NTR-WORLD WIDE-Ver5.0`, Lite v6 and v7 are `USG-WORLD WIDE-Ver2.0` and `Ver3.0`), and not FlashMe's versions (`v1` to `v8a`).
>
> Public FlashMe images use Phat v3 and Lite v6. This project adds Phat v5 and Lite v7. Only the international (`WORLD WIDE`) firmware is supported, not iQue or Korean.
>
> Match your firmware by build date, not by number. See [DS firmware history](https://wokann.github.io/2026/04/28/DS-firmware-history.html).

## Firmware research

[dsofw](https://github.com/Wokann/dsofw) documents the original firmware and its addresses. Its [v5](https://github.com/Wokann/dsofw/blob/master/include/official_v5_sym.inc) and [v7](https://github.com/Wokann/dsofw/blob/master/include/official_v7_sym.inc) maps match the ones used here. See also its [technical notes](https://github.com/Wokann/dsofw/blob/master/TECHNICAL.md) and the [Wokann DS firmware toolset](WOKANN-TOOLSET.md).

## Reporting a problem

Attach `logs/build.log` and [open an issue](https://github.com/tasken/flashme-v8a-builder/issues) with what you ran and what happened.
