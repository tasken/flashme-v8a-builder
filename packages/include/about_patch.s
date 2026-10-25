.nds

; About stamp, run by about.mk after the package's patch step; edits build/fp1.bin.
.include "../../../include/common.inc"
.if AboutFirmware == 3
.include "../../../include/official_v3_sym.inc"
.elseif AboutFirmware == 5
.include "../../../include/official_v5_sym.inc"
.elseif AboutFirmware == 6
.include "../../../include/official_v6_sym.inc"
.elseif AboutFirmware == 7
.include "../../../include/official_v7_sym.inc"
.endif
.include "include/symbol.inc"
.include "../include/about_map.inc"

.open "build/fp1.bin", 0
    .headersize FlashMeFp1RamAddress

; Keypad hook in the free end of the FP1 prefix; Select swaps the Settings description message.
    .org AboutSelectPrevAddress
    .area FlashMeFp1RamAddress + FlashMePrefixBytes - AboutSelectPrevAddress, 0x00
    .db 0x00

; Redo the latch prologue, then detect a Select press edge.
    .org AboutKeyHookAddress
    .arm
about_key_hook:
    stmdb sp!, {r4, lr}
    sub sp, sp, #16
    ldr r12, =REG_KEYINPUT
    ldrh r12, [r12]
    tst r12, #KEY_SELECT
    movne r4, #0
    moveq r4, #1
    ldr r3, =AboutSelectPrevAddress
    ldrb r2, [r3]
    strb r4, [r3]
    cmp r2, #0
    bne about_key_done
    cmp r4, #0
    beq about_key_done
; Only on the Settings root (screen 14), after its slide-in.
    ldr r3, =AboutScreenAddress
    ldr r2, [r3]
    cmp r2, #AboutSettingsRootScreen
    bne about_key_done
    ldrh r2, [r3, #AboutScreenSlideOffset]
    cmp r2, #0
    bne about_key_done
; Swap the description message id.
    ldr r3, =AboutSettingsDescIdAddress
    ldrh r2, [r3]
    cmp r2, #AboutDefaultMessage
    moveq r2, #AboutMessage
    movne r2, #AboutDefaultMessage
    strh r2, [r3]
; Redraw the header text, as the Language page does.
    ldr r3, =AboutHeaderRenderFunction | 1
    blx r3
about_key_done:
    ldr r0, =REG_KEYINPUT
    ldrh r1, [r0]
    ldr r3, =AboutKeyLatchResumeAddress | 1
    bx r3
    .pool
    .endarea

; Jump from the keypad latch to the hook; the hook redoes the 8 overwritten bytes.
    .org AboutKeyLatchAddress
    .thumb
    ldr r3, [pc, #0]
    bx r3
    .word AboutKeyHookAddress
.close
