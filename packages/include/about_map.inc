; About stamp addresses. Set AboutFirmware (3, 5, 6 or 7) first; only these four differ per version.
.if AboutFirmware == 3
.definelabel AboutKeyLatchAddress,                    RetailP1RamAddress + 0x0000415c
.definelabel AboutHeaderRenderFunction,               RetailP1RamAddress + 0x000021ac
.definelabel AboutScreenTableAddress,                 RetailP1RamAddress + 0x0000ffb4
.definelabel AboutScreenAddress,                      RetailP1RamAddress + 0x00011e04
.elseif AboutFirmware == 5
.definelabel AboutKeyLatchAddress,                    RetailP1RamAddress + 0x0000415c
.definelabel AboutHeaderRenderFunction,               RetailP1RamAddress + 0x000021ac
.definelabel AboutScreenTableAddress,                 RetailP1RamAddress + 0x00010074
.definelabel AboutScreenAddress,                      RetailP1RamAddress + 0x00011ec4
.elseif AboutFirmware == 6
.definelabel AboutKeyLatchAddress,                    RetailP1RamAddress + 0x00004118
.definelabel AboutHeaderRenderFunction,               RetailP1RamAddress + 0x00002168
.definelabel AboutScreenTableAddress,                 RetailP1RamAddress + 0x000100c4
.definelabel AboutScreenAddress,                      RetailP1RamAddress + 0x00011f04
.elseif AboutFirmware == 7
.definelabel AboutKeyLatchAddress,                    RetailP1RamAddress + 0x00004118
.definelabel AboutHeaderRenderFunction,               RetailP1RamAddress + 0x00002168
.definelabel AboutScreenTableAddress,                 RetailP1RamAddress + 0x00010068
.definelabel AboutScreenAddress,                      RetailP1RamAddress + 0x00011c24
.else
    .error "About map: AboutFirmware must be 3, 5, 6 or 7"
.endif

; Shared: 0-based message ids, screen-table entry size, slide halfword.
.definelabel AboutDefaultMessage,                     0x0000007a
.definelabel AboutMessage,                            0x000000a3
.definelabel AboutSettingsRootScreen,                 0x0000000e
.definelabel AboutScreenEntrySize,                    0x0000000e
.definelabel AboutSettingsDescIdAddress,              AboutScreenTableAddress + AboutSettingsRootScreen * AboutScreenEntrySize + 4
.definelabel AboutScreenSlideOffset,                  0x00000004
.definelabel AboutKeyLatchResumeAddress,              AboutKeyLatchAddress + 8

; Free FP1 prefix bytes, the same in every package.
.definelabel AboutSelectPrevAddress,                  FlashMeFp1RamAddress + 0x00000260
.definelabel AboutKeyHookAddress,                     FlashMeFp1RamAddress + 0x00000280
