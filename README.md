# embedded-learn

My journey into embedded systems, from scratch, on real hardware. It follows the **required** topics of the
[Embedded Systems Engineering Roadmap](https://github.com/m3y54m/Embedded-Engineering-Roadmap)
([interactive map](https://m3y54m.github.io/Embedded-Engineering-Roadmap/)), and every lab is **seen on the wire**
with the Kingst LA5016 logic analyzer: if the code says something happened, the analyzer has to agree.

**How a lab works:** open its folder (`labs/NN-name`) in "Visual Studio Code (on embedded)", read its README,
write the code yourself (the `TODO`s), build-flash-monitor with the flame button, measure, answer the questions,
commit. Stuck? Ask Claude in that folder: it is set up as a tutor (hints first, see [CLAUDE.md](CLAUDE.md)).

## Hardware

| What | Notes |
| --- | --- |
| **ESP32-C6-DevKitC-1 v1.2** (main board) | RISC-V, 160 MHz, 8 MB flash. Use the **"USB"** port: flash, console and JTAG debugger on one cable (`/dev/ttyACM0`). |
| **Kingst LA5016** | 16 channels, up to 500 MS/s, decoders for UART/I2C/SPI and more, 2 PWM outputs (signal generator). Inputs tolerate ±50 V. |
| ESP32-S3-EYE, S3-LCD-EV-Board, S3-Korvo-1 | Phase 9: camera, display, audio. |
| Jumper wires (female-female) | Board header ↔ analyzer clips. A breadboard, LEDs, 330 Ω resistors, a button and a potentiometer help later. |

### Wiring convention (same in every lab)

| Analyzer | C6 header | Used for |
| --- | --- | --- |
| **GND** | any **G** pin | **Always first.** The analyzer shares ground with the laptop. |
| CH0 | GPIO18 (J3) | main output of the lab |
| CH1 | GPIO19 (J3) | second output / "what the firmware thinks" |
| CH2 | GPIO20 (J3) | |
| CH3 | GPIO21 (J3) | |
| CH4 | GPIO9 (J3) | BOOT button (input, Lab 03) |

GPIO18–23 sit next to each other on J3. **Avoid** GPIO4, 5, 8, 9, 15 as outputs (strapping pins: they choose the
boot mode), GPIO12/13 (USB) and GPIO16/17 (UART0 console). KingstVIS threshold: **1.65 V** (3.3 V logic).
Sample rate: at least 10x the fastest signal you want to see.

## The journey

Each phase lists the roadmap topics it covers. Tick a box when its "Done when" list is complete.

### Phase 0: Tools (Git, build, the analyzer)
- [ ] [00-hello](labs/00-hello): build, flash, monitor; read the boot log; your first commit. *Roadmap: Git, Compilers/GCC, Make/CMake.*

### Phase 1: GPIO and time
- [ ] [01-gpio-out](labs/01-gpio-out): drive a pin, measure the period. Why can't `vTaskDelay` wait 1 ms? *GPIO, RTOS ticks.*
- [ ] [02-fast-toggle](labs/02-fast-toggle): toggle as fast as possible: driver call vs direct register write, then read the assembly. *Computer Architecture, Assembly.*
- [ ] [03-button-bounce](labs/03-button-bounce): see a button bounce on the analyzer, then debounce it with a state machine. *GPIO input, State Machines.*

### Phase 2: Interrupts, timers, PWM, watchdog (labs written when you get here)
- [ ] 04-interrupt-latency: the analyzer's PWM output drives an input; an ISR answers on an output. Measure edge-to-edge latency. *Interrupts.*
- [ ] 05-hw-timer: a hardware timer (gptimer) toggles a pin. Compare its jitter with `vTaskDelay`. *Timers/Counters.*
- [ ] 06-pwm: LEDC: set frequency and duty, verify both on the analyzer, fade an LED. *PWM, Clock Management.*
- [ ] 07-watchdog: hang a task, watch the watchdog bite (log + a heartbeat pin going silent). *Watchdog.*

### Phase 3: Talking to other chips
- [ ] 08-uart: send bytes on UART1, decode them in KingstVIS; use a wrong baud rate on purpose; loopback. *UART.*
- [ ] 09-spi: SPI master, decode CLK/MOSI/MISO/CS; loopback MOSI→MISO; clock modes 0–3. *SPI.*
- [ ] 10-i2c: I2C scan: see address + NACK on every empty address; then a real device (S3 board as I2C slave, or a sensor). *I2C.*

### Phase 4: Analog
- [ ] 11-adc: read a voltage (potentiometer or divider), calibrate, compare with a multimeter. *ADC, Multimeter.* (The C6 has no DAC; PWM + RC filter instead.)

### Phase 5: Under the hood
- [ ] 12-memory-map: where code and variables live (`.text`, `.data`, `.bss`, flash vs RAM), `idf.py size`, the linker map. *Memory Management.*
- [ ] 13-gdb-jtag: debug over the built-in USB-JTAG: breakpoints, registers, step through Lab 02's register write. *JTAG, GDB.*
- [ ] 14-bare-registers: drive GPIO and a timer only through registers, from the Technical Reference Manual. *Computer Architecture.*

### Phase 6: RTOS
- [ ] 15-tasks-on-the-wire: each task toggles its own pin: watch the scheduler on the analyzer; priorities, queues, mutexes, priority inversion. *RTOS Basics.*

### Phase 7: DMA
- [ ] 16-dma: a large SPI transfer with DMA vs CPU: gaps on the clock line tell the story. *DMA.*

### Phase 8: Testing
- [ ] 17-unit-tests: test Lab 03's debouncer on the laptop (ESP-IDF `linux` target + Unity), test first. *TDD & Unit Testing.*

### Phase 9: The S3 boards (specializations)
- [ ] LCD-EV-Board: display + touch (I2C on the analyzer). *Display protocols, Embedded GUI.*
- [ ] Korvo-1: microphones and speaker over I2S (decode I2S in KingstVIS). *Digital audio protocols.*
- [ ] S3-EYE: camera + face detection (esp-who). *Camera protocols, Edge AI.*

**Alongside, at your own pace (theory):** C (K&R or "Modern C"), electric circuits and electronics fundamentals,
digital design: links are in the roadmap under each topic. Each lab README points to the ones it needs.

## Later (not now)

A "Microcorruption on real hardware" project: step through real firmware from reset, instruction by instruction,
seeing registers, memory and the pins at the same time. Phases 5 and 6 build the foundations for it.

## References

- Roadmap clone: `~/projects/references/Embedded-Engineering-Roadmap` (commit 4d6a18c).
- [ESP32-C6 Technical Reference Manual](https://www.espressif.com/sites/default/files/documentation/esp32-c6_technical_reference_manual_en.pdf) and [datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-c6_datasheet_en.pdf).
- [ESP-IDF v6.1 docs for ESP32-C6](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32c6/); local copy in `~/projects/espressif/esp-idf/docs/en`.
- Board guide: `~/projects/espressif/esp-dev-kits/docs/en/esp32-c6-devkitc-1/user_guide.rst`.
- KingstVIS manual: inside the env, `~/.local/opt/KingstVIS-3.6.6/Resource/ug-en.pdf`.
