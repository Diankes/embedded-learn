# Lab 00: hello (the tools)

## Goal
Build, flash and monitor a program, read what the chip prints while booting, and commit your work.

## Read first
- Roadmap: [Git](https://github.com/m3y54m/Embedded-Engineering-Roadmap#-git),
  [Compilers / GCC](https://github.com/m3y54m/Embedded-Engineering-Roadmap#-compilers--gcc),
  [Make / CMake](https://github.com/m3y54m/Embedded-Engineering-Roadmap#-make--cmake).
- ESP-IDF: [Build System](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32c6/api-guides/build-system.html) (skim: project vs component).

## Wire
Only the USB cable to the board's **"USB"** port. No analyzer yet.

## Do
1. Open `labs/00-hello` (this folder) in "Visual Studio Code (on embedded)".
2. Flame button (build, flash, monitor). Or in a terminal: `idf`, then `idf.py build flash monitor` (Ctrl+] exits).
3. Scroll up to the very first lines after reset and find: the ROM bootloader message (`ESP-ROM:`), the
   second-stage bootloader (`I (..) boot:`), the partition table, and `main_task: Calling app_main()`.
4. Change the message, flash again. Then make one commit: `git add -A && git commit -m "lab00: hello"`.
5. In a terminal: `ls build/*.bin build/*.elf` and `idf.py size`.

## Look inside: your C as the CPU sees it
1. In a terminal in this folder: `riscv32-esp-elf-objdump -d -S build/lab00_hello.elf | less`, then type
   `/<app_main>` and Enter. Each line of your C, with the instructions it became under it: address, the
   instruction's bytes (2 or 4), and the instruction. Don't try to understand them all yet: that's Part 1.
2. Find `addi sp,sp,-32` at the top of `app_main` and `jal ... <esp_chip_info>`. Guess what each does.
3. VS Code's Disassembly view shows `.word` for everything on this chip (a bug in its debug adapter: it can't
   decode 2-byte instructions). The terminal view in step 1 and GDB (Lab 02) show them correctly.

## Think
1. Three programs ran before `app_main`. Which ones, and which one can you never change?
2. `build/` has an `.elf` and a `.bin`. Which one goes into flash, and what is the other one for?
3. `idf.py size` shows flash and RAM usage. How much of it is *your* code?
4. Why is `build/` in `.gitignore`?
5. In the `objdump` output, the addresses of `app_main` start with `0x42...`. Some functions start with `0x408...`
   or `0x400...`. Three kinds of memory: guess which is which (Lab 12 answers).

## Done when
- [ ] Your own message prints on the monitor.
- [ ] You can point to the ROM, bootloader and app parts of the boot log.
- [ ] One commit pushed (`git push`).
