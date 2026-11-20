# Lab 01: your first RISC-V program (in Ripes)

## Goal
Write a few lines of RISC-V assembly and watch each instruction go through a processor: the registers it reads, the
ALU result, the memory it touches. No board today: this is the nand2tetris part, and the instructions are the same
ones the C6 runs.

## Read first
- *The RISC-V Reader*, chapter 2 (RV32I), or *Digital Design and Computer Architecture, RISC-V Edition*, 6.1–6.4.
- The [RISC-V reference card](https://github.com/jameslzhu/riscv-card): keep it open.
- In Ripes: Help → the "Getting started" pages (5 minutes).

## Setup
1. App menu → **Ripes (on embedded)**.
2. Processor (chip icon, top left) → **RISC-V 32-bit**, **5-stage processor** (try "w/o forwarding or hazard
   detection" later), and tick extensions **M** and **C**: the same RV32IMC as the C6 (the C6 also has A, atomics).
3. Editor tab → File → Load program → `labs/01-ripes/sum.s` (from this folder).

## Do
1. TODO 1. Processor tab: **step** (the arrow) one cycle at a time. Follow your `addi` from IF (fetch) to WB
   (write back). In which stage does the register panel change?
2. TODO 2. Run it (fast-forward). The console prints `n/3 passed`. Then step through the loop slowly: how many
   cycles per iteration? Look at the branch: what happens to the instructions behind it when it is taken?
3. TODO 3. Memory tab: find `numbers` and `result2`. Your `sw` changes them: watch.
4. Until the console says `3/3 passed`. Save your `sum.s` and commit.

## See
- Editor tab, right side: the **binary** of each instruction. Pick one `addi` and decode it by hand with the
  reference card (opcode, rd, rs1, imm). This is all the CPU ever sees.
- Tick the C extension on and off and reload: some instructions become 2 bytes (`c.addi`...). In your C6's
  `objdump` output, the instructions whose bytes column has only 2 bytes are these.

## Think
1. `li`, `la` and `mv` are not real instructions. What do they turn into (Editor tab, right side)? Why does `li`
   with a big number need two?
2. Why is there no "subtract immediate" instruction?
3. Register `x0` (`zero`): what is it for? Find three uses in the binary.
4. On the 5-stage processor without forwarding, the loop is slower. Which instruction waits for which, and why?
5. Count the cycles of the whole program, and the instructions executed (bottom panel: "Cycles", "Instrs. retired").
   Why aren't they equal?

## Done when
- [ ] `3/3 passed`.
- [ ] You decoded one instruction's 32 bits by hand (write it at the bottom of this file).
- [ ] Answers to *Think* at the bottom of this file. Committed.
