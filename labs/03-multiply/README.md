# Lab 03: multiply with shifts and adds

## Goal
Multiplication is not magic: build it from the simplest instructions (shift, add, branch), the way a CPU without a
multiplier must. Then measure, in CPU cycles, what the C6's hardware multiplier saves you.

## Read first
- Binary long multiplication: Harris & Harris 5.2.6 (multiplication), or any "shift-and-add multiplication" page.
- *The RISC-V Reader*, chapter 4 (the M extension): why it is an *extension*, and not in the base set.

## Do
1. On paper: multiply 6 × 5 in binary (110 × 101), the long way. Each row is either 0 or a shifted copy of 110.
2. Write `mul_soft` in `main/multiply.S`. Hint: loop while b is not 0: if b's lowest bit is 1, add a to the result;
   then shift a left by 1 and b right by 1. Try it in Ripes first (with the M extension **unticked**, so you can't
   cheat).
3. Flash until `7/7 passed`. Then read the cycle table.

## See
- `stepi` through `mul_soft(6, 5)` in GDB (`idf.py openocd gdbtui`, `break mul_soft`, `continue`, `tui reg general`):
  watch a, b and the result change, iteration by iteration. It is the paper calculation from step 1.
- The cycle table on the monitor: plot (on paper) mul_soft cycles against the highest bit set in b.

## Think
1. b = 0x80000000 has one bit set, b = 0xFFFFFFFF has 32, and both have the highest bit set. Compare their cycles:
   what does mul_soft's time depend on, the number of 1 bits or the position of the highest one? Why?
2. How many cycles per loop iteration? Count your loop's instructions: do they match? Which instruction costs more
   than one cycle, and why? (Think of Lab 01's pipeline: what happens after a taken branch?)
3. mul_hw takes a few cycles *including the call*. Is the `mul` itself one cycle? How could you find out? (Hint:
   time an empty function the same way.)
4. Some RISC-V chips (RV32I only, like some tiny cores) have no multiplier. What does the C compiler do there when
   you write `a * b`? (Try it on [Compiler Explorer](https://godbolt.org) with `-march=rv32i -mabi=ilp32`: look for
   `__mulsi3`.)
5. Does your mul_soft work for signed numbers too (e.g. -3 × 4)? Why does that work with no change?

## Done when
- [ ] `7/7 passed`.
- [ ] The cycle table copied at the bottom of this file, explained in two sentences.
- [ ] Answers to *Think*. Committed.
