# FlashMe v8a Builder

Build FlashMe v8a installers for the Nintendo DS and DS Lite, including ones for the latest Phat and Lite firmware.

> [!WARNING]
> Flashing firmware can permanently brick your console. These installers are provided as is, with no warranty of any kind, and you use them at your own risk.

> [!NOTE]
> This repository contains no Nintendo firmware, BIOS or prebuilt FlashMe files, only build scripts and patch sources. You supply your own firmware dumps and the public FlashMe release. The images and installers you build contain Nintendo's firmware, so don't share them. This project isn't affiliated with or endorsed by Nintendo. Nintendo DS and DS Lite are trademarks of Nintendo.

> [!IMPORTANT]
> The `--update` build is experimental. It is not an official FlashMe release, so back up your own firmware before flashing it.

> [!CAUTION]
> This writes to your console's firmware flash. A power loss while flashing can brick it. Use a charged battery, back up your own `firmware.bin` first, and keep the SL1 short ready. There is no warranty of any kind.

> [!WARNING]
> The default installers put the Phat v3 and Lite v6 firmware on your console. On a newer console (Phat v4 or v5, Lite v7) that is a downgrade. Use `--update` for those.

> [!NOTE]
> The installer picks the Phat or Lite image by the console's power-management chip, not by the firmware on it. Late Phat boards (marked CPU20) have the Lite chip, so they receive the Lite image.

## Documentation

*   [Building](docs/BUILDING.md): inputs, build commands, installers, version numbers and reporting a problem.

## Credits

*   [dscfw](https://github.com/Wokann/dscfw), [dsfwtool](https://github.com/Wokann/dsfwtool) and the [armips](https://github.com/Wokann/armips) fork by `Wokann` do the build. This project drives them and adds `packages/phat_v5/` and `packages/lite_v7/`
*   [armips](https://github.com/Kingcom/armips) by `Kingcom`
*   FlashMe v8a, by its original authors

## License

GPL-3.0 - see [LICENSE](LICENSE).

Copyright © 2026 `Tasken`.

Nintendo, Nintendo DS and Nintendo DS Lite are trademarks of Nintendo. This project is not affiliated with, endorsed by, or connected to Nintendo in any way, and contains no Nintendo code or data.
