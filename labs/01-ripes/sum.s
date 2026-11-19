# Lab 01: your first RISC-V program, in Ripes. Fill in the TODOs (see README.md).
# Comments start with '#'. Registers: x0..x31, also called by their ABI names (zero, ra, sp, a0..a7, t0..t6, s0..s11).

.data
numbers: .word 3, 1, 4, 1, 5, 9, 2, 6     # 8 words (4 bytes each) in memory
count:   .word 8
result1: .word 0                           # TODO 2 stores here
result2: .word 0                           # TODO 3 stores here

.text
main:
    # TODO 1: registers only. Put 7 in a0 and 5 in a1, then a0 = a0 + a1 - 2.
    #         Instructions: li (load immediate), add, addi (add an immediate; there is no "subi": add -2).
    #         Click "step" and watch the registers panel after each one.


    # TODO 2: a loop. Sum 1 + 2 + ... + 10 into t1, then store t1 into result1.
    #         You need: a counter register, addi, a branch (blt / bne / bge) back to a label, sw.
    #         la t0, result1   puts the address of result1 into t0; then  sw t1, 0(t0)  writes the word there.


    # TODO 3: memory. Sum the 8 words at 'numbers' (their count is at 'count') and store it into result2.
    #         lw t2, 0(t0) reads a word; the next word is 4 bytes further.


# ---- The test (don't change below): like nand2tetris' .tst/.cmp, it prints PASS or FAIL. ----
test:
    li   s0, 0                  # number of passes
    li   t3, 10                 # expected a0 (TODO 1)
    bne  a0, t3, test2
    addi s0, s0, 1
test2:
    la   t0, result1
    lw   t1, 0(t0)
    li   t3, 55                 # expected result1 (TODO 2)
    bne  t1, t3, test3
    addi s0, s0, 1
test3:
    la   t0, result2
    lw   t1, 0(t0)
    li   t3, 31                 # expected result2 (TODO 3)
    bne  t1, t3, report
    addi s0, s0, 1
report:
    mv   a0, s0                 # print "<passes>/3 passed"
    li   a7, 1                  # ecall 1: print the integer in a0
    ecall
    la   a0, msg
    li   a7, 4                  # ecall 4: print the string at a0
    ecall
    li   a7, 10                 # ecall 10: exit
    ecall

.data
msg: .string "/3 passed\n"
