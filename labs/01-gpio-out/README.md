# Lab 01: GPIO out, and what "wait 1 ms" really means

## Goal
Drive a pin, then **measure** its timing with the logic analyzer. Discover the RTOS tick, and that the code you
wrote and what the chip does are not always the same thing.

## Read first
- Roadmap: [GPIO](https://github.com/m3y54m/Embedded-Engineering-Roadmap#-gpio),
  [Logic / Protocol Analyzer](https://github.com/m3y54m/Embedded-Engineering-Roadmap#-logic--protocol-analyzer).
- ESP-IDF: [GPIO](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32c6/api-reference/peripherals/gpio.html).
- KingstVIS manual (`~/.local/opt/KingstVIS-3.6.6/Resource/ug-en.pdf` inside the env): "Connect the logic analyzer" and "Threshold voltage".

## Wire
| Analyzer | C6 |
| --- | --- |
| GND | G (first!) |
| CH0 | GPIO18 |

KingstVIS: threshold 1.65 V, sample rate 1 MHz, enough samples for ~3 s.

## Do
1. Finish TODO 1 and 2 in `main/main.c`. Flash. The monitor prints the tick rate.
2. In KingstVIS press start. Put two cursors on rising edges: measure the **period** and **duty cycle**.
3. Change `HALF_MS` to **15** and measure again. Then to **1**. Then to **10**. Write down each measured period.
4. With `HALF_MS = 1` wait ~5 s and read the monitor. Something complains: read the message carefully.

## Think
1. `HALF_MS = 15` did not give a 30 ms period. What did it give, and why? (Hint: the printed tick rate.)
2. What does `pdMS_TO_TICKS(1)` return here, what does `vTaskDelay` do with that value, and why does the
   *task watchdog* fire? Who is not getting CPU time?
3. How would you get a real 1 ms? (Name two ways; you will build one in Lab 05.)
4. The analyzer needs GND connected first. What could happen if it were connected last?

## Done when
- [ ] Measured period matches `2 * HALF_MS` for 500 ms, with a screenshot in this folder (`period.png`).
- [ ] You can explain the 15 ms and the 1 ms results in one sentence each (write them at the bottom of this file).
- [ ] Committed.
