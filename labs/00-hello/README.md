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

## Think
1. Three programs ran before `app_main`. Which ones, and which one can you never change?
2. `build/` has an `.elf` and a `.bin`. Which one goes into flash, and what is the other one for?
3. `idf.py size` shows flash and RAM usage. How much of it is *your* code?
4. Why is `build/` in `.gitignore`?

## Done when
- [ ] Your own message prints on the monitor.
- [ ] You can point to the ROM, bootloader and app parts of the boot log.
- [ ] One commit pushed (`git push`).
