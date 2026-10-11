# FlashMe v8a Builder

Build FlashMe v8a installers for the Nintendo DS and DS Lite, including ones for the latest Phat and Lite firmware.

> [!WARNING]
> Flashing firmware can permanently brick your console. These installers are provided as is, with no warranty of any kind, and you use them at your own risk.

> [!NOTE]
> This repository contains no Nintendo firmware, BIOS or prebuilt FlashMe files, only build scripts and patch sources. You supply your own firmware dumps and the public FlashMe release. The images and installers you build contain Nintendo's firmware, so don't share them. This project isn't affiliated with or endorsed by Nintendo. Nintendo DS and DS Lite are trademarks of Nintendo.

## Getting started

1. Put your firmware dumps in `inputs/`, named as in the table below.
1. Run `./docker-build.sh build`, or `./docker-build.sh build --update` for the latest firmware.
1. Find the installers in `out/installers/` and the firmware images in `out/firmware/`.

| File in `inputs/` | What it is | SHA-256 |
|---|---|---|
| `official_v3.bin` | DS Phat firmware, 2005/02/28 | `b53bdcbfaed186137ef30d574c7b89799754eb29db14b24347502ce85ed00e59` |
| `official_v5.bin` | DS Phat firmware, 2005/12/07 (only for `--update`) | `30096cfc584accea91c9ee978b7ba2edecb5b72916ad16f4ddd192741f34ca4d` |
| `official_v6.bin` | DS Lite firmware, 2006/02/05 | `de8606c25734f5e7ed2d6ce2aff4ee613d3b9a20fb071fb6c718b3c2bebcd8da` |
| `official_v7.bin` | DS Lite firmware, 2006/03/08 (only for `--update`) | `c0cdca32a58c33a288a2007fa0593b59fe689173ceeee973488e6aef7899fe06` |
| `flashme/FlashMe_v8a.zip` | The public FlashMe v8a release | `6bb7efdba869a0d8887f176770d2f6c2c3ae880dec94f436bb9f6a8c879c16be` |

The build checks every file against these hashes (kept in `tools/inputs.sha256`) and stops if one doesn't match.

> [!NOTE]
> Three numbering systems are in play:
> *   **Community naming** (`v3`, `v5`, `v6`, `v7`): the names used in this project and in [dscfw](https://github.com/Wokann/dscfw). The community assigned them from the firmware build date and release order, so they run on from the Phat to the Lite.
> *   **Nintendo's own versions**: Phat v5 is `NTR-WORLD WIDE-Ver5.0`, but the Lite restarts the count, so v6 is `USG-WORLD WIDE-Ver2.0` and v7 is `USG-WORLD WIDE-Ver3.0`. `NTR` is the DS Phat and `USG` is the DS Lite. `WORLD WIDE` is the international release, the only one this project supports. The iQue (`CHN [iQue]`) and Korean (`KOR`) firmware are not supported.
> *   **FlashMe's own versions**: `v8a` is the FlashMe release, unrelated to the two above.
>
> Match your firmware by build date, not by number. See [DS firmware history](https://wokann.github.io/2026/04/28/DS-firmware-history.html) for details.

> [!NOTE]
> The installer picks the Phat or Lite image by the console's power-management chip, not by the firmware on it. Late Phat boards (marked CPU20) have the Lite chip, so they receive the Lite image.

## Installers

| File | Contains |
|---|---|
| `flashme_v8a*.nds` | Phat v3 and Lite v6 images. Identical to the public installers |
| `flashme_v8a_update*.nds` | Phat v5 and Lite v7 images. Built with `--update` |

Every installer comes in four variants:

*   `flashme_v8a`: Select boots the stock firmware, and A+B+X+Y starts FlashMe
*   `_noauto`: Select at power-on starts FlashMe
*   `_stealth`: skips the backlight fade on a normal boot
*   `_stealth_noauto`: both of the above

> [!CAUTION]
> This writes to your console's firmware flash. A power loss while flashing can brick it. Use a charged battery, back up your own `firmware.bin` first, and keep the SL1 short ready. There is no warranty of any kind.

> [!WARNING]
> The default installers put the Phat v3 and Lite v6 firmware on your console. On a newer console (Phat v4 or v5, Lite v7) that is a downgrade. Use `--update` for those.

## Building

You need Docker with `sudo` access, and Python 3.

```shell
git clone https://github.com/tasken/flashme-v8a-builder.git
cd flashme-v8a-builder/
./docker-build.sh build
```

`build` cleans first, then builds one set: the default one, or the latest with `--update`. `./docker-build.sh clean` only removes `out/` and `logs/`. The first build needs internet, and later builds reuse the cached image.

The build runs as your own user, so `out/` and `logs/` belong to you.

To check the installers against the public release, copy `out/` aside after the default build, run the update build, then run `python3 tools/check_installers.py <default out> out`.

## Reporting a problem

Attach `logs/build.log` and [open an issue](https://github.com/tasken/flashme-v8a-builder/issues) with what you ran and what happened.

## Credits

*   [dscfw](https://github.com/Wokann/dscfw), [dsfwtool](https://github.com/Wokann/dsfwtool) and the [armips](https://github.com/Wokann/armips) fork by `Wokann` do the build. This project drives them and adds `packages/phat_v5/` and `packages/lite_v7/`
*   [armips](https://github.com/Kingcom/armips) by `Kingcom`
*   FlashMe v8a, by its original authors

## License

GPL-3.0 - see [LICENSE](LICENSE).

Copyright © 2026 `Tasken`.

Nintendo, Nintendo DS and Nintendo DS Lite are trademarks of Nintendo. This project is not affiliated with, endorsed by, or connected to Nintendo in any way, and contains no Nintendo code or data.
