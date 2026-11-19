# Lab 02: toggle as fast as possible (driver vs registers vs assembly)

## Goal
Measure how fast the CPU can toggle a pin, first through the ESP-IDF driver, then by writing the GPIO registers
directly. Then read the machine instructions the compiler produced and count them.

## Read first
- Roadmap: [Computer Architecture](https://github.com/m3y54m/Embedded-Engineering-Roadmap#-computer-architecture),
  [Assembly](https://github.com/m3y54m/Embedded-Engineering-Roadmap#-assembly).
- ESP32-C6 Technical Reference Manual, chapter "GPIO Matrix and IO MUX": the `GPIO_OUT_W1TS_REG` and
  `GPIO_OUT_W1TC_REG` registers (base `0x60091000`, offsets `0x8` and `0xC`).

## Wire
Same as Lab 01: GND, CH0 ↔ GPIO18. KingstVIS: **only CH0 enabled**, sample rate **500 MHz** (or the highest it offers
for one channel), trigger on CH0 rising edge.

## Do
1. TODO 1 only (leave TODO 2 empty). Flash, capture, zoom in: measure the **period of one toggle**. Frequency = 1/period.
2. TODO 2. Capture again: two bursts now, the driver one and the register one. Measure both.
3. Look at the instructions. In a terminal in this folder:
   `riscv32-esp-elf-objdump -d build/lab02_fast_toggle.elf | grep -A30 '<burst_with_registers>:'`
   Find the loop: the two store instructions (`sw`) and the branch back.
4. Optimization level: `idf.py menuconfig` → Compiler options → Optimization Level → `-O2` (performance). Rebuild,
   measure again, read the assembly again.

## Think
1. How many CPU cycles (at 160 MHz) does one register toggle take? Does it match the number of instructions in the loop?
2. Why is the driver slower? (Open `gpio_set_level` in ESP-IDF: `components/esp_driver_gpio/src/gpio.c`.)
3. Is the high time equal to the low time? If not, which instruction makes the difference?
4. Why does each burst end with `vTaskDelay(1)` instead of looping forever? (Remember Lab 01.)

## Done when
- [ ] Table in this README: driver vs registers, at the default optimization and at `-O2`, in MHz.
- [ ] You can point at the loop's instructions and explain each one.
- [ ] Committed.
