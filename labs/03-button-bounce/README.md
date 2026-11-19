# Lab 03: button bounce and a debouncing state machine

## Goal
See mechanical bounce on the analyzer, watch a naive counter get it wrong, then fix it with a state machine
whose output you can also see on the wire.

## Read first
- Roadmap: [State Machines](https://github.com/m3y54m/Embedded-Engineering-Roadmap#-state-machines),
  [GPIO](https://github.com/m3y54m/Embedded-Engineering-Roadmap#-gpio).
- Jack Ganssle, ["A Guide to Debouncing"](https://www.ganssle.com/debouncing.htm) (part 1 is enough).

## Wire
| Analyzer | C6 | What |
| --- | --- | --- |
| GND | G | first |
| CH4 | GPIO9 | the BOOT button itself |
| CH1 | GPIO19 | what the firmware read |
| CH2 | GPIO20 | debounced output |

KingstVIS: sample rate 10 MHz, trigger on **CH4 falling edge**. GPIO9 is a strapping pin: reading it is fine,
just don't hold BOOT while pressing RESET (that enters download mode).

## Do
1. TODO 1. Flash. Press BOOT a few times: capture, zoom in on the falling edge. Do you see bounce? Some buttons are
   quite clean; if yours is, touch a jumper wire from a **G** pin onto the GPIO9 pin instead of pressing BOOT:
   a wire bounces a lot.
2. Compare the "naive" count on the monitor with the number of presses you really made.
3. Draw your state machine, then TODO 2. Capture CH4, CH1, CH2 together: CH2 should change once per press,
   `STABLE_US` after the last bounce.

## Think
1. How long did the worst bounce you captured last? Is `STABLE_US = 5000` a good choice? Too long hurts how?
2. CH1 lags CH4 a little. By how much, and where does that time go?
3. Why is the debouncer a *state machine* and not just "wait 5 ms after an edge"? (What happens with a glitch while
   nothing is pressed?)
4. Polling every 50 µs keeps the CPU busy. What would let it sleep instead? (Phase 2: interrupts and timers.)

## Done when
- [ ] Screenshot `bounce.png` with CH4 (bounce), CH1 and CH2 (one clean edge).
- [ ] Naive count wrong, debounced count right, for 10 presses (write the numbers here).
- [ ] Your state diagram as `state-machine.png` (photo of paper is fine). Committed.
