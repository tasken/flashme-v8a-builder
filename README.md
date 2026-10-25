# FlashMe v8a Builder

Build FlashMe v8a installers for the Nintendo DS and DS Lite, including ones for the latest Phat and Lite firmware.

> [!CAUTION]
> Flashing can permanently brick your console. Back up your own `firmware.bin`, use a charged battery and keep the SL1 short ready. Provided as is, with no warranty.

> [!IMPORTANT]
> Pick the build for your console. The default installers flash Phat v3 and Lite v6, which downgrades a newer console. The `--update` installers flash Phat v5 and Lite v7 and are experimental. Phat boards marked CPU20 receive the Lite image.

> [!NOTE]
> This repository contains no Nintendo firmware. You supply your own dumps, and the images you build contain Nintendo's firmware, so don't share them.

## Documentation

*   [Building](docs/BUILDING.md): inputs, build commands, installers, version numbers and reporting a problem.
*   [Wokann DS firmware toolset](docs/WOKANN-TOOLSET.md): related tools for inspecting, building, researching, and restoring DS firmware.

## Credits

*   [dscfw](https://github.com/Wokann/dscfw), [dsfwtool](https://github.com/Wokann/dsfwtool) and the [armips](https://github.com/Wokann/armips) fork by `Wokann` do the build. This project drives them and adds `packages/phat_v5/`, `packages/lite_v7/` and the opt-in About stamp in `packages/include/`
*   [armips](https://github.com/Kingcom/armips) by `Kingcom`
*   FlashMe v8a, by its original authors

## License

GPL-3.0 - see [LICENSE](LICENSE).

Copyright © 2026 `Tasken`.

Nintendo, Nintendo DS and Nintendo DS Lite are trademarks of Nintendo. This project is not affiliated with, endorsed by, or connected to Nintendo in any way, and contains no Nintendo code or data.
