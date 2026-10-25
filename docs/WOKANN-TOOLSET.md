# Wokann DS firmware toolset

Inventory checked on 2026-10-23. This covers Wokann projects relevant to
working with DS/DS Lite system firmware, building FlashMe images, and writing
firmware to a console. It is not a catalog of Wokann's unrelated game,
emulator, and save-file projects.

## Image inspection and research

| Job | Project | What it does | Use and limits |
| --- | --- | --- | --- |
| Inspect, extract, and assemble firmware images | [dsfwtool](https://github.com/Wokann/dsfwtool) | Reports firmware component layout; exports headers and components; compresses, encrypts, decrypts, and assembles images. | Use `dsfwtool -i image.bin` to inspect a dump. It operates on image files; it does not connect to or flash a console. |
| Research original firmware | [dsofw](https://github.com/Wokann/dsofw) | Documents and reconstructs original Nintendo, iQue, and Korean firmware components, addresses, and version differences. | Use to check symbols and original firmware behavior before changing a version-specific patch. It is a research/build project, not a flasher. |
| Build custom firmware | [dscfw](https://github.com/Wokann/dscfw) | Reconstructs historical FlashMe and DS Lite TV-out firmware builds from user-supplied firmware. Includes per-build layouts, source patches, and CRC records. | Use as source/reference when comparing a FlashMe variant. It requires the correct user-supplied base firmware and does not write to hardware. |
| Assemble ARM code | [armips](https://github.com/Wokann/armips) | ARM/MIPS assembler, including Wokann's `flashme-arm-immediate-encoding` branch used by some DS firmware source builds. | Build dependency, not a firmware editor or flasher by itself. This builder pins its source revision in the Dockerfile. |
| Build NDS ROM containers | [ndstool](https://github.com/Wokann/ndstool) | General NDS ROM packaging utility. | It packages homebrew ROMs; it does not inspect or write the internal firmware chip. |

## Firmware editing and flashing

| Job | Project | What it does | Use and limits |
| --- | --- | --- | --- |
| Flash or restore console firmware | [CFW-Suite `fwManager`](https://github.com/Wokann/CFW-Suite/tree/extend/fwManager) | DS homebrew that browses firmware files on the flashcart storage, prepares a selected image, then writes it to internal firmware. It reports progress and the ARM7 writer reads back pages to verify them. | This is the relevant Wokann tool for restoring a full dump with DSpico. The tool itself warns that it can damage the system, requires SL1 to remain shorted during writing, and cannot run in DSi/3DS mode. |
| Edit setup-screen text | [CFW-Suite `guiTool`](https://github.com/Wokann/CFW-Suite/tree/extend/guiTool) | Extracts or reinserts the compressed firmware GUI data used for text changes. | This changes GUI data, not firmware security checks or the firmware layout. A modified image still needs inspection and flashing by a separate tool. |
| Inject an image into a FlashMe installer | [CFW-Suite `FlashMeInjector`](https://github.com/Wokann/CFW-Suite/tree/extend/FlashMeInjector) | Intended to put a custom firmware image into a FlashMe NDS installer for older homebrew environments. | Do not use the current source without independently fixing/reviewing it: its image-copy call is commented out, and the active code clears the target region instead. `fwManager` is the documented recommended route in the project's README. |
| Flash SuperCard device firmware | [superfw-nds-flasher-tool](https://github.com/Wokann/superfw-nds-flasher-tool) | DS homebrew for dumping and flashing SuperCard firmware. | This is for the flashcart's own firmware, not the DS/DS Lite's internal system firmware. It is not a replacement for `fwManager`. |

The CFW-Suite README also mentions `NoFlashMe` as an uninstall option, but
there is no `NoFlashMe` source or binary in the repository tree checked for
this inventory. Do not treat it as a supplied CFW-Suite tool.

## Recommended workflow here

1. Keep a separate original dump for each console. Do not swap dumps between
   consoles: the firmware includes console-specific calibration, wireless,
   and settings data.
2. Inspect each dump with `dsfwtool -i <dump.bin>` and compare the component
   layout, not only whole-file hashes. Whole dumps can differ in console-owned
   data even when their firmware components are identical.
3. For the FlashMe v8a builder, use the existing pinned build environment. The
   project uses Wokann's `armips` and the native `dsfwtool` as build
   dependencies; the pinned `dsfwtool` revision supports `--layout`, so the
   source package Makefiles call it directly.
4. To restore an original dump on a DS/DS Lite, use CFW-Suite `fwManager` from
   the DSpico storage. Keep a copy of the correct console's backup, select its
   complete firmware image, and follow the on-screen prompt to short SL1 and
   keep it short throughout the write. Keep power stable and do not interrupt
   the operation.

## fwManager safety details

These points were checked in CFW-Suite's `fwManager/arm9/source/main.c` and
`fwManager/arm7/source/main.c` on branch `extend`:

- It accepts firmware images from 0x3FE00 through 0x80000 bytes and selects a
  256 KiB or 512 KiB write size from the image's console-type byte.
- Its default menu selection preserves the running console's Wi-Fi
  calibration, Wi-Fi slots, and user settings while applying the selected
  firmware.
- `Flash Complete Firmware` instead writes the complete selected image. For a
  full restore, choose the dump belonging to that same console.
- The source's console-type mismatch refusal is commented out. It displays
  source and target types, but does not enforce a match. It also has a TODO
  noting that the boot CRC check is not implemented. Verify model, region,
  image size, and backup identity yourself before confirming a write.
- The ARM7 writer verifies each page by reading it back. This cannot protect
  against selecting the wrong image or power loss during flashing.
- The firmware write path explicitly tells the user to keep SL1 shorted to
  progress. Follow the program's on-screen procedure exactly.

## Relationship to this builder

This repository creates FlashMe installer and firmware images. It does not
provide a firmware restore writer. `dsfwtool` can inspect, extract, and build
image files, but cannot flash them. For the hardware write/restore operation,
CFW-Suite `fwManager` is the relevant Wokann tool.

The images in `out/firmware/` lack your console's own data. To flash one, keep
`fwManager`'s default `Reserve old ...` options, which keep that data. Never
use `Flash Complete Firmware` with them: it breaks Wi-Fi.

## Source references

- [CFW-Suite README](https://github.com/Wokann/CFW-Suite/blob/extend/README.md)
- [`fwManager` writer](https://github.com/Wokann/CFW-Suite/blob/extend/fwManager/arm9/source/main.c)
- [`fwManager` flash-page code](https://github.com/Wokann/CFW-Suite/blob/extend/fwManager/arm7/source/nvram.c)
- [`FlashMeInjector` source](https://github.com/Wokann/CFW-Suite/blob/extend/FlashMeInjector/source/main.c)
- [dsfwtool README](https://github.com/Wokann/dsfwtool/blob/master/README.md)
- [dscfw README](https://github.com/Wokann/dscfw/blob/main/README.md)
- [dsofw README](https://github.com/Wokann/dsofw/blob/master/README.md)
- [SuperFW tool README](https://github.com/Wokann/superfw-nds-flasher-tool/blob/master/README.md)
- [Wokann armips](https://github.com/Wokann/armips)
