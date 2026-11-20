# Lab 02: assembly on the chip

## Goal
Write real functions in RISC-V assembly, call them from C, and run them on the C6. A test harness says PASS or
FAIL. Then step through your own instructions on the real CPU and watch its registers change.

## Read first
- The calling convention, at the top of `main/functions.S` (and the
  [RISC-V ABI document](https://github.com/riscv-non-isa/riscv-elf-psabi-doc/blob/master/riscv-cc.adoc), section
  "Integer Calling Convention", if you want the source).
- *The RISC-V Reader*, chapter 3 (assembly language), or Harris & Harris 6.4.6 (function calls).

## Do
1. Plug the board's **"USB"** port. Open this folder in "Visual Studio Code (on embedded)", flame button
   (or a terminal here: `idf`, then `idf.py build flash monitor`; Ctrl+] exits). Every test FAILs: good.
2. Write the TODOs in `main/functions.S`, one at a time. Flash after each one, until `15/15 passed`.
3. You can try a function in Ripes first (Lab 01), then paste it here.

## See: your instructions on the real CPU
1. In VS Code: put a breakpoint on the first line of `add3` in `functions.S`. Debug (ESP-IDF: "Launch Debug").
   Step over (F10) one instruction at a time. Variables panel → **Registers**: watch `a0`, `a1`, `a2`, `pc`, `ra`.
2. Same in a terminal, closer to the metal: `idf.py openocd gdbtui` (stop the VS Code debug session first). In GDB:
   ```
   source ../../tools/gdb-rom-fix.py    # once per session, else x/i shows ".word" (see the script)
   break add3
   continue
   layout split          # your source above, the instructions below
   tui reg general       # the registers
   stepi                 # one instruction; press Enter to repeat
   info registers pc ra
   finish                # run until add3 returns to main.c
   ```
3. The instructions as they ended up in flash, with addresses:
   `riscv32-esp-elf-objdump -d build/lab02_asm_on_chip.elf | grep -A12 '<add3>:'`. Compare with what you wrote:
   which ones did the assembler turn into 2-byte (compressed) instructions?

## Think
1. `ra` when you are inside `add3`: which address is it? Find it in `objdump` output for `app_main`: which
   instruction is just before it, and why does `ret` land exactly there?
2. Your function overwrote `t0` (or `a1`...) and `app_main` didn't break. Why? What would happen if you overwrote
   `s0` without restoring it?
3. `add3(2147483647, 1, 0)` returns a negative number. Why doesn't the CPU complain? (Look for an "overflow" flag
   in the RISC-V spec: is there one?)
4. `max2` with `blt` vs `bltu`: which test fails with the wrong one, and why?
5. Where in memory do your functions live (address range)? Flash or RAM? (Lab 12 explains it all.)

## Done when
- [ ] `15/15 passed` on the monitor.
- [ ] You stepped through `count_ones` with `stepi` and saw its loop counter change in the registers.
- [ ] Answers to *Think* at the bottom of this file. Committed.
