# About stamp for any package: make -f Makefile -f ../include/about.mk about ABOUT_FIRMWARE=<3|5|6|7> BUILD_VERSION=...
# Stamped images differ from the public ones, so the CRC-16 is recorded, not checked.

ABOUT_FIRMWARE ?=
BUILD_VERSION ?= unknown

define CheckFlashMeCrc
$(call DisplayFlashMeCrc,$(1),$(2))
endef

.PHONY: about
about:
	$(MAKE) -f Makefile patch
	$(ARMIPS) -armimmediate max-imm8 -root . -definelabel AboutFirmware $(ABOUT_FIRMWARE) ../include/about_patch.s
	python3 $(TOOLS_ROOT)/about_text.py $(BUILD_DIR)/p5.bin "$(BUILD_VERSION)"
	$(MAKE) -f Makefile -f ../include/about.mk -o patch -o unpack pack
