.create "build/p3.bin", 0
    .headersize RetailP3RamAddress
    .incbin "temp/p3.bin"

; NOP the Logo gate; make the next two P3 verifier routines return success. See after .close.
    .org NintendoLogoStateGate
    .thumb
; Patch 1: replace the retained Nintendo Logo decision with no operation.
    nop

    .org RSA_verify
    .thumb
; Patch 2: make the first verifier report success before returning.
    mov r0, #1
    bx lr

    .org RSA_verify_with_SHA1
    .thumb
; Patch 3: make the second verifier report success before returning.
    mov r0, #1
    bx lr
.close

; Detailed analysis:
; 1. The first patched instruction is a NOP at the retained P3 Nintendo Logo decision point.
; 2. The second and third patched sites each load `r0 = 1` and return immediately, replacing their verifier bodies.
; 3. These changes affect this retained P3 GUI/verification path only. They should not be read as a general claim
;    that all NDS cartridge or network verification is disabled.
