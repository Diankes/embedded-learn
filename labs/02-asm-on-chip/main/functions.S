# Lab 02: assembly functions the C6 runs. Fill in the TODOs (see README.md).
#
# The calling convention (the deal between caller and callee, same as C uses):
#   arguments arrive in a0, a1, a2, ...      the return value goes back in a0
#   ra holds the return address              `ret` jumps back to it
#   t0..t6 and a0..a7: yours to overwrite    s0..s11 and sp: restore them if you change them
# Every function below starts as a stub that returns 0, so the tests fail until you write it.

    .text                       # code goes in the code section

    .global add3                # make the name visible to main.c
    .type   add3, @function
# int add3(int a, int b, int c): return a + b + c
add3:
    # TODO 1
    li      a0, 0
    ret

    .global max2
    .type   max2, @function
# int max2(int a, int b): the larger one (signed)
max2:
    # TODO 2: a branch (blt / bge) and a label. Or, for a challenge: no branch at all.
    li      a0, 0
    ret

    .global sum_to
    .type   sum_to, @function
# int sum_to(int n): 1 + 2 + ... + n, and 0 when n <= 0. Your loop from Lab 01, now a function.
sum_to:
    # TODO 3
    li      a0, 0
    ret

    .global count_ones
    .type   count_ones, @function
# int count_ones(unsigned x): how many bits of x are 1 (count_ones(0b1011) = 3)
count_ones:
    # TODO 4: andi, srli, a loop.
    li      a0, 0
    ret
