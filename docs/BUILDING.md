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

The build checks every file against these hashes (kept in `tools/inputs.sha256`) and stops if one doesn't match. For firmware dumps, the hash covers only the valid firmware data, the same range the official CRC covers, and sets the private header bytes `0x28` to `0x16F` (MAC address, Wi-Fi calibration) to `FF` first. A dump from another console that differs only in that private data gives the same hash. The FlashMe release zip is hashed whole.

## What gets built

Each installer holds a Phat image and a Lite image. Each image is built from your dump if you have it, or else taken from the FlashMe release.

*   `build`: Phat v3 and Lite v6, the same as the public installers. No dumps needed. With `official_v3.bin` or `official_v6.bin`, it rebuilds that image and stops if it differs from the public one.
*   `build --update`: Phat v5 and Lite v7. Experimental. Needs `official_v5.bin`, `official_v7.bin` or both. A missing dump keeps the public v3 or v6 image, so that installer downgrades the other model. The build warns you.

`build` always cleans first. `./docker-build.sh clean` removes `out/` and `logs/`. The first build from a dump needs internet to set up Docker.

## Variants

Every installer comes in four variants:

*   `flashme_v8a`: starts a Slot-2 (GBA slot) flash cart on its own when the cart is a DS loader (`PASS` or `DSBooter`). Hold A+B+X+Y at power-on to force it, or Select to start the normal firmware
*   `_noauto`: never starts Slot-2 on its own. Hold Select at power-on to start it
*   `_stealth`: skips the backlight fade on a normal boot
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
> Three numbering systems are in play:
> *   **Community naming** (`v3`, `v5`, `v6`, `v7`): the names used in this project and in [dscfw](https://github.com/Wokann/dscfw). The community assigned them from the firmware build date and release order, so they run on from the Phat to the Lite.
> *   **Nintendo's own versions**: Phat v5 is `NTR-WORLD WIDE-Ver5.0`, but the Lite restarts the count, so v6 is `USG-WORLD WIDE-Ver2.0` and v7 is `USG-WORLD WIDE-Ver3.0`. These names combine Nintendo's separate console, region, and version fields; they are not single strings stored in the firmware. `NTR` is the DS Phat and `USG` is the DS Lite. `WORLD WIDE` is the international release, the only one this project supports. The iQue (`CHN [iQue]`) and Korean (`KOR`) firmware are not supported.
> *   **FlashMe's own versions** (`v1` to `v8a`): FlashMe's release history, independent of the two above.
>
> Every public FlashMe Phat image is based on official v3 and every Lite image on official v6. This project adds a Phat image based on official v5 and a Lite image based on official v7.
>
> Match your firmware by build date, not by number. See [DS firmware history](https://wokann.github.io/2026/04/28/DS-firmware-history.html) for details.

## Firmware research

[dsofw](https://github.com/Wokann/dsofw) documents reconstructed original firmware components, their runtime addresses, and the evidence used to identify those addresses. Its v5 and v7 symbol maps match the maps used by this builder. See its [technical notes](https://github.com/Wokann/dsofw/blob/master/TECHNICAL.md) and [v5](https://github.com/Wokann/dsofw/blob/master/include/official_v5_sym.inc) and [v7](https://github.com/Wokann/dsofw/blob/master/include/official_v7_sym.inc) maps.

For the surrounding firmware workflow, including image inspection and hardware restore tools, see [Wokann DS firmware toolset](WOKANN-TOOLSET.md).

## Reporting a problem

Attach `logs/build.log` and [open an issue](https://github.com/tasken/flashme-v8a-builder/issues) with what you ran and what happened.
