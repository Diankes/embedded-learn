# embedded-learn

Learning embedded systems from the bottom up, on a real chip. The idea is
[nand2tetris](https://nand2tetris.github.io/web-ide/), but on silicon you can hold: the ESP32-C6, a **RISC-V** CPU.
You don't start by gluing library examples together: you start from the instructions the CPU runs, and climb until
you have written your own drivers, your own startup code and your own tiny operating system. Only then do you use
the vendor's.

Topics follow the required ones of the
[Embedded Systems Engineering Roadmap](https://github.com/m3y54m/Embedded-Engineering-Roadmap), in a different order.

## How every lab works (the nand2tetris loop)

| nand2tetris | here |
| --- | --- |
| You build a chip in HDL | You write a part: an assembly function, a driver, a boot routine |
| The simulator shows pins and registers | **Ripes** shows the CPU inside; **GDB** shows registers and memory of the real chip, one instruction at a time; the **logic analyzer** shows the pins |
| The `.tst` script compares with a `.cmp` file: green or red | Each lab has a test harness: the monitor prints `PASS` / `FAIL` per case, then `N/M passed` |
| Each project uses the previous ones | Same: Lab 05's GPIO driver is what Lab 08 uses, not ESP-IDF's |

Starter code always **builds and fails its tests**. Your job is to make it pass, then answer the README's *Think*
questions. Stuck? Ask Claude in this repo: it is set up as a tutor (hints first, see [CLAUDE.md](CLAUDE.md)).

## The three ways to see

1. **Inside the CPU (simulated): Ripes.** App menu → "Ripes (on embedded)". A RISC-V processor drawn as a datapath;
   each instruction moves through the pipeline as you click. The real C6 has a similar small in-order pipeline, but
   Espressif doesn't publish its insides, so this is where you see them.
2. **Inside the real chip: GDB.** Registers, memory, one instruction at a time. In a terminal in the lab folder:
   `idf`, then `idf.py openocd gdbtui`. In GDB: `source ../../tools/gdb-rom-fix.py` (once), `layout split` (source + instructions), `tui reg general`
   (registers), `stepi` (one instruction), `x/8xw 0x40800000` (memory). Or in VS Code: breakpoints work in `.S`
   files too, and the Variables panel shows registers.
   VS Code's *Disassembly view* (right-click in the source while stopped) works too: the labs' `launch.json` runs
   [`tools/gdb-rom-fix.py`](tools/gdb-rom-fix.py), without which it shows `.word` for your code (the script says why).
3. **The pins: the logic analyzer.** KingstVIS (on embedded), from Lab 05 on.

And the always-works view of what the compiler produced, in a terminal:
`riscv32-esp-elf-objdump -d -S build/<name>.elf | less` (your C, with its instructions under each line).

## Hardware

| What | Notes |
| --- | --- |
| **ESP32-C6-DevKitC-1 v1.2** | RISC-V RV32IMAC, 160 MHz, 8 MB flash. Use the **"USB"** port: flash, console and the JTAG debugger on one cable (`/dev/ttyACM0`). |
| **Kingst LA5016** | 16 channels, up to 500 MS/s, protocol decoders, 2 PWM outputs. Inputs tolerate ±50 V. |
| ESP32-S3-EYE, S3-LCD-EV-Board, S3-Korvo-1 | Part 7. Their CPU is **Xtensa**, a different instruction set: a good comparison by then. |

### Wiring convention (from Part 3 on)

| Analyzer | C6 header | Used for |
| --- | --- | --- |
| **GND** | any **G** pin | **Always first.** The analyzer shares ground with the laptop. |
| CH0–CH3 | GPIO18–21 (J3, side by side) | outputs of the lab |
| CH4 | GPIO9 (J3) | BOOT button (input) |

Never drive GPIO4, 5, 8, 9, 15 (strapping pins: they choose the boot mode), 12/13 (USB) or 16/17 (UART0 console).
KingstVIS threshold **1.65 V** (3.3 V logic); sample at least 10× faster than the signal.

## The journey

Tick a box when its lab's *Done when* list is complete. Labs are written when you reach them, so they build on what
you actually did.

### Part 0: Tools
- [ ] [00-hello](labs/00-hello): build, flash, monitor; read the boot log; first look at the instructions. *Git, GCC, CMake.*

### Part 1: The machine (the RISC-V instruction set)
- [ ] [01-ripes](labs/01-ripes): your first assembly program, in the simulator: registers, a loop, memory, the pipeline. *Computer Architecture, Assembly.*
- [ ] [02-asm-on-chip](labs/02-asm-on-chip): the same, as functions the real C6 runs, with a test harness; step them in GDB. *Calling convention.*
- [ ] [03-multiply](labs/03-multiply): multiply using only shifts and adds (no `mul`), then count the CPU cycles yours takes vs the hardware's.
- [ ] 04-memory: bytes, words, endianness, arrays and strings in assembly (`strlen`, `memcpy`); read memory with GDB and the hex editor.

### Part 2: From C to the machine
- [ ] 05-c-to-asm: predict the instructions for small C functions, then check with `objdump`: stack frames, `-O0` vs `-O2`, `volatile`, pointers.
- [ ] 06-a-pin-from-an-instruction: memory-mapped I/O: `stepi` the one `sw` that drives a pin high, and see it on the analyzer. *GPIO.*

### Part 3: Peripherals from the manual (no ESP-IDF drivers)
Each driver is written from the ESP32-C6 Technical Reference Manual (TRM), registers only, and checked on the wire.
- [ ] 07-gpio: output and input, IO MUX and GPIO matrix; a button, its bounce, and a debouncing state machine. *GPIO, State Machines.*
- [ ] 08-time: the system timer's registers; busy-wait delays measured on the analyzer; how fast can a pin toggle. *Timers, Clocks.*
- [ ] 09-uart: a UART driver from the TRM; decode your bytes in KingstVIS; a wrong baud rate on purpose. *UART.*
- [ ] 10-interrupts: the trap vector (`mtvec`), the interrupt matrix, your own handler; latency measured edge to edge. *Interrupts.*
- [ ] 11-timer-interrupt: a periodic interrupt; jitter on the analyzer; a watchdog. *Timers, Watchdog.*

### Part 4: Boot and bare metal
- [ ] 12-memory-map: where code and data live (flash, SRAM, `.text`, `.data`, `.bss`); the linker script and map file. *Memory Management.*
- [ ] 13-from-reset: follow the chip from reset to `app_main` in GDB: ROM, bootloader, startup code.
- [ ] 14-no-os: your own startup code and `main` without FreeRTOS, using only your Part 3 drivers.

### Part 5: Your own operating system
- [ ] 15-context-switch: two tasks and a scheduler you write, with the register save/restore in assembly; each task toggles a pin, so the analyzer shows the switching. *RTOS.*
- [ ] 16-freertos: now the real one: tasks, priorities, queues, mutexes, priority inversion, all on the wire; compare with yours. *RTOS Basics.*

### Part 6: More buses, analog, DMA, testing
- [ ] 17-spi, 18-i2c: from registers first, then ESP-IDF's driver; decode both in KingstVIS. *SPI, I2C.*
- [ ] 19-adc: read a voltage, calibrate, check with a multimeter. *ADC.*
- [ ] 20-dma: the same SPI transfer by the CPU and by DMA; gaps on the clock line tell the story. *DMA.*
- [ ] 21-unit-tests: test your debouncer and drivers on the laptop (ESP-IDF `linux` target + Unity). *TDD.*

### Part 7: The S3 boards (Xtensa)
- [ ] Compare: Lab 02's functions on Xtensa (`xtensa-esp32s3-elf-objdump`). Then display (LCD-EV), audio over I2S (Korvo-1), camera and face detection (S3-EYE). *Display, Audio, Edge AI.*

## Later (not now)

"Microcorruption on real hardware": step through real firmware from reset, find and exploit bugs on the chip,
seeing registers, memory and pins together. Parts 1, 2 and 4 are its foundations.

## Books and references

- *Digital Design and Computer Architecture, RISC-V Edition* (Harris & Harris): builds a RISC-V CPU from logic
  gates: the closest book to nand2tetris for this chip. Chapter 6 (architecture) fits Part 1, chapter 7
  (microarchitecture) is what Ripes animates.
- [The RISC-V Reader](http://www.riscvbook.com/) (Patterson & Waterman): short, the instruction set explained. Plus
  the [RISC-V reference card](https://github.com/jameslzhu/riscv-card).
- [RISC-V ABI: calling convention](https://github.com/riscv-non-isa/riscv-elf-psabi-doc/blob/master/riscv-cc.adoc)
  (which register holds what across a call).
- [ESP32-C6 Technical Reference Manual](https://www.espressif.com/sites/default/files/documentation/esp32-c6_technical_reference_manual_en.pdf)
  and [datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-c6_datasheet_en.pdf).
- [ESP-IDF v6.1 docs for ESP32-C6](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32c6/); the source is in
  the env at `~/.espressif/v6.1/esp-idf`.
- [Compiler Explorer](https://godbolt.org): C on the left, RISC-V instructions on the right (pick "RISC-V rv32gc gcc").
- KingstVIS manual: inside the env, `~/.local/opt/KingstVIS-3.6.6/Resource/ug-en.pdf`.
